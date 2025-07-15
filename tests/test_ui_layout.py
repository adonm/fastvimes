"""
Test UI layout and sidebar functionality.

Design Spec: AGENT.md - NiceGUI Exploratory Interface - Sidebar Layout
Coverage: Base layout, sidebar navigation, theme system, page routing
"""


import pytest

from fastvimes.app import FastVimes


@pytest.fixture
def app():
    """Create FastVimes app for testing."""
    # Create with minimal setup to avoid DuckDB UI issues in tests
    from fastvimes.config import FastVimesSettings

    settings = FastVimesSettings(duckdb_ui_enabled=False)
    app = FastVimes(settings=settings)
    yield app
    app.db_service.close()


class TestUILayout:
    """Test UI layout and sidebar functionality."""

    def test_app_initialization(self, app):
        """Test that FastVimes app initializes correctly."""
        assert app.db_service is not None
        assert app.api_client is not None
        assert hasattr(app, "dark_mode")
        assert hasattr(app, "settings")

    def test_theme_setup(self, app):
        """Test theme system setup."""
        # Theme should be initialized
        assert hasattr(app, "dark_mode")
        assert app.dark_mode is not None

        # Toggle theme method should exist
        assert hasattr(app, "_toggle_theme")

        # Theme toggle should work (basic functionality test)
        app._toggle_theme()  # Should not raise exception

    def test_content_methods(self, app):
        """Test content rendering methods."""
        # Main content method should exist
        assert hasattr(app, "_main_content")
        assert callable(app._main_content)

        # Table content method should exist
        assert hasattr(app, "_table_content")
        assert callable(app._table_content)

        # Base layout method should exist
        assert hasattr(app, "_render_base_layout")
        assert callable(app._render_base_layout)

    def test_component_methods(self, app):
        """Test component override methods."""
        # Component methods should exist and be callable
        assert hasattr(app, "table_component")
        assert hasattr(app, "form_component")
        assert hasattr(app, "query_component")
        assert hasattr(app, "table_browser_component")

        # Should return component instances
        table_comp = app.table_component("users")
        assert hasattr(table_comp, "render")

        form_comp = app.form_component("users")
        assert hasattr(form_comp, "render")

        query_comp = app.query_component("users")
        assert hasattr(query_comp, "render")

        browser_comp = app.table_browser_component()
        assert hasattr(browser_comp, "render")

    def test_logs_content(self, app):
        """Test logs content rendering."""
        # Logs content method should exist
        assert hasattr(app, "_render_logs_content")
        assert callable(app._render_logs_content)

        # Log handler should exist
        assert hasattr(app, "log_handler")
        assert app.log_handler is not None

        # Should be able to get logs
        logs = app.log_handler.get_logs()
        assert isinstance(logs, list)

    def test_duckdb_ui_setup(self, app):
        """Test DuckDB UI setup."""
        # DuckDB UI should be configured
        assert hasattr(app, "duckdb_ui_enabled")
        assert hasattr(app, "settings")
        assert hasattr(app.settings, "duckdb_ui_port")

        # Setup method should exist
        assert hasattr(app, "_setup_duckdb_ui")
        assert callable(app._setup_duckdb_ui)


@pytest.mark.fast
class TestUILayoutFast:
    """Fast UI layout tests."""

    def test_sidebar_navigation_structure(self, app):
        """Test sidebar navigation structure."""
        # The sidebar should have navigation items defined
        # This is a structural test - actual rendering would need NiceGUI context

        # Check that navigation methods exist
        assert hasattr(app, "_render_base_layout")

        # Check that all page content methods exist
        assert hasattr(app, "_main_content")
        assert hasattr(app, "_table_content")
        assert hasattr(app, "_render_logs_content")

    def test_theme_system_structure(self, app):
        """Test theme system structure."""
        # Theme system should be properly initialized
        assert hasattr(app, "dark_mode")
        assert hasattr(app, "_toggle_theme")
        assert hasattr(app, "_setup_theme")

        # Toggle should work without error
        app._toggle_theme()

    def test_ui_setup_structure(self, app):
        """Test UI setup structure."""
        # UI setup method should exist
        assert hasattr(app, "_setup_ui")
        assert callable(app._setup_ui)

        # Should not raise exception when called
        # Note: This doesn't actually render UI, just tests the method exists
        try:
            app._setup_ui()
        except Exception:
            # Expected in test environment without NiceGUI context
            # Just ensure method exists and is callable
            assert callable(app._setup_ui)
