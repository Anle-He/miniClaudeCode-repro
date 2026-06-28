'''Permission system -- a two-layer gate run before every tool execution.

Distilled from Claude Code's 5-layer permission model (tool self-check / settings
allow-deny / sandbox / active mode / hooks); this mini keeps two layers:
  Layer 1  tool.check_permissions()           -- each tool vetoes its own dangerous params
  Layer 2  permission mode (ASK / AUTO / PLAN) -- a global stance, independent of the tool

check() returns None to allow, or a ToolResult(is_error=True) to deny. Denials are
returned, not raised: the loop feeds them back to the model as a tool_result, so the
agent can adapt instead of crashing.
'''

from __future__ import annotations

from typing import Any

from .config import Config, PermissionMode
from .tools.base import Tool, ToolResult


# Kept for completeness/parity with upstream; currently unused -- the gate signals a
# denial by returning a ToolResult rather than raising.
class PermissionDenied(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class PermissionGate:
    '''Two-layer permission gate, consulted by the agent loop before each tool runs.'''

    def __init__(self, config: Config) -> None:
        self.config = config

    def check(self, tool: Tool, params: dict[str, Any]) -> ToolResult | None:
        '''Run the two layers in order; the first veto wins. None means allow.'''
        # Layer 1: the tool vets its own params. Mode-independent, so it runs first and
        # short-circuits -- this is why e.g. `rm -rf /` is blocked in every mode.
        denial = tool.check_permissions(params)
        if denial is not None:
            return ToolResult(output=f'Permission denied: {denial}', is_error=True)

        # Layer 2: the active mode's stance.
        mode = self.config.permission_mode

        # PLAN = read-only: block write-capable tools BY NAME (never inspects the command),
        # so even a harmless `bash: ls` is refused simply for being the bash tool.
        if mode == PermissionMode.PLAN:
            write_tools = {'bash', 'write_file'}
            if tool.name in write_tools:
                return ToolResult(
                    output=f"Permission denied: '{tool.name}' is blocked in plan (read-only) mode.",
                    is_error=True,
                )

        # ASK only gates bash: an unsafe command prompts the user. Other tools
        # (e.g. write_file) aren't checked here and fall through to allow.
        if mode == PermissionMode.ASK:
            if tool.name == 'bash':
                cmd = params.get('command', '')
                if not self._is_safe_command(cmd):
                    if not self._ask_user(tool.name, params):
                        return ToolResult(output='Permission denied: user rejected.', is_error=True)

        # AUTO, or anything that passed the checks above: allow.
        return None

    def _is_safe_command(self, command: str) -> bool:
        # Safe == starts with one of the read-only / allow-listed command prefixes.
        cmd_lower = command.strip().lower()
        return any(cmd_lower.startswith(safe) for safe in self.config.allowed_commands)

    @staticmethod
    def _ask_user(tool_name: str, params: dict[str, Any]) -> bool:
        # Interactive y/N prompt; treat EOF / Ctrl-C (e.g. non-interactive runs) as a refusal.
        detail = ''
        if tool_name == 'bash':
            detail = params.get('command', '')
        elif tool_name == 'write_file':
            detail = params.get('path', '')
        prompt = f"\n[Permission] Allow '{tool_name}'"
        if detail:
            prompt += f': {detail}'
        prompt += '? [y/N] '
        try:
            answer = input(prompt).strip().lower()
            return answer in ('y', 'yes')
        except (EOFError, KeyboardInterrupt):
            return False
