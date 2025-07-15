"""FastVimes main application class with NiceGUI + DuckLake integration."""

import atexit
import logging
import shutil
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import (
    Body,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from nicegui import app, ui

from .api_client import FastVimesAPIClient
from .components.data_explorer import DataExplorer
from .components.form_generator import FormGenerator
from .components.query_builder import QueryBuilder
from .components.table_browser import TableBrowser
from .config import FastVimesSettings
from .database_service import DatabaseService
from .middleware.auth_authlib import (
    require_auth,
)


class LogHandler(logging.Handler):
    """Custom logging handler that stores logs in memory for the logs page."""

    def __init__(self, max_logs: int = 1000):
        super().__init__()
        self.max_logs = max_logs
        self.logs = deque(maxlen=max_logs)

    def emit(self, record):
        """Store log record in memory."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": self.format(record),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
            "source": "Python",
        }
        self.logs.append(log_entry)

    def get_logs(self):
        """Get all stored logs."""
        return list(self.logs)

    def clear_logs(self):
        """Clear all stored logs."""
        self.logs.clear()


class FastVimes:
    """FastVimes application with auto-generated NiceGUI interface."""

    def __init__(
        self,
        db_path: str | None = None,
        settings: FastVimesSettings | None = None,
    ):
        """Initialize FastVimes with DuckLake backend.

        Args:
            db_path: Path to DuckLake database. If None, creates temp DuckLake with sample data.
            settings: Configuration settings. If None, loads from environment/config files.
        """
        self.settings = settings or FastVimesSettings()

        # Setup logging
        self.log_handler = LogHandler()
        self.logger = logging.getLogger("fastvimes")
        self.logger.setLevel(logging.INFO)

        # Setup formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.log_handler.setFormatter(formatter)

        # Add handler to root logger to capture all logs
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        root_logger.setLevel(logging.INFO)

        # Also add to FastVimes logger specifically
        self.logger.addHandler(self.log_handler)

        # Setup DuckLake database
        if db_path is None:
            self._setup_temp_database()
        else:
            self.db_path = Path(db_path)

        self.logger.info(f"FastVimes initialized with database: {self.db_path}")

        # Initialize database service
        create_sample = db_path is None  # Create sample data if using temp database
        self.db_service = DatabaseService(
            self.db_path, create_sample_data=create_sample
        )

        # Initialize API client for NiceGUI components (in-process mode for development)
        self.api_client = FastVimesAPIClient(db_service=self.db_service)

        # DuckDB UI status tracking
        self.duckdb_ui_enabled = False

        # Setup authentication if enabled
        if self.settings.auth_enabled:
            # Note: Auth middleware implementation would go here
            # For now, disable authentication until middleware is properly set up
            self.auth_manager = None
            self.auth_ui = None
        else:
            self.auth_manager = None
            self.auth_ui = None

        # Setup FastAPI for RQL endpoints
        self.api = FastAPI(title="FastVimes API", version="0.1.0")
        self._setup_api_routes()

        # Setup NiceGUI interface
        self._setup_ui()

        # Setup authentication routes if enabled
        if self.auth_manager:
            self._setup_auth_routes()

        # Setup DuckDB UI extension
        self._setup_duckdb_ui()

        # Setup theme system
        self._setup_theme()

        # Register cleanup
        atexit.register(self._cleanup)

    def _setup_duckdb_ui(self):
        """Setup DuckDB UI extension using built-in commands."""
        if not self.settings.admin_enabled or not self.settings.duckdb_ui_enabled:
            return

        try:
            # Use the same connection from database service
            conn = self.db_service.connection

            # Install and load UI extension
            conn.execute("INSTALL ui")
            conn.execute("LOAD ui")

            # Configure UI server
            conn.execute(f"SET ui_local_port = {self.settings.duckdb_ui_port}")

            # Enable logging if admin enabled
            if self.settings.admin_enabled:
                conn.execute("PRAGMA enable_logging")
                self.logger.info("DuckDB logging enabled")

            # Start UI server if auto-launch is enabled
            if self.settings.duckdb_ui_auto_launch:
                conn.execute("CALL start_ui_server()")
                self.logger.info(
                    f"DuckDB UI started on port {self.settings.duckdb_ui_port}"
                )

            self.duckdb_ui_enabled = True

        except Exception as e:
            self.logger.error(f"Could not setup DuckDB UI: {e}")
            self.duckdb_ui_enabled = False

    def _cleanup(self):
        """Clean up resources on shutdown."""
        if hasattr(self, "db_service") and self.db_service:
            self.db_service.close()

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
        if hasattr(self, "temp_dir") and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def _setup_api_routes(self):
        """Setup FastAPI routes with namespaced v1 API structure."""

        from fastapi import Response

        # =============================================================================
        # AUTHENTICATION ENDPOINTS
        # =============================================================================

        if self.auth_manager:

            @self.api.post("/v1/auth/login")
            async def login(credentials: dict[str, str]):
                """Login with username and password."""
                username = credentials.get("username")
                password = credentials.get("password")

                if not username or not password:
                    raise HTTPException(
                        status_code=400, detail="Username and password required"
                    )

                user = self.auth_manager.authenticate_user(username, password)
                if not user:
                    raise HTTPException(status_code=401, detail="Invalid credentials")

                token = self.auth_manager.create_access_token(user)
                return {"access_token": token, "token_type": "bearer", "user": user}

            @self.api.post("/v1/auth/logout")
            async def logout(
                current_user: dict[str, Any] = Depends(require_auth(self.auth_manager)),
            ):
                """Logout current user."""
                token = current_user.get("token")
                if token:
                    self.auth_manager.logout_user(token)
                return {"message": "Logged out successfully"}

            @self.api.get("/v1/auth/me")
            async def get_current_user(
                current_user: dict[str, Any] = Depends(require_auth(self.auth_manager)),
            ):
                """Get current user information."""
                return current_user

        # =============================================================================
        # META ENDPOINTS - Database introspection
        # =============================================================================

        @self.api.get("/v1/meta/tables")
        async def list_tables(
            current_user: dict[str, Any] = Depends(require_auth(self.auth_manager))
            if self.auth_manager
            else None,
        ):
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
                table_names = [t["name"] for t in tables]
                if table_name not in table_names:
                    raise HTTPException(
                        status_code=404, detail=f"Table '{table_name}' not found"
                    )

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
            limit: int | None = 100,
            offset: int | None = 0,
            format: str = "json",
        ):
            """Get table data with RQL filtering and multi-format support."""
            try:
                # Verify table exists
                tables = self.db_service.list_tables()
                table_names = [t["name"] for t in tables]
                if table_name not in table_names:
                    raise HTTPException(
                        status_code=404, detail=f"Table '{table_name}' not found"
                    )

                # Extract RQL query from query parameters
                rql_query = None
                if request.url.query:
                    # Remove limit, offset, and format from query string for RQL processing
                    query_parts = []
                    for part in str(request.url.query).split("&"):
                        if not part.startswith(("limit=", "offset=", "format=")):
                            query_parts.append(part)
                    if query_parts:
                        rql_query = "&".join(query_parts)

                # Get table data with RQL filtering
                result = self.db_service.get_table_data(
                    table_name=table_name,
                    rql_query=rql_query,
                    limit=limit,
                    offset=offset,
                    format=format,
                )

                # Handle different response formats
                if format.lower() == "json":
                    return result
                elif format.lower() == "csv":
                    return Response(
                        content=result,
                        media_type="text/csv",
                        headers={
                            "Content-Disposition": f"attachment; filename={table_name}.csv"
                        },
                    )
                elif format.lower() == "parquet":
                    return Response(
                        content=result,
                        media_type="application/octet-stream",
                        headers={
                            "Content-Disposition": f"attachment; filename={table_name}.parquet"
                        },
                    )
                else:
                    raise HTTPException(
                        status_code=400, detail=f"Unsupported format: {format}"
                    )

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.api.post("/v1/data/{table_name}")
        async def create_record(
            table_name: str,
            record_data: dict[str, Any] = Body(...),
            current_user: dict[str, Any] = Depends(require_auth(self.auth_manager))
            if self.auth_manager
            else None,
        ):
            """Create a new record in the specified table."""
            try:
                # Verify table exists
                tables = self.db_service.list_tables()
                table_names = [t["name"] for t in tables]
                if table_name not in table_names:
                    raise HTTPException(
                        status_code=404, detail=f"Table '{table_name}' not found"
                    )

                # Create record
                created_record = self.db_service.create_record(table_name, record_data)
                return {
                    "message": "Record created successfully",
                    "record": created_record,
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.api.put("/v1/data/{table_name}")
        async def update_records(
            table_name: str,
            request: Request,
            record_data: dict[str, Any] = Body(),
            current_user: dict[str, Any] = Depends(require_auth(self.auth_manager))
            if self.auth_manager
            else None,
        ):
            """Update records in the specified table."""
            try:
                # Verify table exists
                tables = self.db_service.list_tables()
                table_names = [t["name"] for t in tables]
                if table_name not in table_names:
                    raise HTTPException(
                        status_code=404, detail=f"Table '{table_name}' not found"
                    )

                # Extract RQL query from query parameters
                rql_query = None
                if request.url.query:
                    rql_query = str(request.url.query)

                # Update records
                count = self.db_service.update_records(
                    table_name=table_name, data=record_data, rql_query=rql_query
                )
                return {"message": f"Updated {count} records", "count": count}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.api.delete("/v1/data/{table_name}")
        async def delete_records(
            table_name: str,
            request: Request,
            current_user: dict[str, Any] = Depends(require_auth(self.auth_manager))
            if self.auth_manager
            else None,
        ):
            """Delete records from the specified table."""
            try:
                # Verify table exists
                tables = self.db_service.list_tables()
                table_names = [t["name"] for t in tables]
                if table_name not in table_names:
                    raise HTTPException(
                        status_code=404, detail=f"Table '{table_name}' not found"
                    )

                # Extract RQL query from query parameters
                rql_query = None
                if request.url.query:
                    rql_query = str(request.url.query)

                if not rql_query:
                    raise HTTPException(
                        status_code=400,
                        detail="RQL query required for deletion to prevent accidental deletion of all records",
                    )

                # Delete records
                count = self.db_service.delete_records(
                    table_name=table_name, rql_query=rql_query
                )
                return {"message": f"Deleted {count} records", "count": count}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        # =============================================================================
        # QUERY ENDPOINT - Raw SQL execution
        # =============================================================================

        @self.api.post("/v1/query")
        async def execute_query(query_data: dict[str, Any]):
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
                            headers={
                                "Content-Disposition": "attachment; filename=query_result.csv"
                            },
                        )
                    else:
                        return Response(content="", media_type="text/csv")
                elif format.lower() == "parquet":
                    # Convert to Parquet format
                    if result:
                        columns = list(result[0].keys())
                        parquet_bytes = self.db_service._export_to_parquet(
                            columns, result
                        )
                        return Response(
                            content=parquet_bytes,
                            media_type="application/octet-stream",
                            headers={
                                "Content-Disposition": "attachment; filename=query_result.parquet"
                            },
                        )
                    else:
                        return Response(
                            content=b"", media_type="application/octet-stream"
                        )
                else:
                    raise HTTPException(
                        status_code=400, detail=f"Unsupported format: {format}"
                    )

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # Bulk Operations Endpoints
        @self.api.post("/v1/data/{table_name}/bulk-insert")
        async def bulk_insert(
            table_name: str,
            file: UploadFile = File(...),
            file_format: str = Query(
                "auto", description="File format: auto, parquet, csv, json"
            ),
            current_user: dict[str, Any] = Depends(require_auth(self.auth_manager))
            if self.auth_manager
            else None,
        ):
            """Bulk insert records from uploaded file."""
            try:
                # Verify table exists
                tables = self.db_service.list_tables()
                table_names = [t["name"] for t in tables]
                if table_name not in table_names:
                    raise HTTPException(
                        status_code=404, detail=f"Table '{table_name}' not found"
                    )

                # Save uploaded file temporarily
                import os
                import tempfile

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=f".{file_format}"
                ) as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    temp_file_path = temp_file.name

                try:
                    # Perform bulk insert
                    records_inserted = self.db_service.bulk_insert_from_file(
                        table_name, temp_file_path, file_format
                    )
                    return {
                        "message": "Bulk insert completed successfully",
                        "records_inserted": records_inserted,
                        "table_name": table_name,
                    }
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)

            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.api.post("/v1/data/{table_name}/bulk-upsert")
        async def bulk_upsert(
            table_name: str,
            file: UploadFile = File(...),
            key_columns: str = Query(
                ..., description="Comma-separated list of key columns for matching"
            ),
            file_format: str = Query(
                "auto", description="File format: auto, parquet, csv, json"
            ),
            current_user: dict[str, Any] = Depends(require_auth(self.auth_manager))
            if self.auth_manager
            else None,
        ):
            """Bulk upsert (insert or update) records from uploaded file."""
            try:
                # Verify table exists
                tables = self.db_service.list_tables()
                table_names = [t["name"] for t in tables]
                if table_name not in table_names:
                    raise HTTPException(
                        status_code=404, detail=f"Table '{table_name}' not found"
                    )

                # Parse key columns
                key_columns_list = [col.strip() for col in key_columns.split(",")]

                # Save uploaded file temporarily
                import os
                import tempfile

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=f".{file_format}"
                ) as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    temp_file_path = temp_file.name

                try:
                    # Perform bulk upsert
                    result = self.db_service.bulk_upsert_from_file(
                        table_name, temp_file_path, key_columns_list, file_format
                    )
                    return {
                        "message": "Bulk upsert completed successfully",
                        "records_inserted": result["inserted"],
                        "records_updated": result["updated"],
                        "table_name": table_name,
                        "key_columns": key_columns_list,
                    }
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)

            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.api.post("/v1/data/{table_name}/bulk-delete")
        async def bulk_delete(
            table_name: str,
            file: UploadFile = File(...),
            key_columns: str = Query(
                ..., description="Comma-separated list of key columns for matching"
            ),
            file_format: str = Query(
                "auto", description="File format: auto, parquet, csv, json"
            ),
            current_user: dict[str, Any] = Depends(require_auth(self.auth_manager))
            if self.auth_manager
            else None,
        ):
            """Bulk delete records based on keys from uploaded file."""
            try:
                # Verify table exists
                tables = self.db_service.list_tables()
                table_names = [t["name"] for t in tables]
                if table_name not in table_names:
                    raise HTTPException(
                        status_code=404, detail=f"Table '{table_name}' not found"
                    )

                # Parse key columns
                key_columns_list = [col.strip() for col in key_columns.split(",")]

                # Save uploaded file temporarily
                import os
                import tempfile

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=f".{file_format}"
                ) as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    temp_file_path = temp_file.name

                try:
                    # Perform bulk delete
                    records_deleted = self.db_service.bulk_delete_from_file(
                        table_name, temp_file_path, key_columns_list, file_format
                    )
                    return {
                        "message": "Bulk delete completed successfully",
                        "records_deleted": records_deleted,
                        "table_name": table_name,
                        "key_columns": key_columns_list,
                    }
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)

            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

    def _setup_ui(self):
        """Setup NiceGUI interface with auto-generated components."""

        # Main page with table browser
        @ui.page("/")
        def index():
            self._render_main_interface()

        # Table detail pages
        @ui.page("/table/{table_name}")
        def table_detail(table_name: str):
            self._render_table_detail(table_name)

        # Embedded UIs
        @ui.page("/admin/duckdb-ui")
        def duckdb_ui():
            self._render_admin_page("DuckDB UI", "duckdb-ui")

        @ui.page("/admin/api-docs")
        def api_docs():
            self._render_admin_page("API Documentation", "api-docs")

        @ui.page("/admin/logs")
        def logs():
            self._render_admin_page("Server Logs", "logs")

    def _render_admin_page(self, title: str, page_type: str):
        """Render admin page with navigation."""
        with ui.header().classes("items-center px-4"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/")).props(
                "flat"
            )
            ui.label(title).classes("text-h5 font-bold ml-2")
            ui.space()
            self._render_admin_nav()

        with ui.column().classes("w-full h-full"):
            if page_type == "duckdb-ui":
                ui.html(
                    f'<iframe src="http://localhost:{self.settings.duckdb_ui_port}" width="100%" height="600" style="border: none;"></iframe>'
                )
            elif page_type == "api-docs":
                ui.html(
                    '<iframe src="/docs" class="w-full h-full" style="border: none;"></iframe>'
                )
            elif page_type == "logs":
                self._render_logs_content()

    def _render_admin_nav(self):
        """Render admin navigation buttons."""
        with ui.row().classes("items-center gap-2"):
            ui.button(
                "API Docs",
                icon="api",
                on_click=lambda: ui.navigate.to("/admin/api-docs"),
            ).props("flat")
            ui.button(
                "SQL Console",
                icon="code",
                on_click=lambda: ui.navigate.to("/admin/duckdb-ui"),
            ).props("flat")
            ui.button(
                "Logs", icon="article", on_click=lambda: ui.navigate.to("/admin/logs")
            ).props("flat")

    def _render_logs_content(self):
        """Render logs page content."""
        with ui.column().classes("w-full p-4"):
            with ui.row().classes("w-full items-center justify-between mb-4"):
                ui.label("Server Logs").classes("text-h6")
                with ui.row().classes("items-center gap-2"):
                    ui.button("Clear", icon="clear", on_click=self._clear_logs).props(
                        "outline"
                    )
                    ui.button(
                        "Refresh", icon="refresh", on_click=self._refresh_logs
                    ).props("outline")

            # Log container
            self.logs_container = (
                ui.column()
                .classes("w-full")
                .style("max-height: 600px; overflow-y: auto;")
            )
            self._refresh_logs()

    def _clear_logs(self):
        """Clear all logs."""
        self.log_handler.clear_logs()
        self.logger.info("Logs cleared by user")
        # Only refresh if the container exists (UI is rendered)
        if hasattr(self, "logs_container"):
            self._refresh_logs()

    def _refresh_logs(self):
        """Refresh logs display."""
        # Only refresh if the container exists (UI is rendered)
        if not hasattr(self, "logs_container"):
            return

        self.logs_container.clear()

        # Get both Python logs and DuckDB logs
        python_logs = self.log_handler.get_logs()
        duckdb_logs = self._get_duckdb_logs()

        # Combine and sort logs by timestamp
        all_logs = python_logs + duckdb_logs
        all_logs.sort(key=lambda x: x["timestamp"], reverse=True)

        if not all_logs:
            with self.logs_container:
                ui.label("No logs available").classes("text-gray-500 italic")
        else:
            with self.logs_container:
                for log in all_logs:  # Already sorted newest first
                    level_color = {
                        "DEBUG": "log-debug",
                        "INFO": "log-info",
                        "WARNING": "log-warning",
                        "ERROR": "log-error",
                        "CRITICAL": "log-error",
                    }.get(log["level"], "log-debug")

                    source_color = (
                        "log-duckdb" if log.get("source") == "DuckDB" else "log-python"
                    )
                    source_label = log.get("source", "Python")

                    with ui.row().classes("w-full items-start gap-2 p-2 log-entry"):
                        ui.label(log["timestamp"][:19]).classes(
                            "text-xs text-gray-500 min-w-fit"
                        )
                        ui.label(source_label).classes(
                            f"text-xs font-semibold {source_color} min-w-fit"
                        )
                        ui.label(log["level"]).classes(
                            f"text-xs font-semibold {level_color} min-w-fit"
                        )
                        ui.label(log["message"]).classes("text-sm flex-1")

    def _get_duckdb_logs(self):
        """Get DuckDB logs from the connection."""
        try:
            # Try to get DuckDB logs if logging is enabled
            if self.duckdb_ui_enabled and hasattr(self, "db_service"):
                # Check if we can get logs from DuckDB
                result = self.db_service.connection.execute(
                    "PRAGMA log_query_path"
                ).fetchall()
                if result:
                    # This is a placeholder - DuckDB logs would need to be read from log files
                    # For now, just return empty list
                    return []
            return []
        except Exception:
            return []

    def _setup_theme(self):
        """Setup Gruvbox color theme with light/dark/auto modes."""
        # Add custom CSS for Gruvbox theme
        ui.add_head_html("""
        <style>
        :root {
            /* Gruvbox Dark Theme */
            --gruvbox-bg: #282828;
            --gruvbox-bg-soft: #32302f;
            --gruvbox-bg-hard: #1d2021;
            --gruvbox-fg: #ebdbb2;
            --gruvbox-fg-soft: #d5c4a1;
            --gruvbox-red: #cc241d;
            --gruvbox-green: #98971a;
            --gruvbox-yellow: #d79921;
            --gruvbox-blue: #458588;
            --gruvbox-purple: #b16286;
            --gruvbox-aqua: #689d6a;
            --gruvbox-orange: #d65d0e;
            --gruvbox-gray: #a89984;
        }
        
        /* Light theme (for light mode) */
        [data-theme="light"] {
            --gruvbox-bg: #fbf1c7;
            --gruvbox-bg-soft: #f2e5bc;
            --gruvbox-bg-hard: #f9f5d7;
            --gruvbox-fg: #3c3836;
            --gruvbox-fg-soft: #504945;
            --gruvbox-red: #cc241d;
            --gruvbox-green: #98971a;
            --gruvbox-yellow: #d79921;
            --gruvbox-blue: #458588;
            --gruvbox-purple: #b16286;
            --gruvbox-aqua: #689d6a;
            --gruvbox-orange: #d65d0e;
            --gruvbox-gray: #7c6f64;
        }
        
        /* Apply theme to body */
        body {
            background-color: var(--gruvbox-bg) !important;
            color: var(--gruvbox-fg) !important;
            transition: background-color 0.3s ease, color 0.3s ease;
        }
        
        /* Header styling */
        .q-header {
            background-color: var(--gruvbox-bg-soft) !important;
            border-bottom: 1px solid var(--gruvbox-gray) !important;
        }
        
        /* Button styling */
        .q-btn {
            color: var(--gruvbox-fg) !important;
        }
        
        .q-btn:hover {
            background-color: var(--gruvbox-bg-hard) !important;
        }
        
        /* Card styling */
        .q-card {
            background-color: var(--gruvbox-bg-soft) !important;
            border: 1px solid var(--gruvbox-gray) !important;
        }
        
        /* Input styling */
        .q-input {
            color: var(--gruvbox-fg) !important;
        }
        
        .q-field__control {
            background-color: var(--gruvbox-bg-hard) !important;
        }
        
        /* Table styling */
        .q-table {
            background-color: var(--gruvbox-bg-soft) !important;
            color: var(--gruvbox-fg) !important;
        }
        
        .q-table__top {
            background-color: var(--gruvbox-bg-hard) !important;
        }
        
        /* Log styling */
        .log-entry {
            border-color: var(--gruvbox-gray) !important;
        }
        
        .log-info { color: var(--gruvbox-blue) !important; }
        .log-warning { color: var(--gruvbox-yellow) !important; }
        .log-error { color: var(--gruvbox-red) !important; }
        .log-debug { color: var(--gruvbox-gray) !important; }
        .log-python { color: var(--gruvbox-purple) !important; }
        .log-duckdb { color: var(--gruvbox-green) !important; }
        </style>
        """)

        # Add theme toggle functionality
        ui.add_head_html("""
        <script>
        function toggleTheme() {
            const body = document.body;
            const currentTheme = body.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        }
        
        // Auto-detect theme on load
        function initTheme() {
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme) {
                document.body.setAttribute('data-theme', savedTheme);
            } else {
                // Auto-detect based on system preference
                const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                document.body.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
            }
        }
        
        // Initialize theme on page load
        document.addEventListener('DOMContentLoaded', initTheme);
        </script>
        """)

    def _toggle_theme(self):
        """Toggle between light and dark theme."""
        ui.run_javascript("toggleTheme()")

    def _render_main_interface(self):
        """Render the main Datasette-style interface."""
        with ui.header().classes("items-center px-4"):
            ui.label("FastVimes").classes("text-h5 font-bold")
            ui.space()
            # Add theme toggle button
            ui.button(icon="brightness_6", on_click=self._toggle_theme).props(
                "flat round"
            ).tooltip("Toggle theme")
            self._render_admin_nav()

        with ui.column().classes("w-full max-w-4xl mx-auto p-4"):
            # Header with search
            with ui.row().classes("w-full items-center justify-between mb-6"):
                ui.label("Database Tables").classes("text-h4")
                ui.input(placeholder="Search tables...").classes("w-64").props(
                    "outlined dense"
                )

            # Table browser component (can be overridden)
            table_browser = self.table_browser_component()
            table_browser.render()

    def _render_table_detail(self, table_name: str):
        """Render detailed view for a specific table."""
        with ui.header().classes("items-center px-4"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/")).props(
                "flat"
            )
            ui.label(f"{table_name}").classes("text-h5 font-bold ml-2")
            ui.space()
            self._render_admin_nav()

        with ui.column().classes("w-full max-w-5xl mx-auto p-4"):
            with ui.tabs().classes("w-full") as tabs:
                data_tab = ui.tab("Data")
                query_tab = ui.tab("Query")
                add_tab = ui.tab("Add Record")

            with ui.tab_panels(tabs, value=data_tab).classes("w-full"):
                with ui.tab_panel(data_tab):
                    # Data explorer component (can be overridden)
                    data_explorer = self.table_component(table_name)
                    data_explorer.render()

                with ui.tab_panel(query_tab):
                    # Query builder component (can be overridden)
                    query_builder = self.query_component(table_name)
                    query_builder.render()

                with ui.tab_panel(add_tab):
                    # Form generator component (can be overridden)
                    form_generator = self.form_component(table_name)
                    form_generator.render()

    def serve(self, host: str = "127.0.0.1", port: int = 8000):
        """Start the FastVimes server."""
        # DuckDB UI is already set up during initialization

        # Mount FastAPI app for API routes
        app.mount("/api", self.api)

        self.logger.info(f"Starting FastVimes server on {host}:{port}")

        # Start NiceGUI with embedded FastAPI
        ui.run(
            host=host,
            port=port,
            title="FastVimes",
            favicon="🦆",
            reload=False,
            show=False,
        )

    # Override methods for customization
    def table_component(self, table_name: str):
        """Override this method to customize table display for specific tables."""
        return DataExplorer(self.api_client, table_name)

    def form_component(self, table_name: str):
        """Override this method to customize forms for specific tables."""
        return FormGenerator(self.api_client, table_name)

    def query_component(self, table_name: str):
        """Override this method to customize query builder for specific tables."""
        return QueryBuilder(self.api_client, table_name)

    def table_browser_component(self):
        """Override this method to customize the table browser."""
        return TableBrowser(self.api_client)

    def _setup_auth_routes(self):
        """Setup authentication routes for NiceGUI."""

        @ui.page("/login")
        def login_page():
            """Login page."""
            self.auth_ui.render_login_page()

        @ui.page("/logout")
        def logout_page():
            """Logout page."""
            self.auth_ui._handle_logout()

        # Add authentication check to protected routes
        def require_auth_ui():
            """Check authentication for UI routes."""
            if not self.auth_manager:
                return None

            # Check if user is authenticated
            current_user = self.auth_ui.check_authentication()
            if not current_user:
                ui.navigate.to("/login")
                return None
            return current_user

        # Override main pages to require authentication
        @ui.page("/")
        def protected_main():
            """Protected main page."""
            current_user = require_auth_ui()
            if current_user:
                self._render_main_page(current_user)

        @ui.page("/table/{table_name}")
        def protected_table_detail(table_name: str):
            """Protected table detail page."""
            current_user = require_auth_ui()
            if current_user:
                self._render_table_detail(table_name, current_user)

    def _render_main_page(self, current_user=None):
        """Render main page with optional user context."""
        # Header with authentication info
        if current_user and self.auth_ui:
            with ui.header().classes("items-center px-4"):
                ui.label("FastVimes").classes("text-h6")
                with ui.row().classes("ml-auto"):
                    self.auth_ui.render_user_info(current_user)
        else:
            with ui.header().classes("items-center px-4"):
                ui.label("FastVimes").classes("text-h6")

        # Main content (existing main page logic)
        with ui.column().classes("w-full max-w-5xl mx-auto p-4"):
            with ui.row().classes("w-full items-center justify-between mb-6"):
                ui.label("Database Tables").classes("text-h4")
                ui.input(placeholder="Search tables...").classes("w-64").props(
                    "outlined dense"
                )

            # Table browser component (can be overridden)
            table_browser = self.table_browser_component()
            table_browser.render()

    def _render_table_detail(self, table_name: str, current_user=None):
        """Render table detail page with optional user context."""
        # Header with authentication info
        if current_user and self.auth_ui:
            with ui.header().classes("items-center px-4"):
                ui.button(
                    icon="arrow_back", on_click=lambda: ui.navigate.to("/")
                ).props("flat")
                ui.label(f"Table: {table_name}").classes("text-h6")
                with ui.row().classes("ml-auto"):
                    self.auth_ui.render_user_info(current_user)
        else:
            with ui.header().classes("items-center px-4"):
                ui.button(
                    icon="arrow_back", on_click=lambda: ui.navigate.to("/")
                ).props("flat")
                ui.label(f"Table: {table_name}").classes("text-h6")

        # Admin links (if admin user)
        if current_user and current_user.get("role") == "admin":
            with ui.row().classes("w-full justify-end p-4"):
                ui.button(
                    "API Docs",
                    icon="api",
                    on_click=lambda: ui.navigate.to("/docs", new_tab=True),
                ).props("flat")
                ui.button(
                    "SQL",
                    icon="code",
                    on_click=lambda: ui.navigate.to("/admin/duckdb-ui", new_tab=True),
                ).props("flat")

        # Main content (existing table detail logic)
        with ui.column().classes("w-full max-w-5xl mx-auto p-4"):
            with ui.tabs().classes("w-full") as tabs:
                data_tab = ui.tab("Data")
                query_tab = ui.tab("Query")
                add_tab = ui.tab("Add Record")

            with ui.tab_panels(tabs, value=data_tab).classes("w-full"):
                with ui.tab_panel(data_tab):
                    # Data explorer component (can be overridden)
                    data_explorer = self.table_component(table_name)
                    data_explorer.render()

                with ui.tab_panel(query_tab):
                    # Query builder component (can be overridden)
                    query_builder = self.query_component(table_name)
                    query_builder.render()

                with ui.tab_panel(add_tab):
                    # Form generator component (can be overridden)
                    form_generator = self.form_component(table_name)
                    form_generator.render()
