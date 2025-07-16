"""Test RQL integration with pyrql."""

from pathlib import Path

import pytest

from fastvimes.database_service import DatabaseService

pytestmark = pytest.mark.fast


@pytest.fixture
def db_service():
    """Create a test database service with sample data."""
    service = DatabaseService(Path(":memory:"), create_sample_data=True)
    yield service
    service.close()


def test_rql_filtering_basic(db_service):
    """Test basic RQL filtering."""
    # Test equality filter
    result = db_service.get_table_data("users", rql_query="eq(active,true)")
    assert len(result["data"]) > 0
    assert all(user["active"] for user in result["data"])


def test_rql_filtering_complex(db_service):
    """Test complex RQL filtering."""
    # Test multiple conditions
    result = db_service.get_table_data(
        "users", rql_query="eq(active,true)&eq(department,Engineering)"
    )
    assert len(result["data"]) > 0
    assert all(
        user["active"] and user["department"] == "Engineering"
        for user in result["data"]
    )


def test_rql_sorting(db_service):
    """Test RQL sorting."""
    # Test sorting by age
    result = db_service.get_table_data("users", rql_query="sort(age)")
    ages = [user["age"] for user in result["data"]]
    assert ages == sorted(ages)


def test_rql_selection(db_service):
    """Test RQL field selection."""
    # Test selecting specific fields
    result = db_service.get_table_data("users", rql_query="select(name,email)")
    assert len(result["data"]) > 0
    for user in result["data"]:
        assert set(user.keys()) == {"name", "email"}


def test_rql_limit(db_service):
    """Test RQL limiting."""
    # Test limiting results
    result = db_service.get_table_data("users", rql_query="limit(2)")
    assert len(result["data"]) == 2


def test_rql_error_handling(db_service):
    """Test RQL error handling for invalid queries."""
    # Should not crash on invalid RQL
    result = db_service.get_table_data(
        "users", rql_query="invalid_operator(field,value)"
    )
    assert "data" in result
    # Should fall back to returning all data
    assert len(result["data"]) > 0


def test_no_rql_query(db_service):
    """Test that no RQL query returns all data."""
    result = db_service.get_table_data("users")
    assert len(result["data"]) > 0
    assert "columns" in result
    assert "total_count" in result


def test_rql_with_pagination(db_service):
    """Test RQL with pagination parameters."""
    # Test RQL filtering with pagination
    result = db_service.get_table_data(
        "users", rql_query="eq(active,true)", limit=2, offset=1
    )
    assert len(result["data"]) <= 2
