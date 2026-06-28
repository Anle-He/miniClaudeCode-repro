'''Tool system: the Tool contract (ABC) + ToolRegistry (register / name-dispatch / api_schemas).

Concrete tools (bash / file_read / file_write / ...) subclass Tool and get registered here;
the registry hands their schemas to the model and looks them up by name at call time.
'''

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolResult:
    # Uniform return shape for every tool; frozen so a result can't be mutated after the fact.
    output: str
    is_error: bool = False


class Tool(ABC):
    '''The contract every tool must satisfy.

    Abstract members differ per tool and MUST be implemented; the concrete methods
    (to_api_schema / check_permissions) are shared defaults inherited for free.
    '''

    # name / description / input_schema are packed into the tool definition sent to the
    # model via the API's `tools=` parameter -- this is how the model learns which tools
    # exist and how to call each one. Hence they are abstract: every tool defines its own.
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @property
    @abstractmethod
    def input_schema(self) -> dict[str, Any]:
        ...

    def check_permissions(self, params: dict[str, Any]) -> str | None:
        '''Per-tool permission self-check. Return None if allowed, or a denial reason string.'''
        # Default: allow. A tool overrides this only if it needs to guard its own operations.
        return None

    @abstractmethod
    def execute(self, tool_input: dict) -> ToolResult:
        # The actual work; each concrete tool implements its own.
        ...

    def to_api_schema(self) -> dict:
        # Pack the three descriptors into the dict shape the API expects under `tools=`.
        return {
            'name': self.name,
            'description': self.description,
            'input_schema': self.input_schema,
        }


class ToolRegistry:
    '''Holds tools keyed by name; produces API schemas and looks tools up by name.'''

    def __init__(self, tools: list | None = None) -> None:
        # name -> Tool. Accept an initial list, or build up incrementally via register().
        self._tools = {tool.name: tool for tool in (tools or [])}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Any:
        # Name dispatch: the model emits a tool_use name; map it back to the instance.
        return self._tools.get(name)

    def all_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def api_schemas(self) -> list[dict[str, Any]]:
        # Collect every registered tool's schema for the `tools=` API parameter.
        return [tool.to_api_schema() for tool in self._tools.values()]

    @classmethod
    def default(cls) -> ToolRegistry:
        # Local imports (not at module top) to break the circular dependency: the tool
        # modules import Tool / ToolResult from this file, so a top-level import back
        # would form a cycle. Deferring to call time lets base.py finish loading first.
        from .append_file import AppendFileTool
        from .bash_tool import BashTool
        from .file_read import FileReadTool
        from .file_write import FileWriteTool
        from .list_dir import ListDirTool

        registry = cls()
        for tool_cls in (BashTool, FileReadTool, FileWriteTool, AppendFileTool, ListDirTool):
            registry.register(tool_cls())
        return registry
