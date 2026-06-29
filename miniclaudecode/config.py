'''Configuration: runtime settings + the permission-mode enum.

A single Config dataclass holds the model, limits, the active permission mode, and the
command allow/deny lists consulted by the permission system.
'''

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field


class PermissionMode(Enum):
    ASK = 'ask'
    AUTO = 'auto'
    PLAN = 'plan'


@dataclass
class Config:
    model: str = 'claude-sonnet-4-6'
    max_turns: int = 30                 # max agent-loop turns per user message
    max_context_messages: int = 100     # truncation threshold in ConversationContext
    max_output_chars: int = 50_000
    max_retries: int = 3                # passed to the Anthropic client to retry transient errors
    permission_mode: PermissionMode = PermissionMode.ASK
    # ASK-mode safe-command allow-list: PermissionGate._is_safe_command lets a bash
    # command through (no prompt) when it starts with one of these prefixes.
    allowed_commands: list[str] = field(default_factory=lambda: [
        'ls', 'cat', 'head', 'tail', 'wc', 'find', 'grep', 'rg',
        'git status', 'git diff', 'git log', 'git branch',
        'python', 'python3', 'pip', 'npm', 'node',
        'echo', 'pwd', 'which', 'env', 'date',
    ])
    # NOTE: currently unused -- the active deny-list lives in BashTool.DANGEROUS_PATTERNS
    # (layer-1 self-check). Kept for parity / a possible future settings-level denylist.
    denied_patterns: list[str] = field(default_factory=lambda: [
        'rm -rf /', 'rm -rf ~', 'sudo rm',
        'git push --force', 'git reset --hard',
        '> /dev/sda', 'mkfs', 'dd if=',
    ])