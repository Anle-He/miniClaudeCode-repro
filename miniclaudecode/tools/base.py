# STAGE-2 STUB -- replaced by the real tool system in stage 3.
'''Tool system (stub): just enough for the agent loop to run with one fake tool.

Provides only what agent_loop.py calls:
  ToolRegistry.default() / .api_schemas() / .get(name)
  tool.execute(input) -> ToolResult(.output, .is_error)
'''

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    output: str
    is_error: bool = False


class WeatherTool:
    '''Fake tool: pretends to look up the weather for a city.

    Picked because the model cannot know real-time weather, so it will
    reliably emit a tool_use -- which is what makes the loop actually loop.
    '''

    name = 'get_weather'

    def to_api_schema(self) -> dict:
        return {
            'name': self.name,
            'description': 'Get the current weather for a given city.',
            'input_schema': {
                'type': 'object',
                'properties': {
                    'city': {'type': 'string', 'description': 'City name'},
                },
                'required': ['city'],
            },
        }

    def execute(self, tool_input: dict) -> ToolResult:
        city = tool_input.get('city', 'somewhere')
        return ToolResult(output=f'Sunny, about 25 degrees Celsius in {city}.')


class ToolRegistry:
    '''Holds tools by name; produces API schemas and looks tools up.'''

    def __init__(self, tools: list | None = None) -> None:
        self._tools = {tool.name: tool for tool in (tools or [])}

    @classmethod
    def default(cls) -> ToolRegistry:
        return cls([WeatherTool()])

    def get(self, name: str) -> Any:
        return self._tools.get(name)

    def api_schemas(self) -> list[dict]:
        return [tool.to_api_schema() for tool in self._tools.values()]
