"""MCP server that runs GRASS modules in a configured GRASS mapset."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path

from mcp.server.fastmcp import FastMCP


SERVER_NAME = "grass-mcp"
OUTPUT_LIMIT = 200_000
MODULE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9]*\.[A-Za-z0-9][A-Za-z0-9_.]*$")
BLOCKED_MODULES = {
    "bash",
    "cmd",
    "exec",
    "powershell",
    "python",
    "python3",
    "sh",
}
MODULE_DISCOVERY_SCRIPT = Path(__file__).with_name("grass_mcp_module_discovery.py")
_mapset_lock = threading.Lock()

mcp = FastMCP(SERVER_NAME)


def _grass_executable() -> str:
    configured = os.environ.get("GRASS_EXECUTABLE")
    executable = configured or shutil.which("grass")
    if not executable:
        raise RuntimeError(
            "GRASS was not found. Set GRASS_EXECUTABLE to the GRASS launcher path "
            "or add the launcher to PATH."
        )

    path = Path(executable).expanduser()
    if path.is_file():
        return str(path.resolve())
    if configured:
        raise RuntimeError(f"GRASS_EXECUTABLE does not exist: {path}")
    return executable


def _mapset_path() -> Path:
    configured = os.environ.get("GRASS_MAPSET")
    if not configured:
        raise RuntimeError(
            "Set GRASS_MAPSET to the full path of the project mapset to use, "
            "for example C:\\grassdata\\project\\PERMANENT."
        )

    path = Path(configured).expanduser().resolve()
    if not path.is_dir():
        raise RuntimeError(f"GRASS_MAPSET is not an existing directory: {path}")
    if not (path / "WIND").is_file():
        raise RuntimeError(f"GRASS_MAPSET does not look like a mapset (missing WIND): {path}")
    return path


def _run_grass(arguments: list[str], timeout_seconds: int = 120) -> str:
    executable = _grass_executable()
    mapset = _mapset_path()
    command = [executable, str(mapset), "--exec", *arguments]

    # A single mapset cannot safely serve concurrent GRASS sessions.
    with _mapset_lock:
        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                shell=False,
            )
        except subprocess.TimeoutExpired as error:
            stdout = error.stdout or ""
            stderr = error.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            return f"GRASS command timed out after {timeout_seconds} seconds.\n{stdout}{stderr}"
        except OSError as error:
            raise RuntimeError(
                f"Could not start GRASS using {executable}: {error}. "
                "On Windows, configure GRASS_EXECUTABLE with the executable launcher "
                "provided by your GRASS installation."
            ) from error

    output = (result.stdout + result.stderr).strip()
    if not output:
        output = "(GRASS produced no output)"
    if len(output) > OUTPUT_LIMIT:
        output = output[:OUTPUT_LIMIT] + "\n[output truncated]"
    return f"Exit code: {result.returncode}\n{output}"


def _validate_module_call(
    module: str, args: list[str] | None, timeout_seconds: int
) -> list[str]:
    if not MODULE_NAME.fullmatch(module) or module.lower() in BLOCKED_MODULES:
        raise ValueError(f"Invalid or unsupported GRASS module name: {module!r}")
    if args is None:
        args = []
    if not isinstance(args, list) or any(not isinstance(arg, str) for arg in args):
        raise ValueError("args must be a list of strings")
    if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 900:
        raise ValueError("timeout_seconds must be between 1 and 900")
    if any("\x00" in arg for arg in args):
        raise ValueError("args cannot contain NUL characters")
    return [module, *args]


def _discover_modules() -> list[str]:
    if not MODULE_DISCOVERY_SCRIPT.is_file():
        raise RuntimeError(f"GRASS module discovery script is missing: {MODULE_DISCOVERY_SCRIPT}")

    result = subprocess.run(
        [
            _grass_executable(),
            str(_mapset_path()),
            "--exec",
            "python",
            str(MODULE_DISCOVERY_SCRIPT),
        ],
        check=False,
        capture_output=True,
        stdin=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        shell=False,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Could not discover installed GRASS modules: {detail}")

    try:
        modules = json.loads(result.stdout)
    except ValueError as error:
        raise RuntimeError("GRASS module discovery returned invalid JSON") from error
    if not isinstance(modules, list) or any(
        not isinstance(module, str)
        or not MODULE_NAME.fullmatch(module)
        or module.lower() in BLOCKED_MODULES
        for module in modules
    ):
        raise RuntimeError("GRASS module discovery returned invalid module names")
    return sorted(set(modules))


def _register_module_tools() -> int:
    modules = _discover_modules()
    names: set[str] = set()
    for module in modules:
        tool_name = f"grass_{module.replace('.', '_')}"
        if tool_name in names:
            raise RuntimeError(f"MCP tool name collision for GRASS module {module}")
        names.add(tool_name)

        def make_tool(module_name: str, name: str):
            def run_module(
                args: list[str] | None = None,
                timeout_seconds: int = 120,
            ) -> str:
                """Run this GRASS module in the configured mapset."""
                arguments = _validate_module_call(
                    module_name, args, timeout_seconds
                )
                return _run_grass(arguments, timeout_seconds)

            run_module.__name__ = name
            return run_module

        mcp.add_tool(
            make_tool(module, tool_name),
            name=tool_name,
            description=(
                f"Run GRASS module {module} in the configured mapset. "
                "Pass its options and parameters as separate strings in args, "
                "using normal GRASS command syntax. This module may modify data."
            ),
        )
    return len(modules)


@mcp.tool()
def grass_status() -> str:
    """Show the configured GRASS launcher, mapset, and GRASS version."""
    executable = _grass_executable()
    mapset = _mapset_path()
    version = subprocess.run(
        [executable, "--config", "version"],
        check=False,
        capture_output=True,
        stdin=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        shell=False,
    )
    if version.returncode:
        detail = (version.stderr or version.stdout).strip()
        raise RuntimeError(f"GRASS version check failed: {detail}")
    return f"GRASS version: {version.stdout.strip()}\nMapset: {mapset}"


@mcp.tool()
def run_grass_module(
    module: str,
    args: list[str] | None = None,
    timeout_seconds: int = 120,
) -> str:
    """Run a GRASS module in GRASS_MAPSET and return its output.

    Arguments are passed directly without a shell. Use GRASS module syntax, for
    example module='g.region', args=['-p'] or module='g.list', args=['type=raster'].
    This can modify data in the configured mapset.
    """
    arguments = _validate_module_call(module, args, timeout_seconds)
    return _run_grass(arguments, timeout_seconds)


if __name__ == "__main__":
    try:
        count = _register_module_tools()
    except Exception as error:
        print(f"grass-mcp: {error}", file=sys.stderr, flush=True)
        raise
    print(f"grass-mcp: loaded {count} GRASS module tools", file=sys.stderr, flush=True)
    mcp.run(transport="stdio")
