'''Stage-4 runner: exercise PermissionGate across the three modes.

Only calls gate.check(tool, params) -- the pure permission verdict, no tool.execute,
so this has zero filesystem side effects and needs no API key. Run it to see the
two-layer / three-mode behaviour as a matrix.
'''

import builtins
import sys

from miniclaudecode.config import Config, PermissionMode
from miniclaudecode.permissions import PermissionGate
from miniclaudecode.tools.base import ToolRegistry

# ASK mode calls input() to ask the human. When run non-interactively (no real
# terminal), auto-answer 'n' so the matrix run doesn't block on the prompt.
# In a real terminal this shim is skipped and the gate asks for real.
if not sys.stdin.isatty():
    builtins.input = lambda prompt='': (print(prompt + 'n  [auto: non-interactive]'), 'n')[1]

# (label, tool_name, params) probes covering reads, writes, and bash variants.
PROBES = [
    ('write_file', 'write_file', {'path': 'out.txt', 'content': 'hi'}),
    ('list_dir (read)', 'list_dir', {'path': '.'}),
    ('bash: ls (safe)', 'bash', {'command': 'ls'}),
    ('bash: rm -rf / (dangerous)', 'bash', {'command': 'rm -rf /'}),
    ('bash: curl ... (unsafe, not dangerous)', 'bash', {'command': 'curl http://example.com'}),
]


def verdict(gate: PermissionGate, registry: ToolRegistry, name: str, params: dict) -> str:
    tool = registry.get(name)
    if tool is None:
        return f'(no such tool: {name})'
    result = gate.check(tool, params)
    if result is None:
        return 'ALLOW'
    return f'DENY  <- {result.output}'


def main() -> None:
    registry = ToolRegistry.default()
    for mode in (PermissionMode.AUTO, PermissionMode.PLAN, PermissionMode.ASK):
        gate = PermissionGate(Config(permission_mode=mode))
        print(f'\n=== mode = {mode.value.upper()} ===')
        for label, name, params in PROBES:
            print(f'  {label:<42} {verdict(gate, registry, name, params)}')
    print()


if __name__ == '__main__':
    main()
