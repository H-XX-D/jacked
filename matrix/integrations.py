"""Optional adapters for installed project tools and local services."""

import json
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

from matrix.model import request_json


def integration_status(config, workspace):
    """Describe configured contracts and local dependencies without starting services."""
    def installed(name):
        try:
            return importlib.util.find_spec(name) is not None
        except (ImportError, ValueError):
            return False

    details = {
        "recall-memory-substrate": ("consult_recall", bool(shutil.which("recall")), bool(config.get("recall_requested"))),
        "AURA": ("AIWire task export", installed("aura_compression") or bool(os.environ.get("MATRIX_AURA_SOURCE")), True),
        "ephemeralskill": ("list_project_skills, load_project_skill", True, True),
        "aide": ("task reports, local program execution", True, workspace.allow_execute),
        "GAL.Graph_Abstraction_Layer": ("GAL export and verification", bool(shutil.which("gal")), True),
        "nexus-architecture": ("assess_claim", bool(config.get("nexus_url")), bool(config.get("nexus_url"))),
        "CRAMPACS-Governance": ("acceptance checks, check_study_package", True, True),
        "RRT-": ("typed task evidence graph", True, True),
        "ZetaZero": ("local zeta provider profile", True, config["model"]["provider"] == "zeta"),
        "zeta-zero-point-nine": ("local text-only zeta09 profile", True, config["model"]["provider"] == "zeta09"),
        "AI-Safety-System-Design": ("tool authorization, workspace checks, execution receipts", True, True),
        "psyche-v2": ("assess_inference_signals", installed("psyche"), bool(config.get("psyche_calibration"))),
        "Orkestra": ("plan, execute, review", True, bool(config.get("workflow_requested"))),
        "Medicine-Cabinet": ("capsule import, capsule and tablet export", True, True),
    }
    manifest = json.loads(Path(__file__).with_name("integrations.json").read_text(encoding="utf-8"))
    for item in manifest["repositories"]:
        action, dependency, enabled = details[item["name"]]
        item.update(action=action, local_dependency_available=dependency, enabled=enabled)
    manifest["workspace"] = str(workspace.root)
    manifest["service_health"] = "Local services and calibrations are validated when used."
    return manifest


def project_skills(workspace):
    """Discover project-local skill projections without importing executable code."""
    names = set()
    for adapter in (".agents", ".claude"):
        directory = workspace / adapter / "skills"
        if directory.is_dir() and directory.resolve().is_relative_to(workspace):
            names.update(path.name for path in directory.iterdir() if path.is_dir())
    available = []
    for name in sorted(names)[:100]:
        try:
            body = project_context(workspace, "", False, name, check_registry=False)
        except (OSError, ValueError):
            continue
        description = next((line.partition(":")[2].strip().strip('"\'')
                            for line in body.splitlines() if line.startswith("description:")), "")
        available.append({"name": name, "description": description[:300]})
    return available


def command(name, arguments, root, *, timeout=20):
    program = shutil.which(name)
    if program is None:
        raise ValueError(f"Install {name} to use this integration.")
    try:
        process = subprocess.run(
            [program, *arguments], cwd=root, capture_output=True, text=True,
            encoding="utf-8", timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"{name} timed out.") from error
    if process.returncode:
        detail = (process.stderr or process.stdout).strip()[:500]
        raise RuntimeError(f"{name} exited {process.returncode}: {detail}")
    return process.stdout


def project_context(workspace, goal, use_recall, skill, *, check_registry=True):
    sections = []
    if use_recall:
        packet = command("recall", ["compile", goal, "--words", "450"], workspace)
        sections.append("Recall context packet:\n" + packet[:6_000])
    if skill:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill) or len(skill) > 64:
            raise ValueError("Use an EphemeralSkill name containing lowercase words and hyphens.")
        if check_registry and shutil.which("esk") and (workspace / ".esk/project.json").is_file():
            registry = json.loads(command("esk", ["list", "--json"], workspace))
            if not any(entry["name"] == skill for entry in registry["project"]["skills"]):
                raise ValueError(f"EphemeralSkill is not available in this workspace: {skill}")
        copies = set()
        for adapter in (".agents", ".claude"):
            path = workspace / adapter / "skills" / skill / "SKILL.md"
            if not path.is_file():
                continue
            resolved = path.resolve()
            if not resolved.is_relative_to(workspace) or resolved.stat().st_size > 8_000:
                raise ValueError("Project skill resolves outside the workspace or exceeds 8 KB.")
            body = resolved.read_text(encoding="utf-8")
            if not body.startswith("---\n") or f"\nname: {skill}\n" not in body.partition("\n---\n")[0] + "\n":
                raise ValueError(f"Project skill metadata does not identify {skill}.")
            copies.add(body)
        if len(copies) != 1:
            raise ValueError("The selected skill is missing or its project projections differ.")
        sections.append("Selected project skill:\n" + copies.pop())
    return "\n\n".join(sections)


def nexus_claim(url, claim, evidence):
    if not isinstance(evidence, dict) or not 1 <= len(claim.strip()) <= 4_000:
        raise ValueError("Supply a claim and a JSON evidence object.")
    key = os.environ.get("NEXUS_API_KEY")
    headers = {"X-API-Key": key} if key else None
    result = request_json(
        url, "POST", "/api/verify", {"claim": claim, "evidence": evidence}, headers=headers
    )
    if not isinstance(result, dict) or result.get("label") not in {
        "SUPPORTS", "REFUTES", "NOT_ENOUGH_INFO"
    }:
        raise RuntimeError("Nexus returned an unrecognized assessment.")
    confidence = result.get("confidence")
    if type(confidence) not in {float, int} or not 0 <= confidence <= 1:
        raise RuntimeError("Nexus returned an invalid confidence.")
    return {
        "schema": "jacked.claim-assessment.v1",
        "assessment": result["label"],
        "model_confidence": confidence,
        "verification": "model_assessment",
    }


def cramps_check(checkout, package, level):
    checkout = checkout.expanduser().resolve(strict=True)
    package = package.expanduser().resolve(strict=True)
    script = checkout / "tools" / "cramps_cli.py"
    if not script.is_file() or not package.is_dir():
        raise ValueError("Choose a CRAMPS checkout and an existing study package.")
    report = json.loads(command(
        sys.executable, [str(script), "check", str(package), "--level", level],
        checkout, timeout=60,
    ))
    if not isinstance(report, dict) or not {"blockers", "package_sha256"} <= report.keys():
        raise RuntimeError("CRAMPS returned an invalid package report.")
    return {"schema": "jacked.cramps-check.v1", "report": report}


def task_packet(task, receipts):
    config = task["config"]
    return {
        "schema": "jacked.task.v1",
        "id": task["id"],
        "status": task["status"],
        "attempt": task["attempt"],
        "goal": task["goal"],
        "model_answer": task["answer"],
        "error": task["error"],
        "updated_at": task["updated_at"],
        "requirements": config.get("requirements", []),
        "receipts": receipts,
    }


def export_aiwire(packet):
    source = os.environ.get("MATRIX_AURA_SOURCE")
    if source and source not in sys.path:
        sys.path.append(source)
    try:
        from aura_compression.aiwire import AIWireSessionDecoder, AIWireSessionEncoder
    except ImportError as error:
        raise ValueError("Install AURA's aura-compression package to export AIWire.") from error
    encoder, decoder = AIWireSessionEncoder(), AIWireSessionDecoder()
    try:
        frame = encoder.compress_message(packet)
        if decoder.decompress_message(frame) != packet:
            raise RuntimeError("AURA export failed a round-trip comparison.")
        return frame
    finally:
        encoder.close()
        decoder.close()


def evidence_graph(packet):
    task_id = "task_" + packet["id"]
    nodes = [{"id": task_id, "kind": "task", "status": packet["status"]}]
    edges = []
    for number, receipt in enumerate(packet["receipts"], 1):
        target = f"receipt_{number}"
        status = receipt["status"]
        relation = {"verified": "supports", "advisory": "advises", "started": "pending"}.get(status, "concerns")
        nodes.append({"id": target, "kind": "receipt", "tool": receipt["tool"], "status": status})
        edges.append({"from": target, "to": task_id, "relation": relation})
    return {"schema": "jacked.evidence-graph.v1", "nodes": nodes, "edges": edges}


def export_gal(packet, state):
    # A typed graph of what ran and what was observed. Model prose is never supporting evidence.
    lines = ["@gal netlist.v0", "@dialect mal.v0", ""]
    root = "task_" + packet["id"]
    lines.extend([f'{root} "Task {packet["id"]} ({packet["status"]})" [kind: claim]', ""])
    for number, receipt in enumerate(packet["receipts"], 1):
        target = f"receipt_{number}"
        relation = "supports" if receipt["status"] == "verified" else "concerns"
        title = json.dumps(f'{receipt["tool"][:72]} ({receipt["status"]})', ensure_ascii=False)
        lines.append(f"{target} {title} [kind: obs]")
        if receipt["status"] != "advisory":
            lines.append(f"{relation}> {root}(1.0)")
        lines.append("")
    document = "\n".join(lines)
    with NamedTemporaryFile(dir=state, suffix=".mal.gal", delete=False) as temp:
        temp.write(document.encode("utf-8"))
    path = Path(temp.name)
    try:
        report = json.loads(command("gal", ["verify", str(path), "--json"], state))
        if report.get("ok") is not True:
            raise RuntimeError("GAL did not verify the task graph.")
    finally:
        path.unlink(missing_ok=True)
    return document


def export_content(task, receipts, format_name, state):
    from matrix.cabinet import capsule, tablet

    packet = task_packet(task, receipts)
    if format_name == "capsule":
        return capsule(packet, Path(task["config"].get("workspace", "workspace")).name or "workspace")
    if format_name == "tablet":
        return tablet(packet)
    if format_name == "aiwire":
        return export_aiwire(packet)
    if format_name == "gal":
        return export_gal(packet, state).encode("utf-8")
    if format_name == "graph":
        packet = evidence_graph(packet)
    return (json.dumps(packet, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
