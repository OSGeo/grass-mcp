"""
@package session

@brief GRASS session package exports.

Classes:
 - session::GrassSession
 - session::SessionCheck

SPDX-FileCopyrightText: GRASS Development Team
SPDX-License-Identifier: GPL-2.0-or-later

`grass-mcp` currently operates on the active GRASS runtime session of
the process where it is started. This package exposes the primitives
needed for that: `GrassSession` for environment/version inspection and
`SessionCheck` for requirement validation.
"""

from .session import MINIMUM_VERSION, GrassSession, SessionCheck

__all__ = [
    "GrassSession",
    "SessionCheck",
    "MINIMUM_VERSION",
]
