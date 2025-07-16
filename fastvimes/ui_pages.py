"""NiceGUI pages using built-in components - no custom wrappers."""

import json
from typing import TYPE_CHECKING

from nicegui import ui

if TYPE_CHECKING:
    from .app import FastVimes


def register_pages(app: "FastVimes"):
    """Register all NiceGUI pages with the app."""
    
    def _create_navigation_drawer():
        """Create the navigation sidebar with table browser."""
        with ui.left_drawer(value=True).classes("bg-grey-2") as drawer:
            drawer.props("width=300")
            
            with ui.column().classes("w-full p-4"):
                # Header
                ui.label("FastVimes").classes("text-lg font-bold mb-4")
                
                # Search box
                search_input = ui.input(
                    placeholder="Search tables...",
                    on_change=lambda e: _filter_tables(e.value)
                ).classes("w-full mb-4")
                
                # Tables section
                ui.label("Tables").classes("text-sm font-medium text-grey-6 mb-2")
                
                # Get tables for navigation
                tables = app.db_service.list_tables()
                
                # Store original tables for filtering
                search_input.original_tables = tables
                
                # Table list container
                with ui.column().classes("w-full") as table_list:
                    table_list.bind_visibility_from(search_input, "value", lambda x: len(x or "") == 0)
                    for table in tables:
                        with ui.row().classes("w-full items-center cursor-pointer hover:bg-grey-3 p-2 rounded") as table_row:
                            ui.icon("table_view").classes("text-primary mr-2")
                            ui.label(table["name"]).classes("text-sm")
                        # Make the whole row clickable
                        table_row.on("click", lambda t=table["name"]: ui.navigate.to(f"/table/{t}"))
                
                # Filtered results container (hidden by default)
                with ui.column().classes("w-full") as filtered_list:
                    filtered_list.bind_visibility_from(search_input, "value", lambda x: len(x or "") > 0)
                    # Will be populated by _filter_tables
                
                # Store reference for filtering
                search_input.filtered_list = filtered_list
                
                # Quick actions
                ui.separator().classes("my-4")
                ui.label("Quick Actions").classes("text-sm font-medium text-grey-6 mb-2")
                
                with ui.row().classes("w-full"):
                    ui.button("DuckDB UI", on_click=lambda: ui.navigate.to("/duckdb-ui")).props("flat size=sm")
                    ui.button("Home", on_click=lambda: ui.navigate.to("/")).props("flat size=sm")
        
        return drawer
    
    def _filter_tables(search_term: str):
        """Filter tables based on search term."""
        search_input = ui.context.client.elements.get(list(ui.context.client.elements.keys())[-1])
        if not hasattr(search_input, 'filtered_list') or not hasattr(search_input, 'original_tables'):
            return
            
        # Clear previous filtered results
        search_input.filtered_list.clear()
        
        if not search_term:
            return
            
        # Filter tables
        filtered_tables = [
            table for table in search_input.original_tables 
            if search_term.lower() in table["name"].lower()
        ]
        
        # Add filtered results
        with search_input.filtered_list:
            if filtered_tables:
                for table in filtered_tables:
                    with ui.row().classes("w-full items-center cursor-pointer hover:bg-grey-3 p-2 rounded") as filtered_row:
                        ui.icon("table_view").classes("text-primary mr-2")
                        ui.label(table["name"]).classes("text-sm")
                    # Make the whole row clickable
                    filtered_row.on("click", lambda t=table["name"]: ui.navigate.to(f"/table/{t}"))
            else:
                ui.label("No tables found").classes("text-grey-5 text-sm italic")
    
    @ui.page("/")
    def index():
        """Home page with navigation sidebar and welcome content."""
        _create_navigation_drawer()
        
        with ui.column().classes("w-full h-full p-8"):
            ui.label("Welcome to FastVimes").classes("text-3xl font-bold mb-4")
            ui.label("Auto-generated pgweb-style apps with NiceGUI + DuckDB").classes("text-grey-6 mb-8")
            
            # Quick stats
            tables = app.db_service.list_tables()
            with ui.card().classes("w-full max-w-2xl"):
                with ui.card_section():
                    ui.label("Database Overview").classes("text-lg font-medium mb-4")
                    with ui.grid(columns=3).classes("gap-4"):
                        ui.number(
                            label="Tables",
                            value=len(tables),
                            format="%.0f"
                        ).props("readonly")
                        
                        # Get total record count
                        total_records = 0
                        for table in tables:
                            try:
                                result = app.db_service.execute_query(
                                    f"SELECT COUNT(*) as count FROM {table['name']}", []
                                )
                                if result:
                                    total_records += result[0]["count"]
                            except:
                                pass
                        
                        ui.number(
                            label="Total Records",
                            value=total_records,
                            format="%.0f"
                        ).props("readonly")
                        
                        ui.input(
                            label="Database Type",
                            value="DuckDB"
                        ).props("readonly")
            
            # Quick actions
            if tables:
                ui.label("Quick Actions").classes("text-lg font-medium mt-8 mb-4")
                with ui.row().classes("gap-4"):
                    for table in tables[:3]:  # Show first 3 tables
                        ui.button(
                            f"Browse {table['name']}",
                            on_click=lambda t=table["name"]: ui.navigate.to(f"/table/{t}")
                        ).props("color=primary")

    @ui.page("/table/{table_name}")
    def table_page(table_name: str):
        """Table data explorer using NiceGUI's built-in ui.aggrid."""
        # Check for custom override
        override_content = app.override_table_page(table_name)
        if override_content:
            return override_content
        
        _create_navigation_drawer()
            
        with ui.column().classes("w-full h-full p-8"):
            # Header with navigation
            with ui.row().classes("w-full items-center mb-4"):
                ui.label(f"Table: {table_name}").classes("text-2xl font-bold")
                ui.space()
                ui.button("Add Record", on_click=lambda: ui.navigate.to(f"/form/{table_name}")).props("color=primary")
            
            # Tabs for Data and Charts
            with ui.tabs().classes("w-full") as tabs:
                data_tab = ui.tab("Data")
                charts_tab = ui.tab("Charts")
            
            with ui.tab_panels(tabs, value=data_tab).classes("w-full"):
                # Data Tab Panel
                with ui.tab_panel(data_tab):
                    try:
                        data = app.db_service.get_table_data(table_name, limit=1000)
                        schema = app.db_service.get_table_schema(table_name)
                        
                        # Convert data to format AGGrid expects
                        if isinstance(data, dict):
                            if "data" in data:
                                rows = data["data"]
                            elif "records" in data:
                                rows = data["records"]
                            else:
                                rows = []
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
                        with ui.row().classes("mt-4"):
                            ui.button("Export CSV", on_click=lambda: _export_data(table_name, "csv", app))
                            ui.button("Export Parquet", on_click=lambda: _export_data(table_name, "parquet", app))
                        
                    except Exception as e:
                        ui.label(f"Error loading table: {e}").classes("text-red-500")
                
                # Charts Tab Panel
                with ui.tab_panel(charts_tab):
                    try:
                        chart_data = app.db_service.get_chart_data(table_name)
                        
                        if chart_data["charts"]:
                            ui.label("Auto-generated Charts").classes("text-lg font-medium mb-4")
                            
                            # Create charts in a grid layout
                            with ui.grid(columns=2).classes("w-full gap-6"):
                                for chart_config in chart_data["charts"]:
                                    with ui.card().classes("w-full"):
                                        with ui.card_section():
                                            ui.label(chart_config["title"]).classes("text-md font-medium mb-2")
                                            
                                            # Prepare chart data for NiceGUI echarts
                                            if chart_config["type"] == "bar":
                                                chart_options = {
                                                    "title": {"text": chart_config["title"]},
                                                    "xAxis": {
                                                        "type": "category",
                                                        "data": [str(item[chart_config["x_key"]]) for item in chart_config["data"]]
                                                    },
                                                    "yAxis": {"type": "value"},
                                                    "series": [{
                                                        "type": "bar",
                                                        "data": [item[chart_config["y_key"]] for item in chart_config["data"]]
                                                    }]
                                                }
                                            elif chart_config["type"] == "line":
                                                chart_options = {
                                                    "title": {"text": chart_config["title"]},
                                                    "xAxis": {
                                                        "type": "category",
                                                        "data": [str(item[chart_config["x_key"]]) for item in chart_config["data"]]
                                                    },
                                                    "yAxis": {"type": "value"},
                                                    "series": [{
                                                        "type": "line",
                                                        "data": [item[chart_config["y_key"]] for item in chart_config["data"]]
                                                    }]
                                                }
                                            
                                            ui.echart(chart_options).classes("w-full h-64")
                        else:
                            with ui.card().classes("w-full max-w-lg mx-auto"):
                                with ui.card_section():
                                    ui.label("No charts available").classes("text-grey-5 mb-2")
                                    ui.label("This table doesn't have suitable data for automatic chart generation.").classes("text-sm")
                                    
                                    # Show what columns are available
                                    if chart_data.get("numeric_columns") or chart_data.get("categorical_columns"):
                                        ui.label("Available columns:").classes("text-sm font-medium mt-4 mb-2")
                                        if chart_data.get("numeric_columns"):
                                            ui.label(f"• Numeric: {', '.join(chart_data['numeric_columns'])}").classes("text-sm")
                                        if chart_data.get("categorical_columns"):
                                            ui.label(f"• Categorical: {', '.join(chart_data['categorical_columns'])}").classes("text-sm")
                        
                    except Exception as e:
                        ui.label(f"Error loading charts: {e}").classes("text-red-500")

    @ui.page("/form/{table_name}")
    def form_page(table_name: str):
        """Record creation form using NiceGUI's built-in form components."""
        # Check for custom override
        override_content = app.override_form_page(table_name)
        if override_content:
            return override_content
        
        _create_navigation_drawer()
            
        with ui.column().classes("w-full max-w-md mx-auto p-8"):
            # Header
            with ui.row().classes("w-full items-center mb-6"):
                ui.label(f"Add Record to {table_name}").classes("text-2xl font-bold")
                ui.space()
                ui.button("← Back to Table", on_click=lambda: ui.navigate.to(f"/table/{table_name}")).props("flat")
            
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
        _create_navigation_drawer()
        
        with ui.column().classes("w-full h-full p-4"):
            ui.label("DuckDB UI").classes("text-2xl font-bold mb-4")
            
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
                with ui.card().classes("w-full max-w-lg"):
                    with ui.card_section():
                        ui.label("DuckDB UI is not enabled").classes("text-gray-500 mb-4")
                        ui.label("To enable DuckDB UI, set FASTVIMES_DUCKDB_UI_ENABLED=true in your environment.").classes("text-sm")


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
