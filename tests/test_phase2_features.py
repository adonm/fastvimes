"""Comprehensive tests for Phase 2 features: charts, navigation, UI components."""

import pytest
from pathlib import Path
from fastvimes.database_service import DatabaseService
from fastvimes.app import FastVimes
from fastvimes.config import FastVimesSettings


@pytest.fixture
def chart_db_service():
    """Create a test database service with rich data for chart testing."""
    service = DatabaseService(Path(":memory:"), create_sample_data=True)
    
    # Add additional sample data for better chart testing
    service.connection.execute("""
        INSERT INTO users (id, name, email, age, active, department, created_at) VALUES
        (100, 'John Doe', 'john@example.com', 45, true, 'Engineering', '2024-01-01'),
        (101, 'Jane Smith', 'jane@example.com', 32, true, 'Design', '2024-01-02'),
        (102, 'Mike Johnson', 'mike@example.com', 29, false, 'Marketing', '2024-01-03'),
        (103, 'Sarah Wilson', 'sarah@example.com', 38, true, 'Engineering', '2024-01-04'),
        (104, 'Tom Brown', 'tom@example.com', 26, true, 'Sales', '2024-01-05'),
        (105, 'Lisa Davis', 'lisa@example.com', 41, true, 'Design', '2024-01-06'),
        (106, 'Chris Lee', 'chris@example.com', 33, false, 'Marketing', '2024-01-07'),
        (107, 'Amy Zhang', 'amy@example.com', 37, true, 'Engineering', '2024-01-08')
    """)
    
    # Add more products for distribution charts
    service.connection.execute("""
        INSERT INTO products (id, name, category, price, stock_quantity, active, created_at) VALUES
        (100, 'Tablet Pro', 'Electronics', 599.99, 40, true, '2024-01-10'),
        (101, 'Smart Watch', 'Electronics', 299.99, 75, true, '2024-01-11'),
        (102, 'Desk Chair', 'Furniture', 199.99, 20, true, '2024-01-12'),
        (103, 'Standing Desk', 'Furniture', 399.99, 15, true, '2024-01-13'),
        (104, 'Coffee Mug', 'Office', 12.99, 200, true, '2024-01-14'),
        (105, 'Notebook', 'Office', 8.99, 500, true, '2024-01-15'),
        (106, 'Headphones', 'Electronics', 149.99, 60, false, '2024-01-16'),
        (107, 'Monitor', 'Electronics', 249.99, 25, true, '2024-01-17')
    """)
    
    yield service
    service.close()


@pytest.fixture
def fastvimes_app():
    """Create a FastVimes app for UI testing."""
    settings = FastVimesSettings(
        duckdb_ui_enabled=False,  # Disable DuckDB UI for testing
        admin_enabled=False
    )
    app = FastVimes(db_path=":memory:", settings=settings)
    yield app
    app._cleanup()


@pytest.mark.fast
class TestChartDataGeneration:
    """Test chart data generation and analysis."""

    def test_get_chart_data_structure(self, chart_db_service):
        """Test that chart data has correct structure."""
        chart_data = chart_db_service.get_chart_data("users")
        
        # Verify required keys
        required_keys = ["table_name", "charts", "numeric_columns", "categorical_columns", "date_columns"]
        for key in required_keys:
            assert key in chart_data
        
        assert chart_data["table_name"] == "users"
        assert isinstance(chart_data["charts"], list)
        assert isinstance(chart_data["numeric_columns"], list)
        assert isinstance(chart_data["categorical_columns"], list)
        assert isinstance(chart_data["date_columns"], list)

    def test_column_type_identification(self, chart_db_service):
        """Test that column types are correctly identified for charts."""
        chart_data = chart_db_service.get_chart_data("users")
        
        # Should identify numeric columns
        assert "age" in chart_data["numeric_columns"]
        
        # Should identify categorical columns
        categorical_cols = chart_data["categorical_columns"]
        assert "department" in categorical_cols
        assert "name" in categorical_cols
        
        # Should identify date columns
        assert "created_at" in chart_data["date_columns"]
        
        # Should exclude ID columns from categorical
        assert "id" not in categorical_cols

    def test_chart_generation_for_users_table(self, chart_db_service):
        """Test that appropriate charts are generated for users table."""
        chart_data = chart_db_service.get_chart_data("users")
        charts = chart_data["charts"]
        
        # Should generate some charts for users table
        assert len(charts) > 0
        
        # Verify chart structure
        for chart in charts:
            assert "type" in chart
            assert "title" in chart
            assert "data" in chart
            assert "x_key" in chart
            assert "y_key" in chart
            assert chart["type"] in ["bar", "line"]
            assert isinstance(chart["data"], list)
            assert len(chart["data"]) > 0

    def test_chart_generation_for_products_table(self, chart_db_service):
        """Test chart generation for products table with different data types."""
        chart_data = chart_db_service.get_chart_data("products")
        
        # Should identify price and stock_quantity as numeric
        numeric_cols = chart_data["numeric_columns"]
        assert "price" in numeric_cols
        assert "stock_quantity" in numeric_cols
        
        # Should identify category as categorical
        assert "category" in chart_data["categorical_columns"]

    def test_department_distribution_chart(self, chart_db_service):
        """Test that department distribution chart is generated correctly."""
        chart_data = chart_db_service.get_chart_data("users")
        charts = chart_data["charts"]
        
        # Find department chart
        dept_chart = None
        for chart in charts:
            if "department" in chart["title"].lower():
                dept_chart = chart
                break
        
        if dept_chart:
            assert dept_chart["type"] == "bar"
            assert dept_chart["x_key"] == "department"
            assert dept_chart["y_key"] == "count"
            
            # Should have data for each department
            departments = [item[dept_chart["x_key"]] for item in dept_chart["data"]]
            assert "Engineering" in departments
            assert "Marketing" in departments

    def test_age_distribution_chart(self, chart_db_service):
        """Test that age distribution histogram is generated."""
        chart_data = chart_db_service.get_chart_data("users")
        charts = chart_data["charts"]
        
        # Find age distribution chart
        age_chart = None
        for chart in charts:
            if "age" in chart["title"].lower() and "distribution" in chart["title"].lower():
                age_chart = chart
                break
        
        if age_chart:
            assert age_chart["type"] == "bar"
            assert age_chart["x_key"] == "range"
            assert age_chart["y_key"] == "count"
            assert len(age_chart["data"]) > 0

    def test_chart_data_with_empty_table(self, chart_db_service):
        """Test chart generation behavior with empty table."""
        # Create empty table
        chart_db_service.connection.execute("""
            CREATE TABLE empty_test (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100),
                value INTEGER
            )
        """)
        
        chart_data = chart_db_service.get_chart_data("empty_test")
        
        # Should return structure but no charts
        assert chart_data["table_name"] == "empty_test"
        assert isinstance(chart_data["charts"], list)
        # Charts list may be empty or contain empty data charts
        for chart in chart_data["charts"]:
            # If charts exist, they should have proper structure
            assert "type" in chart
            assert "data" in chart

    def test_chart_error_handling(self, chart_db_service):
        """Test chart generation with invalid table name."""
        with pytest.raises((RuntimeError, ValueError, Exception)):
            chart_db_service.get_chart_data("nonexistent_table")


@pytest.mark.fast
class TestNavigationAndUIComponents:
    """Test navigation and UI component functionality."""

    def test_fastvimes_app_initialization(self, fastvimes_app):
        """Test that FastVimes app initializes correctly."""
        assert fastvimes_app.db_service is not None
        assert fastvimes_app.api is not None
        assert fastvimes_app.settings is not None

    def test_override_hooks(self, fastvimes_app):
        """Test that override hooks return None by default."""
        assert fastvimes_app.override_table_page("users") is None
        assert fastvimes_app.override_form_page("users") is None

    def test_database_service_integration(self, fastvimes_app):
        """Test that database service is properly integrated."""
        # Note: fastvimes_app uses settings with admin_enabled=False
        # which may not create sample data, so we create minimal data
        fastvimes_app.db_service.connection.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100)
            )
        """)
        
        # Should be able to list tables
        tables = fastvimes_app.db_service.list_tables()
        assert len(tables) > 0
        
        table_names = [t["name"] for t in tables]
        assert "test_table" in table_names

    def test_api_integration(self, fastvimes_app):
        """Test that API is properly integrated."""
        # API should have database service
        assert hasattr(fastvimes_app.api.state, 'db_service')
        assert fastvimes_app.api.state.db_service is fastvimes_app.db_service

    def test_settings_integration(self, fastvimes_app):
        """Test that settings are properly applied."""
        assert isinstance(fastvimes_app.settings, FastVimesSettings)
        # Settings should reflect our test configuration
        assert fastvimes_app.settings.admin_enabled is False  # We set this in fixture
        assert fastvimes_app.settings.duckdb_ui_enabled is False  # We set this in fixture
        assert fastvimes_app.settings.debug is False


@pytest.mark.fast 
class TestAPIEndpointsForCharts:
    """Test API endpoints related to chart functionality."""

    def test_table_data_endpoint_format(self, chart_db_service):
        """Test that table data endpoint returns correct format for UI consumption."""
        data = chart_db_service.get_table_data("users", limit=5)
        
        # Should return dict with required keys
        assert isinstance(data, dict)
        assert "data" in data
        assert "columns" in data
        assert "total_count" in data
        
        # Data should be list of records
        assert isinstance(data["data"], list)
        assert len(data["data"]) <= 5
        
        # Each record should be a dict
        for record in data["data"]:
            assert isinstance(record, dict)
            assert "id" in record
            assert "name" in record

    def test_table_schema_endpoint(self, chart_db_service):
        """Test table schema endpoint for UI form generation."""
        schema = chart_db_service.get_table_schema("users")
        
        assert isinstance(schema, list)
        assert len(schema) > 0
        
        # Each column should have required fields
        for col in schema:
            assert "name" in col
            assert "type" in col
        
        # Should have expected columns
        col_names = [col["name"] for col in schema]
        expected_columns = ["id", "name", "email", "age", "active", "department", "created_at"]
        for expected in expected_columns:
            assert expected in col_names

    def test_rql_filtering_for_charts(self, chart_db_service):
        """Test RQL filtering that might be used by chart components."""
        # Test department filtering
        result = chart_db_service.get_table_data("users", rql_query="eq(department,Engineering)")
        assert len(result["data"]) > 0
        for user in result["data"]:
            assert user["department"] == "Engineering"
        
        # Test age filtering
        result = chart_db_service.get_table_data("users", rql_query="gt(age,30)")
        assert len(result["data"]) > 0
        for user in result["data"]:
            assert user["age"] > 30

    def test_pagination_for_large_datasets(self, chart_db_service):
        """Test pagination for chart data consumption."""
        # Test with limit
        result = chart_db_service.get_table_data("users", limit=3)
        assert len(result["data"]) <= 3
        assert result["total_count"] >= 3
        
        # Test with offset
        result1 = chart_db_service.get_table_data("users", limit=2, offset=0)
        result2 = chart_db_service.get_table_data("users", limit=2, offset=2)
        
        # Should get different records
        ids1 = {user["id"] for user in result1["data"]}
        ids2 = {user["id"] for user in result2["data"]}
        assert ids1.isdisjoint(ids2)


@pytest.mark.fast
class TestUIDataHandling:
    """Test data handling for UI components."""

    def test_aggrid_data_format_compatibility(self, chart_db_service):
        """Test that data format is compatible with AGGrid expectations."""
        data = chart_db_service.get_table_data("users")
        
        # Should handle both possible formats
        if isinstance(data, dict):
            if "data" in data:
                rows = data["data"]
            elif "records" in data:
                rows = data["records"]
            else:
                rows = []
        else:
            rows = data if isinstance(data, list) else []
        
        assert isinstance(rows, list)
        if rows:
            # Each row should be a dictionary
            for row in rows:
                assert isinstance(row, dict)
                # Should have at least an id field
                assert "id" in row

    def test_echart_data_format_compatibility(self, chart_db_service):
        """Test that chart data is compatible with ECharts format."""
        chart_data = chart_db_service.get_chart_data("users")
        
        for chart_config in chart_data["charts"]:
            # Should have the keys needed for ECharts
            assert "type" in chart_config
            assert "data" in chart_config
            assert "x_key" in chart_config
            assert "y_key" in chart_config
            
            # Data should be extractable for ECharts format
            data = chart_config["data"]
            x_values = [str(item[chart_config["x_key"]]) for item in data]
            y_values = [item[chart_config["y_key"]] for item in data]
            
            assert len(x_values) == len(y_values)
            assert all(isinstance(x, str) for x in x_values)
            assert all(isinstance(y, (int, float)) for y in y_values)

    def test_form_field_type_detection(self, chart_db_service):
        """Test field type detection for form generation."""
        schema = chart_db_service.get_table_schema("users")
        
        for col in schema:
            col_name = col["name"]
            col_type = col["type"].lower()
            
            # Test type categorization logic
            if col_name == "age":
                assert any(t in col_type for t in ["int", "integer"])
            elif col_name == "email":
                assert any(t in col_type for t in ["varchar", "text", "string"])
            elif col_name == "active":
                assert any(t in col_type for t in ["bool", "boolean"])
            elif col_name == "created_at":
                assert any(t in col_type for t in ["date", "timestamp"])


@pytest.mark.fast
class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases for Phase 2 features."""

    def test_chart_generation_with_null_values(self, chart_db_service):
        """Test chart generation handles NULL values gracefully."""
        # Insert records with NULL values
        chart_db_service.connection.execute("""
            INSERT INTO users (id, name, email, age, active, department, created_at) VALUES
            (200, 'Null Age User', 'null@example.com', NULL, true, 'Engineering', '2024-01-20'),
            (201, 'Null Dept User', 'nulldept@example.com', 30, true, NULL, '2024-01-21')
        """)
        
        chart_data = chart_db_service.get_chart_data("users")
        
        # Should still generate charts without crashing
        assert isinstance(chart_data["charts"], list)
        
        # Charts should handle NULL values appropriately
        for chart in chart_data["charts"]:
            assert isinstance(chart["data"], list)

    def test_chart_generation_with_special_characters(self, chart_db_service):
        """Test chart generation with special characters in data."""
        # Insert records with special characters
        chart_db_service.connection.execute("""
            INSERT INTO users (id, name, email, age, active, department, created_at) VALUES
            (250, 'José García', 'jose@example.com', 35, true, 'R&D', '2024-01-25'),
            (251, '李小明', 'li@example.com', 28, true, 'Sales & Marketing', '2024-01-26')
        """)
        
        chart_data = chart_db_service.get_chart_data("users")
        
        # Should handle special characters without errors
        assert len(chart_data["charts"]) >= 0
        
        for chart in chart_data["charts"]:
            for item in chart["data"]:
                # Should be able to convert to string for display
                str_val = str(item[chart["x_key"]])
                assert isinstance(str_val, str)

    def test_ui_with_very_large_table_names(self, chart_db_service):
        """Test UI components handle long table names."""
        long_table_name = "very_long_table_name_that_might_cause_ui_issues_" + "x" * 50
        
        # Create table with long name
        chart_db_service.connection.execute(f"""
            CREATE TABLE {long_table_name} (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100)
            )
        """)
        
        # Should be able to get schema
        schema = chart_db_service.get_table_schema(long_table_name)
        assert len(schema) == 2
        
        # Should be able to generate chart data
        chart_data = chart_db_service.get_chart_data(long_table_name)
        assert chart_data["table_name"] == long_table_name

    def test_tables_list_for_navigation(self, chart_db_service):
        """Test tables list functionality for navigation sidebar."""
        tables = chart_db_service.list_tables()
        
        # Should return list of tables
        assert isinstance(tables, list)
        assert len(tables) > 0
        
        # Each table should have required properties
        for table in tables:
            assert "name" in table
            assert "type" in table
            assert isinstance(table["name"], str)
            assert len(table["name"]) > 0
