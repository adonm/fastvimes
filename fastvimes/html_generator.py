"""FastHTML-based HTML generation for FastVimes."""

from fasthtml.common import *
from .database_service import DatabaseService


class HTMLGenerator:
    """Generate FastHTML components for FastVimes."""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def generate_base_layout(self, title: str, content, active_nav: str = ""):
        """Generate base layout with navigation."""
        return Html(
            Head(
                Title(f"{title} - FastVimes"),
                Meta(charset="utf-8"),
                Meta(name="viewport", content="width=device-width, initial-scale=1"),
                Link(rel="stylesheet", href="https://unpkg.com/bulma@1.0.4/css/bulma.css"),
                Script(src="https://unpkg.com/htmx.org@2.0.6/dist/htmx.js"),
                Script(defer=True, src="https://use.fontawesome.com/releases/v5.15.4/js/all.js"),
            ),
            Body(
                Section(
                    Div(
                        H1(title, cls="title"),
                        H2("Database Management Interface", cls="subtitle"),
                        cls="container"
                    ),
                    cls="hero is-primary"
                ),
                Section(
                    Div(
                        Div(
                            Div(
                                self._generate_nav(active_nav),
                                cls="column is-3"
                            ),
                            Div(
                                content,
                                cls="column"
                            ),
                            # Table data viewing area (initially hidden)
                            Div(
                                id="table-data-area",
                                cls="column is-hidden",
                                style="border-left: 1px solid #dbdbdb;"
                            ),
                            cls="columns"
                        ),
                        cls="container"
                    ),
                    cls="section"
                )
            )
        )

    def _generate_nav(self, active: str = ""):
        """Generate navigation menu."""
        return Aside(
            P("General", cls="menu-label"),
            Ul(
                Li(A("Dashboard", href="/admin/html/", cls="is-active" if active == "dashboard" else "")),
                Li(A("Tables", href="/admin/html/tables", cls="is-active" if active == "tables" else "")),
                Li(A("Schema", href="/admin/html/schema", cls="is-active" if active == "schema" else "")),
                Li(A("Configuration", href="/admin/html/config", cls="is-active" if active == "config" else "")),
                cls="menu-list"
            ),
            P("Open Tables", cls="menu-label", id="open-tables-label", style="display: none;"),
            Ul(
                # Dynamic table nav items will be added here
                cls="menu-list",
                id="open-tables-list"
            ),
            cls="menu"
        )

    def generate_tables_page(self):
        """Generate static tables page with HTMX loading."""
        content = Div(
            H3("Available Tables", cls="title is-4"),
            Div(
                P("Loading tables..."),
                hx_get="/admin/api/tables/html",
                hx_trigger="load",
                hx_target="this",
                id="tables-list"
            ),
            Div(
                # Table details will be loaded here
                id="table-detail",
                cls="mt-4"
            ),
            cls="box"
        )
        return self.generate_base_layout("Tables", content, "tables")

    def generate_dashboard_page(self):
        """Generate static dashboard page."""
        content = Div(
            H3("Welcome to FastVimes", cls="title is-4"),
            P("This is the admin dashboard for your FastVimes application."),
            P("Use the navigation menu to manage your database tables and configuration."),
            cls="box"
        )
        return self.generate_base_layout("FastVimes Admin", content, "dashboard")

    def generate_tables_fragment(self, tables):
        """Generate tables list fragment."""
        if not tables:
            return P("No tables found.")
        
        rows = []
        for name, config in tables.items():
            mode_class = "is-success" if config.mode == "readwrite" else "is-warning"
            rows.append(
                Tr(
                    Td(name),
                    Td(Span(config.mode, cls=f"tag {mode_class}")),
                    Td("Yes" if config.html else "No"),
                    Td(
                        Button(
                            "View Data",
                            cls="button is-small is-primary",
                            hx_get=f"/admin/fragments/data/{name}",
                            hx_target="#table-detail",
                            hx_indicator="#loading"
                        ),
                        " ",
                        Button(
                            "View HTML",
                            cls="button is-small is-info",
                            hx_get=f"/{name}/html",
                            hx_target="#table-detail",
                            hx_indicator="#loading"
                        ),
                        " ",
                        Button(
                            "Schema",
                            cls="button is-small is-light",
                            hx_get=f"/admin/fragments/schema/{name}",
                            hx_target="#table-detail",
                            hx_indicator="#loading"
                        ),
                    )
                )
            )
        
        return Div(
            Table(
                Thead(
                    Tr(
                        Th("Table"),
                        Th("Mode"),
                        Th("HTML"),
                        Th("Actions")
                    )
                ),
                Tbody(*rows),
                cls="table is-fullwidth"
            ),
            Div(
                Progress(max="100", cls="progress is-small is-primary"),
                id="loading",
                cls="htmx-indicator"
            )
        )

    def generate_data_fragment(self, table_name: str, data: list):
        """Generate table data fragment."""
        if not data:
            return P(f'No data found in table "{table_name}".')

        import json
        json_data = {"data": data, "table": table_name}
        formatted_json = json.dumps(json_data, indent=2)
        
        return Div(
            H4(f"{table_name.title()} Data (JSON)", cls="title is-5"),
            Pre(Code(formatted_json), cls="has-background-light p-4"),
            cls="content"
        )

    def generate_schema_fragment(self, table_name: str, schema: dict):
        """Generate schema fragment."""
        rows = []
        for field_name, field_type in schema.items():
            rows.append(
                Tr(
                    Td(Code(field_name)),
                    Td(Span(str(field_type), cls="tag is-info"))
                )
            )
        
        return Div(
            H4(f"{table_name.title()} Schema", cls="title is-5"),
            Table(
                Thead(
                    Tr(
                        Th("Field"),
                        Th("Type")
                    )
                ),
                Tbody(*rows),
                cls="table is-fullwidth"
            ),
            cls="content"
        )

    def generate_schema_page(self):
        """Generate static schema management page."""
        content = Div(
            H3("Schema Management", cls="title is-4"),
            P("Manage database tables and views"),
            Div(
                P("Loading schema information..."),
                hx_get="/admin/api/tables/html",
                hx_trigger="load",
                hx_target="this",
                id="schema-info"
            ),
            cls="box"
        )
        return self.generate_base_layout("Schema", content, "schema")

    def generate_config_page(self):
        """Generate static configuration page."""
        content = Div(
            H3("Configuration", cls="title is-4"),
            P("FastVimes configuration settings"),
            Div(
                P("Loading configuration..."),
                hx_get="/admin/api/config/html",
                hx_trigger="load",
                hx_target="this",
                id="config-info"
            ),
            cls="box"
        )
        return self.generate_base_layout("Configuration", content, "config")

    def generate_table_html(self, table_name: str, data: list[dict]):
        """Generate HTML table using FastHTML."""
        if not data:
            return Div(
                H1(table_name.title(), cls="title"),
                P("No data available", cls="subtitle"),
                cls="container"
            )
        
        # Generate table headers
        headers = list(data[0].keys())
        thead = Thead(
            Tr(*[Th(header.title()) for header in headers])
        )
        
        # Generate table rows
        tbody = Tbody(
            *[Tr(*[Td(str(row[header])) for header in headers]) for row in data]
        )
        
        return Div(
            H1(table_name.title(), cls="title"),
            Table(thead, tbody, cls="table is-striped is-hoverable"),
            cls="container"
        )

    def generate_tables_fragment(self, tables: dict):
        """Generate HTML fragment for tables list."""
        table_items = []
        for name, config in tables.items():
            table_items.append(
                Div(
                    H5(name.title(), cls="title is-5"),
                    P(f"Mode: {config.mode}"),
                    P(f"HTML enabled: {'Yes' if config.html else 'No'}"),
                    P(f"Primary key: {config.primary_key or 'None'}"),
                    Button(
                        "View Data", 
                        hx_post=f"/admin/api/open-table/{name}",
                        hx_target="#table-data-area",
                        hx_swap="innerHTML",
                        cls="button is-small is-primary"
                    ),
                    cls="box"
                )
            )
        
        if not table_items:
            return Div(P("No tables found"), cls="notification is-info")
        
        return Div(*table_items, cls="tables-list")

    def generate_config_fragment(self, config: dict):
        """Generate HTML fragment for configuration."""
        config_items = []
        for key, value in config.items():
            config_items.append(
                Div(
                    Strong(f"{key}: "),
                    Span(str(value)),
                    cls="field"
                )
            )
        
        return Div(
            H5("Current Configuration", cls="title is-5"),
            *config_items,
            cls="box"
        )

    def generate_table_viewer(self, table_name: str, data: list[dict]):
        """Generate table viewer with data and controls."""
        if not data:
            return Div(
                H4(f"{table_name.title()} - No Data", cls="title is-4"),
                P("This table is empty"),
                cls="content"
            )
        
        # Generate table headers
        headers = list(data[0].keys())
        thead = Thead(
            Tr(*[Th(header.title()) for header in headers])
        )
        
        # Generate table rows (limit to first 100 for performance)
        display_data = data[:100]
        tbody = Tbody(
            *[Tr(*[Td(str(row[header])) for header in headers]) for row in display_data]
        )
        
        # Add pagination info if data is truncated
        pagination_info = ""
        if len(data) > 100:
            pagination_info = P(f"Showing first 100 of {len(data)} records", cls="has-text-grey is-size-7")
        
        return Div(
            H4(f"{table_name.title()}", cls="title is-4"),
            pagination_info,
            Table(thead, tbody, cls="table is-striped is-hoverable is-fullwidth"),
            cls="content"
        )

    def generate_table_nav_item(self, table_name: str):
        """Generate navigation item for opened table with close button."""
        return Li(
            A(
                Span(table_name.title()),
                Button(
                    cls="delete is-small",
                    style="float: right; margin-top: 2px;",
                    hx_delete=f"/admin/api/close-table/{table_name}",
                    hx_confirm="Close this table?"
                ),
                href="#",
                hx_get=f"/admin/api/table-data/{table_name}/html",
                hx_target="#table-data-area",
                cls="is-active"
            ),
            id=f"nav-{table_name}",
            hx_swap_oob="beforeend:#open-tables-list"
        )

    def render_to_string(self, element) -> str:
        """Render FastHTML element to string."""
        from fasthtml.common import to_xml
        return to_xml(element)
