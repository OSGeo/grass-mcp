"""
@package tools::project

@brief Provide GRASS project and database context.

Classes:
 - tools::project::ProjectTools

SPDX-FileCopyrightText: GRASS Development Team
SPDX-License-Identifier: GPL-2.0-or-later

`ProjectTools` exposes high-level project context (database, project,
mapset, CRS, search path) independent of specific GRASS module tools.
"""

import gettext

try:
    import grass.script as gs
except ModuleNotFoundError:  # pragma: no cover
    gs = None

try:
    from grass.tools import Tools
except ModuleNotFoundError:  # pragma: no cover
    Tools = None

_ = gettext.gettext


class ProjectTools:
    """Provide the current GRASS database, project, mapset, and CRS context."""

    def __init__(self, tools=None):
        if tools is not None:
            self._tools = tools
            return

        if Tools is None:
            raise ModuleNotFoundError(
                _("GRASS Python package is required when tools mock is not provided")
            )
        if gs is None:
            raise ModuleNotFoundError(
                _("GRASS Python package is required when tools mock is not provided")
            )

        self._tools = Tools()

    def get_project_context(self):
        """Return the current GRASS database, project, mapset, CRS, and search path."""
        if gs is None:
            raise ModuleNotFoundError(_("GRASS Python package is required"))

        env = gs.gisenv()

        projection = self._tools.g_proj(
            flags="p",
            format="projjson",
        ).json
        crs_id = projection.get("id") or {}

        search_path = self._tools.g_mapsets(
            flags="p",
            format="json",
        ).json

        epsg = crs_id.get("code") if crs_id.get("authority") == "EPSG" else None

        return {
            "grassdb": env.get("GISDBASE"),
            "project": env.get("LOCATION_NAME"),
            "mapset": env.get("MAPSET"),
            "crs": {
                "name": projection.get("name"),
                "epsg": epsg,
            },
            "search_path": search_path,
        }
