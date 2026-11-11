"""Medicine Cabinet v1 context and task-history interchange."""

import json
import struct
from datetime import datetime
from pathlib import Path

CAPSULE_MAGIC = b"AURACTX1"
TABLET_MAGIC = b"AURATAB1"
VERSION = 1
MAX_CAPSULE = 1_000_000
CONTEXT_SECTIONS = {
    "task_objective", "relevant_files", "working_plan", "error_state",
    "code_symbols_of_interest", "jacked_task",
}


def blob(payload):
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return struct.pack(">I", len(payload)) + payload


def pack_json(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, allow_nan=False)


def header(magic, metadata, entries):
    created = datetime.fromisoformat(metadata["created_at"])
    return (
        magic + struct.pack(">HQ", VERSION, int(created.timestamp() * 1_000))
        + blob(pack_json(metadata)) + struct.pack(">I", len(entries))
    )


def capsule(packet, project):
    metadata = {
        "project": project, "summary": packet["goal"][:400],
        "created_at": packet["updated_at"], "extra": {"task_id": packet["id"]},
    }
    paths = sorted({
        receipt["request"]["path"] for receipt in packet["receipts"]
        if isinstance(receipt["request"].get("path"), str)
    })
    sections = [
        ("task_objective", 1, packet["goal"]),
        ("relevant_files", 2, pack_json(paths)),
        ("jacked_task", 2, pack_json(packet)),
    ]
    return header(CAPSULE_MAGIC, metadata, sections) + b"".join(
        blob(name) + bytes([kind]) + blob(payload) for name, kind, payload in sections
    )


def tablet(packet):
    metadata = {
        "title": "Jacked task " + packet["id"], "summary": packet["goal"][:400],
        "created_at": packet["updated_at"], "tags": ["jacked", "task-history"],
        "extra": {"task_id": packet["id"], "status": packet["status"]},
    }
    entries = [("jacked-task-" + packet["id"] + ".json", "", pack_json(packet))]
    return header(TABLET_MAGIC, metadata, entries) + b"".join(
        blob(path) + blob(diff) + blob(notes) for path, diff, notes in entries
    )


def capsule_context(path):
    with Path(path).expanduser().open("rb") as stream:
        data = stream.read(MAX_CAPSULE + 1)
    if len(data) > MAX_CAPSULE or data[:10] != CAPSULE_MAGIC + struct.pack(">H", VERSION):
        raise ValueError("Supply a Medicine Cabinet v1 capsule up to 1 MB.")
    offset = 18

    def take(size):
        nonlocal offset
        if offset + size > len(data):
            raise ValueError("The Medicine Cabinet capsule is truncated.")
        chunk = data[offset:offset + size]
        offset += size
        return chunk

    def number():
        return struct.unpack(">I", take(4))[0]

    def field():
        return take(number())

    metadata = json.loads(field())
    count = number()
    if not isinstance(metadata, dict) or count > 64:
        raise ValueError("The Medicine Cabinet capsule has invalid metadata or too many sections.")
    result = {"project": str(metadata.get("project", ""))[:100], "sections": {}}
    for _ in range(count):
        name = field().decode("utf-8")
        kind = take(1)[0]
        payload = field()
        if name in CONTEXT_SECTIONS and kind in {1, 2}:
            result["sections"].setdefault(name, payload[:2_000].decode("utf-8", errors="replace"))
    if offset != len(data):
        raise ValueError("The Medicine Cabinet capsule has trailing bytes.")
    return "Medicine Cabinet capsule (reference data):\n" + pack_json(result)[:5_000]
