"""
@package tools::grass_tools

@brief Build Tool wrappers from the installed GRASS Tools API.

Classes:
 - tools::grass_tools::GrassTool

SPDX-FileCopyrightText: GRASS Development Team
SPDX-License-Identifier: GPL-2.0-or-later

Tool definitions are discovered from installed GRASS interfaces at
runtime instead of being hardcoded. This keeps parameter schemas,
flags, and descriptions aligned with the local GRASS installation.
"""

import gettext
import importlib

from tools.base import Tool, ToolResult

_ = gettext.gettext


class GrassTool(Tool):
    """Dynamic `Tool` wrapper around one GRASS tool.

    The tool schema and description are generated from the GRASS tool's
    interface definition.
    """

    def __init__(
        self,
        tool_name,
        definition,
        category="grass",
        runner=None,
    ):
        self.grass_tool_name = tool_name
        self.definition = definition
        self.name = grass_tool_to_tool_name(tool_name)
        self.description = definition["description"]
        self.category = category
        self._runner = runner

    @property
    def schema(self):
        """Return the JSON schema for the GRASS tool parameters."""
        return {
            "type": "object",
            "properties": self.definition["properties"],
            "required": self.definition["required"],
        }

    def execute(self, **kwargs):
        """Execute the wrapped GRASS tool."""
        try:
            result = self._run_tool(**kwargs)
        except Exception as error:  # noqa: BLE001
            return ToolResult(
                success=False,
                error=str(error),
            )

        return ToolResult(
            success=True,
            data=result,
        )

    def _run_tool(self, **kwargs):
        """Run the GRASS tool through `grass.tools.Tools`."""
        runner = self._runner or self._default_runner()
        method_name = self.grass_tool_name.replace(".", "_")
        method = getattr(runner, method_name)

        return method(**self._normalize_arguments(kwargs))

    @staticmethod
    def _normalize_arguments(arguments):
        """Convert tool schema arguments to `grass.tools.Tools` arguments.

        Boolean `flag_<name>` parameters are combined into the GRASS
        `flags` string.
        """
        normalized = {}
        flags = []

        for key, value in arguments.items():
            if key.startswith("flag_"):
                if value:
                    flags.append(key[len("flag_") :])
                continue

            normalized[key] = value

        if flags:
            normalized["flags"] = "".join(sorted(flags))

        return normalized

    @staticmethod
    def _default_runner():
        """Create the default GRASS Tools API runner."""
        grass_tools = importlib.import_module("grass.tools")
        return grass_tools.Tools()


def grass_tool_to_tool_name(tool_name):
    """Return a registry-safe name for a GRASS tool.

    For example, `v.buffer` becomes `v_buffer`.
    """
    return tool_name.replace(".", "_")


def discover_grass_tool(
    tool_name,
    category="grass",
    runner=None,
    parse_interface=None,
):
    """Build a `GrassTool` from the installed GRASS tool interface.

    The tool's parameters, flags, defaults, and description are read
    directly from its GRASS interface definition.

    If the interface cannot be parsed, no incomplete tool is created and
    a `RuntimeError` is raised. The caller can decide whether to skip the
    tool or propagate the error.
    """
    parse = parse_interface or _default_parse_interface

    try:
        task = parse(tool_name)
        definition = _tool_definition_from_task(
            tool_name,
            task,
        )
    except Exception as error:  # noqa: BLE001
        raise RuntimeError(
            _("Unable to discover interface for GRASS tool '{}': {}").format(
                tool_name, error
            )
        ) from error

    return GrassTool(
        tool_name,
        definition,
        category=category,
        runner=runner,
    )


def _default_parse_interface(tool_name):
    """Parse a GRASS tool interface using the installed GRASS API."""
    grass_task = importlib.import_module("grass.script.task")
    return grass_task.parse_interface(tool_name)


def _value(item, key, default=None):
    """Read a value from metadata represented as a dict or object."""
    if isinstance(item, dict):
        return item.get(key, default)

    if hasattr(item, key):
        return getattr(item, key)

    getter = getattr(item, "get", None)

    if callable(getter):
        try:
            return getter(key, default)
        except TypeError:
            return default

    return default


def _iter_items(task, key):
    """Return a metadata collection as an iterable."""
    return _value(task, key, []) or []


def _is_required(parameter):
    """Return whether a tool parameter is required."""
    required = _value(parameter, "required", False)

    if isinstance(required, str):
        return required.lower() in {"yes", "true", "1"}

    return bool(required)


def _is_multiple(parameter):
    """Return whether a tool parameter accepts multiple values."""
    multiple = _value(parameter, "multiple", False)

    if isinstance(multiple, str):
        return multiple.lower() in {"yes", "true", "1"}

    return bool(multiple)


def _normalize_option_type(raw_type):
    """Map a GRASS tool option type to a JSON schema type."""
    type_map = {
        "integer": "integer",
        "int": "integer",
        "float": "number",
        "double": "number",
        "string": "string",
        "file": "string",
        "map": "string",
    }

    if not raw_type:
        return "string"

    return type_map.get(
        str(raw_type).strip().lower(),
        "string",
    )


def _option_values(parameter):
    """Read enumeration values from tool parameter metadata."""
    values = _value(parameter, "values") or _value(parameter, "options")

    if not values:
        return []

    if isinstance(values, str):
        return [item.strip() for item in values.split(",") if item.strip()]

    if isinstance(values, (list, tuple)):
        return [str(item) for item in values]

    return []


def _parameter_to_schema(parameter):
    """Build a JSON schema object for one GRASS tool parameter."""
    option_type = _normalize_option_type(_value(parameter, "type"))
    values = _option_values(parameter)
    description = _value(parameter, "description") or ""

    if _is_multiple(parameter):
        item_schema = {
            "type": option_type,
        }

        if values:
            item_schema["enum"] = values

        return {
            "type": "array",
            "description": description,
            "items": item_schema,
        }

    schema = {
        "type": option_type,
        "description": description,
    }

    if values:
        schema["enum"] = values

    default = _value(parameter, "default")

    if default in (None, ""):
        default = _value(parameter, "answer")

    if default not in (None, ""):
        schema["default"] = default

    return schema


def _tool_definition_from_task(tool_name, task):
    """Build a normalized tool definition from a GRASS tool interface."""
    description = (
        _value(task, "description")
        or _value(task, "label")
        or _("Run GRASS tool {}.").format(tool_name)
    )

    properties = {}
    required = []

    for parameter in _iter_items(task, "params"):
        key = _value(parameter, "name")

        if not key:
            continue

        properties[key] = _parameter_to_schema(parameter)

        if _is_required(parameter):
            required.append(key)

    for flag in _iter_items(task, "flags"):
        flag_name = _value(flag, "name")

        if not flag_name:
            continue

        properties["flag_{}".format(flag_name)] = {
            "type": "boolean",
            "description": (
                _value(flag, "description") or _("Enable -{} flag").format(flag_name)
            ),
            "default": False,
        }

    return {
        "description": description,
        "properties": properties,
        "required": required,
    }
