"""
FastVimes forms generation using python-fasthtml.

This module provides form generation capabilities for FastVimes using the
python-fasthtml library for clean, safe HTML generation.
"""

from typing import Any, Union

from fasthtml.common import (
    A,
    Body,
    Button,
    Div,
    Form,
    Head,
    Html,
    Input,
    Label,
    Link,
    Meta,
    Option,
    P,
    Script,
    Select,
    Table,
    Tbody,
    Td,
    Th,
    Thead,
    Title,
    Tr,
)
from pydantic import BaseModel


class FormGenerator:
    """Generate HTML forms using python-fasthtml."""

    def __init__(self, app: Any):
        self.app = app

    def generate_form(
        self,
        model: type[BaseModel],
        action: str,
        method: str = "POST",
        submit_text: str = "Submit",
        data: dict[str, Any] | None = None,
        **kwargs,
    ) -> str:
        """Generate a form from a Pydantic model."""

        form_fields = []

        # Generate form fields from model
        for field_name, field_info in model.model_fields.items():
            field_type = field_info.annotation
            field_value = data.get(field_name, "") if data else ""

            # Create field based on type
            field_html = self._create_field(
                field_name, field_type, field_value, field_info
            )
            form_fields.append(field_html)

        # Create form
        form_html = Form(
            *form_fields,
            Button(submit_text, type="submit", cls="button is-primary"),
            action=action,
            method=method,
            cls="box",
        )

        return self._render_html(form_html)

    def _create_field(
        self, field_name: str, field_type: type, value: Any = "", field_info: Any = None
    ) -> Div:
        """Create a form field based on type."""

        field_label = Label(self._format_field_name(field_name), cls="label")

        # Determine input type
        input_type = self._get_input_type(field_type)

        if input_type == "select":
            # For select fields, you'd need to define options
            field_input = Select(
                Option("", value="", selected=not value),
                name=field_name,
                id=field_name,
                cls="select",
            )
        elif input_type == "checkbox":
            field_input = Input(
                type="checkbox",
                name=field_name,
                id=field_name,
                value="true",
                checked=bool(value),
                cls="checkbox",
            )
        elif input_type == "textarea":
            field_input = Input(
                type="text",  # FastHTML doesn't have textarea, use text
                name=field_name,
                id=field_name,
                value=str(value),
                cls="textarea",
            )
        else:
            field_input = Input(
                type=input_type,
                name=field_name,
                id=field_name,
                value=str(value),
                cls="input",
            )

        return Div(field_label, Div(field_input, cls="control"), cls="field")

    def _get_input_type(self, field_type: type) -> str:
        """Get HTML input type from Python type."""

        # Handle Optional types
        if hasattr(field_type, "__origin__") and field_type.__origin__ is type(None):
            return "text"

        # Handle Union types (Optional is Union[T, None])
        if hasattr(field_type, "__origin__"):
            if field_type.__origin__ is Union:
                # Get the non-None type
                args = [arg for arg in field_type.__args__ if arg is not type(None)]
                if args:
                    field_type = args[0]

        # Type-based mapping
        if field_type is int or field_type is float:
            return "number"
        elif field_type is bool:
            return "checkbox"
        elif field_type is str:
            return "text"
        else:
            return "text"

    def _format_field_name(self, field_name: str) -> str:
        """Format field name for display."""
        return field_name.replace("_", " ").title()

    def generate_table_list(
        self,
        data: list[dict[str, Any]],
        table_name: str,
        columns: list[str] | None = None,
        actions: list[str] | None = None,
    ) -> str:
        """Generate a table listing with data."""

        if not data:
            return self._render_html(
                Div(P("No data available", cls="has-text-centered"), cls="box")
            )

        # Use provided columns or infer from first row
        if columns is None:
            columns = list(data[0].keys()) if data else []

        # Create table headers
        headers = [Th(self._format_field_name(col)) for col in columns]
        if actions:
            headers.append(Th("Actions"))

        # Create table rows
        rows = []
        for row_data in data:
            cells = [Td(str(row_data.get(col, ""))) for col in columns]

            # Add action buttons if specified
            if actions:
                action_buttons = []
                for action in actions:
                    action_buttons.append(
                        A(
                            action.title(),
                            href=f"/{table_name}/{row_data.get('id', '')}/{action}",
                            cls="button is-small is-link",
                        )
                    )
                cells.append(Td(*action_buttons))

            rows.append(Tr(*cells))

        table_html = Table(
            Thead(Tr(*headers)), Tbody(*rows), cls="table is-fullwidth is-striped"
        )

        return self._render_html(table_html)

    def wrap_in_html(self, content: str, title: str = "FastVimes") -> str:
        """Wrap content in a full HTML document."""

        html_doc = Html(
            Head(
                Meta(charset="utf-8"),
                Meta(name="viewport", content="width=device-width, initial-scale=1"),
                Title(title),
                Link(
                    rel="stylesheet",
                    href="https://unpkg.com/bulma@1.0.4/css/bulma.css",
                ),
                Script(src="https://unpkg.com/htmx.org@2.0.6/dist/htmx.js"),
                Script(
                    defer=True,
                    src="https://use.fontawesome.com/releases/v5.15.4/js/all.js",
                ),
            ),
            Body(Div(content, cls="container mt-4")),
        )

        return self._render_html(html_doc)

    def _render_html(self, element) -> str:
        """Render FastHTML element to string."""
        if hasattr(element, "__html__"):
            return element.__html__()
        elif hasattr(element, "render"):
            return element.render()
        else:
            return str(element)


def generate_form_for_table(
    app: Any,
    table_name: str,
    action: str,
    method: str = "POST",
    data: dict[str, Any] | None = None,
) -> str:
    """Convenience function to generate a form for a database table."""

    model = app.get_table_dataclass(table_name)
    generator = FormGenerator(app)

    return generator.generate_form(model=model, action=action, method=method, data=data)
