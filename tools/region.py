"""
@package tools::region

@brief Provide high-level computational region tools.

Classes:
 - tools::region::RegionTools

SPDX-FileCopyrightText: GRASS Development Team
SPDX-License-Identifier: GPL-2.0-or-later

Region operations are implemented as explicit, high-level capabilities
because computational region is central to many GRASS workflows and
benefits from stable, easy-to-understand tool contracts.
"""

import gettext
import re

try:
    from grass.tools import Tools
except ModuleNotFoundError:  # pragma: no cover
    Tools = None

_ = gettext.gettext

_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")


def _validate_region_name(name):
    """Check that a region name is safe for `g.region` save/region options."""
    if not name:
        return False, _("Region name cannot be empty")
    if not _NAME_PATTERN.match(name):
        return False, _("Region name contains unsupported characters")
    return True, "ok"


class RegionTools:
    """Provide small, reliable computational region operations."""

    def __init__(self, tools=None):
        if tools is not None:
            self._tools = tools
            return

        if Tools is None:
            raise ModuleNotFoundError(
                _("GRASS Python package is required when tools mock is not provided")
            )

        self._tools = Tools()

    def get_current_region(self):
        """Return the current computational region including 2D and 3D data."""
        return self._tools.g_region(
            flags="p3",
            format="json",
        )

    def get_default_region(self):
        """Return the default computational region including 2D and 3D data."""
        return self._tools.g_region(
            flags="du3",
            format="json",
        )

    def set_current_region(self, name):
        """Set the current computational region from a saved region."""
        is_valid, reason = _validate_region_name(name)
        if not is_valid:
            raise ValueError(reason)

        self._tools.g_region(region=name)

        return {"current_region": name}

    def save_region(self, name):
        """Save the current computational region under a given name."""
        is_valid, reason = _validate_region_name(name)
        if not is_valid:
            raise ValueError(reason)

        self._tools.g_region(save=name)

        return {"saved_region": name}

    def list_saved_regions(self):
        """List saved regions available in the current mapset."""
        regions = self._tools.g_list(
            type="region",
            mapset=".",
            format="json",
        )

        return {"regions": regions}
