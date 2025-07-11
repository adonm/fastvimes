"""Test RQL operator functionality systematically."""

import pytest
from tests.conftest import assert_filters


class TestRQLOperators:
    """Test all RQL operators systematically."""

    # Define operator test cases
    COMPARISON_OPERATORS = [
        ("eq", 123, "id__eq", 123),
        ("ne", 123, "id__ne", 123),
        ("gt", 18, "age__gt", 18),
        ("ge", 18, "age__ge", 18),
        ("lt", 65, "age__lt", 65),
        ("le", 65, "age__le", 65),
    ]

    SET_OPERATORS = [
        ("in", "(1,2,3)", "id__in", [1, 2, 3]),
        ("out", "(banned,deleted)", "status__out", ["banned", "deleted"]),
        ("contains", "alice", "name__contains", "alice"),
        ("excludes", "test", "name__excludes", "test"),
    ]

    @pytest.mark.parametrize("operator,value,expected_key,expected_value", COMPARISON_OPERATORS)
    def test_comparison_operators(self, rql_filter, operator, value, expected_key, expected_value):
        """Test all comparison operators."""
        field = "id" if "id" in expected_key else "age"
        query = f"{operator}({field},{value})"
        result = rql_filter.parse_query_string(query)
        assert_filters(result, **{expected_key: expected_value})

    @pytest.mark.parametrize("operator,value,expected_key,expected_value", SET_OPERATORS)
    def test_set_operators(self, rql_filter, operator, value, expected_key, expected_value):
        """Test all set operators."""
        field = expected_key.split("__")[0]
        query = f"{operator}({field},{value})"
        result = rql_filter.parse_query_string(query)
        assert_filters(result, **{expected_key: expected_value})

    @pytest.mark.parametrize("operator,field,value", [
        ("eq", "name", "alice"),
        ("ne", "status", "inactive"),
        ("gt", "score", 85),
        ("ge", "rating", 4.5),
        ("lt", "price", 99.99),
        ("le", "discount", 0.2),
        ("contains", "description", "test"),
        ("excludes", "tags", "hidden"),
    ])
    def test_operators_with_different_fields(self, rql_filter, operator, field, value):
        """Test operators work with different field names."""
        query = f"{operator}({field},{value})"
        result = rql_filter.parse_query_string(query)
        expected_key = f"{field}__{operator}"
        assert expected_key in result["filters"]
        assert result["filters"][expected_key] == value

    def test_in_operator_with_various_types(self, rql_filter):
        """Test 'in' operator with different value types."""
        test_cases = [
            ("in(id,(1,2,3))", "id__in", [1, 2, 3]),
            ("in(status,(active,pending,inactive))", "status__in", ["active", "pending", "inactive"]),
            ("in(score,(85,90,95))", "score__in", [85, 90, 95]),
        ]
        
        for query, expected_key, expected_value in test_cases:
            result = rql_filter.parse_query_string(query)
            assert_filters(result, **{expected_key: expected_value})

    def test_out_operator_exclusions(self, rql_filter):
        """Test 'out' operator for exclusions."""
        test_cases = [
            ("out(status,(banned,deleted))", "status__out", ["banned", "deleted"]),
            ("out(id,(1,2,3))", "id__out", [1, 2, 3]),
            ("out(category,(hidden,private))", "category__out", ["hidden", "private"]),
        ]
        
        for query, expected_key, expected_value in test_cases:
            result = rql_filter.parse_query_string(query)
            assert_filters(result, **{expected_key: expected_value})

    def test_contains_and_excludes_operators(self, rql_filter):
        """Test string contains and excludes operators."""
        test_cases = [
            ("contains(name,alice)", "name__contains", "alice"),
            ("contains(description,test)", "description__contains", "test"),
            ("excludes(content,spam)", "content__excludes", "spam"),
            ("excludes(title,draft)", "title__excludes", "draft"),
        ]
        
        for query, expected_key, expected_value in test_cases:
            result = rql_filter.parse_query_string(query)
            assert_filters(result, **{expected_key: expected_value})

    def test_multiple_operators_combination(self, rql_filter):
        """Test combining multiple different operators."""
        query = "gt(age,18)&lt(age,65)&contains(name,alice)&in(status,(active,pending))&ne(id,123)"
        result = rql_filter.parse_query_string(query)
        
        expected_filters = {
            "age__gt": 18,
            "age__lt": 65,
            "name__contains": "alice",
            "status__in": ["active", "pending"],
            "id__ne": 123
        }
        
        assert_filters(result, **expected_filters)

    def test_operator_value_type_conversion(self, rql_filter):
        """Test value type conversion for operators."""
        test_cases = [
            ("eq(id,123)", "id__eq", 123),  # int
            ("gt(price,99.99)", "price__gt", 99.99),  # float
            ("eq(active,true)", "active__eq", True),  # bool true
            ("eq(active,false)", "active__eq", False),  # bool false
            ("eq(value,null)", "value__eq", None),  # null
            ("eq(name,alice)", "name__eq", "alice"),  # string
        ]
        
        for query, expected_key, expected_value in test_cases:
            result = rql_filter.parse_query_string(query)
            assert_filters(result, **{expected_key: expected_value})

    def test_operators_with_special_characters(self, rql_filter):
        """Test operators with special characters in values."""
        test_cases = [
            ("contains(email,test)", "email__contains", "test"),
            ("eq(path,api)", "path__eq", "api"),
            ("contains(description,hello)", "description__contains", "hello"),
        ]
        
        for query, expected_key, expected_value in test_cases:
            result = rql_filter.parse_query_string(query)
            assert_filters(result, **{expected_key: expected_value})


class TestRQLOperatorApplication:
    """Test applying RQL operators to mock tables."""

    def test_eq_operator_application(self, rql_filter, mock_table):
        """Test applying eq operator to table."""
        filters = {"id__eq": 123}
        result = rql_filter.apply_filters(mock_table, filters)
        
        assert "id == 123" in result.applied_filters

    def test_comparison_operators_application(self, rql_filter, mock_table):
        """Test applying comparison operators to table."""
        filters = {
            "age__gt": 18,
            "age__lt": 65,
            "score__ge": 85,
            "price__le": 99.99,
            "id__ne": 123
        }
        
        result = rql_filter.apply_filters(mock_table, filters)
        
        expected_filters = [
            "age > 18",
            "age < 65", 
            "score >= 85",
            "price <= 99.99",
            "id != 123"
        ]
        
        for expected in expected_filters:
            assert expected in result.applied_filters

    def test_set_operators_application(self, rql_filter, mock_table):
        """Test applying set operators to table."""
        filters = {
            "id__in": [1, 2, 3],
            "status__out": ["banned", "deleted"],
            "name__contains": "alice",
        }
        
        result = rql_filter.apply_filters(mock_table, filters)
        
        expected_filters = [
            "id in [1, 2, 3]",
            "name contains alice"
        ]
        
        for expected in expected_filters:
            assert expected in result.applied_filters

    def test_invalid_operator_skipped(self, rql_filter, mock_table):
        """Test that invalid operators are skipped gracefully."""
        filters = {
            "id__eq": 123,
            "age__invalid": 18,  # Invalid operator
            "name__contains": "alice"
        }
        
        result = rql_filter.apply_filters(mock_table, filters)
        
        # Should only apply valid operators
        assert "id == 123" in result.applied_filters
        assert "name contains alice" in result.applied_filters
        assert len(result.applied_filters) == 2

    def test_invalid_field_skipped(self, rql_filter, mock_table):
        """Test that invalid fields are skipped gracefully."""
        filters = {
            "id__eq": 123,
            "nonexistent_field__eq": "value",  # Invalid field
            "name__contains": "alice"
        }
        
        result = rql_filter.apply_filters(mock_table, filters)
        
        # Should only apply valid fields
        assert "id == 123" in result.applied_filters
        assert "name contains alice" in result.applied_filters
        assert len(result.applied_filters) == 2
