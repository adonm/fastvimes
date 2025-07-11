"""Test schema introspection and model generation."""

import pytest
from fastapi import HTTPException
from pydantic import BaseModel


class TestSchemaIntrospection:
    """Test database schema introspection."""

    def test_table_discovery(self, app_with_sample_data):
        """Test automatic table discovery."""
        app = app_with_sample_data

        # Should discover both tables
        tables = app.list_tables()
        assert "users" in tables
        assert "posts" in tables

        # Tables should be Ibis table expressions
        users_table = app.get_table("users")
        posts_table = app.get_table("posts")

        assert users_table is not None
        assert posts_table is not None

    def test_schema_extraction(self, app_with_sample_data):
        """Test schema extraction from tables."""
        app = app_with_sample_data

        users_schema = app.get_table("users").schema()

        # Check expected columns exist
        expected_columns = {"id", "name", "email", "age", "active"}
        actual_columns = set(users_schema.names)
        assert expected_columns.issubset(actual_columns)

    def test_column_types(self, app_with_sample_data):
        """Test column type detection."""
        app = app_with_sample_data
        schema = app.get_table("users").schema()

        # Test specific column types
        assert schema["id"].is_integer()
        assert schema["name"].is_string()
        assert schema["email"].is_string()
        assert schema["age"].is_integer()
        assert schema["active"].is_boolean()

    def test_nullable_columns(self, app_with_sample_data):
        """Test nullable column detection."""
        app = app_with_sample_data
        schema = app.get_table("users").schema()

        # id and name should be non-nullable
        assert not schema["id"].nullable
        assert not schema["name"].nullable

    def test_pydantic_model_generation(self, app_with_sample_data):
        """Test Pydantic model generation from schema."""
        app = app_with_sample_data

        # Generate Pydantic model
        UserModel = app.get_table_dataclass("users")

        # Should be a Pydantic model
        assert issubclass(UserModel, BaseModel)

        # Test model validation
        user = UserModel(
            id="1", name="Test User", email="test@example.com", age=30, active=True
        )

        assert user.id == "1"
        assert user.name == "Test User"

    def test_model_generation_consistency(self, app_with_sample_data):
        """Test that generated models are consistent."""
        app = app_with_sample_data

        # Generate models multiple times
        model1 = app.get_table_dataclass("users")
        model2 = app.get_table_dataclass("users")

        # Should have same name and fields
        assert model1.__name__ == model2.__name__
        assert model1.model_fields.keys() == model2.model_fields.keys()

    def test_nonexistent_table(self, app_with_sample_data):
        """Test handling of nonexistent table."""
        app = app_with_sample_data

        # Should raise error for nonexistent table
        with pytest.raises((HTTPException, ValueError)):
            app.get_table_dataclass("nonexistent")

    def test_complex_schema(self, app_with_sample_data):
        """Test complex schema with foreign keys."""
        app = app_with_sample_data

        # Posts table has foreign key to users
        posts_schema = app.get_table("posts").schema()

        # Check foreign key column
        assert "user_id" in posts_schema.names
        assert posts_schema["user_id"].is_integer()

        # Generate model
        PostModel = app.get_table_dataclass("posts")
        assert PostModel is not None
        assert issubclass(PostModel, BaseModel)

    def test_type_conversion(self, app_with_sample_data):
        """Test Ibis to Python type conversion."""
        app = app_with_sample_data

        # Test type conversion methods
        assert app.db_service._ibis_to_python_type("int64") is int
        assert app.db_service._ibis_to_python_type("string") is str
        assert app.db_service._ibis_to_python_type("boolean") is bool
        assert app.db_service._ibis_to_python_type("float64") is float

    def test_optional_field_handling(self, app_with_sample_data):
        """Test handling of optional/nullable fields."""
        app = app_with_sample_data

        # Create model and check optional fields
        UserModel = app.get_table_dataclass("users")

        # Should be able to create with all required fields
        user = UserModel(
            id="1", name="Test User", email="test@example.com", age=30, active=True
        )

        assert user.id == "1"
        assert user.name == "Test User"
        assert user.email == "test@example.com"

    def test_field_definitions(self, app_with_sample_data):
        """Test that field definitions are correct."""
        app = app_with_sample_data

        UserModel = app.get_table_dataclass("users")

        # Check that model has expected fields
        # This depends on the actual implementation
        assert hasattr(UserModel, "model_fields")

        fields = UserModel.model_fields
        assert "id" in fields
        assert "name" in fields
        assert "email" in fields
        assert "age" in fields
        assert "active" in fields
