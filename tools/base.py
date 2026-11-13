"""
@package tools::base

@brief Shared tool contract for GRASS capabilities.

Classes:
 - tools::base::ToolResult
 - tools::base::Tool
 - tools::base::FunctionTool

SPDX-FileCopyrightText: GRASS Development Team
SPDX-License-Identifier: GPL-2.0-or-later

`Tool` and `ToolResult` define the stable capability interface used by
`ToolRegistry`. The contract is transport-agnostic, so these tools can
be reused by MCP, OpenCode workflows, and future GRASS agent backends.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    """Normalized result of a tool execution returned by `ToolRegistry.execute()."""

    success: bool
    data: Any = None
    error: str | None = None


class Tool(ABC):
    """Common interface implemented by every GRASS capability registered
    in `ToolRegistry`.

    A tool provides a stable name, description, input schema, and execution
    method. The registry can expose these capabilities through MCP, while
    other GRASS integrations or agents can use the same tools directly.
    """

    name: str
    description: str
    category = "core"

    @property
    @abstractmethod
    def schema(self):
        """JSON schema describing the tool parameters."""

    @abstractmethod
    def execute(self, **kwargs):
        """Execute the tool and return a `ToolResult`."""


class FunctionTool(Tool):
    """Adapt a plain callable into the shared `Tool` contract.

    Used for hand-written, high-level capabilities (session, project,
    region) whose parameters are simple and stable enough to declare
    explicitly here, as opposed to GRASS tools whose schemas are
    discovered from GRASS documentation at runtime.
    """

    def __init__(self, name, description, schema, handler, category="core"):
        self.name = name
        self.description = description
        self._schema = schema
        self._handler = handler
        self.category = category

    @property
    def schema(self):
        return self._schema

    def execute(self, **kwargs):
        try:
            data = self._handler(**kwargs)
        except Exception as error:  # noqa: BLE001
            return ToolResult(success=False, error=str(error))

        return ToolResult(success=True, data=data)
