"""Run operator-enabled local programs with bounded capture and process cleanup."""

import json
import os
import signal
import subprocess
import time
from threading import Thread


def stop_process(process):
    if os.name == "nt":
        if process.poll() is None:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=10, check=False,
            )
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        except ProcessLookupError:
            pass
        # A program may exit while its children still hold the output pipe.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process.poll() is None:
        process.kill()
    process.wait(timeout=5)


def run_program(workspace, argv_json, timeout_seconds=30, *, cancelled=None):
    if not workspace.allow_execute:
        raise ValueError("Local programs are disabled for this session.")
    if len(argv_json) > 16_000 or not 1 <= timeout_seconds <= 120:
        raise ValueError("Use up to 16,000 argument characters and a timeout of 1–120 seconds.")
    argv = json.loads(argv_json)
    if not isinstance(argv, list) or not 1 <= len(argv) <= 64 or any(
        not isinstance(value, str) or not value or "\0" in value for value in argv
    ):
        raise ValueError("Provide a JSON array of nonempty program arguments.")
    if cancelled is not None and cancelled.is_set():
        raise InterruptedError("Task interrupted before the local program started.")

    options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    process = subprocess.Popen(
        argv, cwd=workspace.root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, **options,
    )
    captured = bytearray()
    received = 0

    def drain():
        nonlocal received
        while chunk := process.stdout.read(4096):
            received += len(chunk)
            captured.extend(chunk[:max(0, 24_000 - len(captured))])

    reader = Thread(target=drain, name="jacked-program-output", daemon=True)
    reader.start()
    started = time.monotonic()
    reason = None
    try:
        while process.poll() is None:
            if cancelled is not None and cancelled.is_set():
                reason = "interrupted"
                break
            if time.monotonic() - started >= timeout_seconds:
                reason = "timed out"
                break
            time.sleep(0.05)
    finally:
        stop_process(process)
        reader.join(timeout=2)
        process.stdout.close()
    if reason == "interrupted":
        raise InterruptedError("Local program interrupted.")
    return {
        "ok": process.returncode == 0 and reason is None, "argv": argv,
        "exit_code": process.returncode, "error": reason,
        "output": captured.decode("utf-8", errors="replace"),
        "output_bytes": received, "truncated": received > len(captured),
        "check": "Local process exit status", "elapsed_seconds": round(time.monotonic() - started, 2),
    }
