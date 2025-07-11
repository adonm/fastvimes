"""Test RQL integration with real Ibis tables."""

import pytest
from fastvimes.rql import apply_rql_to_table


class TestRQLIbisIntegration:
    """Test RQL with real Ibis tables."""

    def test_simple_filter_on_ibis_table(self, sample_table):
        """Test applying simple RQL filter to Ibis table."""
        result = apply_rql_to_table(sample_table, "gt(age,26)")
        
        # Execute the query and check results
        data = result.execute().to_dict("records")
        
        # Should return alice (30), charlie (35), diana (28)
        assert len(data) == 3
        ages = [row["age"] for row in data]
        assert all(age > 26 for age in ages)
        
        names = [row["name"] for row in data]
        assert set(names) == {"alice", "charlie", "diana"}

    def test_equality_filter_on_ibis_table(self, sample_table):
        """Test equality filter on Ibis table."""
        result = apply_rql_to_table(sample_table, "eq(name,alice)")
        
        data = result.execute().to_dict("records")
        
        assert len(data) == 1
        assert data[0]["name"] == "alice"
        assert data[0]["age"] == 30

    def test_boolean_filter_on_ibis_table(self, sample_table):
        """Test boolean filter on Ibis table."""
        result = apply_rql_to_table(sample_table, "eq(active,true)")
        
        data = result.execute().to_dict("records")
        
        # Should return alice, charlie, diana (bob is inactive)
        assert len(data) == 3
        names = [row["name"] for row in data]
        assert set(names) == {"alice", "charlie", "diana"}
        
        # All should be active
        assert all(row["active"] for row in data)

    def test_contains_filter_on_ibis_table(self, sample_table):
        """Test contains filter on Ibis table."""
        result = apply_rql_to_table(sample_table, "contains(name,a)")
        
        data = result.execute().to_dict("records")
        
        # Should return alice, charlie, diana (all contain 'a')
        assert len(data) == 3
        names = [row["name"] for row in data]
        assert set(names) == {"alice", "charlie", "diana"}

    def test_in_operator_on_ibis_table(self, sample_table):
        """Test in operator on Ibis table."""
        result = apply_rql_to_table(sample_table, "in(id,(1,3))")
        
        data = result.execute().to_dict("records")
        
        # Should return alice (id=1) and charlie (id=3)
        assert len(data) == 2
        ids = [row["id"] for row in data]
        assert set(ids) == {1, 3}
        
        names = [row["name"] for row in data]
        assert set(names) == {"alice", "charlie"}

    def test_multiple_filters_on_ibis_table(self, sample_table):
        """Test multiple filters on Ibis table."""
        result = apply_rql_to_table(sample_table, "gt(age,25)&eq(active,true)")
        
        data = result.execute().to_dict("records")
        
        # Should return alice (30, active), charlie (35, active), diana (28, active)
        # bob is excluded (age 25 not > 25, and also inactive)
        assert len(data) == 3
        
        for row in data:
            assert row["age"] > 25
            assert row["active"] is True

    def test_sorting_on_ibis_table(self, sample_table):
        """Test sorting on Ibis table."""
        result = apply_rql_to_table(sample_table, "sort(+age)")
        
        data = result.execute().to_dict("records")
        
        # Should be sorted by age ascending: bob(25), diana(28), alice(30), charlie(35)
        assert len(data) == 4
        ages = [row["age"] for row in data]
        assert ages == [25, 28, 30, 35]
        
        names = [row["name"] for row in data]
        assert names == ["bob", "diana", "alice", "charlie"]

    def test_reverse_sorting_on_ibis_table(self, sample_table):
        """Test reverse sorting on Ibis table."""
        result = apply_rql_to_table(sample_table, "sort(-age)")
        
        data = result.execute().to_dict("records")
        
        # Should be sorted by age descending: charlie(35), alice(30), diana(28), bob(25)
        assert len(data) == 4
        ages = [row["age"] for row in data]
        assert ages == [35, 30, 28, 25]
        
        names = [row["name"] for row in data]
        assert names == ["charlie", "alice", "diana", "bob"]

    def test_multiple_sort_fields_on_ibis_table(self, sample_table):
        """Test multiple sort fields on Ibis table."""
        result = apply_rql_to_table(sample_table, "sort(+city,-age)")
        
        data = result.execute().to_dict("records")
        
        # Should be sorted by city ascending, then age descending within city
        assert len(data) == 4
        
        # Group by city and check sorting
        cities = [row["city"] for row in data]
        assert cities == ["Chicago", "New York", "New York", "San Francisco"]
        
        # Within New York, should be alice (30) then diana (28)
        ny_rows = [row for row in data if row["city"] == "New York"]
        assert len(ny_rows) == 2
        assert ny_rows[0]["name"] == "alice"  # age 30
        assert ny_rows[1]["name"] == "diana"  # age 28

    def test_limit_on_ibis_table(self, sample_table):
        """Test limit on Ibis table."""
        result = apply_rql_to_table(sample_table, "limit(2)")
        
        data = result.execute().to_dict("records")
        
        # Should return only 2 rows
        assert len(data) == 2

    def test_limit_with_offset_on_ibis_table(self, sample_table):
        """Test limit with offset on Ibis table."""
        result = apply_rql_to_table(sample_table, "limit(2,1)")
        
        data = result.execute().to_dict("records")
        
        # Should skip 1 row and return 2 rows
        assert len(data) == 2

    def test_select_fields_on_ibis_table(self, sample_table):
        """Test field selection on Ibis table."""
        result = apply_rql_to_table(sample_table, "select(id,name)")
        
        data = result.execute().to_dict("records")
        
        # Should return all 4 rows but only id and name columns
        assert len(data) == 4
        
        for row in data:
            assert set(row.keys()) == {"id", "name"}
            assert "age" not in row
            assert "active" not in row
            assert "city" not in row

    def test_complex_query_on_ibis_table(self, sample_table):
        """Test complex query combining multiple features."""
        result = apply_rql_to_table(
            sample_table, 
            "gt(age,25)&eq(active,true)&sort(-age)&limit(2)&select(id,name,age)"
        )
        
        data = result.execute().to_dict("records")
        
        # Should:
        # 1. Filter: age > 25 AND active = true (alice, charlie, diana)
        # 2. Sort: by age descending (charlie 35, alice 30, diana 28)
        # 3. Limit: first 2 rows (charlie, alice)
        # 4. Select: only id, name, age columns
        
        assert len(data) == 2
        
        # Check order and values
        assert data[0]["name"] == "charlie"
        assert data[0]["age"] == 35
        assert data[1]["name"] == "alice"
        assert data[1]["age"] == 30
        
        # Check only selected columns
        for row in data:
            assert set(row.keys()) == {"id", "name", "age"}

    def test_no_match_filter_on_ibis_table(self, sample_table):
        """Test filter that matches no records."""
        result = apply_rql_to_table(sample_table, "gt(age,100)")
        
        data = result.execute().to_dict("records")
        
        # Should return empty result
        assert len(data) == 0

    def test_invalid_field_in_filter_on_ibis_table(self, sample_table):
        """Test filter with invalid field name."""
        result = apply_rql_to_table(sample_table, "eq(nonexistent_field,value)")
        
        data = result.execute().to_dict("records")
        
        # Should return all records (filter ignored)
        assert len(data) == 4

    def test_invalid_field_in_sort_on_ibis_table(self, sample_table):
        """Test sort with invalid field name."""
        result = apply_rql_to_table(sample_table, "sort(+nonexistent_field)")
        
        data = result.execute().to_dict("records")
        
        # Should return all records in original order
        assert len(data) == 4

    def test_invalid_field_in_select_on_ibis_table(self, sample_table):
        """Test select with invalid field name."""
        result = apply_rql_to_table(sample_table, "select(id,nonexistent_field)")
        
        data = result.execute().to_dict("records")
        
        # Should return all records with only valid fields
        assert len(data) == 4
        
        for row in data:
            assert "id" in row
            assert "nonexistent_field" not in row


class TestRQLDataQueryEngine:
    """Test RQL with direct data queries using pyrql Query engine."""

    def test_simple_filter_on_data(self, rql_filter, sample_data):
        """Test applying simple RQL filter to data."""
        result = rql_filter.apply_rql_to_data(sample_data, "gt(age,26)")
        
        # Should return alice (30), charlie (35), diana (28)
        assert len(result) == 3
        ages = [row["age"] for row in result]
        assert all(age > 26 for age in ages)
        
        names = [row["name"] for row in result]
        assert set(names) == {"alice", "charlie", "diana"}

    def test_equality_filter_on_data(self, rql_filter, sample_data):
        """Test equality filter on data."""
        result = rql_filter.apply_rql_to_data(sample_data, "eq(name,alice)")
        
        assert len(result) == 1
        assert result[0]["name"] == "alice"
        assert result[0]["age"] == 30

    def test_boolean_filter_on_data(self, rql_filter, sample_data):
        """Test boolean filter on data."""
        result = rql_filter.apply_rql_to_data(sample_data, "eq(active,true)")
        
        # Should return alice, charlie, diana (bob is inactive)
        assert len(result) == 3
        names = [row["name"] for row in result]
        assert set(names) == {"alice", "charlie", "diana"}

    def test_sorting_on_data(self, rql_filter, sample_data):
        """Test sorting on data."""
        result = rql_filter.apply_rql_to_data(sample_data, "sort(+age)")
        
        # Should be sorted by age ascending
        assert len(result) == 4
        ages = [row["age"] for row in result]
        assert ages == [25, 28, 30, 35]

    def test_complex_query_on_data(self, rql_filter, sample_data):
        """Test complex query on data."""
        result = rql_filter.apply_rql_to_data(sample_data, "gt(age,25)&sort(-age)")
        
        # Should filter age > 25 and sort by age descending
        assert len(result) == 3
        ages = [row["age"] for row in result]
        assert ages == [35, 30, 28]  # charlie, alice, diana
        
        names = [row["name"] for row in result]
        assert names == ["charlie", "alice", "diana"]

    def test_invalid_query_on_data(self, rql_filter, sample_data):
        """Test invalid query returns original data."""
        result = rql_filter.apply_rql_to_data(sample_data, "invalid(syntax")
        
        # Should return original data when query fails
        assert result == sample_data
        assert len(result) == 4

    def test_empty_query_on_data(self, rql_filter, sample_data):
        """Test empty query returns original data."""
        result = rql_filter.apply_rql_to_data(sample_data, "")
        
        # Should return original data
        assert result == sample_data
        assert len(result) == 4
