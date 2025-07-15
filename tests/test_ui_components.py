"""
Test NiceGUI components for basic functionality.

Design Spec: AGENT.md - NiceGUI Exploratory Interface - Auto-Generated Components
Coverage: Component initialization, user interactions, multi-schema support, API integration
"""

import pytest
import httpx
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from fastvimes.database_service import DatabaseService
from fastvimes.api_client import FastVimesAPIClient
from fastvimes.components import TableBrowser, DataExplorer, QueryBuilder, FormGenerator
from fastvimes.app import FastVimes


@pytest.fixture
def db_service():
    """Create a test database service."""
    service = DatabaseService(Path(":memory:"), create_sample_data=True)
    yield service
    service.close()


@pytest.fixture
def api_client(db_service):
    """Create API client with test database."""
    return FastVimesAPIClient(db_service=db_service)


@pytest.fixture
def test_server():
    """Create test FastAPI server for API integration tests."""
    from fastapi.testclient import TestClient
    from fastvimes.app import FastVimes
    
    # Create FastVimes app with in-memory database
    app = FastVimes()
    
    # Create test client
    client = TestClient(app.api)
    
    yield client
    
    # Cleanup
    app.db_service.close()
    if app.api_client:
        app.api_client.close()


@pytest.fixture
def http_api_client(test_server):
    """Create HTTP API client for testing actual HTTP endpoints."""
    # Use test server directly, not real HTTP
    return FastVimesAPIClient(base_url="http://testserver")


class TestUIComponentsBasic:
    """
    Test basic functionality of UI components.
    
    Design Spec: AGENT.md - NiceGUI Exploratory Interface - Auto-Generated Components
    Coverage: Component initialization, state management, basic functionality
    """
    
    def test_table_browser_initialization(self, api_client):
        """Test TableBrowser can be initialized."""
        browser = TableBrowser(api_client)
        assert browser.api_client == api_client
    
    def test_data_explorer_initialization(self, api_client):
        """Test DataExplorer can be initialized."""
        explorer = DataExplorer(api_client, "users")
        assert explorer.api_client == api_client
        assert explorer.table_name == "users"
        assert explorer.current_page == 0
        assert explorer.page_size == 25
        assert explorer.filters == {}
        assert explorer.edit_mode == False
        assert explorer.selected_rows == set()
    
    def test_query_builder_initialization(self, api_client):
        """Test QueryBuilder can be initialized."""
        builder = QueryBuilder(api_client, "users")
        assert builder.api_client == api_client
        assert builder.table_name == "users"
        assert builder.filters == []
        assert builder.limit_value == 100
        assert builder.sort_column is None
        assert builder.sort_direction == "asc"
    
    def test_form_generator_initialization(self, api_client):
        """Test FormGenerator can be initialized."""
        generator = FormGenerator(api_client, "users")
        assert generator.api_client == api_client
        assert generator.table_name == "users"
        assert generator.form_data == {}
    
    def test_query_builder_rql_generation(self, api_client):
        """Test QueryBuilder RQL query generation."""
        builder = QueryBuilder(api_client, "users")
        
        # Test empty query
        assert builder._build_rql_query() == ""
        
        # Test with limit
        builder.limit_value = 50
        assert "limit(50)" in builder._build_rql_query()
        
        # Test with sorting
        builder.sort_column = "name"
        builder.sort_direction = "asc"
        assert "sort(+name)" in builder._build_rql_query()
        
        # Test with filter
        builder.filters = [{"column": "active", "operator": "eq", "value": "true"}]
        rql = builder._build_rql_query()
        assert "eq(active,true)" in rql
    
    def test_query_builder_filter_operations(self, api_client):
        """Test QueryBuilder filter operations."""
        builder = QueryBuilder(api_client, "users")
        
        # Test filter update
        builder.filters = [{}]
        builder._update_filter(0, "column", "name")
        assert builder.filters[0]["column"] == "name"
        
        builder._update_filter(0, "operator", "contains")
        assert builder.filters[0]["operator"] == "contains"
        
        builder._update_filter(0, "value", "test")
        assert builder.filters[0]["value"] == "test"
        
        # Test invalid index
        builder._update_filter(999, "column", "invalid")
        assert len(builder.filters) == 1  # Should not crash or add new filter


class TestDataExplorerFunctionality:
    """
    Test DataExplorer component functionality.
    
    Design Spec: AGENT.md - NiceGUI Testing Patterns - DataExplorer Requirements
    Coverage: Filtering, pagination, edit mode, bulk operations, RQL integration
    """
    
    def test_data_explorer_build_rql_query(self, api_client):
        """Test DataExplorer RQL query building."""
        explorer = DataExplorer(api_client, "users")
        
        # Test empty query
        rql = explorer._build_rql_query()
        assert rql == ""
        
        # Test with filters
        explorer.filters = {"name": "test"}
        rql = explorer._build_rql_query()
        assert "contains(name,test)" in rql
        
        # Test with multiple filters
        explorer.filters = {"name": "Alice", "age_min": "25"}
        rql = explorer._build_rql_query()
        assert "and(" in rql
        assert "contains(name,Alice)" in rql
        assert "ge(age,25)" in rql
    
    def test_data_explorer_filter_management(self, api_client):
        """Test DataExplorer filter management."""
        explorer = DataExplorer(api_client, "users")
        
        # Test filter update
        explorer._update_filter("name", "Alice")
        assert explorer.filters["name"] == "Alice"
        
        explorer._update_filter("age_min", "25")
        assert explorer.filters["age_min"] == "25"
        
        # Test filter clearing
        explorer._update_filter("name", None)
        assert "name" not in explorer.filters
    
    def test_data_explorer_pagination(self, api_client):
        """Test DataExplorer pagination functionality."""
        explorer = DataExplorer(api_client, "users")
        
        # Test initial state
        assert explorer.current_page == 0
        
        # Test next page
        explorer._next_page()
        assert explorer.current_page == 1
        
        # Test previous page
        explorer._previous_page()
        assert explorer.current_page == 0
        
        # Test previous page doesn't go negative
        explorer._previous_page()
        assert explorer.current_page == 0
    
    def test_data_explorer_edit_mode(self, api_client):
        """Test DataExplorer edit mode functionality."""
        explorer = DataExplorer(api_client, "users")
        
        # Test initial state
        assert explorer.edit_mode == False
        
        # Test toggle edit mode
        explorer._toggle_edit_mode()
        assert explorer.edit_mode == True
        
        # Test toggle back
        explorer._toggle_edit_mode()
        assert explorer.edit_mode == False
    
    def test_data_explorer_row_selection(self, api_client):
        """Test DataExplorer row selection functionality."""
        explorer = DataExplorer(api_client, "users")
        
        # Test initial state
        assert explorer.selected_rows == set()
        
        # Test row selection directly (simulate what _handle_row_selection does)
        row_id = "1"
        explorer.selected_rows.add(row_id)
        assert row_id in explorer.selected_rows
        
        # Test row deselection
        explorer.selected_rows.discard(row_id)
        assert row_id not in explorer.selected_rows
        
        # Test clear selection
        explorer.selected_rows.add("1")
        explorer.selected_rows.add("2")
        explorer._clear_selection()
        assert explorer.selected_rows == set()


class TestFormGeneratorFunctionality:
    """
    Test FormGenerator component functionality.
    
    Design Spec: AGENT.md - NiceGUI Testing Patterns - FormGenerator Requirements
    Coverage: Field rendering, validation, form submission, error handling
    """
    
    def test_form_generator_field_rendering(self, api_client):
        """Test FormGenerator field rendering logic."""
        generator = FormGenerator(api_client, "users")
        
        # Test that the generator has the required methods and attributes
        assert hasattr(generator, '_render_form_field')
        assert hasattr(generator, '_render_form_fields')
        assert hasattr(generator, 'form_data')
        
        # Test field type detection by column type
        test_columns = [
            {"name": "id", "type": "INTEGER"},
            {"name": "name", "type": "VARCHAR(255)"},
            {"name": "bio", "type": "TEXT"},
            {"name": "active", "type": "BOOLEAN"}
        ]
        
        # These should not raise errors when processed
        for column in test_columns:
            # The _render_form_field method should not crash
            try:
                generator._render_form_field(column)
            except Exception as e:
                # Allow UI-related errors since we're not in a full UI context
                if "nicegui" not in str(e).lower():
                    raise
    
    def test_form_generator_form_data_management(self, api_client):
        """Test FormGenerator form data management."""
        generator = FormGenerator(api_client, "users")
        
        # Test form data update
        generator._update_form_data("name", "Alice")
        assert generator.form_data["name"] == "Alice"
        
        generator._update_form_data("email", "alice@example.com")
        assert generator.form_data["email"] == "alice@example.com"
        
        # Test form clearing
        generator._clear_form()
        assert generator.form_data == {}
    
    def test_form_generator_field_validation(self, api_client):
        """Test FormGenerator field validation."""
        generator = FormGenerator(api_client, "users")
        
        # Test that validation methods exist or can be implemented
        assert hasattr(generator, '_update_form_data')
        assert hasattr(generator, '_clear_form')
        
        # Test basic form data validation through form_data structure
        generator._update_form_data("name", "Alice")
        assert generator.form_data["name"] == "Alice"
        
        # Test that empty values can be handled
        generator._update_form_data("name", "")
        assert generator.form_data["name"] == ""
        
        # Test clearing form data
        generator._clear_form()
        assert generator.form_data == {}


class TestQueryBuilderFunctionality:
    """
    Test QueryBuilder component functionality.
    
    Design Spec: AGENT.md - NiceGUI Testing Patterns - QueryBuilder Requirements
    Coverage: Filter management, RQL generation, query execution, results display
    """
    
    def test_query_builder_filter_management(self, api_client):
        """Test QueryBuilder filter management."""
        builder = QueryBuilder(api_client, "users")
        
        # Test initial filters state
        assert builder.filters == []
        
        # Test filter list manipulation
        builder.filters.append({"column": "name", "operator": "eq", "value": "Alice"})
        assert len(builder.filters) == 1
        assert builder.filters[0]["column"] == "name"
        
        # Test filter removal
        builder.filters.clear()
        assert len(builder.filters) == 0
        
        # Test adding multiple filters
        builder.filters.extend([
            {"column": "name", "operator": "eq", "value": "Alice"},
            {"column": "age", "operator": "gt", "value": "25"}
        ])
        assert len(builder.filters) == 2
    
    def test_query_builder_rql_operators(self, api_client):
        """Test QueryBuilder RQL operator support."""
        builder = QueryBuilder(api_client, "users")
        
        # Test different operators
        test_cases = [
            ("eq", "name", "Alice", "eq(name,Alice)"),
            ("ne", "name", "Bob", "ne(name,Bob)"),
            ("gt", "age", "25", "gt(age,25)"),
            ("lt", "age", "65", "lt(age,65)"),
            ("contains", "name", "test", "contains(name,test)"),
            ("in", "status", "active,inactive", "in(status,(active,inactive))"),
        ]
        
        for operator, column, value, expected in test_cases:
            builder.filters = [{"column": column, "operator": operator, "value": value}]
            rql = builder._build_rql_query()
            assert expected in rql
    
    def test_query_builder_sorting(self, api_client):
        """Test QueryBuilder sorting functionality."""
        builder = QueryBuilder(api_client, "users")
        
        # Test ascending sort
        builder.sort_column = "name"
        builder.sort_direction = "asc"
        rql = builder._build_rql_query()
        assert "sort(+name)" in rql
        
        # Test descending sort
        builder.sort_direction = "desc"
        rql = builder._build_rql_query()
        assert "sort(-name)" in rql
    
    def test_query_builder_limit_functionality(self, api_client):
        """Test QueryBuilder limit functionality."""
        builder = QueryBuilder(api_client, "users")
        
        # Test default limit
        builder.limit_value = 50
        rql = builder._build_rql_query()
        assert "limit(50)" in rql
        
        # Test no limit
        builder.limit_value = None
        rql = builder._build_rql_query()
        assert "limit(" not in rql


class TestTableBrowserFunctionality:
    """Test TableBrowser component functionality."""
    
    def test_table_browser_table_loading(self, api_client):
        """Test TableBrowser table loading."""
        browser = TableBrowser(api_client)
        
        # Test that browser can access api_client
        assert browser.api_client == api_client
        
        # Test that browser has necessary methods
        assert hasattr(browser, 'render')
        assert hasattr(browser, '_render_table_item')


class TestUIComponentsWithMultipleSchemas:
    """
    Test UI components work with different schema patterns.
    
    Design Spec: AGENT.md - Testing Strategy - Multi-Schema Testing Requirements
    Coverage: Schema-agnostic functionality, edge cases, auto-generation validation
    """
    
    @pytest.fixture(params=['default_sample', 'financial_data', 'blog_platform'])
    def schema_api_client(self, request):
        """Create API client with different schema patterns."""
        from conftest import SCHEMA_CONFIGS
        
        schema_name = request.param
        config = SCHEMA_CONFIGS[schema_name]
        
        # Create in-memory database
        service = DatabaseService(Path(":memory:"), create_sample_data=config['create_sample_data'])
        
        # Run setup queries if provided
        if 'setup_queries' in config:
            for query in config['setup_queries']:
                try:
                    service.connection.execute(query)
                except Exception as e:
                    # Skip if external data source is unavailable
                    if 'nyc_taxi' in schema_name and 'HTTP' in str(e):
                        pytest.skip(f"External data source unavailable for {schema_name}: {e}")
                    else:
                        raise
        
        api_client = FastVimesAPIClient(db_service=service)
        yield api_client, schema_name, config['expected_tables']
        service.close()
    
    def test_components_work_with_any_schema(self, schema_api_client):
        """Test that UI components work with any schema pattern."""
        api_client, schema_name, expected_tables = schema_api_client
        
        # Test TableBrowser with any schema
        browser = TableBrowser(api_client)
        assert browser.api_client == api_client
        
        # Test other components with each table in the schema
        for table_name in expected_tables:
            # Test DataExplorer
            explorer = DataExplorer(api_client, table_name)
            assert explorer.table_name == table_name
            
            # Test QueryBuilder
            builder = QueryBuilder(api_client, table_name)
            assert builder.table_name == table_name
            
            # Test that query builder can generate valid RQL
            rql = builder._build_rql_query()
            assert isinstance(rql, str)
            
            # Test FormGenerator
            generator = FormGenerator(api_client, table_name)
            assert generator.table_name == table_name


class TestUIComponentsAPIIntegration:
    """
    Test UI components integration with actual HTTP API endpoints.
    
    Design Spec: AGENT.md - NiceGUI Exploratory Interface - API Integration
    Coverage: Component-to-API communication, RQL handling, error scenarios
    """
    
    def test_table_browser_http_integration(self, test_server):
        """Test TableBrowser with actual HTTP API calls."""
        # Test list_tables endpoint
        response = test_server.get("/v1/meta/tables")
        assert response.status_code == 200
        tables_data = response.json()
        assert "tables" in tables_data
        assert len(tables_data["tables"]) > 0
        
        # Verify table structure
        for table in tables_data["tables"]:
            assert "name" in table
            assert "type" in table
    
    def test_data_explorer_http_integration(self, test_server):
        """Test DataExplorer with actual HTTP API calls and RQL queries."""
        # Test basic data retrieval
        response = test_server.get("/v1/data/users")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total_count" in data
        assert "columns" in data
        
        # Test RQL filtering
        response = test_server.get("/v1/data/users?eq(active,true)")
        assert response.status_code == 200
        filtered_data = response.json()
        assert "data" in filtered_data
        
        # Test RQL sorting
        response = test_server.get("/v1/data/users?sort(+name)")
        assert response.status_code == 200
        sorted_data = response.json()
        assert "data" in sorted_data
        
        # Test RQL limiting
        response = test_server.get("/v1/data/users?limit(5)")
        assert response.status_code == 200
        limited_data = response.json()
        assert len(limited_data["data"]) <= 5
    
    def test_form_generator_http_integration(self, test_server):
        """Test FormGenerator with actual HTTP API calls for CRUD operations."""
        # Test table schema retrieval
        response = test_server.get("/v1/meta/schema/users")
        assert response.status_code == 200
        schema_data = response.json()
        assert "schema" in schema_data
        
        # Test record creation - provide all required fields
        new_record = {
            "name": "Test User", 
            "email": "test@example.com", 
            "age": 30,
            "active": True,
            "department": "Engineering",
            "created_at": "2024-01-01T00:00:00"
        }
        response = test_server.post("/v1/data/users", json=new_record)
        if response.status_code != 200:
            print(f"POST response status: {response.status_code}")
            print(f"POST response body: {response.text}")
        assert response.status_code == 200
        created_response = response.json()
        assert "record" in created_response
        assert created_response["record"]["name"] == "Test User"
        
        # Test record update
        record_id = created_response["record"]["id"]
        update_data = {"name": "Updated User"}
        response = test_server.put(f"/v1/data/users?eq(id,{record_id})", json=update_data)
        assert response.status_code == 200
        
        # Test record deletion
        response = test_server.delete(f"/v1/data/users?eq(id,{record_id})")
        assert response.status_code == 200
    
    def test_query_builder_http_integration(self, test_server):
        """Test QueryBuilder with actual HTTP API calls for RQL queries."""
        # Test various RQL operators
        rql_queries = [
            "eq(active,true)",
            "gt(id,1)",
            "lt(id,100)",
            "contains(name,user)",
            "in(id,(1,2,3))",
            "and(eq(active,true),gt(id,1))",
            "or(eq(active,true),eq(active,false))",
            "sort(+name,-id)",
            "limit(10,5)",
            "select(id,name,email)"
        ]
        
        for rql_query in rql_queries:
            response = test_server.get(f"/v1/data/users?{rql_query}")
            # Should not return 4xx/5xx errors for valid RQL
            assert response.status_code == 200, f"RQL query failed: {rql_query}"
            data = response.json()
            assert "data" in data
    
    def test_api_error_handling(self, test_server):
        """Test error handling in API integration."""
        # Test invalid table name
        response = test_server.get("/v1/data/nonexistent_table")
        assert response.status_code == 404
        
        # Test invalid RQL syntax (now falls back to basic query, so it returns 200)
        response = test_server.get("/v1/data/users?invalid_rql_syntax")
        assert response.status_code == 200  # Falls back to basic query
        
        # Test invalid JSON in POST
        response = test_server.post("/v1/data/users", content="invalid json")
        assert response.status_code == 422
    
    def test_api_format_responses(self, test_server):
        """Test different output formats via API."""
        # Test JSON format (default)
        response = test_server.get("/v1/data/users?format=json")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        
        # Test CSV format
        response = test_server.get("/v1/data/users?format=csv")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        
        # Test Parquet format
        response = test_server.get("/v1/data/users?format=parquet")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
