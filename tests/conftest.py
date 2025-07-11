"""Test configuration and fixtures for FastVimes."""

import os
import tempfile
from collections.abc import Generator
from typing import Any

import ibis
import pytest

from fastvimes.app import FastVimes
from fastvimes.config import FastVimesSettings
from fastvimes.rql import RQLFilter


@pytest.fixture(scope="function")
def temp_db_path() -> Generator[str]:
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass


@pytest.fixture(scope="function")
def sample_data_connection(
    temp_db_path: str,
) -> Generator[ibis.BaseBackend]:
    """Create a DuckDB connection with sample data."""
    if os.path.exists(temp_db_path):
        os.unlink(temp_db_path)

    conn = ibis.duckdb.connect(database=temp_db_path)

    # Create sample tables
    conn.raw_sql("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            email VARCHAR UNIQUE,
            age INTEGER,
            active BOOLEAN DEFAULT TRUE
        )
    """)

    conn.raw_sql("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            title VARCHAR NOT NULL,
            content TEXT,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Insert sample data
    conn.raw_sql("""
        INSERT INTO users (id, name, email, age, active) VALUES
        (1, 'Alice', 'alice@example.com', 30, TRUE),
        (2, 'Bob', 'bob@example.com', 25, FALSE),
        (3, 'Charlie', 'charlie@example.com', 35, TRUE)
    """)

    conn.raw_sql("""
        INSERT INTO posts (id, title, content, user_id) VALUES
        (1, 'First Post', 'This is the first post', 1),
        (2, 'Second Post', 'This is the second post', 2),
        (3, 'Third Post', 'This is the third post', 1)
    """)

    yield conn


@pytest.fixture(scope="function")
def app_with_sample_data(
    temp_db_path: str, sample_data_connection: ibis.BaseBackend
) -> FastVimes:
    """Create FastVimes app with sample data."""
    config = FastVimesSettings(
        db_path=temp_db_path,
        default_mode="readwrite",
        default_html=True,
        admin_enabled=True,
    )
    return FastVimes(config=config)


@pytest.fixture(scope="function")
def env_vars() -> Generator[dict[str, Any]]:
    """Fixture to manage environment variables during tests."""
    original_env = os.environ.copy()

    def set_env(**kwargs):
        for key, value in kwargs.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = str(value)

    yield set_env

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean environment variables before each test."""
    original_env = {}
    fastvimes_vars = [key for key in os.environ.keys() if key.startswith("FASTVIMES_")]

    for key in fastvimes_vars:
        original_env[key] = os.environ[key]
        del os.environ[key]

    yield

    # Restore original values
    for key in [k for k in os.environ.keys() if k.startswith("FASTVIMES_")]:
        del os.environ[key]

    for key, value in original_env.items():
        os.environ[key] = value


# RQL Testing Fixtures
@pytest.fixture
def rql_filter():
    """Create an RQLFilter instance for testing."""
    return RQLFilter()


@pytest.fixture
def sample_table():
    """Create a sample Ibis table for testing."""
    data = [
        {"id": 1, "name": "alice", "age": 30, "active": True, "city": "New York"},
        {"id": 2, "name": "bob", "age": 25, "active": False, "city": "San Francisco"},
        {"id": 3, "name": "charlie", "age": 35, "active": True, "city": "Chicago"},
        {"id": 4, "name": "diana", "age": 28, "active": True, "city": "New York"},
    ]
    return ibis.memtable(data)


@pytest.fixture
def sample_data():
    """Sample data for direct RQL queries."""
    return [
        {"id": 1, "name": "alice", "age": 30, "active": True, "city": "New York"},
        {"id": 2, "name": "bob", "age": 25, "active": False, "city": "San Francisco"},
        {"id": 3, "name": "charlie", "age": 35, "active": True, "city": "Chicago"},
        {"id": 4, "name": "diana", "age": 28, "active": True, "city": "New York"},
    ]


class MockColumn:
    """Mock column for testing filter application."""
    
    def __init__(self, name: str):
        self.name = name
        self.applied_filters = []
    
    def __eq__(self, other):
        filter_expr = f"{self.name} == {other}"
        self.applied_filters.append(filter_expr)
        return filter_expr
    
    def __ne__(self, other):
        filter_expr = f"{self.name} != {other}"
        self.applied_filters.append(filter_expr)
        return filter_expr
    
    def __gt__(self, other):
        filter_expr = f"{self.name} > {other}"
        self.applied_filters.append(filter_expr)
        return filter_expr
    
    def __ge__(self, other):
        filter_expr = f"{self.name} >= {other}"
        self.applied_filters.append(filter_expr)
        return filter_expr
    
    def __lt__(self, other):
        filter_expr = f"{self.name} < {other}"
        self.applied_filters.append(filter_expr)
        return filter_expr
    
    def __le__(self, other):
        filter_expr = f"{self.name} <= {other}"
        self.applied_filters.append(filter_expr)
        return filter_expr
    
    def contains(self, other):
        filter_expr = f"{self.name} contains {other}"
        self.applied_filters.append(filter_expr)
        return filter_expr
    
    def isin(self, other):
        filter_expr = f"{self.name} in {other}"
        self.applied_filters.append(filter_expr)
        return filter_expr


class MockTable:
    """Mock table for testing filter application."""
    
    def __init__(self, columns=None):
        self.columns = columns or ["id", "name", "age", "active", "city", "score", "price"]
        self.applied_filters = []
        
        # Create mock columns
        for col in self.columns:
            setattr(self, col, MockColumn(col))
    
    def filter(self, condition):
        self.applied_filters.append(condition)
        return self


@pytest.fixture
def mock_table():
    """Create a mock table for testing."""
    return MockTable()


def assert_filters(result: dict, **expected_filters):
    """Helper to assert RQL filter results."""
    assert "filters" in result
    for key, value in expected_filters.items():
        assert key in result["filters"], f"Expected filter {key} not found in {result['filters']}"
        assert result["filters"][key] == value, f"Expected {key}={value}, got {result['filters'][key]}"


def assert_sort(result: dict, expected_sort: list):
    """Helper to assert RQL sort results."""
    assert "sort" in result
    assert result["sort"] == expected_sort
