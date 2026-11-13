"""
@package tools::vector

@brief Provide vector tools for GRASS integrations.

Classes:
 - tools::vector::VectorTools

SPDX-FileCopyrightText: GRASS Development Team
SPDX-License-Identifier: GPL-2.0-or-later

Contains both hand-written high-level vector map discovery and dynamic
registration of selected vector GRASS module tools based on local
interface metadata.
"""

import gettext
import sys

try:
    from grass.tools import Tools
except ModuleNotFoundError:  # pragma: no cover
    Tools = None

from tools.grass_tools import discover_grass_tool

_ = gettext.gettext


# GRASS vector tools exposed through the integrations:
VECTOR_TOOLS = (
    "v.info",
    "v.select",
)


class VectorTools:
    """Provide high-level vector map discovery operations."""

    def __init__(self, tools=None):
        if tools is not None:
            self._tools = tools
            return

        if Tools is None:
            raise ModuleNotFoundError(
                _("GRASS Python package is required when tools mock is not provided")
            )

        self._tools = Tools()

    def list_vector_maps(self, pattern=None):
        """List vector maps available in the current mapset search path."""
        kwargs = {
            "type": "vector",
            "format": "json",
        }

        if pattern:
            kwargs["pattern"] = pattern

        vectors = self._tools.g_list(**kwargs)

        return {"vectors": vectors}


def build_tools(runner=None, parse_interface=None):
    """Discover the vector tools listed in `VECTOR_TOOLS`.

    Tools whose interface cannot be discovered are skipped instead of
    creating an incomplete tool or preventing the remaining vector tools
    from being registered.
    """
    tools = []

    for tool_name in VECTOR_TOOLS:
        try:
            tool = discover_grass_tool(
                tool_name,
                category="vector",
                runner=runner,
                parse_interface=parse_interface,
            )
        except RuntimeError as error:
            print(
                "[grass-mcp] skipping vector tool '{}' ({}).".format(
                    tool_name, error
                ),
                file=sys.stderr,
            )
            continue

        tools.append(tool)

    return tools
