"""Handler for creating Datawrapper charts."""

import json
import os
from typing import Any

from datawrapper import Datawrapper
from mcp.types import TextContent

from ..config import CHART_CLASSES, MAP_TYPE_ALIASES
from ..types import CreateChartArgs
from ..utils import json_to_dataframe


async def create_chart(arguments: CreateChartArgs) -> list[TextContent]:
    """Create a chart with full Pydantic model configuration."""
    chart_type = arguments["chart_type"]

    # Convert data to DataFrame
    df = json_to_dataframe(arguments["data"])

    # Map chart types are not currently represented by Pydantic chart classes,
    # so route those through the low-level Datawrapper API.
    if chart_type in MAP_TYPE_ALIASES:
        token = os.getenv("DATAWRAPPER_ACCESS_TOKEN")
        if not token:
            raise ValueError("DATAWRAPPER_ACCESS_TOKEN environment variable is required")

        api_type = MAP_TYPE_ALIASES[chart_type]
        cfg = arguments.get("chart_config", {}) or {}
        title = cfg.get("title", "New Map")

        dw = Datawrapper(access_token=token)
        created = dw.create_chart(title=title, chart_type=api_type, data=df)
        chart_id = created.get("id")

        # Apply chart config as metadata blocks (best effort).
        metadata_updates: dict[str, Any] = {}
        describe_fields = [
            "title",
            "intro",
            "notes",
            "byline",
            "source-name",
            "source-url",
            "aria-description",
        ]
        describe = {k: cfg[k] for k in describe_fields if k in cfg}
        if describe:
            metadata_updates["describe"] = describe

        visualize = {k: v for k, v in cfg.items() if k not in set(describe_fields)}
        if visualize:
            metadata_updates["visualize"] = visualize

        if metadata_updates:
            dw.update_chart(chart_id=chart_id, metadata=metadata_updates)

        edit_url = f"https://app.datawrapper.de/edit/{chart_id}/visualize#refine"
        result = {
            "chart_id": chart_id,
            "chart_type": chart_type,
            "title": title,
            "edit_url": edit_url,
            "message": (
                f"Chart created successfully! Edit it at: {edit_url}\n"
                f"Use publish_chart with chart_id '{chart_id}' to make it public."
            ),
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    # Get chart class and validate config
    chart_class: type[Any] = CHART_CLASSES[chart_type]

    # Validate and create chart using Pydantic model
    try:
        chart = chart_class.model_validate(arguments["chart_config"])
    except Exception as e:
        raise ValueError(
            f"Invalid chart configuration: {str(e)}\n\n"
            f"Use get_chart_schema with chart_type '{chart_type}' "
            f"to see the valid schema."
        )

    # Set data on chart instance
    chart.data = df

    # Create chart using Pydantic instance method
    chart.create()

    result = {
        "chart_id": chart.chart_id,
        "chart_type": chart_type,
        "title": chart.title,
        "edit_url": chart.get_editor_url(),
        "message": (
            f"Chart created successfully! Edit it at: {chart.get_editor_url()}\n"
            f"Use publish_chart with chart_id '{chart.chart_id}' to make it public."
        ),
    }

    return [TextContent(type="text", text=json.dumps(result, indent=2))]
