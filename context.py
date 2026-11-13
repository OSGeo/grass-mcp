"""
@package context

@brief Build a compact snapshot of the current GRASS session.

Classes:
 - context::GrassContext

SPDX-FileCopyrightText: GRASS Development Team
SPDX-License-Identifier: GPL-2.0-or-later

`GrassSession` answers where the server is running; `GrassContext`
answers what is available in that runtime (project, region, raster and
vector map names). The snapshot is intentionally compact so it can be
used as context for an LLM-driven client without pulling heavy metadata.

This layer does not call GRASS modules directly. It only composes
results returned by `ToolRegistry`, so the same semantics are used as in
MCP tool execution.
"""

import gettext

_ = gettext.gettext


class GrassContext:
    """Compose a session and tool registry into a current-state snapshot."""

    def __init__(self, session, registry):
        self.session = session
        self.registry = registry

    def snapshot(self):
        """Return a compact snapshot of the current GRASS session."""
        if not self.session.validate():
            raise RuntimeError(_("No active GRASS session"))

        project = self.registry.execute("get_project_context")
        region = self.registry.execute("get_current_region")
        rasters = self.registry.execute("list_raster_maps")
        vectors = self.registry.execute("list_vector_maps")

        return {
            "session": self.session.info(),
            "project": project.data if project.success else {},
            "region": region.data if region.success else {},
            "rasters": (rasters.data.get("rasters", []) if rasters.success else []),
            "vectors": (vectors.data.get("vectors", []) if vectors.success else []),
        }
