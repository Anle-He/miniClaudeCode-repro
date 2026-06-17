'''Agent Loop:
1. Receive prompt
2. Call Claude API (non-streaming)
3. Parse response for tool_use blocks (single sequential execution)
4. Run permission check (2 layers)
5. Execute tool, append result
6. Repeat until no tool calls or max_turns reached
'''

import sys
from typing import Any

import anthropic

from .config import Config
from .context import ConversationContext
from .permissions import PermissionGate
from .system_prompt import build_system_prompt
from .tools.base import ToolRegistry


class AgentLoop:
    '''prompt -> LLM -> tool_use? -> execute -> loop
    until the LLM produces a final text-only response.'''
    def __init__(
            self,
            config: Config | None = None,
            registry: ToolRegistry | None = None,
    ) -> None:
        self.config = config or Config()
        self.client = anthropic.Anthropic()

        self.registry = registry or ToolRegistry.default()
        self.permission_gate = PermissionGate(self.config)

        self.context = ConversationContext(config=self.config)
        system_prompt = build_system_prompt(
            self.registry,
            permission_mode=self.config.permission_mode.value
        )
        self.context.set_system_prompt(system_prompt)

    def run(self, user_message: str) -> str:
        self.context.add_user_message(user_message)
        final_text = ''
        broke = False

        # Inner agent loop: up to max_turns LLM calls for this ONE user message.
        for turn in range(self.config.max_turns):
            response = self._call_api()
            tool_calls, text_parts = self._parse_response(response)

            # Keep the latest text; the final (no-tool) turn's text ends up winning.
            if text_parts:
                final_text = '\n'.join(text_parts)

            # No tool calls => this is the final answer: store it and stop.
            if not tool_calls:
                self.context.add_assistant_message(response.content)
                broke = True
                break

            # Tool calls present: store the assistant message (holding the tool_use)
            # BEFORE appending tool_result -- the API requires tool_use to precede tool_result.
            self.context.add_assistant_message(response.content)
            self._execute_tool_calls(tool_calls)

        # Loop exhausted all turns without ever producing a final answer.
        if not broke and not final_text:
            final_text = '(max turns reached without a final response)'

        return final_text

    def _call_api(self) -> Any:
        return self.client.messages.create(
            model=self.config.model,
            max_tokens=8192,
            system=self.context.system_prompt,
            tools=self.registry.api_schemas(),
            messages=self.context.get_api_messages(),
        )

    def _parse_response(self, response: Any) -> tuple[list[dict], list[str]]:
        """Extract tool_use blocks and text blocks from the API response."""
        tool_calls: list[dict] = []
        text_parts: list[str] = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
                sys.stdout.write(block.text)
                sys.stdout.flush()
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
                sys.stdout.write(f"\n[Tool: {block.name}] ")
                _input_preview = str(block.input)
                if len(_input_preview) > 120:
                    _input_preview = _input_preview[:120] + "..."
                sys.stdout.write(f"{_input_preview}\n")
                sys.stdout.flush()

        return tool_calls, text_parts

    def _execute_tool_calls(self, tool_calls: list[dict]) -> None:
        """Execute each tool call through the permission gate, append results."""
        tool_results = []
        for call in tool_calls:
            tool = self.registry.get(call["name"])
            if tool is None:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": call["id"],
                    "content": f"Error: unknown tool '{call['name']}'",
                    "is_error": True,
                })
                continue

            # Permission check (2-layer gate)
            denial = self.permission_gate.check(tool, call["input"])
            if denial is not None:
                sys.stdout.write(f"  -> {denial.output}\n")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": call["id"],
                    "content": denial.output,
                    "is_error": True,
                })
                continue

            # Execute the tool
            result = tool.execute(call["input"])
            output_preview = result.output
            if len(output_preview) > 300:
                output_preview = output_preview[:300] + "..."
            status = "ERROR" if result.is_error else "OK"
            sys.stdout.write(f"  -> [{status}] {output_preview}\n")
            sys.stdout.flush()

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": call["id"],
                "content": result.output,
                "is_error": result.is_error,
            })

        # Append all tool results as a single user message (Anthropic API format)
        self.context.messages.append({
            "role": "user",
            "content": tool_results,
        })