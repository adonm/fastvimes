"""NiceGUI pages using built-in components - no custom wrappers."""

import json
from typing import TYPE_CHECKING

from nicegui import ui

if TYPE_CHECKING:
    from .app import FastVimes


def register_pages(app: "FastVimes"):
    """Register all NiceGUI pages with the app."""
    
    @ui.page("/")
    def index():
        """Home page with table browser using NiceGUI's built-in ui.tree."""
        with ui.column().classes("w-full h-full"):
            ui.label("FastVimes").classes("text-2xl font-bold mb-4")
            
            # Get tables for tree structure
            tables = app.db_service.list_tables()
            tree_data = [
                {
                    "id": table["name"],
                    "children": [
                        {"id": f"{table['name']}.{col['name']}", "label": f"{col['name']} ({col['type']})"}
                        for col in app.db_service.get_table_schema(table["name"])
                    ],
                    "label": f"{table['name']} ({table['type']})"
                }
                for table in tables
            ]
            
            tree = ui.tree(tree_data, label_key="label", on_select=lambda e: ui.navigate.to(f"/table/{e.value}"))
            tree.classes("w-full")

    @ui.page("/table/{table_name}")
    def table_page(table_name: str):
        """Table data explorer using NiceGUI's built-in ui.aggrid."""
        # Check for custom override
        override_content = app.override_table_page(table_name)
        if override_content:
            return override_content
            
        with ui.column().classes("w-full h-full"):
            # Header with navigation
            with ui.row().classes("w-full items-center mb-4"):
                ui.button("← Back", on_click=lambda: ui.navigate.to("/")).props("flat")
                ui.label(f"Table: {table_name}").classes("text-xl font-bold")
                ui.button("Add Record", on_click=lambda: ui.navigate.to(f"/form/{table_name}")).props("color=primary")
            
            # Get table data and schema
            try:
                data = app.db_service.get_table_data(table_name, limit=1000)
                schema = app.db_service.get_table_schema(table_name)
                
                # Convert data to format AGGrid expects
                if isinstance(data, dict) and "records" in data:
                    rows = data["records"]
                else:
                    rows = data if isinstance(data, list) else []
                
                # Build column definitions from schema
                column_defs = [
                    {
                        "headerName": col["name"],
                        "field": col["name"],
                        "sortable": True,
                        "filter": True,
                        "editable": True,
                    }
                    for col in schema
                ]
                
                # Use NiceGUI's built-in AGGrid with full feature set
                grid = ui.aggrid({
                    "columnDefs": column_defs,
                    "rowData": rows,
                    "rowSelection": "multiple",
                    "suppressRowClickSelection": False,
                    "pagination": True,
                    "paginationPageSize": 50,
                    "defaultColDef": {
                        "resizable": True,
                        "sortable": True,
                        "filter": True,
                    },
                }).classes("w-full h-96")
                
                # Add export buttons
                with ui.row():
                    ui.button("Export CSV", on_click=lambda: _export_data(table_name, "csv", app))
                    ui.button("Export Parquet", on_click=lambda: _export_data(table_name, "parquet", app))
                
            except Exception as e:
                ui.label(f"Error loading table: {e}").classes("text-red-500")

    @ui.page("/form/{table_name}")
    def form_page(table_name: str):
        """Record creation form using NiceGUI's built-in form components."""
        # Check for custom override
        override_content = app.override_form_page(table_name)
        if override_content:
            return override_content
            
        with ui.column().classes("w-full max-w-md mx-auto"):
            # Header
            with ui.row().classes("w-full items-center mb-4"):
                ui.button("← Back", on_click=lambda: ui.navigate.to(f"/table/{table_name}")).props("flat")
                ui.label(f"Add Record to {table_name}").classes("text-xl font-bold")
            
            # Get schema and build form
            try:
                schema = app.db_service.get_table_schema(table_name)
                form_data = {}
                
                with ui.card().classes("w-full p-4"):
                    for col in schema:
                        field_name = col["name"]
                        field_type = col["type"].lower()
                        
                        # Create appropriate input based on type
                        if "int" in field_type or "float" in field_type or "double" in field_type:
                            form_data[field_name] = ui.number(
                                label=field_name,
                                value=0 if "int" in field_type else 0.0
                            ).classes("w-full mb-2")
                        elif "bool" in field_type:
                            form_data[field_name] = ui.checkbox(field_name, value=False).classes("mb-2")
                        elif "date" in field_type:
                            form_data[field_name] = ui.date(label=field_name).classes("w-full mb-2")
                        else:  # text/varchar/string
                            form_data[field_name] = ui.input(label=field_name).classes("w-full mb-2")
                    
                    # Submit button
                    ui.button(
                        "Create Record",
                        on_click=lambda: _create_record(table_name, form_data, app)
                    ).props("color=primary").classes("w-full mt-4")
                    
            except Exception as e:
                ui.label(f"Error loading form: {e}").classes("text-red-500")

    @ui.page("/duckdb-ui")
    def duckdb_ui_page():
        """Embedded DuckDB UI for advanced SQL features."""
        if app.settings.duckdb_ui_enabled:
            ui.html(f'''
                <iframe 
                    src="http://localhost:{app.settings.duckdb_ui_port}" 
                    width="100%" 
                    height="800px"
                    style="border: none;">
                </iframe>
            ''').classes("w-full h-full")
        else:
            ui.label("DuckDB UI is not enabled").classes("text-gray-500")


def _export_data(table_name: str, format: str, app: "FastVimes"):
    """Export table data in specified format."""
    try:
        data = app.db_service.get_table_data(table_name, format=format, limit=10000)
        # Trigger download
        ui.download(data, filename=f"{table_name}.{format}")
        ui.notify(f"Exported {table_name} as {format.upper()}")
    except Exception as e:
        ui.notify(f"Export failed: {e}", type="negative")


def _create_record(table_name: str, form_data: dict, app: "FastVimes"):
    """Create a new record from form data."""
    try:
        # Extract values from form components
        record_data = {}
        for field_name, component in form_data.items():
            record_data[field_name] = component.value
        
        # Create the record
        result = app.db_service.create_record(table_name, record_data)
        ui.notify(f"Record created successfully", type="positive")
        ui.navigate.to(f"/table/{table_name}")
        
    except Exception as e:
        ui.notify(f"Failed to create record: {e}", type="negative")
