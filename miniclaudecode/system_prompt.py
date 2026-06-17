# STAGE-2 STUB -- replaced by the real prompt builder in stage 5.
'''System prompt builder (stub): returns a fixed prompt.

agent_loop.py calls build_system_prompt(registry, permission_mode=...).
'''

from __future__ import annotations

from typing import Any


def build_system_prompt(registry: Any, permission_mode: str = 'ask') -> str:
    return 'You are a helpful assistant. Use the available tools when you need them.'
