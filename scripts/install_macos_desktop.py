"""Build a local macOS app with its own microphone permission identity."""

import json
import os
import plistlib
import shlex
import site
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


IDENTIFIER = "com.hendrixx.jacked.jarvis"
LAUNCHER = """
#include <Python.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv) {
    char **args = calloc((size_t)argc + 7, sizeof(*args));
    if (!args) return 1;
    if (chdir(JACKED_WORKSPACE) != 0) {
        free(args);
        return 1;
    }
    setenv("PATH", JACKED_PATH, 1);
    setenv("PYTHONDONTWRITEBYTECODE", "1", 0);
    setenv("PYTHONPATH", JACKED_PACKAGES, 1);
    setenv("JACKED_EMBEDDED", "1", 1);
    if (JACKED_AURA_SOURCE[0]) setenv("MATRIX_AURA_SOURCE", JACKED_AURA_SOURCE, 0);
    args[0] = JACKED_PYTHON;
    args[1] = "-S";
    args[2] = JACKED_SCRIPT;
    args[3] = "desktop";
    args[4] = "--workspace";
    args[5] = JACKED_WORKSPACE;
    for (int i = 1; i < argc; i++) args[i + 5] = argv[i];
    int result = Py_BytesMain(argc + 5, args);
    free(args);
    return result;
}
"""


def install(target):
    if sys.platform != "darwin":
        raise RuntimeError("This launcher is for macOS. Use main.py desktop on other platforms.")
    from PyQt6 import QtMultimedia  # noqa: F401
    import psutil  # noqa: F401

    project = Path(__file__).resolve().parent.parent
    target = target.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        with (target / "Contents" / "Info.plist").open("rb") as existing:
            if plistlib.load(existing).get("CFBundleIdentifier") != IDENTIFIER:
                raise RuntimeError(f"Refusing to replace an unrelated app at {target}")
    with TemporaryDirectory(prefix=".jacked-build-", dir=target.parent) as directory:
        staged = Path(directory) / target.name
        build(project, staged)
        if target.exists():
            backup = Path(directory) / "previous.app"
            target.rename(backup)
            try:
                staged.rename(target)
            except OSError:
                backup.rename(target)
                raise
        else:
            staged.rename(target)
    return target


def build(project, target):
    contents = target / "Contents"
    executable = contents / "MacOS" / "JackedJarvis"
    executable.parent.mkdir(parents=True, exist_ok=False)
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    python = Path(sys.executable).absolute()
    python_config = python.with_name(f"python{version}-config")
    flags = shlex.split(subprocess.check_output(
        [python_config, "--embed", "--cflags", "--ldflags"], text=True,
    ))
    defines = {
        "JACKED_PYTHON": str(python),
        "JACKED_SCRIPT": str(project / "main.py"),
        "JACKED_WORKSPACE": str(project),
        "JACKED_PATH": os.pathsep.join(dict.fromkeys((
            str(python.parent), "/opt/homebrew/bin", *os.get_exec_path()
        ))),
        "JACKED_PACKAGES": os.pathsep.join(dict.fromkeys((
            *site.getsitepackages(), site.getusersitepackages(),
        ))),
        "JACKED_AURA_SOURCE": next((path for path in sys.path if path.endswith("/AURA/src")), ""),
    }
    try:
        subprocess.run(
            ["clang", *[f"-D{k}={json.dumps(v)}" for k, v in defines.items()],
             "-x", "c", "-", *flags, "-o", executable],
            input=LAUNCHER, text=True, check=True,
        )
        with (contents / "Info.plist").open("wb") as plist:
            plistlib.dump({
                "CFBundleDisplayName": "Jacked Jarvis",
                "CFBundleExecutable": executable.name,
                "CFBundleIdentifier": IDENTIFIER,
                "CFBundleName": "Jacked Jarvis",
                "CFBundlePackageType": "APPL",
                "CFBundleShortVersionString": "1.0",
                "CFBundleVersion": "1",
                "NSHighResolutionCapable": True,
                "NSMicrophoneUsageDescription": "Record a voice prompt and transcribe it on this Mac.",
            }, plist)
        subprocess.run(["codesign", "--force", "--sign", "-", "--identifier", IDENTIFIER, target], check=True)
    except Exception:
        executable.unlink(missing_ok=True)
        (contents / "Info.plist").unlink(missing_ok=True)
        executable.parent.rmdir()
        contents.rmdir()
        target.rmdir()
        raise
    return target


if __name__ == "__main__":
    default = Path.home() / "Applications" / "Jacked Jarvis.app"
    print(install(Path(sys.argv[1]) if len(sys.argv) > 1 else default))
