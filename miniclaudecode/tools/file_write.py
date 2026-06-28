'''FileWrite tool -- write text to a file, creating parent directories as needed.'''

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import Tool, ToolResult


class FileWriteTool(Tool):
    @property
    def name(self) -> str:
        return 'write_file'

    @property
    def description(self) -> str:
        return "Write content to a file. Create parent directories if they don't exist. Overwrites if the file already exists."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            'type': 'object',
            'properties': {
                'path': {'type': 'string', 'description': 'Absolute or relative path to the file.'},
                'content': {'type': 'string', 'description': 'The content to write.'},
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
            # encoding pinned to utf-8 so writes round-trip with read_file (Windows
            # write_text() would otherwise default to the cp936/GBK codepage).
            filepath.write_text(content, encoding='utf-8')
            return ToolResult(output=f'Wrote {len(content)} chars to {filepath}')
        except Exception as exc:
            return ToolResult(output=f'Error writing file: {exc}', is_error=True)