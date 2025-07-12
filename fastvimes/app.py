"""FastVimes app maintaining RQL alignment and API/CLI/HTML consistency."""

import logging
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .config import FastVimesSettings
from .database_service import DatabaseService

logger = logging.getLogger(__name__)


class FastVimes(FastAPI):
    """FastVimes with RQL-aligned API/CLI/HTML endpoints."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        config: Optional[FastVimesSettings] = None,
        **kwargs
    ):
        """Initialize FastVimes application."""
        
        # Set up configuration
        if config is None:
            config_kwargs = {"db_path": db_path} if db_path else {}
            config_kwargs.update(kwargs)
            config = FastVimesSettings(**config_kwargs)
        
        self.config = config
        
        # Initialize FastAPI
        super().__init__(
            title="FastVimes API",
            description="Auto-generated API from database schema with RQL",
            version="0.1.0",
        )
        
        # Initialize database service
        self.db_service = DatabaseService(config=self.config)
        
        # Set up routes
        self._setup_core_routes()
        self._setup_table_routes()
        
        # Set up admin if enabled
        if self.config.admin_enabled:
            self._setup_admin()

    def _setup_core_routes(self):
        """Set up core API routes."""
        
        @self.get("/")
        async def root():
            return {
                "message": "FastVimes API", 
                "tables": self.db_service.list_tables(),
                "rql_enabled": True
            }
        
        @self.get("/api/tables")
        async def list_tables():
            """List all available tables."""
            return {"tables": list(self.db_service.list_tables().keys())}

    def _setup_table_routes(self):
        """Set up table routes using core operations."""
        for table_name in self.db_service.list_tables().keys():
            self._setup_table_endpoints(table_name)

    def _setup_table_endpoints(self, table_name: str):
        """Set up CRUD endpoints for a table using core operations."""
        from fastapi import Request, HTTPException
        from fastapi.responses import HTMLResponse
        
        # GET /api/{table}/
        @self.get(f"/api/{table_name}/")
        async def get_table_data(request: Request):
            """Get table data with RQL filtering."""
            query_params = dict(request.query_params)
            try:
                data = self.db_service.execute_rql_query(table_name, query_params)
                return {"data": data, "table": table_name}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # POST /api/{table}/
        @self.post(f"/api/{table_name}/")
        async def create_record(record_data: dict):
            """Create a new record."""
            try:
                self.db_service.insert_record(table_name, record_data)
                return {"success": True, "table": table_name}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # PUT /api/{table}/
        @self.put(f"/api/{table_name}/")
        async def update_records(record_data: dict, request: Request):
            """Update records with RQL filtering."""
            query_params = dict(request.query_params)
            # Convert query string to RQL string for database service
            if query_params:
                from .rql_sqlglot import apply_rql_to_sql, RQLSQLGlotTranslator
                translator = RQLSQLGlotTranslator()
                rql_string = translator.parse_query_params(query_params)
                query_params = {"_rql_string": rql_string}
            try:
                updated_count = self.db_service.update_record(table_name, record_data, query_params)
                return {"updated": updated_count, "table": table_name}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # DELETE /api/{table}/
        @self.delete(f"/api/{table_name}/")
        async def delete_records(request: Request):
            """Delete records with RQL filtering."""
            query_params = dict(request.query_params)
            # Convert query string to RQL string for database service
            if query_params:
                from .rql_sqlglot import apply_rql_to_sql, RQLSQLGlotTranslator
                translator = RQLSQLGlotTranslator()
                rql_string = translator.parse_query_params(query_params)
                query_params = {"_rql_string": rql_string}
            try:
                deleted_count = self.db_service.delete_record(table_name, query_params)
                return {"deleted": deleted_count}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # GET /api/{table}/schema
        @self.get(f"/api/{table_name}/schema")
        async def get_table_schema():
            """Get table schema."""
            try:
                schema = self.db_service.get_table_schema(table_name)
                return schema
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # GET /api/{table}/html
        @self.get(f"/api/{table_name}/html", response_class=HTMLResponse)
        async def get_table_html(request: Request):
            """Get HTML view of table."""
            query_params = dict(request.query_params)
            try:
                data = self.db_service.execute_rql_query(table_name, query_params)
                
                # Generate simple HTML table
                html = f"""
                <div class="container">
                  <h1 class="title">{table_name.title()}</h1>
                  <table class="table is-striped is-hoverable">
                    <thead>
                      <tr>
                """
                
                if data:
                    # Add headers
                    for key in data[0].keys():
                        html += f"<th>{key.title()}</th>"
                    html += "</tr></thead><tbody>"
                    
                    # Add rows
                    for row in data:
                        html += "<tr>"
                        for value in row.values():
                            html += f"<td>{value}</td>"
                        html += "</tr>"
            
                html += """
                    </tbody>
                  </table>
                </div>
                """
                
                return html
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

    def _setup_admin(self):
        """Set up minimal admin interface."""
        
        @self.get("/admin", response_class=HTMLResponse)
        async def admin_dashboard():
            """Admin dashboard with table links."""
            tables = list(self.db_service.list_tables().keys())
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>FastVimes Admin</title>
                <link rel="stylesheet" href="https://unpkg.com/bulma@1.0.4/css/bulma.css">
                <script src="https://unpkg.com/htmx.org@2.0.6/dist/htmx.js"></script>
            </head>
            <body>
                <section class="section">
                    <div class="container">
                        <h1 class="title">FastVimes Admin</h1>
                        <h2 class="subtitle">SQLGlot + DuckDB RQL API</h2>
                        <div class="content">
                            <h3>Tables</h3>
                            <ul>
                                {''.join([f'<li><a href="/api/{table}/">{table}</a> | <a href="/api/{table}/html">HTML</a></li>' for table in tables])}
                            </ul>
                            <h3>Example RQL Queries</h3>
                            <pre>
GET /api/users?eq(id,1)           # Filter by ID
GET /api/users?lt(age,30)         # Age less than 30  
GET /api/users?sort(+name,-age)   # Sort by name ASC, age DESC
GET /api/users?limit(10,5)        # Skip 5, take 10
                            </pre>
                        </div>
                    </div>
                </section>
            </body>
            </html>
            """
            return html

    # CLI-compatible API methods using database service
    def list_tables_api(self):
        """List tables (CLI method)."""
        return list(self.db_service.list_tables().keys())
    
    def get_table_data_api(self, table_name: str, query_params: dict = None):
        """Get table data with RQL (CLI method)."""
        query_params = query_params or {}
        return self.db_service.execute_rql_query(table_name, query_params)
    
    def create_record_api(self, table_name: str, record_data: dict):
        """Create record (CLI method)."""
        self.db_service.insert_record(table_name, record_data)
        return {"success": True, "table": table_name}
    
    def update_records_api(self, table_name: str, record_data: dict, query_params: dict = None):
        """Update records (CLI method)."""
        query_params = query_params or {}
        updated_count = self.db_service.update_record(table_name, record_data, query_params)
        return {"updated": updated_count, "table": table_name}
    
    def delete_records_api(self, table_name: str, query_params: dict = None):
        """Delete records (CLI method)."""
        query_params = query_params or {}
        deleted_count = self.db_service.delete_record(table_name, query_params)
        return {"deleted": deleted_count}
    
    def get_table_schema_api(self, table_name: str):
        """Get table schema (CLI method)."""
        return self.db_service.get_table_schema(table_name)
    
    def execute_raw_sql(self, sql: str):
        """Execute raw SQL (CLI method)."""
        return self.db_service.execute_query(sql)

    def refresh_table_routes(self):
        """Refresh table routes after schema changes."""
        # Rediscover tables first
        self.db_service._discover_tables()
        # Set up routes for new tables
        self._setup_table_routes()
