"""Tests for the new lean FastVimes structure."""


import pytest

from fastvimes import FastVimes, FastVimesSettings


class TestLeanStructure:
    """Test the lean 7-file structure works correctly."""

    @pytest.fixture
    def test_settings(self):
        """Test settings."""
        return FastVimesSettings(
            db_path=":memory:",
            log_level="ERROR",  # Reduce test noise
            duckdb_ui_enabled=False,  # Skip UI for tests
        )

    @pytest.fixture
    def app(self, test_settings):
        """Create FastVimes app for testing."""
        return FastVimes(settings=test_settings)

    def test_app_initialization(self, app):
        """Test FastVimes app initializes correctly."""
        assert app.db_service is not None
        assert app.api is not None
        assert app.settings is not None

    def test_database_service_integration(self, app):
        """Test database service works with lean structure."""
        # Test basic operations
        tables = app.db_service.list_tables()
        assert isinstance(tables, list)

        if tables:  # If sample data is present
            first_table = tables[0]["name"]
            schema = app.db_service.get_table_schema(first_table)
            assert isinstance(schema, list)

            data = app.db_service.get_table_data(first_table, limit=5)
            assert data is not None

    def test_api_mount(self, app):
        """Test FastAPI is properly mounted."""
        # The API should be accessible
        assert app.api is not None
        assert hasattr(app.api, "routes")

        # Check some expected routes exist
        route_paths = [route.path for route in app.api.routes]
        assert any("/v1/meta/tables" in path for path in route_paths)
        assert any("/v1/data/" in path for path in route_paths)

    def test_override_hooks(self, app):
        """Test override hooks return None by default."""
        assert app.override_table_page("test_table") is None
        assert app.override_form_page("test_table") is None

    def test_settings_integration(self, test_settings):
        """Test settings work correctly."""
        assert test_settings.log_level == "ERROR"
        assert test_settings.db_path == ":memory:"
        assert not test_settings.duckdb_ui_enabled

    @pytest.mark.asyncio
    async def test_api_endpoints_basic(self, app):
        """Test basic API endpoints work."""
        from fastapi.testclient import TestClient

        client = TestClient(app.api)

        # Test tables endpoint
        response = client.get("/v1/meta/tables")
        assert response.status_code == 200
        tables = response.json()
        assert isinstance(tables, list)

    def test_backward_compatibility_imports(self):
        """Test old imports still work with deprecation warnings."""
        import importlib
        import sys
        
        # Remove cached module to ensure fresh import
        if 'fastvimes.components' in sys.modules:
            del sys.modules['fastvimes.components']
        
        with pytest.warns(DeprecationWarning):
            import fastvimes.components
            from fastvimes.components import AGGridDataExplorer


@pytest.mark.fast
class TestLeanStructureFast:
    """Fast tests for lean structure - no server startup."""

    def test_imports(self):
        """Test all imports work."""
        from fastvimes import FastVimes, FastVimesSettings
        from fastvimes.app import FastVimes as AppFastVimes
        from fastvimes.config import FastVimesSettings as ConfigSettings

        assert FastVimes is AppFastVimes
        assert FastVimesSettings is ConfigSettings

    def test_minimal_initialization(self):
        """Test minimal app initialization."""
        settings = FastVimesSettings(
            db_path=":memory:",
            log_level="ERROR",
            duckdb_ui_enabled=False,
        )
        app = FastVimes(settings=settings)

        assert app.db_service is not None
        assert app.api is not None
        app._cleanup()  # Manual cleanup for test
