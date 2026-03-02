"""Handler for retrieving chart schemas."""

import json
from typing import Any

from mcp.types import TextContent

from config import CHART_CLASSES, MAP_TYPE_ALIASES
from dw_types import GetChartSchemaArgs


async def get_chart_schema(arguments: GetChartSchemaArgs) -> list[TextContent]:
    """Get the Pydantic schema for a chart type."""
    chart_type = arguments["chart_type"]

    if chart_type in MAP_TYPE_ALIASES:
        result = {
            "chart_type": chart_type,
            "class_name": "MapChart (API-backed)",
            "schema": {
                "type": "object",
                "description": (
                    "Map chart config passed through to Datawrapper metadata. "
                    "Common fields include title, intro, notes, byline, source-name, "
                    "source-url, aria-description, tooltip-title, tooltip-body, "
                    "tooltip-enabled, and tooltip-sticky."
                ),
                "additionalProperties": True,
            },
            "usage": (
                "Map chart types are created via Datawrapper's raw chart-type API. "
                "Provide chart_config fields as high-level Datawrapper metadata keys."
            ),
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    chart_class: type[Any] = CHART_CLASSES[chart_type]

    schema = chart_class.model_json_schema()

    # Remove examples that contain DataFrames (not JSON serializable)
    if "examples" in schema:
        del schema["examples"]

    result = {
        "chart_type": chart_type,
        "class_name": chart_class.__name__,
        "schema": schema,
        "usage": (
            "Use this schema to construct a chart_config dict for create_chart_advanced. "
            "The schema shows all available properties, their types, and descriptions."
        ),
    }

    return [TextContent(type="text", text=json.dumps(result, indent=2))]
