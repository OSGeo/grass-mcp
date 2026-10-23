# grass-mcp

Model Context Protocol (MCP) server for GRASS: geospatial raster, vector,
and imagery processing

## Run the MCP server

The server requires Python 3.10 or later, uses the official MCP Python SDK, and
starts over standard input/output. Install its Python dependency with
`python -m pip install -r requirements.txt`.

Set these environment variables in the MCP client configuration:

- `GRASS_EXECUTABLE`: path to the GRASS launcher, or leave unset if `grass` is on
  `PATH`.
- `GRASS_MAPSET`: full path to an existing mapset directory, such as
  `C:\\grassdata\\myproject\\PERMANENT`.

Example MCP server entry (replace the Python and GRASS paths with the paths on
your computer):

```json
{
  "mcpServers": {
    "grass-mcp": {
      "command": "C:\\path\\to\\python.exe",
      "args": [
        "C:\\Users\\guilherme.barbosa\\Documents\\GRASS\\grass-mcp\\grass_mcp_server.py"
      ],
      "env": {
        "GRASS_EXECUTABLE": "C:\\path\\to\\grass launcher",
        "GRASS_MAPSET": "C:\\path\\to\\grassdata\\project\\PERMANENT"
      }
    }
  }
}
```

On startup, the server discovers the modules installed with GRASS and exposes
each one as an MCP tool. A module such as `r.mapcalc` is available as
`grass_r_mapcalc`; pass its command-line options as separate strings in the
`args` list. For example, `grass_g_region` accepts `args: ["-p"]`. The exact
tool list depends on the configured GRASS installation. Restart the MCP client
after changing installations so it reloads the tools.

The server also exposes `grass_status` and `run_grass_module`. The generic
runner accepts a module name and is useful when calling modules not shown as
individual tools. Both forms execute in the configured mapset and can change
its data.
