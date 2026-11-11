"""Connect the original Jarvis HUD to the same local task runner as the CLI."""

from dataclasses import asdict
from pathlib import Path
from queue import Queue
from threading import Event, Lock, Thread

from matrix.model import local_endpoint
from matrix.integrations import integration_status
from matrix.runtime import model_session
from matrix.speech import speak
from matrix.tasks import TaskStore


def launch_desktop(
    state, args, workspace, run, resolve_model, make_workspace, identity, criteria, build_config, *, face=None,
):
    try:
        from PyQt6.QtCore import QObject, pyqtSignal
        from ui import JarvisUI
        from matrix.desktop_controls import configure, task_menu
        from matrix.microphone import Microphone
    except ImportError as error:
        raise RuntimeError("Jarvis desktop requires PyQt6, Qt Multimedia, and psutil.") from error

    ui = JarvisUI(str(face or Path(__file__).resolve().parent.parent / "face.png"), local_mode=True)
    window = ui._win
    ui.set_state("INITIALISING")
    ui.write_log("SYS: Loading the local model…")
    prompts = Queue()
    closed = Event()
    interrupted = Event()
    worker_lock = Lock()
    worker = None
    attachments = []
    spec = None
    config = {
        "model": {"provider": args.provider or "auto", "timeout": args.timeout, "max_tokens": args.max_tokens},
        "workspace": str(workspace.root), "workspace_identity": identity(workspace),
        "write_requested": args.write, "local_memory_requested": True,
        "execute_requested": args.execute,
        "friday_memory_requested": args.friday_memory, "recall_requested": args.recall,
        "workflow_requested": args.workflow, "skill": args.skill, "max_rounds": args.max_rounds,
    }

    class AssessmentRelay(QObject):
        ready = pyqtSignal(str, str, str)
        initial = pyqtSignal(object, object)

    def initialize_settings(model, settings):
        nonlocal spec, config
        spec, config = model, settings
        mic.device_id = config.get("microphone_device", "")

    assessment_relay = AssessmentRelay(window)

    def attach_result(title, result, root):
        if str(workspace.root) == root:
            attachments.append({"source": title, "result": result[:3_000]})
            del attachments[:-3]
            ui.write_log(f"SYS: {title} attached to the next task.")

    assessment_relay.ready.connect(attach_result)
    assessment_relay.initial.connect(initialize_settings)

    def stop_worker():
        with worker_lock:
            if worker is not None and worker.poll() is None:
                try:
                    worker.terminate()
                except ProcessLookupError:
                    pass

    def track_worker(process):
        nonlocal worker
        with worker_lock:
            worker = process
        if closed.is_set():
            stop_worker()

    def apply_settings():
        nonlocal workspace, spec, config
        selected = configure(window, config)
        if selected is None:
            return
        root, args, updated = selected
        try:
            if not root:
                raise ValueError("Choose a workspace directory.")
            candidate = resolve_model(args, state)
            if candidate.provider == "zeta09" and updated["write_requested"]:
                raise ValueError("Zeta v0.9 supports text-only tasks.")
            next_workspace = make_workspace(root, state, updated["write_requested"], updated["execute_requested"])
            for key in ("capsule", "psyche_calibration", "cramps_checkout"):
                if updated[key]:
                    updated[key] = str(Path(updated[key]).expanduser().resolve(strict=True))
            if updated["nexus_url"]:
                local_endpoint(updated["nexus_url"])
            updated["requirements"] = criteria(args)
        except (OSError, ValueError) as error:
            ui.write_log(f"ERR: {error}")
            return
        updated.update(
            model=asdict(candidate), workspace=str(next_workspace.root),
            workspace_identity=identity(next_workspace),
        )
        changed = candidate != spec
        if next_workspace.root != workspace.root:
            attachments.clear()
        spec, workspace, config = candidate, next_workspace, updated
        mic.device_id = config.get("microphone_device", "")
        window._drop_zone.clear_file()
        if changed or window.hud.state == "SLEEPING":
            ui.set_state("INITIALISING")
            prompts.put(("model", candidate))
        ui.write_log(f"SYS: Harness settings applied · {workspace.root}")

    def submit(goal):
        selected = ui.current_file
        if selected:
            try:
                path = Path(selected).resolve(strict=True)
                relative = path.relative_to(workspace.root).as_posix()
                workspace.read_file(relative)
            except (OSError, ValueError):
                ui.write_log("SYS: Choose a supported text file inside the workspace.")
                return
            goal += f"\n\nSelected workspace file: {relative}"
        if len(goal) > 12_000:
            ui.write_log("SYS: Use a prompt up to 12,000 characters.")
            return
        interrupted.clear()
        ui.set_state("THINKING")
        settings = {**config, "attached_assessments": list(attachments)}
        attachments.clear()
        prompts.put(("task", workspace, settings, goal, None, not ui.muted))

    def resume(task_id):
        if window.hud.state != "LISTENING":
            ui.write_log("SYS: Wait for the current task before resuming another.")
            return
        store = TaskStore(state)
        try:
            task = store.get(task_id)
            saved = task["config"]
            if task["status"] == "completed":
                raise ValueError("That task is already completed.")
            restored = make_workspace(saved["workspace"], state)
            if identity(restored) != saved["workspace_identity"]:
                raise ValueError("The original workspace directory identity changed.")
        except (OSError, RuntimeError, ValueError) as error:
            ui.write_log(f"ERR: {error}")
            return
        finally:
            store.close()
        ui.write_log(f"SYS: Resuming {task_id} on the active model with read-only access.")
        interrupted.clear()
        ui.set_state("THINKING")
        prompts.put(("task", restored, saved, task["goal"], task_id, not ui.muted))

    def defer(title, action, *, attach=False):
        root = str(workspace.root)

        def execute():
            try:
                result = action()
                if not closed.is_set():
                    ui.show_content(title, result)
                    if attach:
                        assessment_relay.ready.emit(title, result, root)
            except (OSError, RuntimeError, ValueError, TypeError) as error:
                if not closed.is_set():
                    ui.write_log(f"ERR: {error}")
        Thread(target=execute, name="jacked-inspect", daemon=True).start()

    mic = Microphone(ui._app, window)

    def mic_state(state_name):
        labels = {
            "requesting": ("Waiting for permission…", "RECORDING"),
            "recording": ("Stop recording", "RECORDING"),
            "transcribing": ("Transcribing…", "TRANSCRIBING"),
            "idle": ("Record prompt", "LISTENING"),
        }
        label, status = labels[state_name]
        window._mic_btn.setText(label)
        ui.set_state(status)
        if state_name == "requesting":
            window._mic_btn.setEnabled(False)

    def show_transcript(text):
        window._input.setText(text)
        ui.write_log("SYS: Voice prompt transcribed locally. Press Enter to send.")

    def interrupt():
        if window.hud.state == "RECORDING" and mic.active:
            mic.reset()
            mic_state("idle")
            ui.write_log("SYS: Voice recording canceled.")
        if window.hud.state != "THINKING":
            return
        interrupted.set()
        ui.write_log("SYS: Stopping the active task…")
        stop_worker()

    def serve():
        store = None
        try:
            store = TaskStore(state)
            with store.exclusive_run():
                try:
                    active_spec = resolve_model(args, state)
                    if active_spec.provider == "zeta09" and args.write:
                        raise ValueError("Zeta v0.9 supports text-only tasks.")
                    assessment_relay.initial.emit(
                        active_spec, build_config(args, workspace, active_spec, [], memory=True),
                    )
                except (OSError, RuntimeError, ValueError) as error:
                    ui.write_log(f"ERR: {error}")
                    active_spec = None
                while not closed.is_set():
                    if active_spec is None:
                        ui.set_state("SLEEPING")
                        job = prompts.get()
                        if job is None:
                            return
                        active_spec = job[1]
                    try:
                        with model_session(active_spec, on_worker=track_worker) as model:
                            ui.write_log(f"SYS: Local model ready · {active_spec.provider}")
                            ui.set_state("LISTENING")
                            while not closed.is_set():
                                job = prompts.get()
                                if job is None:
                                    return
                                if job[0] == "model":
                                    active_spec = job[1]
                                    break
                                _, active_workspace, settings, goal, task_id, audio = job
                                recovery = None
                                if task_id is None:
                                    task_id = store.create(goal, settings)
                                else:
                                    recovery = [r for r in store.receipts(task_id) if r["tool"] == "write_file"]
                                try:
                                    answer, status = run(
                                        model, active_workspace, store, task_id, goal, settings, recovery,
                                        cancelled=interrupted,
                                    )
                                except (OSError, RuntimeError, ValueError) as error:
                                    if interrupted.is_set() or closed.is_set():
                                        store.finish(task_id, "interrupted", error="Interrupted in Jarvis.")
                                        break
                                    if store.get(task_id)["status"] in {"ready", "running"}:
                                        store.finish(task_id, "failed", error=str(error)[:1_000])
                                    ui.write_log(f"ERR: {error}")
                                else:
                                    if closed.is_set():
                                        return
                                    ui.write_log(f"{ui.assistant_name}: {answer}")
                                    receipts = store.receipts(task_id)
                                    counts = {kind: sum(r["status"] == kind for r in receipts)
                                              for kind in ("verified", "advisory", "failed")}
                                    evidence = " · ".join(f"{n} {kind}" for kind, n in counts.items() if n)
                                    if evidence:
                                        ui.write_log(f"SYS: Task {task_id} · {evidence}")
                                    ui.show_content(f"TASK {task_id} · {status.upper()}", answer)
                                    if audio and not interrupted.is_set():
                                        try:
                                            ui.set_state("SPEAKING")
                                            speak(answer)
                                        except (OSError, RuntimeError, ValueError) as error:
                                            ui.write_log(f"ERR: {error}")
                                if interrupted.is_set():
                                    break
                                ui.set_state("LISTENING")
                    except (OSError, RuntimeError, ValueError) as error:
                        if not closed.is_set():
                            ui.write_log(f"ERR: {error}")
                            active_spec = None
        except (OSError, RuntimeError, ValueError) as error:
            if not closed.is_set():
                ui.write_log(f"ERR: {error}")
                ui.set_state("SLEEPING")
        finally:
            if store is not None:
                store.close()

    mic.state.connect(mic_state)
    mic.transcript.connect(show_transcript)
    mic.message.connect(lambda text: ui.write_log(f"SYS: {text}"))
    window._mic_btn.clicked.connect(mic.toggle)
    window._harness_btn.clicked.connect(apply_settings)
    window._tasks_btn.setMenu(task_menu(
        window, window._tasks_btn, state, resume, ui.show_content, defer,
        lambda: integration_status(config, workspace),
    ))
    ui.on_text_command = submit
    ui.on_interrupt = interrupt
    thread = Thread(target=serve, name="jacked-local", daemon=True)
    thread.start()
    window.raise_()
    window.activateWindow()
    try:
        ui.root.mainloop()
    finally:
        closed.set()
        mic.reset()
        stop_worker()
        prompts.put(None)
        thread.join(timeout=6)
    return 0
