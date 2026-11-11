"""Run MATRIX with python -m matrix."""

import argparse
import json
import os
import re
import sqlite3
import sys
from dataclasses import asdict
from pathlib import Path

from matrix.cabinet import capsule_context
from matrix.engine import run_task
from matrix.capabilities import task_capabilities
from matrix.integrations import (
    cramps_check, export_content, nexus_claim, project_context, task_packet,
)
from matrix.psyche import assess
from matrix.runtime import MANAGED_PROVIDERS, ModelSpec, model_session, select_weights
from matrix.speech import speak, transcribe
from matrix.tasks import TaskStore
from matrix.workspace import Workspace
from memory.config_manager import load_api_keys
from memory.memory_manager import format_memory_for_prompt, load_memory

DEFAULTS = {
    "ollama": ("http://127.0.0.1:11434", "llama3.2"),
    "openai": ("http://127.0.0.1:1234", "local-model"),
    "zeta": ("http://127.0.0.1:8080", "zeta-cognitive"),
    "zeta09": ("http://127.0.0.1:8080", "zeta-0.9"),
}


def parser():
    cli = argparse.ArgumentParser(description="Local-first MATRIX task harness for FRIDAY")
    cli.add_argument(
        "--state-dir", type=Path, default=Path(os.environ.get("MATRIX_STATE_DIR", Path.home() / ".jacked")),
        help="Private task database and backups directory",
    )
    commands = cli.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Start a workspace task")
    run.add_argument("goal", nargs="?", help="Task prompt")
    run.add_argument("--audio", type=Path, help="Transcribe a local PCM WAV as the task prompt")
    run.add_argument("--speech-out", type=Path, help="Save the spoken answer as a new WAV")
    run.add_argument("--memory", action="store_true", help="Include recent completed tasks from this workspace")
    chat = commands.add_parser("chat", help="Start an interactive local terminal session")
    desktop = commands.add_parser("desktop", help="Open the original Jarvis interface with the local model")
    desktop.add_argument("--face", type=Path, help="Optional local HUD portrait")
    desktop.add_argument("--microphone", default="", help="Qt input device ID in hexadecimal, or automatic selection")
    for command in (run, chat, desktop):
        command.add_argument("--workspace", type=Path, default=Path.cwd())
        command.add_argument("--write", action="store_true", help="Allow guarded text file edits for this session")
        command.add_argument("--execute", action="store_true", help="Allow local programs with host access for this session")
        command.add_argument("--friday-memory", action="store_true", help="Include FRIDAY memory as local context")
        command.add_argument("--recall", action="store_true", help="Compile local Recall context")
        command.add_argument("--skill", help="Load a selected local project skill")
        command.add_argument("--capsule", type=Path, help="Include a local Medicine Cabinet capsule")
        command.add_argument("--nexus-url", help="Enable the local Nexus claim assessment tool")
        command.add_argument("--psyche-calibration", type=Path, help="Enable Psyche with this local calibration")
        command.add_argument("--psyche-architecture", default="dolphin", help="Psyche architecture preset or descriptor")
        command.add_argument("--cramps-checkout", type=Path, help="Trusted local CRAMPS source checkout")
        command.add_argument("--max-rounds", type=int, default=8, help="Task tool-round limit")
        command.add_argument("--workflow", action="store_true", help="Run local plan, execution, and review stages")
        command.add_argument("--speak", action="store_true", help="Speak answers with the local speech engine")
    run.add_argument("--require-python", action="append", default=[], metavar="PATH")
    run.add_argument("--require-sha256", action="append", default=[], metavar="PATH=SHA256")
    run.add_argument("--json", action="store_true", help="Emit a versioned task report for terminal integrations")
    doctor = commands.add_parser("doctor", help="Check the model server and list its models")
    for command in (run, chat, desktop, doctor):
        command.add_argument("--provider", choices=["auto", "mlx", "llamacpp", *DEFAULTS])
        command.add_argument("--weights", type=Path, help="Existing MLX directory or GGUF file")
        command.add_argument("--url", help="Loopback model server URL")
        command.add_argument("--model", help="Model identifier from the server")
        command.add_argument("--timeout", type=int, default=120)
        command.add_argument("--max-tokens", type=int, default=700)
    commands.add_parser("tasks", help="List recent local tasks")
    show = commands.add_parser("show", help="Show a task and its verification receipts")
    show.add_argument("id")
    resume = commands.add_parser("resume", help="Retry an unfinished task with read-only access")
    resume.add_argument("id")
    export = commands.add_parser("export", help="Export a task packet to JSON, GAL or AURA AIWire")
    export.add_argument("id")
    export.add_argument("--format", choices=["json", "graph", "gal", "aiwire", "capsule", "tablet"], default="json")
    export.add_argument("--output", type=Path, help="Write to a new file")
    claim = commands.add_parser("check-claim", help="Get a model assessment from a local Nexus service")
    claim.add_argument("claim")
    claim.add_argument("--url", required=True)
    claim.add_argument("--evidence", default="{}", help="Explicit JSON object to include in the request")
    cramps = commands.add_parser("cramps-check", help="Run the upstream CRAMPS study package check")
    cramps.add_argument("checkout", type=Path, help="Existing CRAMPS source checkout")
    cramps.add_argument("package", type=Path, help="Study package where CRAMPS writes its reports")
    cramps.add_argument("--level", choices=["auto", "preflight", "full"], default="auto")
    transcribe_cmd = commands.add_parser("transcribe", help="Transcribe a local PCM WAV")
    transcribe_cmd.add_argument("audio", type=Path)
    speak_cmd = commands.add_parser("speak", help="Synthesize speech using the local OS engine")
    speak_cmd.add_argument("text")
    speak_cmd.add_argument("--output", type=Path, help="Save a new WAV instead of playing it")
    psyche = commands.add_parser("psyche", help="Assess real local inference signals with Psyche v2")
    psyche.add_argument("signals", type=Path)
    psyche.add_argument("--architecture", required=True)
    psyche.add_argument("--calibration", type=Path, required=True)
    commands.add_parser("integrations", help="List inspected upstream revisions and adapter roles")
    return cli


def model_spec(args, state):
    provider = args.provider or os.environ.get("MATRIX_PROVIDER")
    select_managed = bool(args.weights) or args.provider in {"auto", *MANAGED_PROVIDERS}
    url = args.url or (None if select_managed else os.environ.get("MATRIX_URL"))
    model = args.model or (None if select_managed else os.environ.get("MATRIX_MODEL"))
    configured_weights = args.weights or (None if args.provider in DEFAULTS else os.environ.get("MATRIX_WEIGHTS"))
    if args.weights and args.provider is None:
        provider = "auto"
    config = {}
    if not provider:
        if configured_weights:
            provider = "auto"
        elif url or model:
            config = load_api_keys()
            provider = str(config.get("llm_provider", "ollama")).strip().lower()
            if provider == "llamacpp":
                provider = "openai"
        else:
            provider = "auto"
    if provider in {"lmstudio", "localai", "jan"}:
        provider = "openai"
    if provider == "auto" or provider in MANAGED_PROVIDERS:
        if url or model:
            raise ValueError("Choose an explicit existing-server provider when setting a URL or model ID.")
        provider, weights = select_weights(provider, configured_weights, state)
        return ModelSpec(provider, timeout=args.timeout, weights=str(weights), max_tokens=args.max_tokens)
    if provider not in DEFAULTS or configured_weights:
        raise ValueError("Choose a supported provider and matching local model settings.")
    default_url, default_model = DEFAULTS[provider]
    return ModelSpec(
        provider,
        url or config.get("llm_url") or default_url,
        model or config.get("llm_model") or default_model,
        args.timeout, max_tokens=args.max_tokens,
    )


def workspace_at(root, state, allow_write=False, allow_execute=False):
    workspace = Workspace(root, state / "backups", allow_write, allow_execute)
    if state.is_relative_to(workspace.root):
        parts = state.relative_to(workspace.root).parts
        if not parts or not parts[0].startswith("."):
            raise ValueError("Keep the task database outside the workspace or in a hidden directory.")
    return workspace


def identity(workspace):
    entry = workspace.root.stat()
    return [entry.st_dev, entry.st_ino]


def dump(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def acceptance_criteria(args):
    criteria = [{"check": "python", "path": path} for path in args.require_python]
    for specification in args.require_sha256:
        path, _, expected = specification.rpartition("=")
        if not path or not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
            raise ValueError("Use --require-sha256 PATH=SHA256.")
        criteria.append({"check": "sha256", "path": path, "sha256": expected.lower()})
    if len(criteria) > 20:
        raise ValueError("Set at most 20 acceptance checks per task.")
    return criteria


def task_config(args, workspace, spec, requirements, *, memory):
    if not 1 <= args.max_rounds <= 64:
        raise ValueError("Choose between 1 and 64 tool rounds.")
    if args.nexus_url:
        from matrix.model import local_endpoint

        local_endpoint(args.nexus_url)
    return {
        "model": asdict(spec), "workspace": str(workspace.root),
        "workspace_identity": identity(workspace), "write_requested": args.write,
        "execute_requested": args.execute,
        "friday_memory_requested": args.friday_memory,
        "recall_requested": args.recall, "skill": args.skill,
        "local_memory_requested": memory, "workflow_requested": args.workflow,
        "capsule": str(args.capsule.expanduser().resolve(strict=True)) if args.capsule else None,
        "nexus_url": args.nexus_url, "max_rounds": args.max_rounds,
        "psyche_calibration": str(args.psyche_calibration.expanduser().resolve(strict=True)) if args.psyche_calibration else None,
        "psyche_architecture": args.psyche_architecture,
        "cramps_checkout": str(args.cramps_checkout.expanduser().resolve(strict=True)) if args.cramps_checkout else None,
        "microphone_device": getattr(args, "microphone", ""),
        "requirements": requirements,
    }


def perform_task(model, workspace, store, task_id, goal, config, recovery=None, *, cancelled=None):
    print(f"Task {task_id}", file=sys.stderr, flush=True)
    context = project_context(workspace.root, goal, config.get("recall_requested"), config.get("skill"))
    sections = [context] if context else []
    if config.get("friday_memory_requested"):
        sections.append(format_memory_for_prompt(load_memory())[:2_200])
    if config.get("capsule"):
        sections.append(capsule_context(config["capsule"]))
    if config.get("attached_assessments"):
        sections.append("Operator-attached assessments (reference data):\n" + json.dumps(
            config["attached_assessments"], ensure_ascii=False
        )[:8_000])
    if config.get("local_memory_requested"):
        recent = store.recent_context(workspace.root, config["workspace_identity"])
        if recent:
            sections.append("Recent completed workspace tasks (historical data):\n" + json.dumps(recent, ensure_ascii=False))
    return run_task(
        model, workspace, store, task_id, goal, recovery,
        "\n\n".join(sections), config.get("requirements", []),
        workflow=config.get("workflow_requested", False),
        max_rounds=config.get("max_rounds", 8),
        capabilities=task_capabilities(workspace, store, config, cancelled=cancelled), cancelled=cancelled,
    )


def checked_goal(goal):
    goal = goal.strip()
    if not 1 <= len(goal) <= 12_000:
        raise ValueError("Provide a task prompt of 1–12,000 characters.")
    return goal


def interactive(model, workspace, store, config, speech):
    if sys.stdin.isatty():
        mode = "guarded writes" if workspace.allow_write else "read-only"
        print(f"Jacked · {mode} · type /quit to exit")
    while True:
        try:
            goal = input("You > " if sys.stdin.isatty() else "").strip()
        except EOFError:
            return 0
        if goal == "/quit":
            return 0
        if not goal:
            continue
        try:
            goal = checked_goal(goal)
            task_id = store.create(goal, config)
            answer, _ = perform_task(model, workspace, store, task_id, goal, config)
            print(answer, flush=True)
            if speech:
                speak(answer)
        except (OSError, RuntimeError, ValueError) as error:
            print(f"MATRIX: {error}", file=sys.stderr)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    args = parser().parse_args(argv or ["chat"])
    os.umask(0o077)
    state = args.state_dir.expanduser().resolve()
    store = None
    task_id = None
    try:
        if args.command == "transcribe":
            print(transcribe(args.audio))
            return 0
        if args.command == "speak":
            speak(args.text, args.output)
            return 0
        if args.command == "psyche":
            dump(assess(args.signals, args.architecture, args.calibration))
            return 0
        if args.command == "integrations":
            print(Path(__file__).with_name("integrations.json").read_text(encoding="utf-8"), end="")
            return 0
        if args.command == "check-claim":
            if not 1 <= len(args.claim.strip()) <= 4_000 or len(args.evidence) > 16_000:
                raise ValueError("Provide a claim and a bounded evidence object.")
            evidence = json.loads(args.evidence)
            if not isinstance(evidence, dict):
                raise ValueError("Claim evidence must be a JSON object.")
            dump(nexus_claim(args.url, args.claim, evidence))
            return 0
        if args.command == "cramps-check":
            report = cramps_check(args.checkout, args.package, args.level)
            dump(report)
            return 2 if report["report"]["blockers"] else 0
        if args.command == "doctor":
            spec = model_spec(args, state)
            with model_session(spec) as model:
                dump({
                    "provider": spec.provider, "managed": bool(spec.weights),
                    "weights": spec.weights or None, "url": spec.url or None,
                    "models": model.models(),
                })
            return 0

        if args.command == "desktop":
            from matrix.desktop import launch_desktop

            workspace = workspace_at(args.workspace, state, args.write, args.execute)
            return launch_desktop(
                state, args, workspace, perform_task, model_spec, workspace_at, identity,
                acceptance_criteria, task_config, face=args.face,
            )
        if args.command in {"run", "chat"}:
            spec = model_spec(args, state)
            if spec.provider == "zeta09" and args.write:
                raise ValueError("Zeta v0.9 supports text-only tasks.")
            workspace = workspace_at(args.workspace, state, args.write, args.execute)
        if args.command == "run":
            if bool(args.goal) == bool(args.audio):
                raise ValueError("Supply either a text prompt or --audio.")
            goal = checked_goal(transcribe(args.audio) if args.audio else args.goal)

        store = TaskStore(state)
        if args.command == "tasks":
            dump(store.list())
            return 0
        if args.command == "show":
            dump({**store.get(args.id), "receipts": store.receipts(args.id)})
            return 0

        if args.command == "export":
            content = export_content(store.get(args.id), store.receipts(args.id), args.format, state)
            if args.output:
                with args.output.expanduser().open("xb") as output:
                    output.write(content)
            else:
                sys.stdout.buffer.write(content)
            return 0

        with store.exclusive_run():
            recovery = None
            if args.command == "chat":
                config = task_config(args, workspace, spec, [], memory=True)
                with model_session(spec) as model:
                    return interactive(model, workspace, store, config, args.speak)
            if args.command == "run":
                config = task_config(args, workspace, spec, acceptance_criteria(args), memory=args.memory)
                task_id = store.create(goal, config)
            else:
                task_id = args.id
                task = store.get(task_id)
                if task["status"] == "completed":
                    raise ValueError("Task is already completed. Start a new task to continue.")
                config = task["config"]
                workspace = workspace_at(config["workspace"], state)
                if identity(workspace) != config["workspace_identity"]:
                    raise ValueError("The original workspace directory identity changed.")
                spec = ModelSpec(**config["model"])
                goal = task["goal"]
                recovery = [receipt for receipt in store.receipts(task_id) if receipt["tool"] == "write_file"]

            with model_session(spec) as model:
                answer, status = perform_task(model, workspace, store, task_id, goal, config, recovery)
            if getattr(args, "json", False):
                dump(task_packet(store.get(task_id), store.receipts(task_id)))
            else:
                print(answer, flush=True)
                if status == "needs_review":
                    print("Acceptance checks failed. Inspect this task with show.", file=sys.stderr)
            if getattr(args, "speak", False) or getattr(args, "speech_out", None):
                speak(answer, args.speech_out)
        return 2 if status == "needs_review" else 0
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except (OSError, RuntimeError, ValueError, sqlite3.Error) as error:
        if store is not None and task_id is not None:
            try:
                if store.get(task_id)["status"] in {"ready", "running"}:
                    store.finish(task_id, "failed", error=str(error)[:1_000])
            except (OSError, ValueError, sqlite3.Error):
                pass
        print(f"MATRIX: {error}", file=sys.stderr)
        return 1
    finally:
        if store is not None:
            store.close()


if __name__ == "__main__":
    sys.exit(main())
