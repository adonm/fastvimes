"""Comprehensive tests for DatabaseService with RQL/SQL integration."""

from pathlib import Path

import pytest

from fastvimes.database_service import DatabaseService


@pytest.fixture
def db_service():
    """Create a test database service with sample data."""
    service = DatabaseService(Path(":memory:"), create_sample_data=True)
    yield service
    service.close()


@pytest.mark.fast
class TestDatabaseServiceBasics:
    """Test basic database service functionality."""

    def test_list_tables(self, db_service):
        """Test table listing."""
        tables = db_service.list_tables()
        table_names = [t["name"] for t in tables]

        assert "users" in table_names
        assert "products" in table_names
        assert "orders" in table_names
        assert len(tables) >= 3

    def test_get_table_schema(self, db_service):
        """Test schema introspection."""
        schema = db_service.get_table_schema("users")

        assert len(schema) > 0
        column_names = [col["name"] for col in schema]
        assert "id" in column_names
        assert "name" in column_names
        assert "email" in column_names
        assert "active" in column_names

    def test_get_table_data_no_filters(self, db_service):
        """Test getting all table data."""
        result = db_service.get_table_data("users")

        assert "columns" in result
        assert "data" in result
        assert "total_count" in result
        assert len(result["data"]) > 0
        assert result["total_count"] > 0


@pytest.mark.fast
class TestRQLFiltering:
    """Test RQL filtering with SQL generation."""

    def test_equality_filter(self, db_service):
        """Test basic equality filtering."""
        result = db_service.get_table_data("users", rql_query="eq(active,true)")

        assert len(result["data"]) > 0
        assert all(user["active"] for user in result["data"])

    def test_inequality_filter(self, db_service):
        """Test inequality filtering."""
        result = db_service.get_table_data("users", rql_query="eq(active,false)")

        assert len(result["data"]) >= 1
        assert all(not user["active"] for user in result["data"])

    def test_numeric_comparison(self, db_service):
        """Test numeric comparison operations."""
        # Test greater than
        result = db_service.get_table_data("users", rql_query="gt(age,30)")
        assert len(result["data"]) > 0
        assert all(user["age"] > 30 for user in result["data"])

        # Test less than
        result = db_service.get_table_data("users", rql_query="lt(age,30)")
        assert len(result["data"]) > 0
        assert all(user["age"] < 30 for user in result["data"])

    def test_string_filtering(self, db_service):
        """Test string-based filtering."""
        result = db_service.get_table_data(
            "users", rql_query="eq(department,Engineering)"
        )

        assert len(result["data"]) > 0
        assert all(user["department"] == "Engineering" for user in result["data"])

    def test_contains_filter(self, db_service):
        """Test contains/LIKE filtering."""
        result = db_service.get_table_data("users", rql_query="contains(name,Alice)")

        assert len(result["data"]) >= 1
        assert any("Alice" in user["name"] for user in result["data"])


@pytest.mark.fast
class TestRQLSorting:
    """Test RQL sorting operations."""

    def test_ascending_sort(self, db_service):
        """Test ascending sort."""
        result = db_service.get_table_data("users", rql_query="sort(age)")

        ages = [user["age"] for user in result["data"]]
        assert ages == sorted(ages)

    def test_descending_sort(self, db_service):
        """Test descending sort."""
        result = db_service.get_table_data("users", rql_query="sort(-age)")

        ages = [user["age"] for user in result["data"]]
        assert ages == sorted(ages, reverse=True)

    def test_name_sort(self, db_service):
        """Test string sorting."""
        result = db_service.get_table_data("users", rql_query="sort(name)")

        names = [user["name"] for user in result["data"]]
        assert names == sorted(names)


@pytest.mark.fast
class TestRQLSelection:
    """Test field selection."""

    def test_select_specific_fields(self, db_service):
        """Test selecting only specific fields."""
        result = db_service.get_table_data("users", rql_query="select(id,name)")

        assert len(result["data"]) > 0
        for user in result["data"]:
            assert set(user.keys()) == {"id", "name"}

    def test_select_three_fields(self, db_service):
        """Test selecting three fields."""
        result = db_service.get_table_data(
            "users", rql_query="select(name,email,department)"
        )

        assert len(result["data"]) > 0
        for user in result["data"]:
            assert set(user.keys()) == {"name", "email", "department"}


@pytest.mark.fast
class TestRQLComplexQueries:
    """Test complex RQL queries."""

    def test_and_condition(self, db_service):
        """Test AND logic."""
        result = db_service.get_table_data(
            "users", rql_query="and(eq(active,true),eq(department,Engineering))"
        )

        assert len(result["data"]) > 0
        for user in result["data"]:
            assert user["active"] is True
            assert user["department"] == "Engineering"

    def test_filter_and_sort(self, db_service):
        """Test combining filters and sorting."""
        result = db_service.get_table_data(
            "users", rql_query="and(eq(active,true),sort(age))"
        )

        active_users = [user for user in result["data"] if user["active"]]
        ages = [user["age"] for user in active_users]

        # Should have active users
        assert len(active_users) > 0
        # Should be sorted by age
        assert ages == sorted(ages)

    def test_select_filter_sort(self, db_service):
        """Test select + filter + sort combination."""
        result = db_service.get_table_data(
            "users", rql_query="and(eq(active,true),select(name,age),sort(age))"
        )

        assert len(result["data"]) > 0
        for user in result["data"]:
            # Should only have selected fields
            assert set(user.keys()) <= {"name", "age"}

        # Should be sorted by age
        ages = [user["age"] for user in result["data"]]
        assert ages == sorted(ages)


@pytest.mark.fast
class TestPagination:
    """Test pagination functionality."""

    def test_limit(self, db_service):
        """Test LIMIT functionality."""
        result = db_service.get_table_data("users", limit=3)

        assert len(result["data"]) == 3
        assert result["total_count"] > 3  # Should have more total records

    def test_offset(self, db_service):
        """Test OFFSET functionality."""
        # Get first 2 records
        first_batch = db_service.get_table_data("users", limit=2, offset=0)
        # Get next 2 records
        second_batch = db_service.get_table_data("users", limit=2, offset=2)

        # Should be different records
        first_ids = {user["id"] for user in first_batch["data"]}
        second_ids = {user["id"] for user in second_batch["data"]}
        assert first_ids.isdisjoint(second_ids)

    def test_rql_with_pagination(self, db_service):
        """Test RQL filtering with pagination."""
        result = db_service.get_table_data(
            "users", rql_query="eq(active,true)", limit=2
        )

        assert len(result["data"]) <= 2
        assert all(user["active"] for user in result["data"])


@pytest.mark.fast
class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_table_name(self, db_service):
        """Test behavior with invalid table name."""
        with pytest.raises((RuntimeError, ValueError)):
            db_service.get_table_data("nonexistent_table")

    def test_invalid_rql_fallback(self, db_service):
        """Test fallback behavior with invalid RQL."""
        # Should not crash, should fall back to in-memory filtering
        result = db_service.get_table_data("users", rql_query="invalid_rql_syntax(")

        # Should still return data (fallback behavior)
        assert "data" in result
        assert len(result["data"]) > 0

    def test_empty_rql_query(self, db_service):
        """Test with empty RQL query."""
        result = db_service.get_table_data("users", rql_query="")

        assert "data" in result
        assert len(result["data"]) > 0


@pytest.mark.fast
class TestCRUDOperations:
    """Test Create, Read, Update, Delete operations."""

    def test_create_record(self, db_service):
        """Test record creation."""
        new_user = {
            "name": "Test User",
            "email": "test@example.com",
            "age": 25,
            "active": True,
            "department": "Testing",
        }

        created = db_service.create_record("users", new_user)

        assert created["name"] == "Test User"
        assert created["email"] == "test@example.com"
        assert "id" in created

    def test_update_records(self, db_service):
        """Test record updating."""
        # Update all Engineering users
        updated_count = db_service.update_records(
            "users",
            {"department": "Software Engineering"},
            filters={"department": "Engineering"},
        )

        assert updated_count > 0

        # Verify the update
        result = db_service.get_table_data(
            "users", rql_query="eq(department,Software Engineering)"
        )
        assert len(result["data"]) > 0

    def test_delete_records(self, db_service):
        """Test record deletion."""
        # First, create a test record
        test_user = {
            "name": "Delete Me",
            "email": "delete@example.com",
            "age": 99,
            "active": False,
            "department": "Temporary",
        }
        created = db_service.create_record("users", test_user)

        # Then delete it
        deleted_count = db_service.delete_records(
            "users", filters={"id": created["id"]}
        )

        assert deleted_count == 1

        # Verify it's gone
        try:
            db_service.get_record_by_id("users", created["id"])
            raise AssertionError("Record should have been deleted")
        except ValueError:
            pass  # Expected - record not found

    def test_get_chart_data(self, db_service):
        """Test chart data generation for visualization."""
        # Test with users table (has categorical and numeric data)
        chart_data = db_service.get_chart_data("users")
        
        # Check structure
        assert "table_name" in chart_data
        assert "charts" in chart_data
        assert "numeric_columns" in chart_data
        assert "categorical_columns" in chart_data
        assert "date_columns" in chart_data
        
        assert chart_data["table_name"] == "users"
        
        # Should have some charts for the users table
        charts = chart_data["charts"]
        assert isinstance(charts, list)
        
        # Should identify column types correctly
        assert "age" in chart_data["numeric_columns"]
        assert "department" in chart_data["categorical_columns"]
        assert "created_at" in chart_data["date_columns"]
        
        # Check chart structure if any charts were generated
        for chart in charts:
            assert "type" in chart
            assert "title" in chart
            assert "data" in chart
            assert "x_key" in chart
            assert "y_key" in chart
            assert chart["type"] in ["bar", "line"]
