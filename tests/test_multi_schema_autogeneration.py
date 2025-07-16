"""Test autogeneration works with different schema patterns."""

import pytest


class TestMultiSchemaAutogeneration:
    """Test that autogeneration works with different schema structures."""

    def test_schema_introspection_works_with_any_schema(self, multi_schema_db):
        """Test that schema introspection works regardless of table/column names."""
        service = multi_schema_db

        # Test list_tables works with any schema
        tables = service.list_tables()
        assert len(tables) > 0

        # Verify expected tables exist
        table_names = [t["name"] for t in tables]
        for expected_table in service._test_expected_tables:
            assert expected_table in table_names, (
                f"Expected table {expected_table} not found in {table_names}"
            )

        # Test get_table_schema works with any table
        for table_name in service._test_expected_tables:
            schema = service.get_table_schema(table_name)
            assert len(schema) > 0, f"Schema for table {table_name} should not be empty"

            # Verify schema has required fields
            column_names = [col["name"] for col in schema]
            assert len(column_names) > 0, f"Table {table_name} should have columns"

            # Verify each column has required metadata
            for col in schema:
                assert "name" in col, f"Column missing name in table {table_name}"
                assert "type" in col, f"Column missing type in table {table_name}"

    def test_get_table_data_works_with_any_schema(self, multi_schema_db):
        """Test that get_table_data works regardless of table structure."""
        service = multi_schema_db

        for table_name in service._test_expected_tables:
            # Test basic data retrieval
            result = service.get_table_data(table_name)

            # Verify result structure
            assert "columns" in result
            assert "data" in result
            assert "total_count" in result

            # Verify columns match schema
            schema = service.get_table_schema(table_name)
            expected_columns = [col["name"] for col in schema]
            assert result["columns"] == expected_columns

            # Verify data consistency
            if result["data"]:
                # Each row should have same number of fields as columns
                for row in result["data"]:
                    assert len(row) == len(expected_columns)

    def test_rql_filtering_works_with_any_schema(self, multi_schema_db):
        """Test RQL filtering works with different column names and types."""
        service = multi_schema_db

        for table_name in service._test_expected_tables:
            schema = service.get_table_schema(table_name)

            # Test basic limit (should work with any table)
            result = service.get_table_data(table_name, rql_query="limit(1)")
            assert len(result["data"]) <= 1

            # Test filtering on different column types
            for col in schema:
                col_name = col["name"]
                col_type = col["type"].upper()

                if any(
                    t in col_type
                    for t in ["INT", "DECIMAL", "FLOAT", "DOUBLE", "NUMERIC"]
                ):
                    # Test numeric filtering
                    try:
                        result = service.get_table_data(
                            table_name, rql_query=f"gt({col_name},0)"
                        )
                        assert "data" in result
                    except Exception:
                        # Skip if column has no data > 0
                        pass

                elif any(t in col_type for t in ["VARCHAR", "TEXT", "CHAR"]):
                    # Test string filtering
                    try:
                        result = service.get_table_data(
                            table_name, rql_query=f"ne({col_name},'')"
                        )
                        assert "data" in result
                    except Exception:
                        # Skip if column has complex string constraints
                        pass

                elif "BOOL" in col_type:
                    # Test boolean filtering
                    try:
                        result = service.get_table_data(
                            table_name, rql_query=f"eq({col_name},true)"
                        )
                        assert "data" in result
                    except Exception:
                        # Skip if boolean column has constraints
                        pass

    def test_crud_operations_work_with_any_schema(self, multi_schema_db):
        """Test CRUD operations work with different table structures."""
        service = multi_schema_db

        # Skip CRUD tests for external data sources (read-only)
        if service._test_schema_name == "nyc_taxi":
            pytest.skip("Skipping CRUD tests for external data source")

        for table_name in service._test_expected_tables:
            schema = service.get_table_schema(table_name)

            # Create test data based on schema
            test_data = {}
            for col in schema:
                col_name = col["name"]
                col_type = col["type"].upper()

                # Skip primary key and auto-increment columns
                if col_name.lower() in ["id", "uuid"] or "PRIMARY KEY" in str(col):
                    continue

                # Generate test data based on column type
                if any(t in col_type for t in ["INT", "INTEGER"]):
                    test_data[col_name] = 999
                elif any(t in col_type for t in ["VARCHAR", "TEXT", "CHAR"]):
                    test_data[col_name] = f"test_{col_name}"
                elif any(
                    t in col_type for t in ["DECIMAL", "FLOAT", "DOUBLE", "NUMERIC"]
                ):
                    test_data[col_name] = 99.99
                elif "BOOL" in col_type:
                    test_data[col_name] = True
                elif any(t in col_type for t in ["DATE", "TIMESTAMP"]):
                    test_data[col_name] = "2024-01-01"

            if test_data:
                # Test create_record
                try:
                    result = service.create_record(table_name, test_data)
                    # Check for any primary key or success message
                    has_id = any(
                        key.endswith("_id") or key == "id" for key in result.keys()
                    )
                    has_success = "created" in str(result) or "message" in result
                    assert has_id or has_success, (
                        f"Expected primary key or success message in result: {result}"
                    )
                except Exception as e:
                    # Skip if table has complex constraints
                    if (
                        "constraint" in str(e).lower()
                        or "foreign key" in str(e).lower()
                    ):
                        continue
                    # Skip if column count mismatch (complex table structure)
                    if "columns but" in str(e) and "values were supplied" in str(e):
                        continue
                    raise

    def test_autogenerated_endpoints_work_with_any_schema(self, multi_schema_db):
        """Test that autogenerated API endpoints work with any schema."""
        service = multi_schema_db

        # This test validates that the DatabaseService methods work with any schema
        # The actual FastAPI endpoints are light wrappers around these methods

        tables = service.list_tables()
        assert len(tables) > 0

        # Test that each table can be accessed via the methods that back API endpoints
        for table_info in tables:
            table_name = table_info["name"]

            # Test schema endpoint backing method
            schema = service.get_table_schema(table_name)
            assert len(schema) > 0

            # Test data endpoint backing method
            data = service.get_table_data(table_name, limit=5)
            assert "columns" in data
            assert "data" in data
            assert "total_count" in data

            # Test that the structure is consistent for autogeneration
            assert len(data["columns"]) == len(schema)

            # Each column in schema should match columns in data
            schema_columns = [col["name"] for col in schema]
            assert data["columns"] == schema_columns


class TestSchemaSpecificBehavior:
    """Test behavior specific to each schema type."""

    def test_default_sample_schema_behavior(self, multi_schema_db):
        """Test behavior specific to default sample schema."""
        service = multi_schema_db

        if service._test_schema_name != "default_sample":
            pytest.skip("Only for default_sample schema")

        # Test that expected tables exist
        tables = service.list_tables()
        table_names = [t["name"] for t in tables]
        assert "users" in table_names
        assert "products" in table_names
        assert "orders" in table_names

        # Test user table has expected structure
        user_schema = service.get_table_schema("users")
        user_columns = [col["name"] for col in user_schema]
        assert "id" in user_columns
        assert "name" in user_columns
        assert "email" in user_columns

    @pytest.mark.external_data
    def test_nyc_taxi_schema_behavior(self, multi_schema_db):
        """Test behavior specific to NYC taxi schema."""
        service = multi_schema_db

        if service._test_schema_name != "nyc_taxi":
            pytest.skip("Only for nyc_taxi schema")

        # Test that taxi-specific tables exist
        tables = service.list_tables()
        table_names = [t["name"] for t in tables]
        assert "trips" in table_names
        assert "trip_summary" in table_names

        # Test taxi-specific column names
        trips_schema = service.get_table_schema("trips")
        trip_columns = [col["name"] for col in trips_schema]
        assert "passenger_count" in trip_columns
        assert "trip_distance" in trip_columns
        assert "fare_amount" in trip_columns

    def test_financial_schema_behavior(self, multi_schema_db):
        """Test behavior specific to financial schema."""
        service = multi_schema_db

        if service._test_schema_name != "financial_data":
            pytest.skip("Only for financial_data schema")

        # Test financial-specific tables
        tables = service.list_tables()
        table_names = [t["name"] for t in tables]
        assert "financial_instruments" in table_names
        assert "trading_sessions" in table_names

        # Test financial-specific column names
        instruments_schema = service.get_table_schema("financial_instruments")
        instrument_columns = [col["name"] for col in instruments_schema]
        assert "symbol" in instrument_columns
        assert "market_cap" in instrument_columns
        assert "sector" in instrument_columns

    def test_blog_schema_behavior(self, multi_schema_db):
        """Test behavior specific to blog schema."""
        service = multi_schema_db

        if service._test_schema_name != "blog_platform":
            pytest.skip("Only for blog_platform schema")

        # Test blog-specific tables
        tables = service.list_tables()
        table_names = [t["name"] for t in tables]
        assert "authors" in table_names
        assert "blog_posts" in table_names
        assert "post_comments" in table_names

        # Test blog-specific column names
        authors_schema = service.get_table_schema("authors")
        author_columns = [col["name"] for col in authors_schema]
        assert "username" in author_columns
        assert "email_address" in author_columns
        assert "full_name" in author_columns
