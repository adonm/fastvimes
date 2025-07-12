"""FastHTML-based HTML generation for FastVimes."""

from typing import Any, Callable
from functools import partial
from fasthtml.common import (
    H1,
    H2,
    H3,
    H4,
    H5,
    A,
    Aside,
    Body,
    Button,
    Code,
    Div,
    Head,
    Html,
    Li,
    Link,
    Meta,
    P,
    Pre,
    Progress,
    Script,
    Section,
    Span,
    Strong,
    Table,
    Tbody,
    Td,
    Th,
    Thead,
    Title,
    Tr,
    Ul,
    to_xml,
    Small,
    Label,
    Form,
    Textarea,
    Input,
    Iframe,
    Style,
)

from .database_service import DatabaseService


def is_htmx_request(request=None) -> bool:
    """Check if request is coming from HTMX."""
    if request is None:
        return False
    
    # HTMX sets these headers
    return (
        request.headers.get("HX-Request") == "true" or
        request.headers.get("hx-request") == "true"
    )


def render_fragment_or_standalone(fragment_content, title: str = "FastVimes", request=None):
    """
    Render content as either an HTMX fragment or standalone page.
    
    If it's an HTMX request, return just the content.
    If it's a standalone request, wrap in a minimal HTML page with styling.
    """
    if is_htmx_request(request):
        # Return just the fragment for HTMX requests
        return fragment_content
    else:
        # Return full HTML page for standalone access
        return Html(
            fastvimes_head(title, include_htmx=False, minimal=True),
            Body(
                Section(
                    Div(
                        H1(title, cls=CSS.TITLE),
                        fragment_content,
                        cls=CSS.CONTAINER,
                    ),
                    cls=CSS.SECTION,
                ),
                style="min-height: 100vh;"
            ),
        )


# CSS Class Constants
class CSS:
    """Bulma CSS class constants for consistency."""

    # Layout
    CONTAINER = "container"
    SECTION = "section"
    COLUMNS = "columns"
    COLUMN = "column"
    BOX = "box"
    CONTENT = "content"

    # Typography
    TITLE = "title"
    SUBTITLE = "subtitle"
    TITLE_4 = "title is-4"
    TITLE_5 = "title is-5"

    # Buttons
    BTN_PRIMARY = "button is-small is-primary"
    BTN_INFO = "button is-small is-info"
    BTN_LIGHT = "button is-small is-light"
    BTN_DELETE = "delete is-small"

    # Tables
    TABLE = "table is-striped is-hoverable is-fullwidth"
    TABLE_SIMPLE = "table is-fullwidth"

    # Navigation
    MENU = "menu"
    MENU_LABEL = "menu-label"
    MENU_LIST = "menu-list"
    IS_ACTIVE = "is-active"

    # Hero
    HERO_PRIMARY = "hero is-primary"

    # Tags/Status
    TAG_SUCCESS = "tag is-success"
    TAG_WARNING = "tag is-warning"
    TAG_INFO = "tag is-info"

    # Utilities
    HIDDEN = "is-hidden"
    TEXT_GREY = "has-text-grey is-size-7"
    BG_LIGHT = "has-background-light p-4"


# Common HTML Components
def fastvimes_head(title: str, include_htmx: bool = True, minimal: bool = False) -> Head:
    """Standard head with consistent meta, CSS, and JS."""
    
    # Gruvbox dark theme CSS overrides for Bulma
    gruvbox_css = """
        :root {
            --gruvbox-dark0: #282828;
            --gruvbox-dark1: #3c3836;
            --gruvbox-dark2: #504945;
            --gruvbox-dark3: #665c54;
            --gruvbox-light0: #fbf1c7;
            --gruvbox-light1: #ebdbb2;
            --gruvbox-light2: #d5c4a1;
            --gruvbox-light3: #bdae93;
            --gruvbox-red: #fb4934;
            --gruvbox-green: #b8bb26;
            --gruvbox-yellow: #fabd2f;
            --gruvbox-blue: #83a598;
            --gruvbox-purple: #d3869b;
            --gruvbox-aqua: #8ec07c;
            --gruvbox-orange: #fe8019;
        }
        
        body {
            background-color: var(--gruvbox-dark0) !important;
            color: var(--gruvbox-light1) !important;
        }
        
        /* Hero sections */
        .hero.is-dark {
            background-color: var(--gruvbox-dark1) !important;
            color: var(--gruvbox-light0) !important;
        }
        
        /* Panels and boxes */
        .panel, .box, .notification {
            background-color: var(--gruvbox-dark1) !important;
            color: var(--gruvbox-light1) !important;
            border-color: var(--gruvbox-dark3) !important;
        }
        
        .panel-heading {
            background-color: var(--gruvbox-dark2) !important;
            color: var(--gruvbox-light0) !important;
            border-color: var(--gruvbox-dark3) !important;
        }
        
        .panel-block {
            border-color: var(--gruvbox-dark3) !important;
            color: var(--gruvbox-light2) !important;
        }
        
        .panel-block:hover, .panel-block.is-active {
            background-color: var(--gruvbox-dark2) !important;
            color: var(--gruvbox-light0) !important;
        }
        
        /* Tables */
        .table {
            background-color: var(--gruvbox-dark1) !important;
            color: var(--gruvbox-light1) !important;
        }
        
        .table th {
            background-color: var(--gruvbox-dark2) !important;
            color: var(--gruvbox-light0) !important;
            border-color: var(--gruvbox-dark3) !important;
        }
        
        .table td {
            border-color: var(--gruvbox-dark3) !important;
            color: var(--gruvbox-light2) !important;
        }
        
        .table.is-striped tbody tr:nth-child(even) {
            background-color: var(--gruvbox-dark0) !important;
        }
        
        .table.is-hoverable tbody tr:hover {
            background-color: var(--gruvbox-dark2) !important;
        }
        
        /* Forms */
        .input, .textarea, .select select {
            background-color: var(--gruvbox-dark2) !important;
            color: var(--gruvbox-light1) !important;
            border-color: var(--gruvbox-dark3) !important;
        }
        
        .input:focus, .textarea:focus, .select select:focus {
            border-color: var(--gruvbox-blue) !important;
            box-shadow: 0 0 0 0.125em rgba(131, 165, 152, 0.25) !important;
        }
        
        .label {
            color: var(--gruvbox-light2) !important;
        }
        
        /* Buttons */
        .button.is-primary {
            background-color: var(--gruvbox-blue) !important;
            border-color: var(--gruvbox-blue) !important;
            color: var(--gruvbox-dark0) !important;
        }
        
        .button.is-primary:hover {
            background-color: #7c9584 !important;
            border-color: #7c9584 !important;
        }
        
        .button.is-info {
            background-color: var(--gruvbox-aqua) !important;
            border-color: var(--gruvbox-aqua) !important;
            color: var(--gruvbox-dark0) !important;
        }
        
        .button.is-light {
            background-color: var(--gruvbox-dark3) !important;
            border-color: var(--gruvbox-dark3) !important;
            color: var(--gruvbox-light1) !important;
        }
        
        /* Tabs */
        .tabs ul {
            border-bottom-color: var(--gruvbox-dark3) !important;
        }
        
        .tabs.is-boxed li.is-active a {
            background-color: var(--gruvbox-dark2) !important;
            border-color: var(--gruvbox-dark3) !important;
            color: var(--gruvbox-light0) !important;
        }
        
        .tabs a {
            color: var(--gruvbox-light2) !important;
            border-bottom-color: var(--gruvbox-dark3) !important;
        }
        
        .tabs a:hover {
            color: var(--gruvbox-light0) !important;
            border-bottom-color: var(--gruvbox-blue) !important;
        }
        
        /* Notifications */
        .notification.is-info {
            background-color: var(--gruvbox-dark2) !important;
            color: var(--gruvbox-light1) !important;
        }
        
        .notification.is-danger {
            background-color: rgba(251, 73, 52, 0.1) !important;
            color: var(--gruvbox-red) !important;
        }
        
        .notification.is-warning {
            background-color: rgba(250, 189, 47, 0.1) !important;
            color: var(--gruvbox-yellow) !important;
        }
        
        /* Tags */
        .tag.is-success {
            background-color: var(--gruvbox-green) !important;
            color: var(--gruvbox-dark0) !important;
        }
        
        .tag.is-warning {
            background-color: var(--gruvbox-yellow) !important;
            color: var(--gruvbox-dark0) !important;
        }
        
        .tag.is-info {
            background-color: var(--gruvbox-aqua) !important;
            color: var(--gruvbox-dark0) !important;
        }
        
        /* Links */
        a {
            color: var(--gruvbox-blue) !important;
        }
        
        a:hover {
            color: var(--gruvbox-aqua) !important;
        }
        
        /* Progress bars */
        .progress::-webkit-progress-bar {
            background-color: var(--gruvbox-dark2) !important;
        }
        
        .progress::-webkit-progress-value {
            background-color: var(--gruvbox-blue) !important;
        }
        
        /* Code blocks */
        pre, code {
            background-color: var(--gruvbox-dark2) !important;
            color: var(--gruvbox-light1) !important;
            border: 1px solid var(--gruvbox-dark3) !important;
        }
        
        /* Iframe borders */
        iframe {
            border: 2px solid var(--gruvbox-dark3) !important;
            border-radius: 6px !important;
            background-color: white !important;
        }
        
        /* Subtitle adjustments */
        .subtitle {
            color: var(--gruvbox-light2) !important;
        }
        
        /* Small text */
        small, .has-text-grey {
            color: var(--gruvbox-light3) !important;
        }
        
        /* Section backgrounds */
        .section {
            background-color: transparent !important;
        }
    """
    
    elements = [
        Title(f"{title} - FastVimes"),
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Link(rel="stylesheet", href="https://unpkg.com/bulma@1.0.4/css/bulma.css"),
    ]
    
    # Only add FontAwesome for full pages or when explicitly needed
    if not minimal:
        elements.append(Script(defer=True, src="https://use.fontawesome.com/releases/v5.15.4/js/all.js"))
    
    # Add Gruvbox theme after Bulma
    elements.append(Style(gruvbox_css))
    
    if include_htmx:
        elements.append(Script(src="https://unpkg.com/htmx.org@2.0.6/dist/htmx.js"))
    return Head(*elements)


def page_hero(title: str, subtitle: str = "Database Management Interface") -> Section:
    """Standard hero section."""
    return Section(
        Div(
            H1(title, cls=CSS.TITLE),
            H2(subtitle, cls=CSS.SUBTITLE),
            cls=CSS.CONTAINER,
        ),
        cls=CSS.HERO_PRIMARY,
    )


def nav_link(text: str, href: str, active: bool = False) -> Li:
    """Create a navigation link with optional active state."""
    return Li(A(text, href=href, cls=CSS.IS_ACTIVE if active else ""))


def loading_div(target_id: str = "loading") -> Div:
    """Standard loading indicator."""
    return Div(
        Progress(max="100", cls="progress is-small is-primary"),
        id=target_id,
        cls="htmx-indicator",
    )


def data_table(
    headers: list[str], rows: list[list[Any]], cls: str = CSS.TABLE
) -> Table:
    """Generate a data table from headers and rows."""
    thead = Thead(Tr(*[Th(str(header).title()) for header in headers]))
    tbody = Tbody(*[Tr(*[Td(str(cell)) for cell in row]) for row in rows])
    return Table(thead, tbody, cls=cls)


# Higher-order component builders
def htmx_loader(url: str, target: str = "this", trigger: str = "load") -> dict:
    """Create HTMX loading attributes."""
    return {
        "hx_get": url,
        "hx_target": target,
        "hx_trigger": trigger,
    }


def action_button(
    text: str, url: str, target: str, style: str = CSS.BTN_PRIMARY, **attrs
) -> Button:
    """Create an action button with HTMX attributes."""
    return Button(
        text, cls=style, hx_get=url, hx_target=target, hx_indicator="#loading", **attrs
    )


class HTMLGenerator:
    """Generate FastHTML components for FastVimes."""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def render_fragment_or_page(self, content, title: str = "FastVimes", request=None):
        """Render content as fragment or standalone page based on request type."""
        return render_fragment_or_standalone(content, title, request)

    def generate_base_layout(self, title: str, content, active_nav: str = ""):
        """Generate base layout with navigation."""
        return Html(
            fastvimes_head(title),
            Body(
                page_hero(title),
                Section(
                    Div(
                        Div(
                            Div(self._generate_nav(active_nav), cls="column is-3"),
                            Div(content, cls=CSS.COLUMN),
                            # Table data viewing area (initially hidden)
                            Div(
                                id="table-data-area",
                                cls=f"{CSS.COLUMN} {CSS.HIDDEN}",
                                style="border-left: 1px solid #dbdbdb;",
                            ),
                            cls=CSS.COLUMNS,
                        ),
                        cls=CSS.CONTAINER,
                    ),
                    cls=CSS.SECTION,
                ),
            ),
        )

    def _generate_nav(self, active: str = ""):
        """Generate navigation menu."""
        nav_items = [
            ("Dashboard", "/admin/html/", "dashboard"),
            ("Tables", "/admin/html/tables", "tables"),
            ("Schema", "/admin/html/schema", "schema"),
            ("Configuration", "/admin/html/config", "config"),
        ]

        return Aside(
            P("General", cls=CSS.MENU_LABEL),
            Ul(
                *[nav_link(text, href, active == key) for text, href, key in nav_items],
                cls=CSS.MENU_LIST,
            ),
            P(
                "Open Tables",
                cls=CSS.MENU_LABEL,
                id="open-tables-label",
                style="display: none;",
            ),
            Ul(cls=CSS.MENU_LIST, id="open-tables-list"),
            cls=CSS.MENU,
        )

    def generate_tables_page(self):
        """Generate static tables page with HTMX loading."""
        content = Div(
            H3("Available Tables", cls=CSS.TITLE_4),
            Div(
                P("Loading tables..."),
                id="tables-list",
                **htmx_loader("/admin/api/tables/html"),
            ),
            Div(id="table-detail", cls="mt-4"),
            cls=CSS.BOX,
        )
        return self.generate_base_layout("Tables", content, "tables")

    def generate_dashboard_page(self):
        """Generate static dashboard page."""
        content = Div(
            H3("Welcome to FastVimes", cls=CSS.TITLE_4),
            P("This is the admin dashboard for your FastVimes application."),
            P(
                "Use the navigation menu to manage your database tables and configuration."
            ),
            cls=CSS.BOX,
        )
        return self.generate_base_layout("FastVimes Admin", content, "dashboard")

    def generate_tables_fragment(self, tables):
        """Generate tables list fragment."""
        if not tables:
            return P("No tables found.")

        def table_actions(name: str):
            """Generate action buttons for a table."""
            return [
                action_button(
                    "View Data", f"/admin/fragments/data/{name}", "#table-detail"
                ),
                " ",
                action_button(
                    "View HTML", f"/{name}/html", "#table-detail", CSS.BTN_INFO
                ),
                " ",
                action_button(
                    "Schema",
                    f"/admin/fragments/schema/{name}",
                    "#table-detail",
                    CSS.BTN_LIGHT,
                ),
            ]

        def table_row(name: str, config):
            """Generate a table row for a table."""
            mode_class = (
                CSS.TAG_SUCCESS if config.mode == "readwrite" else CSS.TAG_WARNING
            )
            return [
                name,
                Span(config.mode, cls=mode_class),
                "Yes" if config.html else "No",
                Div(*table_actions(name)),
            ]

        headers = ["Table", "Mode", "HTML", "Actions"]
        rows = [table_row(name, config) for name, config in tables.items()]

        return Div(
            data_table(headers, rows, CSS.TABLE_SIMPLE),
            loading_div(),
        )

    def generate_data_fragment(self, table_name: str, data: list):
        """Generate table data fragment."""
        if not data:
            return P(f'No data found in table "{table_name}".')

        import json

        json_data = {"data": data, "table": table_name}
        formatted_json = json.dumps(json_data, indent=2)

        return Div(
            H4(f"{table_name.title()} Data (JSON)", cls=CSS.TITLE_5),
            Pre(Code(formatted_json), cls=CSS.BG_LIGHT),
            cls=CSS.CONTENT,
        )

    def generate_schema_fragment(self, table_name: str, schema: dict):
        """Generate schema fragment."""
        headers = ["Field", "Type"]
        rows = [
            [Code(field_name), Span(str(field_type), cls=CSS.TAG_INFO)]
            for field_name, field_type in schema.items()
        ]

        return Div(
            H4(f"{table_name.title()} Schema", cls=CSS.TITLE_5),
            data_table(headers, rows, CSS.TABLE_SIMPLE),
            cls=CSS.CONTENT,
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
                id="schema-info",
            ),
            cls="box",
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
                id="config-info",
            ),
            cls="box",
        )
        return self.generate_base_layout("Configuration", content, "config")

    def generate_table_html(self, table_name: str, data: list[dict]):
        """Generate HTML table using FastHTML."""
        if not data:
            content = Div(
                H1(table_name.title(), cls="title"),
                P("No data available", cls="subtitle"),
                cls="container",
            )
            layout = self.generate_base_layout(f"Table: {table_name}", content)
            return self.render_to_string(layout)

        # Generate table headers
        headers = list(data[0].keys())
        thead = Thead(Tr(*[Th(header.title()) for header in headers]))

        # Generate table rows
        tbody = Tbody(
            *[Tr(*[Td(str(row[header])) for header in headers]) for row in data]
        )

        content = Div(
            H1(table_name.title(), cls="title"),
            Table(thead, tbody, cls="table is-striped is-hoverable"),
            cls="container",
        )
        layout = self.generate_base_layout(f"Table: {table_name}", content)
        return self.render_to_string(layout)

    def generate_table_html_with_admin(self, table_name: str, data: list[dict], schema: dict, query_params: dict, is_admin_context: bool):
        """Generate HTML table with optional admin features (filter form)."""
        # Generate main table content
        if not data:
            table_content = Div(
                P(f"Table '{table_name}' is empty", cls="subtitle"),
                cls="notification is-warning"
            )
        else:
            headers = list(data[0].keys())
            rows = [[str(row.get(header, "")) for header in headers] for row in data[:100]]
            
            table_info = Div(
                P(f"Rows: {len(data)} | Columns: {len(schema)}", cls="subtitle is-6"),
                cls="mb-3"
            )
            
            table_display = Div(
                data_table(headers, rows, CSS.TABLE),
                cls="table-container",
                style="overflow-x: auto;"
            )
            
            if len(data) > 100:
                pagination_info = P(
                    f"Showing first 100 of {len(data)} rows", 
                    cls=CSS.TEXT_GREY + " mb-3"
                )
                table_content = Div(table_info, pagination_info, table_display)
            else:
                table_content = Div(table_info, table_display)

        # Add filter form if in admin context
        if is_admin_context:
            filter_form = Form(
                H5("Filter Data", cls="title is-6"),
                Div(
                    Div(
                        Input(
                            type="text",
                            placeholder="RQL query (e.g., eq(name,Alice))",
                            name="rql",
                            value=query_params.get("rql", ""),
                            cls="input"
                        ),
                        cls="control is-expanded"
                    ),
                    Div(
                        Button(
                            "Filter",
                            type="submit",
                            cls="button is-primary"
                        ),
                        cls="control"
                    ),
                    cls="field has-addons"
                ),
                method="GET",
                action=f"/api/{table_name}/html",
                cls="box mb-4"
            )
            
            # Always include admin query param to maintain admin context
            hidden_admin = Input(type="hidden", name="admin", value="true")
            
            # Create new form with hidden admin field
            filter_form = Form(
                filter_form.children[0],  # H5
                filter_form.children[1],  # Div with form fields
                hidden_admin,
                method=filter_form.attrs.get("method", "GET"),
                action=filter_form.attrs.get("action"),
                cls=filter_form.attrs.get("cls", "")
            )
            
            content = Div(
                H1(table_name.title(), cls="title"),
                filter_form,
                table_content,
                cls="container"
            )
        else:
            content = Div(
                H1(table_name.title(), cls="title"),
                table_content,
                cls="container"
            )

        layout = self.generate_base_layout(f"Table: {table_name}", content)
        return self.render_to_string(layout)

    def generate_table_fragment(self, table_name: str, data: list[dict], schema: dict):
        """Generate table fragment suitable for HTMX loading."""
        if not data:
            return Div(
                P(f"Table '{table_name}' is empty", cls="subtitle"),
                cls="notification is-warning"
            )

        # Table info
        table_info = Div(
            P(f"Rows: {len(data)} | Columns: {len(schema)}", cls="subtitle is-6"),
            cls="mb-3"
        )

        # Generate table content
        headers = list(data[0].keys())
        rows = [[str(row.get(header, "")) for header in headers] for row in data[:100]]
        
        table_display = Div(
            data_table(headers, rows, CSS.TABLE),
            cls="table-container",
            style="overflow-x: auto;"
        )
        
        if len(data) > 100:
            pagination_info = P(
                f"Showing first 100 of {len(data)} rows", 
                cls=CSS.TEXT_GREY + " mb-3"
            )
            return Div(table_info, pagination_info, table_display)
        
        return Div(table_info, table_display)

    def generate_config_fragment(self, config: dict):
        """Generate HTML fragment for configuration."""
        config_items = []
        for key, value in config.items():
            config_items.append(Div(Strong(f"{key}: "), Span(str(value)), cls="field"))

        return Div(
            H5("Current Configuration", cls="title is-5"), *config_items, cls="box"
        )

    def generate_table_viewer(self, table_name: str, data: list[dict]):
        """Generate table viewer with data and controls."""
        if not data:
            return Div(
                H4(f"{table_name.title()} - No Data", cls="title is-4"),
                P("This table is empty"),
                cls="content",
            )

        # Generate table headers
        headers = list(data[0].keys())
        thead = Thead(Tr(*[Th(header.title()) for header in headers]))

        # Generate table rows (limit to first 100 for performance)
        display_data = data[:100]
        tbody = Tbody(
            *[Tr(*[Td(str(row[header])) for header in headers]) for row in display_data]
        )

        # Add pagination info if data is truncated
        pagination_info = ""
        if len(data) > 100:
            pagination_info = P(
                f"Showing first 100 of {len(data)} records",
                cls="has-text-grey is-size-7",
            )

        return Div(
            H4(f"{table_name.title()}", cls="title is-4"),
            pagination_info,
            Table(thead, tbody, cls="table is-striped is-hoverable is-fullwidth"),
            cls="content",
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
                    hx_confirm="Close this table?",
                ),
                href="#",
                hx_get=f"/admin/api/table-data/{table_name}/html",
                hx_target="#table-data-area",
                cls="is-active",
            ),
            id=f"nav-{table_name}",
            hx_swap_oob="beforeend:#open-tables-list",
        )

    def render_to_string(self, element) -> str:
        """Render FastHTML element to string."""

        return to_xml(element)

    def generate_admin_portal(self):
        """Generate HTMX-driven admin portal with Datasette-like layout."""
        return Html(
            fastvimes_head("FastVimes Portal", include_htmx=True),
            Body(
                # Header
                Section(
                    Div(
                        H1("FastVimes Portal", cls=CSS.TITLE),
                        H2("Database Management & API Explorer", cls=CSS.SUBTITLE),
                        cls=CSS.CONTAINER,
                    ),
                    cls="hero is-dark is-small",
                ),
                
                # Main content area
                Section(
                    Div(
                        # Navigation tabs
                        Div(
                            Div(
                                Ul(
                                    Li(A("Tables", 
                                        hx_get="/admin/tables",
                                        hx_target="#sidebar",
                                        hx_trigger="click",
                                        cls="is-active")),
                                    Li(A("Query", 
                                        hx_get="/admin/query",
                                        hx_target="#main-content",
                                        hx_trigger="click")),
                                    Li(A("API Docs", 
                                        hx_get="/admin/docs",
                                        hx_target="#main-content", 
                                        hx_trigger="click")),
                                    cls="tabs is-boxed"
                                ),
                                cls="tabs-container"
                            ),
                            cls="column is-full"
                        ),
                        
                        # Portal layout: Sidebar + Main content
                        Div(
                            # Left sidebar for navigation/tables
                            Div(
                                Div("Loading tables...", 
                                    id="sidebar",
                                    hx_get="/admin/tables",
                                    hx_trigger="load",
                                    cls="panel"),
                                cls="column is-3",
                                style="height: 80vh; overflow-y: auto; border-right: 1px solid #dbdbdb;"
                            ),
                            
                            # Main content area
                            Div(
                                Div(
                                    H3("Welcome to FastVimes Portal", cls=CSS.TITLE_4),
                                    P("Select a table from the sidebar to view data, or use the tabs above to explore."),
                                    cls="notification is-info is-light"
                                ),
                                id="main-content",
                                cls="column",
                                style="height: 80vh; overflow-y: auto; padding: 1rem;"
                            ),
                            cls=CSS.COLUMNS
                        ),
                        cls=CSS.CONTAINER
                    ),
                    cls=CSS.SECTION
                )
            ),
        )

    def generate_tables_sidebar(self, tables: dict):
        """Generate tables sidebar with Datasette-like navigation."""
        if not tables:
            return Div(P("No tables found."), cls="panel-block")

        table_items = []
        for name, config in tables.items():
            mode_icon = "🔒" if config.mode == "readonly" else "✏️"
            table_items.append(
                A(
                    Span(cls="panel-icon"),
                    Span(f"{mode_icon} {name}"),
                    Small(f" ({config.mode})", cls="has-text-grey"),
                    cls="panel-block is-active" if name == list(tables.keys())[0] else "panel-block",
                    hx_get=f"/api/{name}/html?admin=true",
                    hx_target="#main-content",
                    hx_trigger="click"
                )
            )

        return Div(
            P("Tables", cls="panel-heading"),
            *table_items,
            cls="panel"
        )

    def generate_table_view(self, table_name: str, data: list[dict], schema: dict, query_params: dict):
        """Generate Datasette-style table view with data and controls."""
        if not data:
            return Div(
                H4(f"{table_name}", cls=CSS.TITLE_4),
                P("This table is empty"),
                cls="notification is-warning"
            )

        # Query info
        query_info = Div(
            H4(f"Table: {table_name}", cls=CSS.TITLE_4),
            P(f"Rows: {len(data)} | Columns: {len(schema)}", cls="subtitle is-6"),
            cls="mb-4"
        )

        # Filter form
        filter_form = Form(
            H5("Filter Data", cls="title is-6"),
            Div(
                Div(
                    Input(
                        type="text",
                        placeholder="RQL query (e.g., eq(name,Alice))",
                        name="rql",
                        value=query_params.get("rql", ""),
                        cls="input"
                    ),
                    cls="control is-expanded"
                ),
                Div(
                    Button(
                        "Filter",
                        type="submit",
                        cls="button is-primary"
                    ),
                    cls="control"
                ),
                cls="field has-addons"
            ),
            hx_get=f"/admin/table/{table_name}",
            hx_target="#main-content",
            hx_include="this",
            cls="box"
        )

        # Table data
        if data:
            headers = list(data[0].keys())
            rows = [[str(row.get(header, "")) for header in headers] for row in data[:100]]
            
            table_display = Div(
                data_table(headers, rows, CSS.TABLE),
                cls="table-container",
                style="overflow-x: auto;"
            )
            
            if len(data) > 100:
                table_display = Div(
                    P(f"Showing first 100 of {len(data)} rows", cls=CSS.TEXT_GREY),
                    table_display
                )
        else:
            table_display = P("No data to display")

        return Div(query_info, filter_form, table_display)



    def generate_docs_embed(self):
        """Generate embedded FastAPI docs iframe."""
        return Div(
            H4("API Documentation", cls=CSS.TITLE_4),
            P("Interactive FastAPI documentation for testing endpoints:"),
            Div(
                Iframe(
                    src="/docs",
                    style="width: 100%; height: 70vh; border: 1px solid #dbdbdb; border-radius: 4px;"
                ),
                cls="mt-4"
            )
        )

    def generate_query_interface(self):
        """Generate SQL query interface."""
        return Div(
            H4("SQL Query Interface", cls=CSS.TITLE_4),
            P("Execute SQL queries directly against your DuckDB database:"),
            
            Form(
                Div(
                    Label("SQL Query:", cls="label"),
                    Textarea(
                        placeholder="SELECT * FROM users LIMIT 10;",
                        name="query",
                        rows="8",
                        cls="textarea",
                    ),
                    cls="field"
                ),
                Div(
                    Button(
                        "Execute Query",
                        type="submit",
                        cls="button is-primary"
                    ),
                    cls="field"
                ),
                hx_post="/admin/query",
                hx_target="#query-results"
            ),
            
            Div(id="query-results", cls="mt-4"),
            cls="box"
        )

    def generate_query_results(self, query: str, columns: list, results: list):
        """Generate query results display."""
        if not results:
            return Div(
                P("Query executed successfully but returned no results."),
                cls="notification is-info"
            )

        return Div(
            H5("Query Results", cls="title is-5"),
            P(f"Query: {query[:100]}{'...' if len(query) > 100 else ''}", cls="subtitle is-6"),
            data_table(columns, results, CSS.TABLE),
            cls="box"
        )

    def generate_error_fragment(self, error_message: str):
        """Generate error display fragment."""
        return Div(
            H5("Error", cls="title is-5 has-text-danger"),
            P(error_message),
            cls="notification is-danger"
        )
