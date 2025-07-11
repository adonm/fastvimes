"""Services for FastVimes components."""

import logging
from pathlib import Path
from typing import Any

import ibis
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from ibis.expr.types import Table
from pydantic import BaseModel, create_model

from .config import FastVimesSettings, TableConfig

logger = logging.getLogger(__name__)


class DatabaseService:
    """Handle database connections and table discovery."""

    def __init__(self, config: FastVimesSettings):
        self.config = config
        self._connection: ibis.BaseBackend | None = None
        self._tables: dict[str, Table] = {}
        self._table_configs: dict[str, TableConfig] = {}

        self._setup_database()
        self._discover_tables()

    def _setup_database(self) -> None:
        """Initialize Ibis connection to DuckDB with extensions."""
        try:
            self._connection = ibis.duckdb.connect(
                database=self.config.db_path, read_only=self.config.read_only
            )

            # Load extensions
            for extension in self.config.extensions:
                try:
                    self._connection.load_extension(extension)
                    logger.info(f"Loaded DuckDB extension: {extension}")
                except Exception as e:
                    logger.warning(f"Failed to load extension {extension}: {e}")

        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise RuntimeError(f"Database initialization failed: {e}")

    def _discover_tables(self) -> None:
        """Discover available tables and setup configurations."""
        if not self._connection:
            return

        try:
            # Get all tables from the database
            table_names = self._connection.list_tables()

            for table_name in table_names:
                # Get table reference
                table = self._connection.table(table_name)
                self._tables[table_name] = table

                # Setup table configuration
                table_config = self.config.get_table_config(table_name)
                self._table_configs[table_name] = table_config

                logger.info(
                    f"Discovered table: {table_name} (mode: {table_config.mode})"
                )

        except Exception as e:
            logger.error(f"Failed to discover tables: {e}")
            # Don't raise an error for table discovery issues during initialization
            # This allows the service to start even if no tables exist initially

    def _discover_table(self, table_name: str) -> None:
        """Discover a specific table dynamically."""
        if not self._connection:
            return

        try:
            # Check if table exists
            if table_name in self._connection.list_tables():
                # Get table reference
                table = self._connection.table(table_name)
                self._tables[table_name] = table

                # Setup table configuration
                table_config = self.config.get_table_config(table_name)
                self._table_configs[table_name] = table_config

                logger.info(
                    f"Discovered table: {table_name} (mode: {table_config.mode})"
                )
        except Exception as e:
            logger.error(f"Failed to discover table {table_name}: {e}")

    @property
    def connection(self) -> ibis.BaseBackend:
        """Get the database connection."""
        if not self._connection:
            raise RuntimeError("Database connection not initialized")
        return self._connection

    def get_table(self, table_name: str) -> Table:
        """Get Ibis table reference."""
        if table_name not in self._tables:
            # Try to discover table dynamically
            self._discover_table(table_name)

        if table_name not in self._tables:
            raise HTTPException(
                status_code=404, detail=f"Table '{table_name}' not found"
            )
        return self._tables[table_name]

    def get_table_config(self, table_name: str) -> TableConfig:
        """Get configuration for a specific table."""
        return self._table_configs.get(
            table_name, self.config.get_table_config(table_name)
        )

    def list_tables(self) -> dict[str, TableConfig]:
        """List all available tables with their configurations."""
        # Refresh table discovery to catch any new tables
        self._discover_tables()
        return self._table_configs.copy()

    def execute_query(self, query: str | Table) -> Any:
        """Execute a query and return results."""
        if not self._connection:
            raise RuntimeError("Database connection not initialized")

        try:
            if isinstance(query, str):
                # Check if it's a DDL statement (CREATE, DROP, ALTER, etc.)
                query_upper = query.strip().upper()
                if any(
                    query_upper.startswith(ddl)
                    for ddl in ["CREATE", "DROP", "ALTER", "INSERT", "UPDATE", "DELETE"]
                ):
                    # Use raw_sql for DDL statements
                    result = self._connection.raw_sql(query)
                    return {
                        "message": "Query executed successfully",
                        "result": str(result),
                    }
                else:
                    # Use sql() for SELECT statements
                    return self._connection.sql(query)
            else:
                return query.execute()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise HTTPException(status_code=500, detail=f"Query execution failed: {e}")

    def get_table_dataclass(self, table_name: str) -> type[BaseModel]:
        """
        Generate a dynamic Pydantic model from Ibis table schema.

        This enables runtime validation and form generation based on
        the actual database schema.
        """
        if table_name not in self._tables:
            # Try to discover table dynamically
            self._discover_table(table_name)

        if table_name not in self._tables:
            raise HTTPException(
                status_code=404, detail=f"Table '{table_name}' not found"
            )

        table = self._tables[table_name]
        schema = table.schema()

        # Convert Ibis types to Pydantic field types
        field_definitions = {}

        for field_name, ibis_type in schema.items():
            python_type = self._ibis_to_python_type(ibis_type)
            field_definitions[field_name] = (python_type, ...)

        # Create dynamic Pydantic model
        model_name = f"{table_name.title()}Model"
        return create_model(model_name, **field_definitions)

    def _ibis_to_python_type(self, ibis_type: Any) -> type:
        """Convert Ibis type to Python type for Pydantic."""
        type_mapping = {
            "int64": int,
            "int32": int,
            "int16": int,
            "int8": int,
            "float64": float,
            "float32": float,
            "string": str,
            "boolean": bool,
            "timestamp": str,  # Could be datetime, but str is safer for forms
            "date": str,
            "time": str,
        }

        # Get the string representation of the type
        type_str = str(ibis_type).lower()

        # Handle nullable types
        if "?" in type_str:
            base_type = type_str.replace("?", "")
            python_type = type_mapping.get(base_type, str)
            return python_type | None

        return type_mapping.get(type_str, str)

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            # Ibis backends don't have a close method, just disconnect
            if hasattr(self._connection, "disconnect"):
                self._connection.disconnect()
            self._connection = None
            logger.info("Database connection closed")


class StaticFilesService:
    """Handle static file serving."""

    def __init__(self, app: FastAPI, config: FastVimesSettings):
        self.app = app
        self.config = config
        self._setup_static_files()

    def _setup_static_files(self) -> None:
        """Setup static file serving for admin interface and user files."""
        # Serve admin static files
        admin_static_path = Path(__file__).parent / "static"
        if admin_static_path.exists():
            self.app.mount(
                "/static", StaticFiles(directory=str(admin_static_path)), name="static"
            )

        # Serve user HTML files if specified
        if self.config.html_path:
            html_path = Path(self.config.html_path)
            if html_path.exists():
                self.app.mount(
                    "/html", StaticFiles(directory=str(html_path)), name="html"
                )


class AdminService:
    """Handle admin interface."""

    def __init__(self, app: FastAPI, config: FastVimesSettings):
        self.app = app
        self.config = config

        if self.config.admin_enabled:
            self._setup_admin_routes()

    def _setup_admin_routes(self) -> None:
        """Setup admin interface routes."""
        from fastapi.responses import HTMLResponse

        admin_path = Path(__file__).parent / "admin"

        @self.app.get("/admin", response_class=HTMLResponse)
        async def admin_dashboard() -> str:
            """Main admin dashboard."""
            dashboard_file = admin_path / "dashboard.html"
            if dashboard_file.exists():
                return dashboard_file.read_text()
            return "<h1>Admin Dashboard</h1><p>No admin interface found</p>"

        @self.app.get("/admin/tables", response_class=HTMLResponse)
        async def admin_tables() -> str:
            """Table browser interface."""
            tables_file = admin_path / "tables.html"
            if tables_file.exists():
                return tables_file.read_text()
            return "<h1>Tables</h1><p>No tables interface found</p>"

        @self.app.get("/admin/schema", response_class=HTMLResponse)
        async def admin_schema() -> str:
            """Schema editor interface."""
            schema_file = admin_path / "schema.html"
            if schema_file.exists():
                return schema_file.read_text()
            return "<h1>Schema</h1><p>No schema interface found</p>"

        @self.app.get("/admin/config", response_class=HTMLResponse)
        async def admin_config() -> str:
            """Configuration management interface."""
            config_file = admin_path / "config.html"
            if config_file.exists():
                return config_file.read_text()
            return "<h1>Configuration</h1><p>No config interface found</p>"

        @self.app.get("/admin/nav", response_class=HTMLResponse)
        async def admin_nav() -> str:
            """Navigation component for HTMX."""
            nav_file = admin_path / "nav.html"
            if nav_file.exists():
                return nav_file.read_text()
            return "<nav>No navigation found</nav>"
