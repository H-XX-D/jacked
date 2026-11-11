"""Bounded text tools and guarded file writes for one workspace."""

import ast
import hashlib
import os
import re
import stat
import tempfile
from pathlib import Path

MAX_FILE_BYTES = 96_000
READ_CHARS = 4_000
SCAN_ENTRIES = 1_000
SKIP_DIRS = {"node_modules", "uploads", "venv", "dist", "build", "backups", "certs"}
DEVICE_NAME = re.compile(r"(?:CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|(?:COM|LPT)[1-9¹²³])$", re.I)
SECRET_STEMS = {"api_keys", "credentials", "secrets", "long_term", "id_rsa", "id_ed25519"}
TEXT_SUFFIXES = {
    ".c", ".cpp", ".cs", ".css", ".csv", ".go", ".h", ".html", ".ini", ".java", ".js",
    ".json", ".jsx", ".md", ".ps1", ".py", ".rb", ".rs", ".sh", ".sql", ".toml", ".ts",
    ".tsx", ".txt", ".xml", ".yaml", ".yml",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def permitted_name(name):
    return (
        bool(name)
        and not name.startswith(".")
        and not name.endswith((" ", "."))
        and not any(ord(char) < 32 or char in '\\:<>|"*?' for char in name)
        and name.lower() not in SKIP_DIRS
        and Path(name).stem.lower() not in SECRET_STEMS
        and not DEVICE_NAME.fullmatch(name.split(".", 1)[0].rstrip())
    )


class Workspace:
    def __init__(self, root, backups, allow_write=False, allow_execute=False):
        self.root = Path(root).expanduser().resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError("Workspace must be an existing directory.")
        self.backups = backups
        self.allow_write = allow_write
        self.allow_execute = allow_execute

    def _path(self, relative, *, may_create=False):
        parts = relative.split("/")
        if not all(map(permitted_name, parts)) or Path(parts[-1]).suffix.lower() not in TEXT_SUFFIXES:
            raise ValueError("Use a visible, workspace-relative text file path.")
        current = self.root
        for index, part in enumerate(parts):
            current = current / part
            final = index == len(parts) - 1
            try:
                entry = current.lstat()
            except FileNotFoundError:
                if final and may_create:
                    return current
                raise
            if stat.S_ISLNK(entry.st_mode) or current.is_junction():
                raise ValueError("Links are outside the workspace tool policy.")
            if final:
                if not stat.S_ISREG(entry.st_mode) or entry.st_nlink != 1:
                    raise ValueError("Only regular, unlinked text files are supported.")
            elif not stat.S_ISDIR(entry.st_mode):
                raise ValueError("A parent path must be a directory.")
        return current

    def _load(self, relative):
        path = self._path(relative)
        with path.open("rb") as handle:
            data = handle.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES or b"\0" in data:
            raise ValueError("File is binary or exceeds the text file size limit.")
        return data, data.decode("utf-8")

    def _paths(self):
        count = 0
        for folder, dirs, files in os.walk(self.root):
            parent = Path(folder)
            dirs[:] = sorted(
                name for name in dirs
                if permitted_name(name)
                and not (parent / name).is_symlink()
                and not (parent / name).is_junction()
            )
            count += len(dirs) + len(files)
            for name in sorted(files):
                relative = (parent / name).relative_to(self.root).as_posix()
                try:
                    self._path(relative)
                except (OSError, ValueError):
                    continue
                yield relative
            if count >= SCAN_ENTRIES:
                break

    def list_files(self):
        files = []
        for relative in self._paths():
            if len(files) == 80:
                return {"files": files, "truncated": True}
            files.append(relative)
        return {"files": files}

    def read_file(self, path, offset=0):
        if type(offset) is not int or offset < 0:
            raise ValueError("offset must be a nonnegative character offset.")
        data, content = self._load(path)
        end = min(offset + READ_CHARS, len(content))
        return {
            "path": path, "sha256": digest(data), "text": content[offset:end],
            "next_offset": end if end < len(content) else None,
        }

    def search_files(self, query):
        if not 1 <= len(query) <= 160 or "\n" in query:
            raise ValueError("Provide a single-line literal query of 1–160 characters.")
        matches = []
        query = query.casefold()
        for path in self._paths():
            try:
                _, content = self._load(path)
            except (OSError, ValueError):
                continue
            for number, line in enumerate(content.splitlines(), 1):
                if query in line.casefold():
                    matches.append({"path": path, "line": number, "text": line[:240]})
                    if len(matches) >= 24:
                        return {"matches": matches, "truncated": True}
        return {"matches": matches}

    def check_python(self, path):
        if not path.lower().endswith(".py"):
            raise ValueError("Provide a Python source file.")
        data, content = self._load(path)
        try:
            ast.parse(content, filename=path)
        except SyntaxError as error:
            return {"ok": False, "path": path, "line": error.lineno, "error": error.msg}
        return {"ok": True, "path": path, "sha256": digest(data), "check": "Python syntax"}

    def write_file(self, path, text, expected_sha256):
        if not self.allow_write:
            raise ValueError("The current task has read-only workspace access.")
        data = text.encode("utf-8")
        if len(data) > MAX_FILE_BYTES or b"\0" in data:
            raise ValueError("New content exceeds the text file policy.")
        if path.lower().endswith(".py"):
            ast.parse(text, filename=path)

        target = self._path(path, may_create=True)
        backup = None
        if expected_sha256 == "missing":
            if target.exists():
                raise ValueError("File already exists. Read it and supply its SHA-256.")
            mode = 0o600
        else:
            previous, _ = self._load(path)
            if digest(previous) != expected_sha256:
                raise ValueError("File changed. Read it again before overwriting.")
            mode = stat.S_IMODE(target.stat().st_mode) & 0o777
            self.backups.mkdir(mode=0o700, parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=self.backups, delete=False) as handle:
                handle.write(previous)
                handle.flush()
                os.fsync(handle.fileno())
                backup = handle.name

        temp = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
                temp = Path(handle.name)
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            temp.chmod(mode)
            self._path(path, may_create=True)
            if expected_sha256 == "missing":
                os.link(temp, target)
                temp.unlink()
            else:
                current, _ = self._load(path)
                if digest(current) != expected_sha256:
                    raise ValueError("File changed while the write was prepared.")
                os.replace(temp, target)
            verified, _ = self._load(path)
            if digest(verified) != digest(data):
                raise RuntimeError("Write completed but readback did not match.")
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
        return {
            "path": path, "previous_sha256": expected_sha256, "sha256": digest(verified),
            "bytes": len(verified), "backup": backup, "verification": "SHA-256 readback",
        }
