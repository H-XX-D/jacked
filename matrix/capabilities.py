"""Task-bound local module capabilities with workspace-scoped access."""

import json
from pathlib import Path
from uuid import uuid4

from matrix.cabinet import capsule_context
from matrix.integrations import (
    cramps_check, evidence_graph, export_content, integration_status, nexus_claim,
    project_context, project_skills, task_packet,
)
from matrix.process import run_program
from matrix.psyche import assess as psyche_assess
from matrix.tools import Capability, STRING, Tool
from matrix.workspace import digest


def task_capabilities(workspace, store, config, *, cancelled=None):
    capabilities = {}
    scope = config["workspace_identity"]

    def bind(name, description, arguments, call, *, advisory=False):
        capabilities[name] = Capability(
            Tool(description, dict.fromkeys(arguments, STRING), tuple(arguments)), call, advisory,
        )

    def history(query):
        if not 1 <= len(query.strip()) <= 200:
            raise ValueError("Provide a workspace history query up to 200 characters.")
        return {"tasks": store.search_context(workspace.root, scope, query.strip())}

    def scoped_task(task_id):
        task = store.get(task_id)
        if task["config"].get("workspace") != str(workspace.root) or task["config"].get("workspace_identity") != scope:
            raise ValueError("The task is outside the active workspace.")
        return task

    def evidence(task_id):
        task = scoped_task(task_id)
        receipts = store.receipts(task_id)
        packet = task_packet(task, receipts)
        return {
            "task_id": task_id, "status": packet["status"], "requirements": packet["requirements"],
            "graph": evidence_graph(packet), "receipts": receipts[:28],
        }

    bind("list_project_skills", "Discover the available project-local skills.", [],
         lambda: {"skills": project_skills(workspace.root)})
    bind("load_project_skill", "Read a project skill discovered with list_project_skills.", ["name"],
         lambda name: {"context": project_context(workspace.root, "", False, name, check_registry=False)})
    bind("get_module_status", "Inspect integrated module actions, configuration, and local dependencies.", [],
         lambda: integration_status(config, workspace))

    def export(task_id, format_name):
        extensions = {"json": "json", "graph": "graph.json", "gal": "gal", "aiwire": "aiwire",
                      "capsule": "auractx", "tablet": "auratab"}
        if format_name not in extensions:
            raise ValueError("Choose json, graph, gal, aiwire, capsule, or tablet.")
        task = scoped_task(task_id)
        content = export_content(task, store.receipts(task_id), format_name, store.directory)
        directory = store.directory / "exports"
        directory.mkdir(mode=0o700, exist_ok=True)
        path = directory / f"{task_id}-{uuid4().hex[:8]}.{extensions[format_name]}"
        try:
            with path.open("xb") as destination:
                destination.write(content)
            if digest(path.read_bytes()) != digest(content):
                raise RuntimeError("Task export readback did not match.")
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return {"path": str(path), "sha256": digest(content), "bytes": len(content), "format": format_name}

    if config.get("local_memory_requested"):
        bind("search_task_history", "Find prior completed tasks in the active workspace.", ["query"], history)
        bind("inspect_task_evidence", "Read recorded evidence for a task in the active workspace.", ["task_id"], evidence)
        bind("export_task_artifact", "Export workspace task evidence into the local task store.",
             ["task_id", "format_name"], export)
    if workspace.allow_execute:
        capabilities["run_local_program"] = Capability(Tool(
            "Run a local program from a JSON argument array in the workspace. The operator enabled host access. "
            "Use it for skill scripts, builds, and tests. Output and runtime are bounded.",
            {"argv_json": STRING, "timeout_seconds": {"type": "integer"}}, ("argv_json",),
        ), lambda argv_json, timeout_seconds=30: run_program(
            workspace, argv_json, timeout_seconds, cancelled=cancelled,
        ))
    if config.get("recall_requested"):
        def recall(query):
            if not 1 <= len(query.strip()) <= 500:
                raise ValueError("Provide a Recall query up to 500 characters.")
            return {"context": project_context(workspace.root, query, True, None)}
        bind("consult_recall", "Retrieve local Recall context for the active workspace.", ["query"], recall)
    if skill := config.get("skill"):
        bind("read_project_skill", "Read the user-selected project skill.", [],
             lambda: {"context": project_context(workspace.root, "", False, skill)})
    if path := config.get("capsule"):
        bind("read_context_capsule", "Read the user-selected Medicine Cabinet capsule.", [],
             lambda: {"context": capsule_context(path)})
    if url := config.get("nexus_url"):
        def assess(claim, evidence_json):
            if not 1 <= len(claim.strip()) <= 4_000 or len(evidence_json) > 16_000:
                raise ValueError("Nexus input exceeds the task limit.")
            evidence = json.loads(evidence_json)
            if not isinstance(evidence, dict):
                raise ValueError("Provide evidence as a JSON object.")
            return nexus_claim(url, claim, evidence)
        bind("assess_claim", "Get a local Nexus model assessment of the supplied claim and evidence.",
             ["claim", "evidence_json"], assess, advisory=True)
    if calibration := config.get("psyche_calibration"):
        bind("assess_inference_signals", "Assess a workspace inference-signal export using the operator's Psyche calibration.",
             ["path"], lambda path: psyche_assess(
                 workspace._path(path), config.get("psyche_architecture", "dolphin"), Path(calibration),
             ), advisory=True)
    if config.get("cramps_checkout") and workspace.allow_write:
        def check_study(path):
            package = (workspace.root / path).resolve(strict=True)
            if not package.is_dir() or not package.is_relative_to(workspace.root):
                raise ValueError("Choose a study package inside the workspace.")
            result = cramps_check(Path(config["cramps_checkout"]), package, "auto")
            return {**result, "ok": not bool(result["report"]["blockers"])}
        bind("check_study_package", "Run the configured local CRAMPS checker on a workspace study package. Writes study reports.",
             ["path"], check_study)
    return capabilities
