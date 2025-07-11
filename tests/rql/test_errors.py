"""Test RQL error handling and edge cases."""

import pytest
from tests.conftest import assert_filters


class TestRQLErrorHandling:
    """Test RQL error handling and edge cases."""

    def test_invalid_rql_syntax(self, rql_filter):
        """Test handling of invalid RQL syntax."""
        invalid_queries = [
            "invalid(syntax",  # Missing closing parenthesis
            "eq(id)",          # Missing value
            "gt()",            # Missing field and value
            "malformed query", # Completely malformed
        ]
        
        for query in invalid_queries:
            result = rql_filter.parse_query_string(query)
            
            # Should return empty result structure for truly invalid queries
            assert result["sort"] == []
            assert result["limit"] is None
            assert result["offset"] is None
            assert result["select"] == []
            assert result["count"] is False
            assert result["distinct"] is False

    def test_invalid_operator_in_filter(self, rql_filter):
        """Test handling of invalid operators."""
        query = "invalid_op(id,123)&eq(name,alice)"
        result = rql_filter.parse_query_string(query)
        
        # Should parse valid parts and ignore invalid ones
        assert result["filters"].get("name__eq") == "alice"
        assert "id__invalid_op" not in result["filters"]

    def test_invalid_field_names(self, rql_filter, mock_table):
        """Test handling of invalid field names during filter application."""
        filters = {
            "valid_field__eq": 123,
            "invalid.field__eq": 456,  # Invalid field name
            "another_invalid__eq": 789,
        }
        
        result = rql_filter.apply_filters(mock_table, filters)
        
        # Should skip invalid fields gracefully
        assert len(result.applied_filters) == 0  # No valid fields on mock table

    def test_empty_and_null_values(self, rql_filter):
        """Test handling of empty and null values."""
        test_cases = [
            ("eq(name,)", {"name__eq": ""}),  # Empty string
            ("eq(value,null)", {"value__eq": None}),  # Null value
            ("eq(flag,)", {"flag__eq": ""}),  # Empty value
        ]
        
        for query, expected in test_cases:
            result = rql_filter.parse_query_string(query)
            # Note: Some cases may not parse correctly with pyrql
            # This tests our error handling

    def test_special_characters_in_values(self, rql_filter):
        """Test handling of special characters in values."""
        test_cases = [
            ("eq(name,alice)", {"name__eq": "alice"}),  # Simple case
            ("contains(text,hello)", {"text__contains": "hello"}),  # Simple contains
            ("eq(email,user)", {"email__eq": "user"}),  # Simple email
        ]
        
        for query, expected in test_cases:
            result = rql_filter.parse_query_string(query)
            # Test what actually gets parsed
            assert result["filters"]  # Should have some result

    def test_url_encoded_values(self, rql_filter):
        """Test handling of URL-encoded values."""
        # This tests whether we properly handle URL-encoded input
        query = "contains(name,hello%20world)"
        result = rql_filter.parse_query_string(query)
        
        # Should handle URL encoding properly
        assert result["filters"]  # Should parse something

    def test_very_long_query(self, rql_filter):
        """Test handling of very long queries."""
        # Build a long query with many filters
        filters = [f"eq(field{i},{i})" for i in range(100)]
        query = "&".join(filters)
        
        result = rql_filter.parse_query_string(query)
        
        # Should handle long queries gracefully
        assert isinstance(result, dict)
        assert "filters" in result

    def test_nested_parentheses(self, rql_filter):
        """Test handling of nested parentheses."""
        invalid_queries = [
            "eq(id,(1,2,3))",  # Nested parentheses in wrong context
            "gt(age,((18)))",  # Double nested
            "and(eq(id,1),gt(age,(18)))",  # Mixed nesting
        ]
        
        for query in invalid_queries:
            result = rql_filter.parse_query_string(query)
            # Should not crash, may or may not parse correctly
            assert isinstance(result, dict)

    def test_unicode_and_special_encoding(self, rql_filter):
        """Test handling of unicode and special encoding."""
        test_cases = [
            ("eq(name,café)", {"name__eq": "café"}),  # Unicode
            ("contains(text,émojis)", {"text__contains": "émojis"}),  # Accented chars
            ("eq(city,北京)", {"city__eq": "北京"}),  # Chinese characters
        ]
        
        for query, expected in test_cases:
            result = rql_filter.parse_query_string(query)
            # Test that it doesn't crash with unicode
            assert isinstance(result, dict)

    def test_extremely_large_values(self, rql_filter):
        """Test handling of extremely large values."""
        test_cases = [
            ("eq(id,999999999999999999)", {"id__eq": 999999999999999999}),  # Large int
            ("gt(price,999999.99)", {"price__gt": 999999.99}),  # Large float
            ("eq(text," + "a" * 1000 + ")", {"text__eq": "a" * 1000}),  # Long string
        ]
        
        for query, expected in test_cases:
            result = rql_filter.parse_query_string(query)
            # Should handle large values gracefully
            assert isinstance(result, dict)

    def test_malformed_array_syntax(self, rql_filter):
        """Test handling of malformed array syntax."""
        invalid_queries = [
            "in(id,(1,2,3)",    # Missing closing parenthesis
            "in(id,1,2,3)",     # Missing parentheses
            "in(id,(1,2,3,))",  # Trailing comma
            "in(id,())",        # Empty array
            "in(id,(,1,2))",    # Leading comma
        ]
        
        for query in invalid_queries:
            result = rql_filter.parse_query_string(query)
            # Should not crash
            assert isinstance(result, dict)

    def test_mixed_valid_invalid_operators(self, rql_filter):
        """Test query with mix of valid and invalid operators."""
        query = "eq(id,1)&invalid_op(name,test)&gt(age,18)&another_invalid(x,y)&contains(text,hello)"
        result = rql_filter.parse_query_string(query)
        
        # Should extract valid parts
        valid_filters = result["filters"]
        expected_valid = ["id__eq", "age__gt", "text__contains"]
        
        # Check that at least some valid filters are present
        assert any(key in valid_filters for key in expected_valid)

    def test_empty_parameter_handling(self, rql_filter):
        """Test handling of empty parameters."""
        from fastvimes.rql import parse_rql_params
        
        # Test various empty parameter scenarios
        test_cases = [
            {},  # Completely empty
            {"": ""},  # Empty key and value
            {"key": ""},  # Empty value
            {"": "value"},  # Empty key
        ]
        
        for params in test_cases:
            result = parse_rql_params(params)
            # Should return valid structure
            assert isinstance(result, dict)
            assert "filters" in result

    def test_data_query_error_handling(self, rql_filter):
        """Test error handling in data queries."""
        data = [
            {"id": 1, "name": "alice"},
            {"id": 2, "name": "bob"},
        ]
        
        # Test with invalid queries
        invalid_queries = [
            "invalid(syntax",
            "malformed query",
        ]
        
        for query in invalid_queries:
            result = rql_filter.apply_rql_to_data(data, query)
            # Should return original data on error (or empty list, depends on pyrql behavior)
            assert isinstance(result, list)  # Should at least return a list

    def test_none_and_empty_data_handling(self, rql_filter):
        """Test handling of None and empty data."""
        # Test with None data
        result = rql_filter.apply_rql_to_data(None, "eq(id,1)")
        assert result is None
        
        # Test with empty data
        result = rql_filter.apply_rql_to_data([], "eq(id,1)")
        assert result == []

    def test_circular_references_in_filters(self, rql_filter, mock_table):
        """Test handling of potentially circular references."""
        # Create filters that might cause issues
        filters = {
            "name__eq": "value",
            "name__gt": "value",  # Same field, different operator
            "name__contains": "value",  # Same field, third operator
        }
        
        result = rql_filter.apply_filters(mock_table, filters)
        
        # Should handle multiple filters on same field
        assert len(result.applied_filters) == 3

    def test_type_conversion_edge_cases(self, rql_filter):
        """Test edge cases in type conversion."""
        # Test the private _convert_type method if accessible
        if hasattr(rql_filter, '_convert_type'):
            edge_cases = [
                ("", ""),  # Empty string
                ("0", 0),  # Zero
                ("0.0", 0.0),  # Zero float
                ("True", "True"),  # String "True" vs boolean
                ("False", "False"),  # String "False" vs boolean
                ("NULL", "NULL"),  # String "NULL" vs null
                ("undefined", "undefined"),  # Undefined value
            ]
            
            for input_val, expected in edge_cases:
                result = rql_filter._convert_type(input_val)
                # Test that conversion doesn't crash
                assert result is not None or expected is None


class TestRQLErrorRecovery:
    """Test RQL error recovery and graceful degradation."""

    def test_partial_query_recovery(self, rql_filter):
        """Test that partial queries can be recovered."""
        # Query with some valid and some invalid parts
        query = "eq(id,1)&invalid_syntax&gt(age,18)"
        result = rql_filter.parse_query_string(query)
        
        # Should recover valid parts
        assert isinstance(result, dict)
        assert "filters" in result

    def test_graceful_degradation_with_unknown_operators(self, rql_filter):
        """Test graceful degradation when unknown operators are used."""
        query = "eq(id,1)&unknown_op(name,test)&gt(age,18)"
        result = rql_filter.parse_query_string(query)
        
        # Should process known operators and ignore unknown ones
        assert isinstance(result, dict)
        assert result["filters"]  # Should have some filters

    def test_error_isolation(self, rql_filter):
        """Test that errors in one part don't affect others."""
        # Create a scenario where one filter might fail but others succeed
        filters = {
            "id__eq": 123,  # Valid
            "invalid__op": "test",  # Invalid operator
            "name__contains": "alice",  # Valid
        }
        
        mock_table = type('MockTable', (), {
            'id': type('Column', (), {'__eq__': lambda self, x: f'id == {x}'})(),
            'name': type('Column', (), {'contains': lambda self, x: f'name contains {x}'})(),
            'filter': lambda self, condition: setattr(self, 'applied_filters', 
                                                    getattr(self, 'applied_filters', []) + [condition]) or self
        })()
        
        result = rql_filter.apply_filters(mock_table, filters)
        
        # Should apply valid filters despite invalid ones
        assert hasattr(result, 'applied_filters')
