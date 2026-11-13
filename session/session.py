"""
@package session::session

@brief Manage the active GRASS runtime session and GISRC environment.

Classes:
 - session::session::SessionCheck
 - session::session::GrassSession

SPDX-FileCopyrightText: GRASS Development Team
SPDX-License-Identifier: GPL-2.0-or-later

`GrassSession` models the currently active GRASS session by reading
`GISRC` and `GISBASE` from process environment, then loading
`GISDBASE`, `LOCATION_NAME`, and `MAPSET` from the `gisrc` file.

The module also validates that the session is complete and checks
minimum supported GRASS version using `$GISBASE/etc/VERSIONNUMBER`.
"""

import gettext
import os
import re
from dataclasses import dataclass, field

_ = gettext.gettext

# Environment variables GRASS sets for a session:
SESSION_ENV_VARIABLES = ("GISRC", "GISBASE")

# Keys stored inside the `gisrc` file, not the process environment:
GISRC_FILE_VARIABLES = ("GISDBASE", "LOCATION_NAME", "MAPSET")

# Minimum GRASS version grass-mcp requires, as a (major, minor) tuple.
MINIMUM_VERSION = (8, 5)

_VERSION_PATTERN = re.compile(r"(\d+)\.(\d+)")


def _is_location_valid(gisdbase, location):
    """Return True when location contains PERMANENT/DEFAULT_WIND."""
    if not gisdbase or not location:
        return False

    default_wind = os.path.join(gisdbase, location, "PERMANENT", "DEFAULT_WIND")
    return os.access(default_wind, os.F_OK)


def _is_mapset_valid(gisdbase, location, mapset):
    """Return True when mapset contains readable WIND file."""
    if not gisdbase or not location or not mapset:
        return False

    wind = os.path.join(gisdbase, location, mapset, "WIND")
    return os.access(wind, os.R_OK)


def _read_gisrc_file(gisrc_path):
    """Return the key-value pairs stored in a GRASS `gisrc` file.

    `gisrc` is a small ini-style file, one `KEY: value` pair per line.
    Returns an empty dict when `gisrc_path` is falsy or the file cannot
    be read, so callers can treat a missing session the same way as an
    empty one instead of handling I/O errors themselves.
    """
    if not gisrc_path:
        return {}

    values = {}
    try:
        with open(gisrc_path, encoding="utf-8") as handle:
            for line in handle:
                key, separator, value = line.partition(":")
                if not separator:
                    continue
                values[key.strip()] = value.strip()
    except OSError:
        return {}

    return values


def _read_installation_version(gisbase):
    """Return the (major, minor) version of a GRASS installation, or None.

    Reads `$GISBASE/etc/VERSIONNUMBER` rather than importing GRASS Python
    bindings (`grass.script`), since initializing those
    (`grass.script.setup.init()`) has known limitations when done more
    than once in the same process, and `grass-mcp` may need to check a
    version before deciding whether to use an installation at all.
    """
    if not gisbase:
        return None

    version_file = os.path.join(gisbase, "etc", "VERSIONNUMBER")
    try:
        with open(version_file, encoding="utf-8") as handle:
            first_line = handle.readline()
    except OSError:
        return None

    match = _VERSION_PATTERN.match(first_line.strip())
    if not match:
        return None

    return (int(match.group(1)), int(match.group(2)))


@dataclass
class SessionCheck:
    """Result of validating a `GrassSession` against grass-mcp's requirements."""

    ok: bool
    errors: list = field(default_factory=list)
    version: tuple | None = None


class GrassSession:
    """Read and describe the GRASS session active in the current process."""

    def __init__(self, env=None):
        self._env = dict(env) if env is not None else os.environ.copy()

    def _gisrc_values(self):
        """Return the `GISDBASE`/`LOCATION_NAME`/`MAPSET` stored in `gisrc`."""
        return _read_gisrc_file(self.gisrc)

    @property
    def gisrc(self):
        """Path to this session's `gisrc` configuration file."""
        return self._env.get("GISRC")

    @property
    def gisbase(self):
        """Installation directory of the GRASS runtime running this session."""
        return self._env.get("GISBASE")

    @property
    def gisdbase(self):
        """GRASS database directory used by this session."""
        return self._gisrc_values().get("GISDBASE")

    @property
    def location(self):
        """Location (project) open in this session."""
        return self._gisrc_values().get("LOCATION_NAME")

    @property
    def mapset(self):
        """Mapset active in this session."""
        return self._gisrc_values().get("MAPSET")

    @property
    def version(self):
        """Return the (major, minor) version of this session's GRASS installation.

        Returns None when it cannot be determined (missing `GISBASE`, or
        an unreadable/unparsable `VERSIONNUMBER` file).
        """
        return _read_installation_version(self.gisbase)

    def validate(self):
        """Return True when the current process runs inside a full GRASS session.

        Checks that `GISRC`, `GISBASE`, `GISDBASE`, `LOCATION_NAME`, and
        `MAPSET` are all set. `GISBASE` (the installation) is included
        deliberately, in addition to the data context variables, since
        the two identify different things (see module docstring).
        """
        return bool(
            self.gisrc
            and self.gisbase
            and self.gisdbase
            and self.location
            and self.mapset
        )

    def environment(self):
        """Return the information identifying this GRASS session.

        `GISRC` and `GISBASE` come from the process environment; `GISDBASE`,
        `LOCATION_NAME`, and `MAPSET` come from the `gisrc` file instead,
        since GRASS does not export them as environment variables (see
        module docstring).
        """
        gisrc_values = self._gisrc_values()
        return {
            "GISRC": self.gisrc,
            "GISBASE": self.gisbase,
            "GISDBASE": gisrc_values.get("GISDBASE"),
            "LOCATION_NAME": gisrc_values.get("LOCATION_NAME"),
            "MAPSET": gisrc_values.get("MAPSET"),
        }

    def info(self):
        """Return a compact summary identifying the current GRASS session."""
        env = self.environment()
        return {
            "gisdbase": env.get("GISDBASE"),
            "location": env.get("LOCATION_NAME"),
            "mapset": env.get("MAPSET"),
        }

    def check(self):
        """Validate this session against grass-mcp's requirements.

        Combines `validate()` with a minimum GRASS version check: v0.1
        only supports running inside an active GRASS session of the
        process it was started from, and requires that installation to
        be at least `MINIMUM_VERSION`.
        """
        errors = []

        if not self.validate():
            errors.append(
                _(
                    "No active GRASS session found. grass-mcp must be started "
                    "from a process with an active GRASS session (GISRC, "
                    "GISBASE, GISDBASE, LOCATION_NAME, and MAPSET all set)."
                )
            )

        env = self.environment()
        gisdbase = env.get("GISDBASE")
        location = env.get("LOCATION_NAME")
        mapset = env.get("MAPSET")

        if self.validate() and not _is_location_valid(gisdbase, location):
            errors.append(
                _(
                    "Current project '{}' in database '{}' is not a valid "
                    "GRASS project (missing PERMANENT/DEFAULT_WIND)."
                ).format(location, gisdbase)
            )

        if self.validate() and not _is_mapset_valid(gisdbase, location, mapset):
            errors.append(
                _(
                    "Current mapset '{}' in project '{}' is not a valid "
                    "GRASS mapset (missing or unreadable WIND)."
                ).format(mapset, location)
            )

        version = self.version
        if self.validate() and version is None:
            errors.append(
                _("Could not determine the GRASS version from GISBASE '{}'").format(
                    self.gisbase
                )
            )
        elif version is not None and version < MINIMUM_VERSION:
            errors.append(
                _("grass-mcp requires GRASS {} or newer, found {}").format(
                    ".".join(str(part) for part in MINIMUM_VERSION),
                    ".".join(str(part) for part in version),
                )
            )

        return SessionCheck(ok=not errors, errors=errors, version=version)
