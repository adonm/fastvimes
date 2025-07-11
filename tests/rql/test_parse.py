"""Test RQL string parsing functionality."""

import pytest
from tests.conftest import assert_filters, assert_sort


class TestRQLParsing:
    """Test RQL query string parsing."""

    @pytest.mark.parametrize("query,expected", [
        # Function syntax
        ("eq(id,123)", {"id__eq": 123}),
        ("gt(age,18)", {"age__gt": 18}),
        ("lt(price,99.99)", {"price__lt": 99.99}),
        ("contains(name,alice)", {"name__contains": "alice"}),
        ("in(status,(active,pending))", {"status__in": ["active", "pending"]}),
        
        # FIQL syntax
        ("id=eq=123", {"id__eq": 123}),
        ("age=gt=18", {"age__gt": 18}),
        ("name=contains=alice", {"name__contains": "alice"}),
        
        # Direct equality
        ("id=123", {"id__eq": 123}),
        ("name=alice", {"name__eq": "alice"}),
        ("active=true", {"active__eq": True}),
        ("active=false", {"active__eq": False}),
        ("value=null", {"value__eq": None}),
    ])
    def test_single_filter_parsing(self, rql_filter, query, expected):
        """Test parsing single filters in different syntaxes."""
        result = rql_filter.parse_query_string(query)
        assert_filters(result, **expected)

    @pytest.mark.parametrize("query,expected", [
        # Multiple filters
        ("eq(id,123)&gt(age,18)", {"id__eq": 123, "age__gt": 18}),
        ("name=alice&age=gt=30", {"name__eq": "alice", "age__gt": 30}),
        ("active=true&city=eq=NYC", {"active__eq": True, "city__eq": "NYC"}),
        
        # Complex combinations
        ("eq(id,1)&contains(name,alice)&gt(age,18)", {
            "id__eq": 1,
            "name__contains": "alice", 
            "age__gt": 18
        }),
    ])
    def test_multiple_filter_parsing(self, rql_filter, query, expected):
        """Test parsing multiple filters."""
        result = rql_filter.parse_query_string(query)
        assert_filters(result, **expected)

    @pytest.mark.parametrize("query,expected", [
        # Basic sorting
        ("sort(+name)", [("name", True)]),
        ("sort(-age)", [("age", False)]),
        ("sort(+name,-age)", [("name", True), ("age", False)]),
        
        # Multiple sort fields
        ("sort(+name,-age,+created)", [
            ("name", True),
            ("age", False),
            ("created", True)
        ]),
    ])
    def test_sort_parsing(self, rql_filter, query, expected):
        """Test parsing sort parameters."""
        result = rql_filter.parse_query_string(query)
        assert_sort(result, expected)

    @pytest.mark.parametrize("query,expected_limit,expected_offset", [
        ("limit(10)", 10, None),
        ("limit(20,5)", 20, 5),
        ("limit(100,50)", 100, 50),
    ])
    def test_limit_parsing(self, rql_filter, query, expected_limit, expected_offset):
        """Test parsing limit parameters."""
        result = rql_filter.parse_query_string(query)
        assert result["limit"] == expected_limit
        assert result["offset"] == expected_offset

    @pytest.mark.parametrize("query,expected", [
        ("select(id)", ["id"]),
        ("select(id,name)", ["id", "name"]),
        ("select(id,name,email,age)", ["id", "name", "email", "age"]),
    ])
    def test_select_parsing(self, rql_filter, query, expected):
        """Test parsing select parameters."""
        result = rql_filter.parse_query_string(query)
        assert result["select"] == expected

    @pytest.mark.parametrize("query,expected_count,expected_distinct", [
        ("count()", True, False),
        ("distinct()", False, True),
        ("count()&distinct()", True, True),
    ])
    def test_aggregation_parsing(self, rql_filter, query, expected_count, expected_distinct):
        """Test parsing aggregation parameters."""
        result = rql_filter.parse_query_string(query)
        assert result["count"] == expected_count
        assert result["distinct"] == expected_distinct

    def test_complex_combined_query(self, rql_filter):
        """Test parsing complex queries with multiple features."""
        query = "gt(age,18)&lt(age,65)&contains(name,alice)&sort(-created)&limit(10,5)&select(id,name,age)"
        result = rql_filter.parse_query_string(query)
        
        # Check filters
        assert_filters(result, age__gt=18, age__lt=65, name__contains="alice")
        
        # Check sort
        assert_sort(result, [("created", False)])
        
        # Check limit/offset
        assert result["limit"] == 10
        assert result["offset"] == 5
        
        # Check select
        assert result["select"] == ["id", "name", "age"]

    def test_empty_query(self, rql_filter):
        """Test parsing empty query string."""
        result = rql_filter.parse_query_string("")
        
        assert result["filters"] == {}
        assert result["sort"] == []
        assert result["limit"] is None
        assert result["offset"] is None
        assert result["select"] == []
        assert result["count"] is False
        assert result["distinct"] is False


class TestRQLParameterParsing:
    """Test parsing RQL from query parameters."""

    @pytest.mark.parametrize("params,expected", [
        # Function syntax in keys
        ({"eq(id,123)": ""}, {"id__eq": 123}),
        ({"gt(age,18)": "", "eq(name,alice)": ""}, {"age__gt": 18, "name__eq": "alice"}),
        
        # FIQL syntax in values
        ({"id": "eq=123"}, {"id__eq": 123}),
        ({"age": "gt=18", "name": "contains=alice"}, {"age__gt": 18, "name__contains": "alice"}),
        
        # Direct values
        ({"id": "123"}, {"id__eq": 123}),
        ({"name": "alice", "active": "true"}, {"name__eq": "alice", "active__eq": True}),
        
        # Mixed syntax
        ({"eq(id,123)": "", "age": "gt=18", "name": "alice"}, {
            "id__eq": 123,
            "age__gt": 18,
            "name__eq": "alice"
        }),
    ])
    def test_parse_rql_params(self, params, expected):
        """Test parsing RQL from query parameters."""
        from fastvimes.rql import parse_rql_params
        result = parse_rql_params(params)
        assert_filters(result, **expected)

    def test_parse_empty_params(self):
        """Test parsing empty parameters."""
        from fastvimes.rql import parse_rql_params
        result = parse_rql_params({})
        
        assert result["filters"] == {}
        assert result["sort"] == []
        assert result["limit"] is None
        assert result["offset"] is None
        assert result["select"] == []
        assert result["count"] is False
        assert result["distinct"] is False

    def test_parse_special_operations(self):
        """Test parsing special operations from parameters."""
        from fastvimes.rql import parse_rql_params
        
        params = {
            "eq(id,123)": "",
            "sort(+name,-age)": "",
            "limit(10,5)": "",
            "select(id,name)": "",
            "count()": ""
        }
        
        result = parse_rql_params(params)
        
        assert_filters(result, id__eq=123)
        assert_sort(result, [("name", True), ("age", False)])
        assert result["limit"] == 10
        assert result["offset"] == 5
        assert result["select"] == ["id", "name"]
        assert result["count"] is True
