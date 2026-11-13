"""
@package server

@brief MCP server entrypoint exposing GRASS capabilities.

Functions:
 - server::build_registry
 - server::create_server
 - server::main

SPDX-FileCopyrightText: GRASS Development Team
SPDX-License-Identifier: GPL-2.0-or-later

The module exposes `ToolRegistry` capabilities over MCP stdio transport.
It stays intentionally thin: request/response translation is here, while
GRASS-specific logic remains in `session` and `tools` modules. This
keeps business logic reusable outside MCP as well.
"""

import asyncio
import gettext
import json

try:
    import mcp_types as types
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp_types import TextContent
    from mcp_types import Tool as MCPTool
except ModuleNotFoundError:  # pragma: no cover
    types = None
    Server = None
    stdio_server = None
    TextContent = None
    MCPTool = None

from session import GrassSession
from tools import FunctionTool, ToolRegistry, raster, vector
from tools.project import ProjectTools
from tools.region import RegionTools

_ = gettext.gettext

MCP_NAME = "GRASS MCP"


def build_registry(session=None, runner=None, parse_interface=None):
    """Build the `ToolRegistry` exposed by the MCP server."""
    session = session or GrassSession()

    check = session.check()
    if not check.ok:
        raise RuntimeError("\n".join(check.errors))

    project_tools = ProjectTools()
    region_tools = RegionTools()
    raster_tools = raster.RasterTools()
    vector_tools = vector.VectorTools()

    registry = ToolRegistry()

    registry.register(
        FunctionTool(
            name="get_session_info",
            description=_(
                "Return identifying information about the active GRASS "
                "session (database, project, and mapset)."
            ),
            schema={"type": "object", "properties": {}, "required": []},
            handler=session.info,
            category="session",
        )
    )
    registry.register(
        FunctionTool(
            name="get_project_context",
            description=_(
                "Return the current GRASS database, project, mapset, CRS, "
                "and mapset search path."
            ),
            schema={"type": "object", "properties": {}, "required": []},
            handler=project_tools.get_project_context,
            category="project",
        )
    )
    registry.register(
        FunctionTool(
            name="get_current_region",
            description=_(
                "Return the current computational region, including 2D "
                "and 3D extent and resolution."
            ),
            schema={"type": "object", "properties": {}, "required": []},
            handler=region_tools.get_current_region,
            category="region",
        )
    )
    registry.register(
        FunctionTool(
            name="get_default_region",
            description=_(
                "Return the default computational region, including 2D "
                "and 3D extent and resolution."
            ),
            schema={"type": "object", "properties": {}, "required": []},
            handler=region_tools.get_default_region,
            category="region",
        )
    )
    registry.register(
        FunctionTool(
            name="save_region",
            description=_(
                "Save the current computational region under the given name."
            ),
            schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            handler=region_tools.save_region,
            category="region",
        )
    )
    registry.register(
        FunctionTool(
            name="set_current_region",
            description=_("Set the current computational region from a saved region."),
            schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            handler=region_tools.set_current_region,
            category="region",
        )
    )
    registry.register(
        FunctionTool(
            name="list_saved_regions",
            description=_("List saved computational regions in the current mapset."),
            schema={"type": "object", "properties": {}, "required": []},
            handler=region_tools.list_saved_regions,
            category="region",
        )
    )
    registry.register(
        FunctionTool(
            name="list_raster_maps",
            description=_(
                "List raster maps available in the current mapset search path."
            ),
            schema={
                "type": "object",
                "properties": {"pattern": {"type": "string"}},
                "required": [],
            },
            handler=raster_tools.list_raster_maps,
            category="raster",
        )
    )
    registry.register(
        FunctionTool(
            name="list_vector_maps",
            description=_(
                "List vector maps available in the current mapset search path."
            ),
            schema={
                "type": "object",
                "properties": {"pattern": {"type": "string"}},
                "required": [],
            },
            handler=vector_tools.list_vector_maps,
            category="vector",
        )
    )

    for tool in raster.build_tools(
        runner=runner,
        parse_interface=parse_interface,
    ):
        registry.register(tool)

    for tool in vector.build_tools(
        runner=runner,
        parse_interface=parse_interface,
    ):
        registry.register(tool)

    return registry


def create_server(registry=None):
    """Create the MCP server backed by `ToolRegistry`."""
    if Server is None:
        raise ModuleNotFoundError(
            _("The 'mcp' package is required to run the GRASS MCP server")
        )

    if registry is None:
        registry = build_registry()

    async def list_tools(ctx, params):
        """Return GRASS capabilities as MCP tool definitions."""
        return types.ListToolsResult(
            tools=[
                MCPTool(
                    name=tool.name,
                    description=tool.description,
                    inputSchema=tool.schema,
                )
                for tool in registry.list()
            ]
        )

    async def call_tool(ctx, params):
        """Execute a GRASS capability requested through MCP."""
        result = registry.execute(params.name, **(params.arguments or {}))
        payload = result.data if result.success else {"error": result.error}

        return types.CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(payload, default=str),
                )
            ],
            is_error=not result.success,
        )

    return Server(
        MCP_NAME,
        on_list_tools=list_tools,
        on_call_tool=call_tool,
    )


async def _run():
    """Run the MCP server over stdio."""
    server = create_server()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Run the GRASS MCP server over stdio."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
