'''Bash tool -- run a shell command via subprocess, with a deny-list safety self-check.'''

from __future__ import annotations

import subprocess
from typing import Any

from .base import Tool, ToolResult


class BashTool(Tool):
    # Deny-list of obviously destructive commands. Substring match -- shallow and bypassable,
    # a toy guard rather than real command security.
    DANGEROUS_PATTERNS = [
        'rm -rf /', 'rm -rf ~', 'sudo rm',
        'git push --force', 'git reset --hard',
        '> /dev/sda', 'mkfs', 'dd if=',
        ':(){ :|:& };:',
    ]

    @property
    def name(self) -> str:
        return 'bash'

    @property
    def description(self) -> str:
        return (
            'Execute a bash command. Use for running scripts, installing packages, '
            'git operations, and any shell task. Commands run in the current working directory.'
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            'type': 'object',
            'properties': {
                'command': {
                    'type': 'string',
                    'description': 'The bash command to execute.',
                },
            },
            'required': ['command'],
        }

    def check_permissions(self, params: dict[str, Any]) -> str | None:
        # Layer-1 per-tool self-check: refuse commands hitting the deny-list.
        # Defined here, but not yet invoked by the loop -- the permission system wires it in later.
        cmd = params.get('command', '')
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in cmd:
                return f"Blocked: command matches dangerous pattern '{pattern}'"
        return None

    def execute(self, tool_input: dict[str, Any]) -> ToolResult:
        command = tool_input.get('command', '')
        if not command.strip():
            return ToolResult(output='Error: empty command', is_error=True)
        try:
            # shell=True allows pipes/globs/etc -- powerful, and the reason the deny-list exists.
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=None,
            )
            output_parts = []
            if result.stdout:
                output_parts.append(result.stdout)
            if result.stderr:
                output_parts.append(f'STDERR:\n{result.stderr}')
            output = '\n'.join(output_parts) or '(no output)'
            if len(output) > 50_000:
                output = output[:50_000] + '\n... (truncated)'
            # Non-zero exit = command ran but failed -> is_error (distinct from a Python exception).
            return ToolResult(output=output, is_error=result.returncode != 0)
        except subprocess.TimeoutExpired:
            return ToolResult(output='Error: command timed out after 120s', is_error=True)
        except Exception as exc:
            return ToolResult(output=f'Error: {exc}', is_error=True)
