"""FastVimes main application class with NiceGUI + DuckLake integration."""

import tempfile
import atexit
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

from nicegui import ui, app
from fastapi import FastAPI

from .config import FastVimesSettings
from .database_service import DatabaseService
from .api_client import FastVimesAPIClient
from .components.table_browser import TableBrowser
from .components.data_explorer import DataExplorer
from .components.form_generator import FormGenerator


class FastVimes:
    """FastVimes application with auto-generated NiceGUI interface."""
    
    def __init__(
        self, 
        db_path: Optional[str] = None,
        settings: Optional[FastVimesSettings] = None
    ):
        """Initialize FastVimes with DuckLake backend.
        
        Args:
            db_path: Path to DuckLake database. If None, creates temp DuckLake with sample data.
            settings: Configuration settings. If None, loads from environment/config files.
        """
        self.settings = settings or FastVimesSettings()
        
        # Setup DuckLake database
        if db_path is None:
            self._setup_temp_database()
        else:
            self.db_path = Path(db_path)
            
        # Initialize database service
        create_sample = db_path is None  # Create sample data if using temp database
        self.db_service = DatabaseService(self.db_path, create_sample_data=create_sample)
        
        # Initialize API client for NiceGUI components (in-process mode for development)
        self.api_client = FastVimesAPIClient(db_service=self.db_service)
        
        # Setup FastAPI for RQL endpoints
        self.api = FastAPI(title="FastVimes API", version="0.1.0")
        self._setup_api_routes()
        
        # Setup NiceGUI interface
        self._setup_ui()
        
    def _setup_temp_database(self):
        """Create temporary DuckLake with sample data."""
        # Use in-memory database for zero-config demo
        self.db_path = Path(":memory:")
        
        # For file-based temp database, uncomment below:
        # self.temp_dir = Path(tempfile.mkdtemp(prefix="fastvimes_"))
        # self.db_path = self.temp_dir / "sample.ducklake"
        # atexit.register(self._cleanup_temp_database)
        
    def _cleanup_temp_database(self):
        """Clean up temporary database directory."""
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            

        
    def _setup_api_routes(self):
        """Setup FastAPI routes with namespaced v1 API structure."""
        from fastapi import HTTPException, Request, Response
        from fastapi.responses import StreamingResponse
        from typing import Optional, Dict, Any, List
        import io
        
        # =============================================================================
        # META ENDPOINTS - Database introspection
        # =============================================================================
        
        @self.api.get("/v1/meta/tables")
        async def list_tables():
            """List all tables in the database."""
            try:
                tables = self.db_service.list_tables()
                return {"tables": tables}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.api.get("/v1/meta/schema/{table_name}")
        async def get_table_schema(table_name: str):
            """Get schema information for a table."""
            try:
                # Verify table exists
                tables = self.db_service.list_tables()
                table_names = [t['name'] for t in tables]
                if table_name not in table_names:
                    raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
                
                # Get schema
                schema = self.db_service.get_table_schema(table_name)
                return {"schema": schema}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # =============================================================================
        # DATA ENDPOINTS - Table CRUD operations
        # =============================================================================
        
        @self.api.get("/v1/data/{table_name}")
        async def get_table_data(
            table_name: str,
            request: Request,
            limit: Optional[int] = 100,
            offset: Optional[int] = 0,
            format: str = "json"
        ):
            """Get table data with RQL filtering and multi-format support."""
            try:
                # Verify table exists
                tables = self.db_service.list_tables()
                table_names = [t['name'] for t in tables]
                if table_name not in table_names:
                    raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
                
                # Extract RQL query from query parameters
                rql_query = None
                if request.url.query:
                    # Remove limit, offset, and format from query string for RQL processing
                    query_parts = []
                    for part in str(request.url.query).split('&'):
                        if not part.startswith(('limit=', 'offset=', 'format=')):
                            query_parts.append(part)
                    if query_parts:
                        rql_query = '&'.join(query_parts)
                
                # Get table data with RQL filtering
                result = self.db_service.get_table_data(
                    table_name=table_name,
                    rql_query=rql_query,
                    limit=limit,
                    offset=offset,
                    format=format
                )
                
                # Handle different response formats
                if format.lower() == "json":
                    return result
                elif format.lower() == "csv":
                    return Response(
                        content=result,
                        media_type="text/csv",
                        headers={"Content-Disposition": f"attachment; filename={table_name}.csv"}
                    )
                elif format.lower() == "parquet":
                    return Response(
                        content=result,
                        media_type="application/octet-stream",
                        headers={"Content-Disposition": f"attachment; filename={table_name}.parquet"}
                    )
                else:
                    raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
                    
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.api.post("/v1/data/{table_name}")
        async def create_record(table_name: str, record_data: Dict[str, Any]):
            """Create a new record in the specified table."""
            try:
                # Verify table exists
                tables = self.db_service.list_tables()
                table_names = [t['name'] for t in tables]
                if table_name not in table_names:
                    raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
                
                # Create record
                created_record = self.db_service.create_record(table_name, record_data)
                return {"message": "Record created successfully", "record": created_record}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.api.put("/v1/data/{table_name}")
        async def update_records(
            table_name: str, 
            record_data: Dict[str, Any],
            request: Request
        ):
            """Update records in the specified table."""
            try:
                # Verify table exists
                tables = self.db_service.list_tables()
                table_names = [t['name'] for t in tables]
                if table_name not in table_names:
                    raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
                
                # Extract RQL query from query parameters
                rql_query = None
                if request.url.query:
                    rql_query = str(request.url.query)
                
                # Update records
                count = self.db_service.update_records(
                    table_name=table_name,
                    data=record_data,
                    rql_query=rql_query
                )
                return {"message": f"Updated {count} records", "count": count}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.api.delete("/v1/data/{table_name}")
        async def delete_records(table_name: str, request: Request):
            """Delete records from the specified table."""
            try:
                # Verify table exists
                tables = self.db_service.list_tables()
                table_names = [t['name'] for t in tables]
                if table_name not in table_names:
                    raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
                
                # Extract RQL query from query parameters
                rql_query = None
                if request.url.query:
                    rql_query = str(request.url.query)
                
                if not rql_query:
                    raise HTTPException(status_code=400, detail="RQL query required for deletion to prevent accidental deletion of all records")
                
                # Delete records
                count = self.db_service.delete_records(
                    table_name=table_name,
                    rql_query=rql_query
                )
                return {"message": f"Deleted {count} records", "count": count}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # =============================================================================
        # QUERY ENDPOINT - Raw SQL execution
        # =============================================================================
        
        @self.api.post("/v1/query")
        async def execute_query(query_data: Dict[str, Any]):
            """Execute a raw SQL query and return results."""
            try:
                sql = query_data.get("sql")
                format = query_data.get("format", "json")
                
                if not sql:
                    raise HTTPException(status_code=400, detail="SQL query is required")
                
                # Execute query
                result = self.db_service.execute_query(sql)
                
                # Handle different response formats
                if format.lower() == "json":
                    return {"data": result}
                elif format.lower() == "csv":
                    # Convert to CSV format
                    if result:
                        import csv
                        import io
                        output = io.StringIO()
                        writer = csv.DictWriter(output, fieldnames=result[0].keys())
                        writer.writeheader()
                        writer.writerows(result)
                        csv_content = output.getvalue()
                        return Response(
                            content=csv_content,
                            media_type="text/csv",
                            headers={"Content-Disposition": "attachment; filename=query_result.csv"}
                        )
                    else:
                        return Response(content="", media_type="text/csv")
                elif format.lower() == "parquet":
                    # Convert to Parquet format
                    if result:
                        columns = list(result[0].keys())
                        parquet_bytes = self.db_service._export_to_parquet(columns, result)
                        return Response(
                            content=parquet_bytes,
                            media_type="application/octet-stream",
                            headers={"Content-Disposition": "attachment; filename=query_result.parquet"}
                        )
                    else:
                        return Response(content=b"", media_type="application/octet-stream")
                else:
                    raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
                    
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
    def _setup_ui(self):
        """Setup NiceGUI interface with auto-generated components."""
        # Main page with table browser
        @ui.page('/')
        def index():
            self._render_main_interface()
            
        # Table detail pages
        @ui.page('/table/{table_name}')
        def table_detail(table_name: str):
            self._render_table_detail(table_name)
            
        # Embedded UIs
        @ui.page('/admin/duckdb-ui')
        def duckdb_ui():
            ui.iframe('http://localhost:4213')  # DuckDB UI extension
            
        @ui.page('/admin/api-docs')
        def api_docs():
            ui.iframe('/docs')  # FastAPI auto-generated docs
            
    def _render_main_interface(self):
        """Render the main Datasette-style interface."""
        with ui.header().classes('items-center'):
            ui.label('FastVimes').classes('text-h5 font-bold')
            with ui.row().classes('ml-auto'):
                ui.button('API Docs', on_click=lambda: ui.navigate.to('/docs', new_tab=True)).props('flat')
        
        with ui.column().classes('w-full max-w-6xl mx-auto p-4'):
            ui.label('Database Tables').classes('text-h4 mb-4')
            
            # Table browser component
            table_browser = TableBrowser(self.api_client)
            table_browser.render()
        
    def _render_table_detail(self, table_name: str):
        """Render detailed view for a specific table."""
        with ui.header().classes('items-center'):
            ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/')).props('flat')
            ui.label(f'Table: {table_name}').classes('text-h5 font-bold ml-2')
            
        with ui.column().classes('w-full max-w-6xl mx-auto p-4'):
            with ui.tabs().classes('w-full') as tabs:
                data_tab = ui.tab('Data')
                add_tab = ui.tab('Add Record')
                
            with ui.tab_panels(tabs, value=data_tab).classes('w-full'):
                with ui.tab_panel(data_tab):
                    # Data explorer component
                    data_explorer = DataExplorer(self.api_client, table_name)
                    data_explorer.render()
                    
                with ui.tab_panel(add_tab):
                    # Form generator component
                    form_generator = FormGenerator(self.api_client, table_name)
                    form_generator.render()
        
    def serve(self, host: str = "127.0.0.1", port: int = 8000):
        """Start the FastVimes server."""
        # Mount FastAPI app for API routes
        app.mount('/api', self.api)
        
        # Start NiceGUI with embedded FastAPI
        ui.run(
            host=host,
            port=port,
            title="FastVimes",
            favicon="🦆",
            reload=False,
            show=False
        )
        
    # Override methods for customization
    def table_component(self, table_name: str):
        """Override this method to customize table display for specific tables."""
        return DataExplorer(self.api_client, table_name)
        
    def form_component(self, table_name: str):
        """Override this method to customize forms for specific tables."""
        return FormGenerator(self.api_client, table_name)
