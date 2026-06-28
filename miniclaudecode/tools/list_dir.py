'''ListDir tool -- list the entries of a directory, marking sub-directories with a trailing slash.'''

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import Tool, ToolResult


class ListDirTool(Tool):
    @property
    def name(self) -> str:
        return 'list_dir'

    @property
    def description(self) -> str:
        return 'List the entries of a directory. Directories are shown with a trailing slash.'

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            'type': 'object',
            'properties': {
                'path': {'type': 'string', 'description': 'Absolute or relative path to the directory. Defaults to the current directory.'},
            },
            'required': ['path'],
        }

    def execute(self, tool_input: dict[str, Any]) -> ToolResult:
        # All in one try (incl. path access + guards), so any failure -> is_error, never raises.
        try:
            path = tool_input.get('path', '.')
            dirpath = Path(path).expanduser()
            # Guard clauses: reject bad targets early, each with a specific message.
            if not dirpath.exists():
                return ToolResult(output=f'Error: directory not found: {dirpath}', is_error=True)
            if not dirpath.is_dir():
                return ToolResult(output=f'Error: not a directory: {dirpath}', is_error=True)

            # Sort entries, directories first then files, each alphabetically (case-insensitive).
            entries = sorted(dirpath.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            names = [f'{p.name}/' if p.is_dir() else p.name for p in entries]
            return ToolResult(output='\n'.join(names) or '(empty directory)')
        except Exception as exc:
            return ToolResult(output=f'Error listing directory: {exc}', is_error=True)
