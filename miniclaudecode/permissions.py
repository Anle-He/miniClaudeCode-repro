# STAGE-2 STUB -- replaced by the real 2-layer permission gate in stage 4.
'''Permission gate (stub): allows everything.

agent_loop.py calls gate.check(tool, input); returning None means "allowed".
'''

from __future__ import annotations

from typing import Any

from .config import Config


class PermissionGate:
    def __init__(self, config: Config) -> None:
        self.config = config

    def check(self, tool: Any, tool_input: dict) -> Any:
        # Stage-2 stub: always allow (None == no denial).
        return None
