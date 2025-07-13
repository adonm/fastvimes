"""Test RQL to SQL conversion using SQLGlot."""

import pytest
from fastvimes.rql_to_sql import RQLToSQLConverter, convert_rql_to_sql


def test_simple_equality():
    """Test basic equality conversion."""
    sql, params = convert_rql_to_sql("users", "eq(active,true)")
    
    assert "SELECT" in sql
    assert "FROM users" in sql
    assert "WHERE" in sql
    assert "active" in sql
    assert len(params) == 1
    assert True in params


def test_comparison_operators():
    """Test various comparison operators."""
    # Test less than
    sql, params = convert_rql_to_sql("users", "lt(age,30)")
    assert "age <" in sql or "age LT" in sql
    assert 30 in params
    
    # Test greater than
    sql, params = convert_rql_to_sql("users", "gt(age,18)")
    assert "age >" in sql or "age GT" in sql
    assert 18 in params
    
    # Test not equal
    sql, params = convert_rql_to_sql("users", "ne(status,deleted)")
    assert "status <>" in sql or "status !=" in sql or "status NE" in sql
    assert "deleted" in params


def test_and_conditions():
    """Test AND logic with multiple conditions."""
    sql, params = convert_rql_to_sql("users", "and(eq(active,true),gt(age,18))")
    
    assert "active" in sql
    assert "age" in sql
    assert "AND" in sql
    assert len(params) == 2
    assert True in params
    assert 18 in params


def test_field_selection():
    """Test field selection."""
    sql, params = convert_rql_to_sql("users", "select(id,name,email)")
    
    assert "SELECT id, name, email" in sql or "SELECT\n  id,\n  name,\n  email" in sql
    assert "FROM users" in sql


def test_sorting():
    """Test sorting operations."""
    # Test ascending sort
    sql, params = convert_rql_to_sql("users", "sort(name)")
    assert "ORDER BY" in sql and "name" in sql
    
    # Test descending sort
    sql, params = convert_rql_to_sql("users", "sort(-created_at)")
    assert "ORDER BY" in sql and "created_at" in sql
    assert "DESC" in sql


def test_limit_and_offset():
    """Test LIMIT and OFFSET."""
    sql, params = convert_rql_to_sql("users", "limit(10,5)")
    
    assert "LIMIT 10" in sql
    assert "OFFSET 5" in sql


def test_contains_operator():
    """Test LIKE/contains functionality."""
    sql, params = convert_rql_to_sql("users", "contains(name,john)")
    
    assert "name LIKE" in sql or "LIKE" in sql
    assert any("%john%" in str(val) for val in params)


def test_in_operator():
    """Test IN operator with arrays."""
    sql, params = convert_rql_to_sql("users", "in(department,(Engineering,Marketing))")
    
    assert "department IN" in sql
    assert "Engineering" in params
    assert "Marketing" in params


def test_invalid_rql():
    """Test error handling for invalid RQL."""
    with pytest.raises(ValueError):
        convert_rql_to_sql("users", "invalid_syntax(")


def test_complex_query():
    """Test complex multi-operator query."""
    rql = "and(eq(active,true),gt(age,18),contains(name,alice))"
    sql, params = convert_rql_to_sql("users", rql)
    
    assert "active" in sql
    assert "age" in sql  
    assert "name" in sql
    assert "AND" in sql
    assert len(params) == 3


def test_converter_class():
    """Test RQLToSQLConverter class directly."""
    converter = RQLToSQLConverter(dialect="duckdb")
    sql, params = converter.convert_to_sql("products", "eq(price,29.99)")
    
    assert "products" in sql
    assert "price" in sql
    assert 29.99 in params


def test_sql_injection_safety():
    """Test that SQLGlot prevents SQL injection."""
    # Try to inject SQL via RQL - pyrql should reject it
    with pytest.raises(ValueError, match="Invalid RQL query"):
        convert_rql_to_sql("users", "eq(name,'Robert'); DROP TABLE users; --')")
    
    # Test valid RQL with potentially dangerous content
    sql, params = convert_rql_to_sql("users", "eq(name,Robert)")
    
    # Should not contain DROP statement in the SQL
    assert "DROP" not in sql.upper()
    # Value should be parameterized
    assert "Robert" in params
