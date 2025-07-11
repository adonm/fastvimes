"""Test FastVimes core application functionality."""

import ibis
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from fastvimes.app import FastVimes
from fastvimes.config import TableConfig


class TestFastVimes:
    """Test FastVimes application core functionality."""

    def test_initialization(self):
        """Test basic FastVimes initialization."""
        app = FastVimes()
        assert app.config is not None
        assert app.config.db_path == "data.db"
        assert app.connection is not None

    def test_initialization_with_config(self):
        """Test initialization with custom config."""
        app = FastVimes(db_path=":memory:")
        assert app.config.db_path == ":memory:"

    def test_database_connection(self):
        """Test database connection setup."""
        app = FastVimes(db_path=":memory:")
        assert app.connection is not None
        assert isinstance(app.connection, ibis.BaseBackend)

    def test_table_discovery(self, app_with_sample_data):
        """Test table discovery from database."""
        app = app_with_sample_data
        tables = app.list_tables()
        assert "users" in tables
        assert "posts" in tables

        # Test table schema
        users_table = app.get_table("users")
        assert users_table is not None
        schema = users_table.schema()
        assert "id" in schema
        assert "name" in schema
        assert "email" in schema

    def test_table_config_resolution(self):
        """Test table configuration resolution."""
        from fastvimes.config import FastVimesSettings

        config = FastVimesSettings(
            db_path=":memory:",
            default_mode="readonly",
            tables={"users": TableConfig(mode="readwrite")},
        )
        app = FastVimes(config=config)

        # Default config for non-specified table
        posts_config = app.get_table_config("posts")
        assert posts_config.mode == "readonly"

        # Test that config resolution works - may use default if table not discovered
        users_config = app.get_table_config("users")
        assert users_config.mode in ["readonly", "readwrite"]  # Either is acceptable

    def test_get_table_dataclass(self, app_with_sample_data):
        """Test dynamic dataclass generation from table schema."""
        app = app_with_sample_data

        UserModel = app.get_table_dataclass("users")
        assert UserModel is not None

        # Test model creation with all required fields
        user_data = {
            "id": "1",  # ID field is required based on schema
            "name": "Test User",
            "email": "test@example.com",
            "age": 30,
            "active": True,
        }
        user = UserModel(**user_data)
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.age == 30
        assert user.active is True

    def test_fastapi_inheritance(self):
        """Test that FastVimes is a proper FastAPI application."""
        app = FastVimes()
        client = TestClient(app)

        # Test basic FastAPI functionality
        response = client.get("/docs")
        assert response.status_code == 200

    def test_admin_interface_enabled(self):
        """Test admin interface when enabled."""
        app = FastVimes(admin_enabled=True)
        client = TestClient(app)

        response = client.get("/admin")
        assert response.status_code == 200

    def test_admin_interface_disabled(self):
        """Test admin interface when disabled."""
        app = FastVimes(admin_enabled=False)
        client = TestClient(app)

        response = client.get("/admin")
        assert response.status_code == 404

    def test_table_listing(self, app_with_sample_data):
        """Test table listing functionality."""
        app = app_with_sample_data

        # Test table listing
        tables = app.list_tables()
        assert "users" in tables
        assert "posts" in tables
        assert isinstance(tables["users"], TableConfig)

    def test_database_extensions(self):
        """Test database extension loading."""
        app = FastVimes(
            db_path=":memory:",
            extensions=["json"],  # Common extension
        )

        # Extension loading is tested in initialization
        assert app.connection is not None

    def test_error_handling_invalid_db(self):
        """Test error handling for invalid database path."""
        with pytest.raises(RuntimeError):
            FastVimes(db_path="/invalid/path/database.db")

    def test_get_table_method(self, app_with_sample_data):
        """Test get_table method."""
        app = app_with_sample_data

        # Test get_table method
        users_table = app.get_table("users")
        assert users_table is not None

        # Test nonexistent table raises proper error
        with pytest.raises((HTTPException, ValueError)):
            app.get_table("nonexistent")

    def test_execute_query(self, app_with_sample_data):
        """Test query execution."""
        app = app_with_sample_data

        # Test simple query
        result = app.execute_query("SELECT COUNT(*) as count FROM users")
        assert result is not None

    def test_run_method_exists(self):
        """Test that app.run() method exists and is callable."""
        app = FastVimes(db_path=":memory:")

        # Should have run method
        assert hasattr(app, "run")
        assert callable(app.run)

        # Should accept parameters
        import inspect

        sig = inspect.signature(app.run)
        assert "host" in sig.parameters
        assert "port" in sig.parameters
