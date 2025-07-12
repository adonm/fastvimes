"""FastVimes app maintaining RQL alignment and API/CLI/HTML consistency."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from .config import FastVimesSettings
from .database_service import DatabaseService

logger = logging.getLogger(__name__)


class FastVimes(FastAPI):
    """FastVimes with RQL-aligned API/CLI/HTML endpoints."""

    def __init__(
        self,
        db_path: str | None = None,
        config: FastVimesSettings | None = None,
        **kwargs,
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

        # Initialize HTML generator
        from .html_generator import HTMLGenerator

        self.html_generator = HTMLGenerator(self.db_service)

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
                "rql_enabled": True,
            }

        @self.get("/api/tables")
        async def list_tables():
            """List all available tables."""
            return {"tables": list(self.db_service.list_tables().keys())}

    def _setup_table_routes(self):
        """Set up table routes using core operations."""
        tables = self.db_service.list_tables()
        for table_name, table_config in tables.items():
            self._setup_table_endpoints(table_name, table_config)

    def _setup_table_endpoints(self, table_name: str, table_config):
        """Set up CRUD endpoints for a table using core operations."""
        from fastapi import HTTPException, Request
        from fastapi.responses import HTMLResponse

        # GET /api/{table}/
        @self.get(f"/api/{table_name}/")
        async def get_table_data(request: Request):
            """Get table data with RQL filtering."""
            query_params = dict(request.query_params)
            try:
                data = self.db_service.execute_rql_query(table_name, query_params)
                return {"data": data, "table": table_name}
            except ValueError as e:
                # Client error - invalid query parameters
                raise HTTPException(status_code=400, detail=str(e))
            except RuntimeError:
                # Server error - database operation failed
                raise HTTPException(status_code=500, detail="Database operation failed")
            except Exception as e:
                logger.error(f"Unexpected error in get_table_data: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        # Only create write endpoints if table allows writes
        if not self.config.read_only and table_config.mode == "readwrite":
            # POST /api/{table}/
            @self.post(f"/api/{table_name}/")
            async def create_record(record_data: dict):
                """Create a new record."""
                try:
                    self.db_service.insert_record(table_name, record_data)
                    return {"success": True, "table": table_name}
                except ValueError as e:
                    # Client error - invalid data
                    raise HTTPException(status_code=400, detail=str(e))
                except RuntimeError:
                    # Server error - database operation failed
                    raise HTTPException(
                        status_code=500, detail="Database operation failed"
                    )
                except Exception as e:
                    logger.error(f"Unexpected error in create_record: {e}")
                    raise HTTPException(status_code=500, detail="Internal server error")

            # PUT /api/{table}/
            @self.put(f"/api/{table_name}/")
            async def update_records(record_data: dict, request: Request):
                """Update records with RQL filtering."""
                query_params = dict(request.query_params)
                # Convert query string to RQL string for database service
                if query_params:
                    from .rql_sqlglot import RQLSQLGlotTranslator

                    translator = RQLSQLGlotTranslator()
                    rql_string = translator.parse_query_params(query_params)
                    query_params = {"_rql_string": rql_string}
                try:
                    updated_count = self.db_service.update_record(
                        table_name, record_data, query_params
                    )
                    return {"updated": updated_count, "table": table_name}
                except ValueError as e:
                    # Client error - invalid data or query
                    raise HTTPException(status_code=400, detail=str(e))
                except RuntimeError:
                    # Server error - database operation failed
                    raise HTTPException(
                        status_code=500, detail="Database operation failed"
                    )
                except Exception as e:
                    logger.error(f"Unexpected error in update_records: {e}")
                    raise HTTPException(status_code=500, detail="Internal server error")

            # DELETE /api/{table}/
            @self.delete(f"/api/{table_name}/")
            async def delete_records(request: Request):
                """Delete records with RQL filtering."""
                query_params = dict(request.query_params)
                # Convert query string to RQL string for database service
                if query_params:
                    from .rql_sqlglot import RQLSQLGlotTranslator

                    translator = RQLSQLGlotTranslator()
                    rql_string = translator.parse_query_params(query_params)
                    query_params = {"_rql_string": rql_string}
                try:
                    deleted_count = self.db_service.delete_record(
                        table_name, query_params
                    )
                    return {"deleted": deleted_count}
                except ValueError as e:
                    # Client error - invalid query
                    raise HTTPException(status_code=400, detail=str(e))
                except RuntimeError:
                    # Server error - database operation failed
                    raise HTTPException(
                        status_code=500, detail="Database operation failed"
                    )
                except Exception as e:
                    logger.error(f"Unexpected error in delete_records: {e}")
                    raise HTTPException(status_code=500, detail="Internal server error")

        # GET /api/{table}/schema
        @self.get(f"/api/{table_name}/schema")
        async def get_table_schema():
            """Get table schema."""
            try:
                schema = self.db_service.get_table_schema(table_name)
                return schema
            except ValueError as e:
                # Client error - table not found
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                logger.error(f"Unexpected error in get_table_schema: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        # GET /api/{table}/html
        @self.get(f"/api/{table_name}/html", response_class=HTMLResponse)
        async def get_table_html(request: Request):
            """Get HTML view of table (supports HTMX fragments and admin context)."""
            query_params = dict(request.query_params)
            
            # Check if this is an admin context (from referer or query param)
            is_admin_context = (
                "admin" in str(request.headers.get("referer", "")).lower() or
                query_params.get("admin") == "true"
            )
            
            # Handle RQL parameter specially - extract from form input
            rql_query = query_params.get("rql", "")
            if rql_query:
                # RQL query comes from form input, parse it directly
                rql_params = {rql_query: ""}  # RQL parser expects query as key
            else:
                # Remove admin parameter from query params for RQL processing
                rql_params = {k: v for k, v in query_params.items() if k not in ["admin", "rql"]}
            
            try:
                data = self.db_service.execute_rql_query(table_name, rql_params)
                schema = self.db_service.get_table_schema(table_name)
                
                # Check if this is an HTMX request for fragment
                is_htmx = request.headers.get("HX-Request") == "true"
                
                if is_htmx:
                    # Return just the table content for HTMX
                    table_content = self.html_generator.generate_table_fragment(table_name, data, schema)
                    return self.html_generator.render_to_string(table_content)
                else:
                    # Return full HTML page with optional admin features
                    html = self.html_generator.generate_table_html_with_admin(
                        table_name, data, schema, query_params, is_admin_context
                    )
                    return html
            except ValueError as e:
                # Client error - invalid query parameters
                raise HTTPException(status_code=400, detail=str(e))
            except RuntimeError:
                # Server error - database operation failed
                raise HTTPException(status_code=500, detail="Database operation failed")
            except Exception as e:
                logger.error(f"Unexpected error in get_table_html: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

    def _setup_admin(self):
        """Set up HTMX-driven admin portal interface."""

        @self.get("/admin", response_class=HTMLResponse)
        async def admin_portal():
            """Main admin portal with layout and navigation."""
            html_element = self.html_generator.generate_admin_portal()
            return self.html_generator.render_to_string(html_element)

        @self.get("/admin/tables", response_class=HTMLResponse)
        async def admin_tables_list(request: Request):
            """HTMX fragment: Table browser sidebar."""
            tables = self.db_service.list_tables()
            sidebar_content = self.html_generator.generate_tables_sidebar(tables)
            html_element = self.html_generator.render_fragment_or_page(
                sidebar_content, "Tables", request
            )
            return self.html_generator.render_to_string(html_element)



        @self.get("/admin/docs", response_class=HTMLResponse)
        async def admin_docs(request: Request):
            """HTMX fragment: Embedded FastAPI docs."""
            docs_content = self.html_generator.generate_docs_embed()
            html_element = self.html_generator.render_fragment_or_page(
                docs_content, "API Documentation", request
            )
            return self.html_generator.render_to_string(html_element)

        @self.get("/admin/query", response_class=HTMLResponse)
        async def admin_query_interface(request: Request):
            """HTMX fragment: SQL query interface."""
            query_content = self.html_generator.generate_query_interface()
            html_element = self.html_generator.render_fragment_or_page(
                query_content, "SQL Query Interface", request
            )
            return self.html_generator.render_to_string(html_element)

        @self.post("/admin/query", response_class=HTMLResponse)
        async def admin_execute_query(request: Request):
            """HTMX fragment: Execute SQL query."""
            form = await request.form()
            query = form.get("query", "")
            try:
                import duckdb
                result = self.db_service.connection.execute(query).fetchall()
                columns = [desc[0] for desc in self.db_service.connection.description] if self.db_service.connection.description else []
                results_content = self.html_generator.generate_query_results(query, columns, result)
                html_element = self.html_generator.render_fragment_or_page(
                    results_content, "Query Results", request
                )
                return self.html_generator.render_to_string(html_element)
            except Exception as e:
                error_content = self.html_generator.generate_error_fragment(str(e))
                html_element = self.html_generator.render_fragment_or_page(
                    error_content, "Query Error", request
                )
                return self.html_generator.render_to_string(html_element)

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

    def update_records_api(
        self, table_name: str, record_data: dict, query_params: dict = None
    ):
        """Update records (CLI method)."""
        query_params = query_params or {}
        updated_count = self.db_service.update_record(
            table_name, record_data, query_params
        )
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

        # For now, just set up table routes for new tables
        # In a production implementation, we would properly rebuild the router
        current_tables = set(self.db_service.list_tables().keys())
        logger.info(f"Table refresh called - current tables: {current_tables}")

        # Set up routes for tables that don't have routes yet
        self._setup_table_routes()
