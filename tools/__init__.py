"""
@package tools

@brief Tool package exports shared by GRASS capabilities.

Classes:
 - tools::Tool
 - tools::ToolResult
 - tools::FunctionTool
 - tools::ToolRegistry
 - tools::GrassTool

SPDX-FileCopyrightText: GRASS Development Team
SPDX-License-Identifier: GPL-2.0-or-later

This package exports the common tool contract, the central registry, and
the adapter for dynamically discovered GRASS module tools. MCP and any
future integrations should depend on these abstractions rather than on
individual GRASS calls.
"""

from .base import FunctionTool, Tool, ToolResult
from .grass_tools import GrassTool, discover_grass_tool, grass_tool_to_tool_name
from .registry import ToolRegistry

__all__ = [
    "Tool",
    "ToolResult",
    "FunctionTool",
    "ToolRegistry",
    "GrassTool",
    "discover_grass_tool",
    "grass_tool_to_tool_name",
]
