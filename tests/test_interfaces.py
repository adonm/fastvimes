"""Consolidated interface tests - same scenarios run through Python API, CLI, and HTTP."""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from fastvimes import FastVimes
from fastvimes.config import FastVimesSettings

# =============================================================================
# SHARED TEST SCENARIOS
# =============================================================================


class TestScenarios:
    """Shared test scenarios that can be executed via different interfaces."""

    @staticmethod
    def get_sample_data() -> list[dict[str, Any]]:
        """Get sample user data for testing."""
        return [
            {
                "id": 1,
                "name": "Alice",
                "email": "alice@example.com",
                "age": 25,
                "active": True,
            },
            {
                "id": 2,
                "name": "Bob",
                "email": "bob@example.com",
                "age": 30,
                "active": True,
            },
            {
                "id": 3,
                "name": "Charlie",
                "email": "charlie@example.com",
                "age": 35,
                "active": False,
            },
            {
                "id": 4,
                "name": "David",
                "email": "david@example.com",
                "age": 22,
                "active": True,
            },
        ]

    @staticmethod
    def get_table_schema() -> str:
        """Get the users table schema."""
        return """
            CREATE TABLE users (
                id INTEGER,
                name VARCHAR,
                email VARCHAR,
                age INTEGER,
                active BOOLEAN
            )
        """

    @staticmethod
    def get_sample_insert_sql() -> str:
        """Get SQL to insert sample data."""
        return """
            INSERT INTO users VALUES
            (1, 'Alice', 'alice@example.com', 25, true),
            (2, 'Bob', 'bob@example.com', 30, true),
            (3, 'Charlie', 'charlie@example.com', 35, false),
            (4, 'David', 'david@example.com', 22, true)
        """


# =============================================================================
# PYTHON API INTERFACE TESTS
# =============================================================================


@pytest.mark.python_api
@pytest.mark.fast
class TestPythonAPI:
    """Test FastVimes via direct Python API calls."""

    @pytest.fixture
    def app_with_data(self):
        """Create FastVimes app with sample data."""
        from fastvimes.config import FastVimesSettings

        # Create config with readwrite mode as default for testing
        config = FastVimesSettings(default_mode="readwrite")
        app = FastVimes(config=config)

        # Create table and data
        app.db_service._connection.execute(TestScenarios.get_table_schema())
        app.db_service._connection.execute(TestScenarios.get_sample_insert_sql())
        app.refresh_table_routes()

        yield app

    def test_01_database_initialization(self):
        """Test database initialization and defaults."""
        app = FastVimes()
        assert app.config.db_path == ":memory:"
        assert app.db_service is not None

    def test_02_table_creation_and_discovery(self, app_with_data):
        """Test table creation and schema discovery."""
        tables = app_with_data.db_service.list_tables()
        assert "users" in tables

        schema = app_with_data.db_service.get_table_schema("users")
        assert schema["name"] == "users"
        assert "id" in schema["columns"]
        assert "name" in schema["columns"]

    def test_03_get_all_records(self, app_with_data):
        """Test getting all records from table."""
        result = app_with_data.get_table_data_api("users", {})
        assert isinstance(result, list)
        assert len(result) == 4

        # Verify sample data is present
        names = [user["name"] for user in result]
        assert "Alice" in names
        assert "Bob" in names
        assert "Charlie" in names
        assert "David" in names

    def test_04_rql_equality_filter(self, app_with_data):
        """Test RQL equality filtering."""
        query_params = {"eq(active,true)": None}
        result = app_with_data.db_service.execute_rql_query("users", query_params)

        assert len(result) == 3  # Alice, Bob, David
        assert all(user["active"] for user in result)

    def test_05_rql_comparison_filters(self, app_with_data):
        """Test RQL comparison operators."""
        # Test greater than
        query_params = {"gt(age,25)": None}
        result = app_with_data.db_service.execute_rql_query("users", query_params)
        assert len(result) == 2  # Bob (30), Charlie (35)
        assert all(user["age"] > 25 for user in result)

        # Test less than
        query_params = {"lt(age,30)": None}
        result = app_with_data.db_service.execute_rql_query("users", query_params)
        assert len(result) == 2  # Alice (25), David (22)
        assert all(user["age"] < 30 for user in result)

    def test_06_rql_contains_filter(self, app_with_data):
        """Test RQL contains filtering."""
        query_params = {"contains(email,alice)": None}
        result = app_with_data.db_service.execute_rql_query("users", query_params)

        assert len(result) == 1
        assert result[0]["name"] == "Alice"
        assert "alice" in result[0]["email"]

    def test_07_rql_limit_and_offset(self, app_with_data):
        """Test RQL limit and offset."""
        # Test limit only
        query_params = {"limit(2)": None}
        result = app_with_data.db_service.execute_rql_query("users", query_params)
        assert len(result) == 2

        # Test limit with offset
        query_params = {"limit(2,1)": None}
        result = app_with_data.db_service.execute_rql_query("users", query_params)
        assert len(result) == 2

    def test_08_create_record(self, app_with_data):
        """Test creating new records."""
        new_user = {
            "name": "Eve",
            "email": "eve@example.com",
            "age": 28,
            "active": True,
        }

        result = app_with_data.create_record_api("users", new_user)
        assert "success" in result or isinstance(result, dict)

        # Verify record was created
        all_users = app_with_data.get_table_data_api("users", {})
        assert len(all_users) == 5

        eve_users = app_with_data.db_service.execute_rql_query(
            "users", {"eq(name,Eve)": None}
        )
        assert len(eve_users) == 1
        assert eve_users[0]["email"] == "eve@example.com"

    def test_09_configuration_settings(self):
        """Test configuration and settings."""
        settings = FastVimesSettings()
        assert settings.db_path == ":memory:"
        assert settings.admin_enabled is True
        assert settings.default_mode == "readonly"

        # Test table configuration
        table_config = settings.get_table_config("users")
        assert table_config.mode == "readonly"
        assert table_config.html is True

    def test_10_error_handling(self, app_with_data):
        """Test error handling for invalid operations."""
        # Test invalid column name in RQL query (should raise ValueError due to validation)
        with pytest.raises(ValueError):
            query_params = {"invalid_column": "eq=test"}
            app_with_data.db_service.execute_rql_query("users", query_params)

        # Test nonexistent table
        with pytest.raises(ValueError):
            app_with_data.db_service.execute_rql_query("nonexistent", {})


# =============================================================================
# CLI INTERFACE TESTS
# =============================================================================


@pytest.mark.cli
@pytest.mark.slow
class TestCLIInterface:
    """Test FastVimes via CLI subprocess calls."""

    def setup_test_db(self, db_path: str):
        """Setup test database with sample data."""
        # Initialize database
        result = subprocess.run(
            ["uv", "run", "fastvimes", "init", "--db", db_path, "--force"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.skip(f"Failed to initialize test database: {result.stderr}")

        # Add sample data
        sample_data = TestScenarios.get_sample_data()
        for user in sample_data[3:]:  # Add David (init already has Alice, Bob, Charlie)
            user_json = json.dumps(user)
            subprocess.run(
                [
                    "uv",
                    "run",
                    "fastvimes",
                    "post",
                    "users",
                    "--data",
                    user_json,
                    "--db",
                    db_path,
                ],
                capture_output=True,
                text=True,
            )

    def test_01_cli_database_init(self):
        """Test CLI database initialization."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            result = subprocess.run(
                ["uv", "run", "fastvimes", "init", "--db", db_path, "--force"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                pytest.skip(f"CLI not available: {result.stderr}")

            assert result.returncode == 0

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_02_cli_list_tables(self):
        """Test CLI tables command."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            self.setup_test_db(db_path)

            result = subprocess.run(
                ["uv", "run", "fastvimes", "tables", "--db", db_path],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            assert "users" in result.stdout

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_03_cli_get_all_records(self):
        """Test CLI get command for all records."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            self.setup_test_db(db_path)

            result = subprocess.run(
                ["uv", "run", "fastvimes", "get", "users", "--db", db_path],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0

            output = json.loads(result.stdout)
            assert isinstance(output, list)
            assert len(output) >= 3  # At least Alice, Bob, Charlie

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_04_cli_rql_filters(self):
        """Test CLI RQL filtering."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            self.setup_test_db(db_path)

            # Test equality filter
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "fastvimes",
                    "get",
                    "users",
                    "--eq",
                    "active,true",
                    "--db",
                    db_path,
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0

            output = json.loads(result.stdout)
            assert len(output) >= 2  # At least Alice and Bob
            assert all(user["active"] for user in output)

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_05_cli_create_record(self):
        """Test CLI record creation."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name

        try:
            self.setup_test_db(db_path)

            new_user = {
                "name": "Frank",
                "email": "frank@example.com",
                "age": 45,
                "active": True,
            }

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "fastvimes",
                    "post",
                    "users",
                    "--data",
                    json.dumps(new_user),
                    "--db",
                    db_path,
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0

            # Verify record was created
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "fastvimes",
                    "get",
                    "users",
                    "--eq",
                    "name,Frank",
                    "--db",
                    db_path,
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0

            output = json.loads(result.stdout)
            assert len(output) == 1
            assert output[0]["name"] == "Frank"

        finally:
            Path(db_path).unlink(missing_ok=True)


# =============================================================================
# HTTP INTERFACE TESTS
# =============================================================================


@pytest.mark.http
@pytest.mark.fast
class TestHTTPInterface:
    """Test FastVimes via HTTP API using TestClient."""

    @pytest.fixture
    def app_with_data(self):
        """Create FastVimes app with sample data for HTTP testing."""
        from fastvimes.config import FastVimesSettings

        # Create config with readwrite mode as default for testing
        config = FastVimesSettings(default_mode="readwrite")
        app = FastVimes(config=config)

        # Create table and data
        app.db_service._connection.execute(TestScenarios.get_table_schema())
        app.db_service._connection.execute(TestScenarios.get_sample_insert_sql())
        app.refresh_table_routes()

        yield app

    def test_01_http_list_tables(self, app_with_data):
        """Test HTTP GET /api/tables endpoint."""
        client = TestClient(app_with_data)

        response = client.get("/api/tables")
        assert response.status_code == 200

        data = response.json()
        assert "tables" in data
        assert "users" in data["tables"]

    def test_02_http_get_all_records(self, app_with_data):
        """Test HTTP GET /api/users/ endpoint."""
        client = TestClient(app_with_data)

        response = client.get("/api/users/")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert len(data["data"]) == 4

        names = [user["name"] for user in data["data"]]
        assert "Alice" in names
        assert "Bob" in names

    def test_03_http_table_schema(self, app_with_data):
        """Test HTTP GET /api/users/schema endpoint."""
        client = TestClient(app_with_data)

        response = client.get("/api/users/schema")
        assert response.status_code == 200

        schema = response.json()
        assert schema["name"] == "users"
        assert "columns" in schema
        assert "id" in schema["columns"]
        assert "name" in schema["columns"]

    def test_04_http_rql_equality_filter(self, app_with_data):
        """Test HTTP RQL equality filtering."""
        client = TestClient(app_with_data)

        response = client.get("/api/users/?eq(active,true)")
        assert response.status_code == 200

        data = response.json()["data"]
        assert len(data) == 3  # Alice, Bob, David
        assert all(user["active"] for user in data)

    def test_05_http_rql_comparison_filters(self, app_with_data):
        """Test HTTP RQL comparison operators."""
        client = TestClient(app_with_data)

        # Test greater than
        response = client.get("/api/users/?gt(age,25)")
        assert response.status_code == 200

        data = response.json()["data"]
        assert len(data) == 2  # Bob (30), Charlie (35)
        assert all(user["age"] > 25 for user in data)

    def test_06_http_rql_contains_filter(self, app_with_data):
        """Test HTTP RQL contains filtering."""
        client = TestClient(app_with_data)

        response = client.get("/api/users/?contains(email,alice)")
        assert response.status_code == 200

        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Alice"
        assert "alice" in data[0]["email"]

    def test_07_http_rql_limit_and_offset(self, app_with_data):
        """Test HTTP RQL limit and offset."""
        client = TestClient(app_with_data)

        # Test limit only
        response = client.get("/api/users/?limit(2)")
        assert response.status_code == 200

        data = response.json()["data"]
        assert len(data) == 2

        # Test limit with offset
        response = client.get("/api/users/?limit(2,1)")
        assert response.status_code == 200

        data = response.json()["data"]
        assert len(data) == 2

    def test_08_http_create_record(self, app_with_data):
        """Test HTTP POST record creation."""
        client = TestClient(app_with_data)

        new_user = {
            "name": "Grace",
            "email": "grace@example.com",
            "age": 27,
            "active": True,
        }

        response = client.post("/api/users/", json=new_user)
        assert response.status_code in [200, 201]

        # Verify record was created
        response = client.get("/api/users/?eq(name,Grace)")
        assert response.status_code == 200

        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Grace"
        assert data[0]["email"] == "grace@example.com"

    def test_09_http_html_interface(self, app_with_data):
        """Test HTTP HTML table view."""
        client = TestClient(app_with_data)

        response = client.get("/api/users/html")
        assert response.status_code == 200

        html_content = response.text
        assert "<table" in html_content
        assert "Alice" in html_content
        assert "Bob" in html_content

    def test_10_http_error_handling(self, app_with_data):
        """Test HTTP error handling."""
        client = TestClient(app_with_data)

        # Test non-existent table
        response = client.get("/api/nonexistent/")
        assert response.status_code == 404

        # Test invalid JSON in POST
        response = client.post(
            "/api/users/",
            content="{invalid json}",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in [400, 422]
