'''FileRead tool -- read a text file as numbered lines, with an optional line range.'''

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import Tool, ToolResult

MAX_FILE_SIZE = 2 * 1024 * 1024 # 2 MB


class FileReadTool(Tool):
    @property
    def name(self) -> str:
        return 'read_file'

    @property
    def description(self) -> str:
        return 'Read the contents of a file. Returns numbered lines for easy reference.'

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or relative path to the file."},
                "offset": {"type": "integer", "description": "1-based start line (optional)."},
                "limit": {"type": "integer", "description": "Number of lines to read (optional)."},
            },
            "required": ["path"],
        }

    def execute(self, tool_input: dict[str, Any]) -> ToolResult:
        # All in one try (incl. path access + guards), so any failure -> is_error, never raises.
        try:
            path = tool_input.get("path")
            if not path:
                return ToolResult(output="Error: 'path' is required", is_error=True)
            filepath = Path(path).expanduser()
            # Guard clauses: reject bad targets early, each with a specific message.
            if not filepath.exists():
                return ToolResult(output=f"Error: file not found: {filepath}", is_error=True)
            if not filepath.is_file():
                return ToolResult(output=f"Error: not a file: {filepath}", is_error=True)
            if filepath.stat().st_size > MAX_FILE_SIZE:
                return ToolResult(output=f"Error: file too large (>{MAX_FILE_SIZE} bytes)", is_error=True)
            lines = filepath.read_text(errors="replace").splitlines(keepends=True)

            # offset is 1-based (floored at 1); limit is optional. Slice the requested window.
            offset = max(1, tool_input.get("offset", 1))
            limit = tool_input.get("limit")
            selected = lines[offset - 1:]
            if limit is not None and limit > 0:
                selected = selected[:limit]

            # Number each line (1-based, right-aligned); fall back to a marker when empty.
            numbered = []
            for i, line in enumerate(selected, start=offset):
                numbered.append(f"{i:>6}|{line.rstrip()}")
            return ToolResult(output="\n".join(numbered) or "(empty file)")
        except Exception as exc:
            return ToolResult(output=f"Error reading file: {exc}", is_error=True)
