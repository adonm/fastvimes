"""Test database connection and operations."""

import ibis

from fastvimes.app import FastVimes


class TestDatabaseOperations:
    """Test database connection and basic operations."""

    def test_connection_setup(self):
        """Test database connection initialization."""
        app = FastVimes(db_path=":memory:")
        assert app.connection is not None
        assert isinstance(app.connection, ibis.BaseBackend)

    def test_table_introspection(self, app_with_sample_data):
        """Test table schema introspection."""
        app = app_with_sample_data

        # Check discovered tables
        tables = app.list_tables()
        assert "users" in tables
        assert "posts" in tables

        # Check schema details
        users_table = app.get_table("users")
        schema = users_table.schema()

        expected_columns = {"id", "name", "email", "age", "active"}
        actual_columns = set(schema.names)
        assert expected_columns.issubset(actual_columns)

    def test_schema_types(self, app_with_sample_data):
        """Test schema type detection."""
        app = app_with_sample_data
        users_table = app.get_table("users")
        schema = users_table.schema()

        # Test column types
        assert schema["id"].is_integer()
        assert schema["name"].is_string()
        assert schema["email"].is_string()
        assert schema["age"].is_integer()
        assert schema["active"].is_boolean()

    def test_basic_query(self, app_with_sample_data):
        """Test basic database query."""
        app = app_with_sample_data

        # Execute a simple query
        result = app.connection.sql("SELECT COUNT(*) as count FROM users").execute()
        assert len(result) == 1
        assert result.iloc[0]["count"] == 3

    def test_foreign_key_relationships(self, app_with_sample_data):
        """Test foreign key relationship detection."""
        app = app_with_sample_data

        # Verify posts table has user_id foreign key
        posts_table = app.get_table("posts")
        schema = posts_table.schema()
        assert "user_id" in schema.names

    def test_extension_loading(self):
        """Test DuckDB extension loading."""
        # Should not raise error
        app = FastVimes(db_path=":memory:", extensions=["json"])
        assert app.connection is not None

    def test_invalid_extension(self):
        """Test handling of invalid extensions."""
        # Should initialize but log warning
        app = FastVimes(db_path=":memory:", extensions=["nonexistent_extension"])
        assert app.connection is not None

    def test_empty_database(self):
        """Test handling of empty database."""
        app = FastVimes(db_path=":memory:")

        # Should initialize with empty table list
        assert len(app.list_tables()) == 0

    def test_connection_reuse(self):
        """Test that connection is reused properly."""
        app = FastVimes(db_path=":memory:")
        conn1 = app.connection
        conn2 = app.connection

        # Should be the same connection object
        assert conn1 is conn2

    def test_connection_properties(self, app_with_sample_data):
        """Test connection property access."""
        app = app_with_sample_data

        # Test connection property
        conn = app.connection
        assert conn is not None

        # Test db alias
        db = app.db
        assert db is app.connection

    def test_query_execution_methods(self, app_with_sample_data):
        """Test different query execution methods."""
        app = app_with_sample_data

        # Test string query
        result = app.execute_query("SELECT * FROM users LIMIT 1")
        assert result is not None

        # Test Ibis table query
        users_table = app.get_table("users")
        result = app.execute_query(users_table.limit(1))
        assert result is not None
