'''CLI entry point'''

from __future__ import annotations

import argparse
import sys

from .agent_loop import AgentLoop
from .config import Config, PermissionMode
from .tools.base import ToolRegistry


BANNER = '''
    miniClaudeCode v0.1.0

    Type your message to start. Commands:
        /tools   -- list available tools
        /mode    -- show/change permission mode
        /help    -- show help
        /quit    -- exit
'''


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='miniClaudeCode -- a distilled Claude Code agent loop',
    )
    parser.add_argument(
        '--model', default='deepseek-v4-flash',
        help='LLM model to use',
    )
    parser.add_argument(
        '--mode', choices=['ask', 'auto', 'plan'], default='ask',
        help='Permission mode (default: ask)',
    )
    parser.add_argument(
        '--max-turns', type=int, default=30,
        help='Max agent loop turns per message (default: 30)',
    )
    parser.add_argument(
        'prompt', nargs='?', default=None,
        help='Optional one-shot prompt (non-interactive mode)',
    )
    return parser


def run_interactive(agent: AgentLoop) -> None:
    '''Interactive REPL: read a line, dispatch slash-commands or run the agent.'''
    print(BANNER)

    while True:
        try:
            user_input = input('\n> ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nGoodbye!')
            break

        if not user_input:
            continue

        # Control channel: slash-commands act on the session, not the model.
        if user_input.startswith('/'):
            cmd = user_input.lower().split()[0]
            if cmd in ('/quit', '/exit', '/q'):
                print('Goodbye!')
                break
            elif cmd == '/tools':
                print('\nAvailable tools:')
                for tool in agent.registry.all_tools():
                    print(f'  - {tool.name}: {tool.description}')
                continue
            elif cmd == '/mode':
                parts = user_input.split()
                if len(parts) > 1 and parts[1] in ('ask', 'auto', 'plan'):
                    # Live-swaps the mode the stage-4 PermissionGate reads on every check.
                    agent.config.permission_mode = PermissionMode(parts[1])
                    print(f'Mode changed to: {parts[1]}')
                else:
                    print(f'Current mode: {agent.config.permission_mode.value}')
                    print('Usage: /mode [ask|auto|plan]')
                continue
            elif cmd == '/help':
                print(BANNER)
                continue
            else:
                print(f'Unknown command: {cmd}. Type /help for help.')
                continue

        # Chat channel: hand the message to the agent loop.
        print()
        try:
            agent.run(user_input)
        except KeyboardInterrupt:
            print('\n(interrupted)')
        except Exception as exc:
            print(f'\nError: {exc}', file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = Config(
        model=args.model,
        permission_mode=PermissionMode(args.mode),
        max_turns=args.max_turns,
    )
    registry = ToolRegistry.default()
    agent = AgentLoop(config=config, registry=registry)

    # Entry point 1: one-shot -- a prompt arg means run once and exit (script/pipe friendly).
    if args.prompt:
        try:
            agent.run(args.prompt)
            print()
        except Exception as exc:
            print(f'Error: {exc}', file=sys.stderr)
            return 1
        return 0

    # Entry point 2: interactive REPL (no prompt arg).
    run_interactive(agent)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
