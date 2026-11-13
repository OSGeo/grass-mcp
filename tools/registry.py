"""
@package tools::registry

@brief Register and dispatch GRASS tools.

Classes:
 - tools::registry::ToolRegistry
 
SPDX-FileCopyrightText: GRASS Development Team
SPDX-License-Identifier: GPL-2.0-or-later

`ToolRegistry` is the single dispatch point for capabilities: it keeps
registered tools, supports category discovery, and normalizes execution
results so integrations can remain thin and transport-specific.
"""

import gettext
import sys

from tools.base import Tool, ToolResult

_ = gettext.gettext


class ToolRegistry:
    """Single point of tool registration, discovery, and execution."""

    def __init__(self):
        self._tools = {}
        self._categories = {}

    def register(self, tool):
        """Register a `Tool` instance."""
        if not isinstance(tool, Tool):
            raise TypeError(_("Only Tool instances can be registered"))

        self._tools[tool.name] = tool

        category = getattr(tool, "category", "core")
        names = self._categories.setdefault(category, [])

        if tool.name not in names:
            names.append(tool.name)

    @staticmethod
    def _log(message):
        """Write diagnostic logs to stderr.

        The MCP server uses stdout for JSON-RPC over stdio.
        """
        print(message, file=sys.stderr)

    def get(self, tool_name):
        """Return the registered tool with the given name.

        GRASS module tools may appear as dotted names (`v.buffer`) or
        normalized names (`v_buffer`) depending on client expectations.
        Accept both forms for compatibility.
        """
        candidates = [tool_name]

        if "." in tool_name:
            candidates.append(tool_name.replace(".", "_"))

        if "_" in tool_name:
            candidates.append(tool_name.replace("_", "."))

        for candidate in candidates:
            tool = self._tools.get(candidate)
            if tool is not None:
                return tool

        raise KeyError(tool_name)

    def list(self, category=None):
        """Return registered tools, optionally filtered by category."""
        if category is None:
            return list(self._tools.values())

        names = self._categories.get(category, [])
        return [self._tools[name] for name in names if name in self._tools]

    def categories(self):
        """Return the sorted tuple of known tool categories."""
        return tuple(sorted(self._categories.keys()))

    def execute(self, tool_name, **kwargs):
        """Execute a registered tool and return a `ToolResult`.

        Unknown tool names are returned as failed results instead of raising
        `KeyError`.
        """
        self._log(
            "[grass-mcp] calling tool '{}' with arguments: {}".format(
                tool_name, kwargs
            )
        )

        try:
            tool = self.get(tool_name)
        except KeyError:
            self._log("[grass-mcp] tool '{}' not found".format(tool_name))
            return ToolResult(
                success=False,
                error=_("Unknown tool '{}'").format(tool_name),
            )

        result = tool.execute(**kwargs)

        self._log(
            "[grass-mcp] tool '{}' finished: success={} error={}".format(
                tool_name, result.success, result.error
            )
        )

        return result
