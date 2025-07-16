"""FastVimes core application - lean implementation leveraging mature dependencies."""

import atexit
import logging
from pathlib import Path

from fastapi import FastAPI
from nicegui import ui, app as nicegui_app

from .api import build_api
from .config import FastVimesSettings
from .database_service import DatabaseService


class FastVimes:
    """FastVimes application with auto-generated NiceGUI interface.
    
    Leverages mature dependencies:
    - NiceGUI: ui.aggrid, ui.tree, ui.dark_mode, Quasar theming
    - FastAPI: dependency injection, routing, security
    - DuckDB: high-performance analytics + UI extension
    """

    def __init__(
        self,
        db_path: str | None = None,
        settings: FastVimesSettings | None = None,
    ):
        """Initialize FastVimes with minimal setup.

        Args:
            db_path: Path to DuckDB database. If None, uses in-memory with sample data.
            settings: Configuration settings. If None, loads from environment/config files.
        """
        self.settings = settings or FastVimesSettings()
        
        # Setup logging using stdlib
        logging.basicConfig(
            level=self.settings.log_level,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        self.logger = logging.getLogger(__name__)

        # Setup database
        if db_path is None:
            self.db_path = Path(":memory:")
            create_sample = True
        else:
            self.db_path = Path(db_path)
            create_sample = False

        self.logger.info(f"FastVimes initialized with database: {self.db_path}")

        # Initialize database service (single source of truth)
        self.db_service = DatabaseService(self.db_path, create_sample_data=create_sample)

        # Setup FastAPI with dependency injection
        self.api = build_api(self.db_service, self.settings)
        
        # Mount API on NiceGUI
        nicegui_app.mount("/api", self.api)

        # Setup NiceGUI pages
        self._setup_ui()

        # Setup DuckDB UI extension
        self._setup_duckdb_ui()

        # Register cleanup
        atexit.register(self._cleanup)

    def _setup_ui(self):
        """Setup NiceGUI pages using built-in components."""
        from . import ui_pages
        ui_pages.register_pages(self)

    def _setup_duckdb_ui(self):
        """Setup DuckDB UI extension if enabled."""
        if not self.settings.admin_enabled or not self.settings.duckdb_ui_enabled:
            return

        # DuckDB UI works with in-memory databases, just won't persist settings
        if self.db_path == Path(":memory:"):
            self.logger.info("DuckDB UI enabled for in-memory database (settings won't persist)")

        try:
            conn = self.db_service.connection
            conn.execute("INSTALL ui")
            conn.execute("LOAD ui")
            conn.execute(f"SET ui_local_port = {self.settings.duckdb_ui_port}")
            
            if self.settings.duckdb_ui_auto_launch:
                conn.execute("CALL start_ui_server()")
                self.logger.info(f"DuckDB UI started on port {self.settings.duckdb_ui_port}")
                
        except Exception as e:
            self.logger.error(f"Could not setup DuckDB UI: {e}")

    def _cleanup(self):
        """Clean up resources on shutdown."""
        if hasattr(self, "db_service") and self.db_service:
            self.db_service.close()

    # Override hooks for customization
    def override_table_page(self, table_name: str):
        """Override hook for custom table pages. Return None to use default."""
        return None
        
    def override_form_page(self, table_name: str):
        """Override hook for custom form pages. Return None to use default."""
        return None

    def serve(self, host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
        """Start the FastVimes server."""
        ui.run(
            host=host,
            port=port,
            reload=reload,
            title="FastVimes",
            dark=self.settings.dark_mode,
        )
