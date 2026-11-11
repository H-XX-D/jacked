"""Find and run model weights already present on the machine."""

import os
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryFile

from matrix.model import LocalModel, request_json

CACHED_MLX = "models--mlx-community--Qwen2.5-7B-Instruct-4bit"
MANAGED_PROVIDERS = {"mlx", "llamacpp"}
OFFLINE_ENV = {
    "HF_HUB_OFFLINE": "1",
    "HF_DATASETS_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "HF_HUB_DISABLE_TELEMETRY": "1",
    "DO_NOT_TRACK": "1",
}


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    url: str = ""
    model: str = ""
    timeout: int = 120
    weights: str = ""
    max_tokens: int = 700

    def __post_init__(self):
        if self.provider in MANAGED_PROVIDERS:
            if not self.weights or self.url or self.model:
                raise ValueError("Managed models use local --weights. A URL and model ID select an existing server.")
            if not 1 <= self.timeout <= 600:
                raise ValueError("Set a timeout between 1 and 600 seconds.")
            if not 128 <= self.max_tokens <= 32_768:
                raise ValueError("Set a model output limit between 128 and 32768 tokens.")
        else:
            if self.weights:
                raise ValueError("Use --provider mlx or llamacpp to open local weights.")
            LocalModel(self.provider, self.url, self.model, self.timeout, self.max_tokens)


def mlx_weights(path):
    return (
        path.is_dir() and (path / "config.json").is_file()
        and (path / "tokenizer.json").is_file()
        and any(
            file.is_file() and file.stat().st_size > 0
            for file in path.glob("*.safetensors")
        )
    )


def select_weights(provider, configured, state):
    if configured:
        path = Path(configured).expanduser().resolve(strict=True)
        selected = "mlx" if path.is_dir() else "llamacpp"
        if provider != "auto" and selected != provider:
            raise ValueError(f"Local weights at {path} do not match {provider}.")
        return selected, checked_weights(selected, path)

    if provider in {"auto", "mlx"} and shutil.which("mlx_lm.server"):
        cache = Path(os.environ.get(
            "HF_HUB_CACHE",
            Path(os.environ.get("HF_HOME", Path.home() / ".cache/huggingface")) / "hub",
        )).expanduser()
        snapshots = cache / CACHED_MLX / "snapshots"
        if snapshots.is_dir():
            for path in sorted(snapshots.iterdir()):
                if mlx_weights(path):
                    return "mlx", path.resolve()

    if provider in {"auto", "llamacpp"}:
        gguf = sorted((state / "models").glob("*.gguf"))
        if len(gguf) == 1:
            return "llamacpp", checked_weights("llamacpp", gguf[0])
        if gguf:
            raise ValueError("Select one of the installed GGUF files with --weights.")

    raise ValueError(
        "No local model weights found. Supply --weights with an MLX model directory or GGUF file, "
        "or choose an installed loopback server with --provider."
    )


def checked_weights(provider, path):
    path = Path(path).expanduser().resolve(strict=True)
    if provider == "mlx":
        if not mlx_weights(path):
            raise ValueError(f"MLX model directory is incomplete: {path}")
    else:
        if not path.is_file():
            raise ValueError(f"Select a local GGUF model file: {path}")
        with path.open("rb") as handle:
            if handle.read(4) != b"GGUF":
                raise ValueError(f"Invalid GGUF file: {path}")
    return path


def launch_command(spec, port):
    path = checked_weights(spec.provider, spec.weights)
    program = "mlx_lm.server" if spec.provider == "mlx" else "llama-server"
    binary = shutil.which(program)
    if binary is None:
        raise ValueError(f"Install {program} to load {spec.provider} weights.")
    bind = ["--host", "127.0.0.1", "--port", str(port)]
    if spec.provider == "mlx":
        return [binary, "--model", str(path), *bind, "--log-level", "WARNING"], str(path)
    return [
        binary, "--model", str(path), *bind, "--alias", "matrix-local",
        "--jinja", "--ctx-size", "8192", "--parallel", "1",
    ], "matrix-local"


def worker_ready(worker, url, timeout):
    deadline = time.monotonic() + min(timeout, 60)
    while worker.poll() is None and time.monotonic() < deadline:
        try:
            listing = request_json(url, "GET", "/v1/models", timeout=1)
            if listing.get("data") and worker.poll() is None:
                return
        except (RuntimeError, AttributeError):
            pass
        time.sleep(0.2)
    raise RuntimeError("The managed local model server did not become ready.")


def interrupt_worker(_signal, _frame):
    raise KeyboardInterrupt


@contextmanager
def model_session(spec, *, on_worker=None):
    if spec.provider not in MANAGED_PROVIDERS:
        yield LocalModel(spec.provider, spec.url, spec.model, spec.timeout, spec.max_tokens)
        return

    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    command, model_id = launch_command(spec, port)
    with TemporaryFile() as log:
        environment = {**os.environ, **OFFLINE_ENV}
        if environment.pop("JACKED_EMBEDDED", None):
            environment.pop("PYTHONPATH", None)
            environment.pop("PYTHONHOME", None)
        worker = subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
            env=environment,
            start_new_session=sys.platform != "win32",
        )
        old_term = None
        try:
            if on_worker is not None:
                on_worker(worker)
            if threading.current_thread() is threading.main_thread():
                old_term = signal.signal(signal.SIGTERM, interrupt_worker)
            try:
                worker_ready(worker, url, spec.timeout)
            except RuntimeError as error:
                log.seek(max(0, os.fstat(log.fileno()).st_size - 1_200))
                tail = log.read().decode("utf-8", errors="replace").strip()
                raise RuntimeError(f"{error} {tail}".strip()) from error
            yield LocalModel("openai", url, model_id, spec.timeout, spec.max_tokens)
        finally:
            if on_worker is not None:
                on_worker(None)
            if old_term is not None:
                signal.signal(signal.SIGTERM, old_term)
            if worker.poll() is None:
                try:
                    if sys.platform == "win32":
                        worker.terminate()
                    else:
                        os.killpg(worker.pid, signal.SIGTERM)
                    worker.wait(timeout=4)
                except ProcessLookupError:
                    worker.wait()
                except subprocess.TimeoutExpired:
                    if sys.platform == "win32":
                        worker.kill()
                    else:
                        try:
                            os.killpg(worker.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    worker.wait()
