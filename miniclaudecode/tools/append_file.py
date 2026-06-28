'''AppendFile tool -- append text to the end of a file, creating it (and parents) if needed.'''

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import Tool, ToolResult


class AppendFileTool(Tool):
    @property
    def name(self) -> str:
        return 'append_file'

    @property
    def description(self) -> str:
        return "Append content to the end of a file. Create the file and parent directories if they don't exist. Unlike write_file, this preserves existing content."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            'type': 'object',
            'properties': {
                'path': {'type': 'string', 'description': 'Absolute or relative path to the file.'},
                'content': {'type': 'string', 'description': 'The content to append.'},
            },
            'required': ['path', 'content'],
        }

    def execute(self, tool_input: dict[str, Any]) -> ToolResult:
        # Everything -- path access, validation, parsing, write -- runs inside one try, so
        # any failure becomes an is_error ToolResult and never raises into the agent loop.
        try:
            path = tool_input.get('path')
            if not path:
                return ToolResult(output="Error: 'path' is required", is_error=True)
            filepath = Path(path).expanduser()
            content = tool_input.get('content', '')
            filepath.parent.mkdir(parents=True, exist_ok=True)  # create missing parent dirs
            # mode 'a' appends instead of truncating; encoding pinned to utf-8 so writes
            # round-trip with read_file (Windows would otherwise default to cp936/GBK).
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(content)
            return ToolResult(output=f'Appended {len(content)} chars to {filepath}')
        except Exception as exc:
            return ToolResult(output=f'Error appending to file: {exc}', is_error=True)
