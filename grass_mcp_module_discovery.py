"""Print installed GRASS module names as JSON for the MCP server."""

from __future__ import annotations

import json
import re

from grass.script.core import get_commands


MODULE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9]*\.[A-Za-z0-9][A-Za-z0-9_.]*$")


def main() -> None:
    commands, _ = get_commands()
    modules = sorted(
        name
        for name in commands
        if MODULE_NAME.fullmatch(name)
        and name.lower()
        not in {"bash", "cmd", "exec", "powershell", "python", "python3", "sh"}
    )
    print(json.dumps(modules))


if __name__ == "__main__":
    main()
