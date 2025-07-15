"""Table browser component for listing and navigating tables."""

from typing import Any

from nicegui import ui

from ..api_client import FastVimesAPIClient


class TableBrowser:
    """Component for browsing available tables and views."""

    def __init__(self, api_client: FastVimesAPIClient):
        """Initialize table browser with API client."""
        self.api_client = api_client

    def render(self):
        """Render the table browser interface."""
        with ui.card().classes("w-full"):
            ui.label("Tables").classes("text-h6")

            # Get list of tables
            try:
                tables = self.api_client.list_tables()
            except Exception as e:
                ui.label(f"Error loading tables: {e}").classes("text-red-500")
                return

            if not tables:
                ui.label("No tables found").classes("text-grey-6")
                return

            # Render table list
            with ui.column().classes("w-full"):
                for table in tables:
                    self._render_table_item(table)

    def _render_table_item(self, table: dict[str, Any]):
        """Render a single table item."""
        table_name = table["name"]
        table_type = table["type"]

        with ui.row().classes("w-full items-center"):
            # Table icon based on type
            icon = "table_chart" if table_type == "table" else "view_module"
            ui.icon(icon).classes("mr-2")

            # Table name and type
            with ui.column().classes("flex-grow"):
                ui.label(table_name).classes("font-bold")
                ui.label(f"({table_type})").classes("text-grey-6 text-sm")

            # Navigate to table button
            ui.button(
                "Explore", on_click=lambda t=table_name: ui.navigate.to(f"/table/{t}")
            ).props("dense outline")
