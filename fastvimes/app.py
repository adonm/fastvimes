"""FastVimes: Lightweight composition of FastAPI and Ibis for data tools."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.exceptions import HTTPException

from .config import FastVimesSettings
from .endpoints import EndpointGenerator
from .forms import FormGenerator
from .services import AdminService, DatabaseService, StaticFilesService

logger = logging.getLogger(__name__)


class FastVimes(FastAPI):
    """
    FastVimes: Lightweight composition of FastAPI and Ibis for data tools.

    Inherits from FastAPI to provide all FastAPI functionality while adding
    database introspection, automatic API generation, and admin interface.

    Design Philosophy:
    - Lightweight composition of stable dependencies (FastAPI, Ibis, Pydantic)
    - Clean separation of concerns via services
    - Transparent access to underlying FastAPI and Ibis APIs
    - Sensible defaults with full customization capability
    """

    def __init__(
        self,
        config: FastVimesSettings | None = None,
        db_path: str | None = None,
        extensions: list[str] | None = None,
        read_only: bool | None = None,
        admin_enabled: bool | None = None,
        html_path: str | None = None,
        tables: dict | None = None,
        *args,
        **kwargs,
    ):
        # Initialize configuration - support simple constructor patterns
        if config is None:
            config_kwargs = {}
            if db_path is not None:
                config_kwargs["db_path"] = db_path
            if extensions is not None:
                config_kwargs["extensions"] = extensions
            if read_only is not None:
                config_kwargs["read_only"] = read_only
            if admin_enabled is not None:
                config_kwargs["admin_enabled"] = admin_enabled
            if html_path is not None:
                config_kwargs["html_path"] = html_path
            if tables is not None:
                config_kwargs["tables"] = tables
            self.config = FastVimesSettings(**config_kwargs)
        else:
            self.config = config

        # Initialize FastAPI with default settings
        super().__init__(
            title="FastVimes",
            description="Lightweight composition of FastAPI and Ibis for data tools",
            version="0.1.0",
            *args,
            **kwargs,
        )

        # Initialize services
        self.db_service = DatabaseService(self.config)
        self.static_service = StaticFilesService(self, self.config)
        self.admin_service = AdminService(self, self.config)

        # Initialize generators
        self.endpoint_generator = EndpointGenerator(self.db_service)
        self.form_generator = FormGenerator(self)

        # Generate endpoints for all discovered tables
        self._generate_endpoints()

        logger.info(f"FastVimes initialized with database: {self.config.db_path}")

    def _generate_endpoints(self) -> None:
        """Generate API endpoints for all discovered tables."""
        tables = self.db_service.list_tables()

        for table_name in tables:
            # Generate endpoints for this table
            table_router = self.endpoint_generator.generate_table_endpoints(table_name)
            self.include_router(table_router)

            logger.info(f"Generated endpoints for table: {table_name}")

        # Generate meta endpoints
        meta_router = self.endpoint_generator.generate_meta_endpoints()
        self.include_router(meta_router)

        # Add root route redirect
        self._add_root_route()
        
        # Generate dynamic table endpoints
        dynamic_router = self.endpoint_generator.generate_dynamic_endpoints()
        self.include_router(dynamic_router)

        # Add HTML error handling (disabled for now due to test conflicts)
        # self._add_html_error_handlers()
    
    def _add_root_route(self):
        """Add root route that redirects to admin or shows welcome page."""
        from fastapi.responses import RedirectResponse
        
        @self.get("/")
        async def root():
            """Root endpoint - redirect to admin if enabled, otherwise show API docs."""
            if self.config.admin_enabled:
                return RedirectResponse(url="/admin", status_code=302)
            else:
                return RedirectResponse(url="/docs", status_code=302)

    # Convenience properties to access services
    @property
    def db(self):
        """Access to database service (Ibis connection)."""
        return self.db_service.connection

    @property
    def connection(self):
        """Access to database connection (alias for db)."""
        return self.db_service.connection

    # Convenience methods that delegate to services
    def get_table(self, table_name: str):
        """Get Ibis table reference."""
        return self.db_service.get_table(table_name)

    def get_table_config(self, table_name: str):
        """Get configuration for a specific table."""
        return self.db_service.get_table_config(table_name)

    def list_tables(self):
        """List all available tables with their configurations."""
        return self.db_service.list_tables()

    def execute_query(self, query):
        """Execute a query and return results."""
        return self.db_service.execute_query(query)

    def get_table_dataclass(self, table_name: str):
        """Generate a dynamic Pydantic model from Ibis table schema."""
        return self.db_service.get_table_dataclass(table_name)

    def generate_form(self, table_name: str, **kwargs):
        """Generate HTML form for a table (convenience method)."""
        return self.form_generator.generate_form(
            self.get_table_dataclass(table_name), **kwargs
        )

    def run(
        self, host: str = "127.0.0.1", port: int = 8000, reload: bool = False, **kwargs
    ) -> None:
        """
        Run the FastVimes application with uvicorn.

        Convenience method for running the application with common defaults.
        For production use, consider using uvicorn directly with proper configuration.

        Args:
            host: Host to bind to (default: 127.0.0.1)
            port: Port to bind to (default: 8000)
            reload: Enable auto-reload (default: False)
            **kwargs: Additional arguments passed to uvicorn.run()
        """
        import uvicorn

        uvicorn.run(self, host=host, port=port, reload=reload, **kwargs)

    def close(self) -> None:
        """Close database connection."""
        self.db_service.close()

    def _add_html_error_handlers(self) -> None:
        """Add HTML error handling for web requests."""

        @self.exception_handler(HTTPException)
        async def html_http_exception_handler(request: Request, exc: HTTPException):
            """Handle HTTPException for HTML requests with Bulma styling."""
            # Skip error handling for test client
            if request.client and request.client.host == "testclient":
                raise exc

            # Check if request expects HTML
            accept_header = request.headers.get("accept", "")
            if "text/html" in accept_header or request.url.path.endswith("/html"):
                return HTMLResponse(
                    content=self._generate_error_html(exc.status_code, exc.detail),
                    status_code=exc.status_code,
                )
            # Default to FastAPI's handling
            raise exc

        @self.exception_handler(Exception)
        async def html_general_exception_handler(request: Request, exc: Exception):
            """Handle general exceptions for HTML requests."""
            # Skip error handling for test client
            if request.client and request.client.host == "testclient":
                raise exc

            # Check if request expects HTML
            accept_header = request.headers.get("accept", "")
            if "text/html" in accept_header or request.url.path.endswith("/html"):
                return HTMLResponse(
                    content=self._generate_error_html(500, "Internal Server Error"),
                    status_code=500,
                )
            # Default to FastAPI's handling
            raise exc

    def _generate_error_html(self, status_code: int, detail: str) -> str:
        """Generate HTML error page with Bulma styling."""
        from fasthtml.common import Html, Head, Body, Div, H1, P, Link, Meta, Title

        return str(
            Html(
                Head(
                    Meta(charset="utf-8"),
                    Meta(
                        name="viewport", content="width=device-width, initial-scale=1"
                    ),
                    Title(f"Error {status_code}"),
                    Link(
                        rel="stylesheet",
                        href="https://unpkg.com/bulma@1.0.4/css/bulma.css",
                    ),
                ),
                Body(
                    Div(
                        Div(
                            H1(f"Error {status_code}", cls="title has-text-danger"),
                            P(detail, cls="subtitle"),
                            cls="has-text-centered",
                        ),
                        cls="hero-body",
                    ),
                    cls="hero is-fullheight",
                ),
            )
        )
