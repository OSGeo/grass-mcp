"""
@package tools::raster

@brief Provide raster tools for GRASS integrations.

Classes:
 - tools::raster::RasterTools

SPDX-FileCopyrightText: GRASS Development Team
SPDX-License-Identifier: GPL-2.0-or-later

Contains both hand-written high-level raster map discovery and dynamic
registration of selected raster GRASS module tools based on local
interface metadata.
"""

import gettext

try:
    from grass.tools import Tools
except ModuleNotFoundError:  # pragma: no cover
    Tools = None

from tools.grass_tools import discover_grass_tool

_ = gettext.gettext


# GRASS raster tools exposed through the integrations:
RASTER_TOOLS = (
    "r.info",
    "r.slope.aspect",
)


class RasterTools:
    """Provide high-level raster map discovery operations."""

    def __init__(self, tools=None):
        if tools is not None:
            self._tools = tools
            return

        if Tools is None:
            raise ModuleNotFoundError(
                _("GRASS Python package is required when tools mock is not provided")
            )

        self._tools = Tools()

    def list_raster_maps(self, pattern=None):
        """List raster maps available in the current mapset search path."""
        kwargs = {
            "type": "raster",
            "format": "json",
        }

        if pattern:
            kwargs["pattern"] = pattern

        rasters = self._tools.g_list(**kwargs)

        return {"rasters": rasters}


def build_tools(runner=None, parse_interface=None):
    """Discover the raster tools listed in `RASTER_TOOLS`.

    Tools whose interface cannot be discovered are skipped instead of
    creating an incomplete tool or preventing the remaining raster tools
    from being registered.
    """
    tools = []

    for tool_name in RASTER_TOOLS:
        try:
            tool = discover_grass_tool(
                tool_name,
                category="raster",
                runner=runner,
                parse_interface=parse_interface,
            )
        except RuntimeError:
            continue

        tools.append(tool)

    return tools
