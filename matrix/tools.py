"""The explicit capabilities exposed to the model."""

import inspect
from typing import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Tool:
    description: str
    parameters: dict
    required: tuple[str, ...] = ()


@dataclass(frozen=True)
class Capability:
    tool: Tool
    run: Callable
    advisory: bool = False


STRING = {"type": "string"}
TOOLS = {
    "list_files": Tool("List visible, supported text files in the workspace.", {}),
    "read_file": Tool(
        "Read a UTF-8 workspace file and its SHA-256. Use next_offset to continue.",
        {"path": STRING, "offset": {"type": "integer"}}, ("path",),
    ),
    "search_files": Tool("Search workspace files for a case-insensitive literal.", {"query": STRING}, ("query",)),
    "check_python": Tool("Parse Python source to check syntax without executing it.", {"path": STRING}, ("path",)),
    "write_file": Tool(
        "Write a UTF-8 file with readback. For an overwrite, pass its current SHA-256 from read_file. "
        "For a new file use expected_sha256=missing. The parent directory must exist.",
        {"path": STRING, "text": STRING, "expected_sha256": STRING},
        ("path", "text", "expected_sha256"),
    ),
}


def definitions(allow_write, capabilities=None):
    registry = dict(TOOLS)
    registry.update({name: bound.tool for name, bound in (capabilities or {}).items()})
    return [
        {"type": "function", "function": {
            "name": name, "description": tool.description,
            "parameters": {
                "type": "object", "properties": tool.parameters,
                "required": list(tool.required), "additionalProperties": False,
            },
        }}
        for name, tool in registry.items() if name != "write_file" or allow_write
    ]


def execute(workspace, name, arguments, capabilities=None):
    bound = (capabilities or {}).get(name)
    tool = bound.tool if bound else TOOLS.get(name)
    if tool is None or (name == "write_file" and not workspace.allow_write):
        raise ValueError(f"Tool unavailable for this task: {name}")
    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a JSON object.")
    function = bound.run if bound else getattr(workspace, name)
    inspect.signature(function).bind(**arguments)
    for argument, value in arguments.items():
        expected = str if tool.parameters[argument]["type"] == "string" else int
        if type(value) is not expected:
            raise ValueError(f"Invalid type for {argument}.")
    return function(**arguments)
