"""Form generator component for creating and editing records."""

from typing import Any

from nicegui import ui

from ..api_client import FastVimesAPIClient


class FormGenerator:
    """Component for generating forms based on table schema."""

    def __init__(self, api_client: FastVimesAPIClient, table_name: str):
        """Initialize form generator for a specific table."""
        self.api_client = api_client
        self.table_name = table_name
        self.form_data = {}

    def render(self):
        """Render the form interface."""
        try:
            schema = self.api_client.get_table_schema(self.table_name)
        except Exception as e:
            ui.label(f"Error loading schema: {e}").classes("text-red-500")
            return

        with ui.card().classes("w-full"):
            ui.label(f"Add New {self.table_name}").classes("text-h6")

            # Generate form fields
            self._render_form_fields(schema)

            # Form actions
            self._render_form_actions()

    def _render_form_fields(self, schema: list[dict[str, Any]]):
        """Render form fields based on table schema."""
        with ui.column().classes("w-full gap-4"):
            for column in schema:
                self._render_form_field(column)

    def _render_form_field(self, column: dict[str, Any]):
        """Render a single form field."""
        column_name = column["name"]
        column_type = column["type"]
        nullable = column.get("nullable", True)
        is_key = column.get("key") == "PRI"

        # Skip primary key fields (auto-generated)
        if is_key and "auto_increment" in str(column).lower():
            return

        # Field label
        label = column_name.replace("_", " ").title()
        if not nullable:
            label += " *"

        # Different input types based on column type
        if "varchar" in column_type.lower() or "text" in column_type.lower():
            if "text" in column_type.lower():
                # Large text field
                ui.textarea(
                    label=label,
                    placeholder=f"Enter {label.lower()}...",
                    on_change=lambda value, col=column_name: self._update_form_data(
                        col, value
                    ),
                ).classes("w-full")
            else:
                # Regular text input
                ui.input(
                    label=label,
                    placeholder=f"Enter {label.lower()}...",
                    on_change=lambda value, col=column_name: self._update_form_data(
                        col, value
                    ),
                ).classes("w-full")

        elif "int" in column_type.lower():
            # Integer input
            ui.number(
                label=label,
                placeholder=f"Enter {label.lower()}...",
                on_change=lambda value, col=column_name: self._update_form_data(
                    col, value
                ),
            ).classes("w-full")

        elif "double" in column_type.lower() or "decimal" in column_type.lower():
            # Decimal input
            ui.number(
                label=label,
                placeholder=f"Enter {label.lower()}...",
                step=0.01,
                on_change=lambda value, col=column_name: self._update_form_data(
                    col, value
                ),
            ).classes("w-full")

        elif "date" in column_type.lower():
            # Date input
            ui.date(
                label=label,
                on_change=lambda value, col=column_name: self._update_form_data(
                    col, value
                ),
            ).classes("w-full")

        elif "bool" in column_type.lower():
            # Boolean checkbox
            ui.checkbox(
                text=label,
                on_change=lambda value, col=column_name: self._update_form_data(
                    col, value
                ),
            )

        else:
            # Generic text input for unknown types
            ui.input(
                label=f"{label} ({column_type})",
                placeholder=f"Enter {label.lower()}...",
                on_change=lambda value, col=column_name: self._update_form_data(
                    col, value
                ),
            ).classes("w-full")

    def _render_form_actions(self):
        """Render form action buttons."""
        with ui.row().classes("w-full justify-end"):
            ui.button("Clear", on_click=self._clear_form).props("outline")

            ui.button("Save", on_click=self._save_record).props("color=primary")

    def _update_form_data(self, column: str, value: Any):
        """Update form data for a column."""
        self.form_data[column] = value

    def _clear_form(self):
        """Clear all form data."""
        self.form_data = {}
        ui.notify("Form cleared", type="info")

    def _save_record(self):
        """Save the form data as a new record."""
        if not self.form_data:
            ui.notify("Please fill in some data before saving", type="warning")
            return

        try:
            # Filter out empty values
            clean_data = {
                k: v for k, v in self.form_data.items() if v is not None and v != ""
            }

            result = self.api_client.create_record(self.table_name, clean_data)
            ui.notify(
                f"Record created successfully! ID: {result.get('id')}", type="positive"
            )
            self._clear_form()
        except Exception as e:
            ui.notify(f"Error creating record: {str(e)}", type="negative")
