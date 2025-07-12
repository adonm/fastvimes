"""Tests for HTMX fragment vs standalone rendering functionality."""

import pytest
from fastapi.testclient import TestClient
from fastvimes.app import FastVimes


@pytest.fixture
def app_with_data():
    """Create FastVimes app with test data."""
    app = FastVimes(db_path=":memory:")
    
    # Create test table with data
    app.db_service.connection.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(50),
            email VARCHAR(100),
            active BOOLEAN
        )
    """)
    
    app.db_service.connection.execute("""
        INSERT INTO users (id, name, email, active) VALUES
        (1, 'Alice', 'alice@example.com', true),
        (2, 'Bob', 'bob@example.com', true),
        (3, 'Charlie', 'charlie@example.com', false)
    """)
    
    # Refresh table discovery and routes
    app.db_service._discover_tables()
    app._setup_table_routes()
    
    return app


class TestHTMXFragments:
    """Test HTMX fragment detection and rendering."""
    
    def test_api_html_standalone_request(self, app_with_data):
        """Test /api/{table}/html returns full HTML page for standalone requests."""
        client = TestClient(app_with_data)
        
        response = client.get("/api/users/html")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        
        content = response.text
        # Should contain full HTML structure for standalone
        assert "<html" in content
        assert "<head>" in content
        assert "<body>" in content
        assert "users" in content.lower()
        assert "alice" in content.lower()
    
    def test_api_html_htmx_fragment_request(self, app_with_data):
        """Test /api/{table}/html returns fragment for HTMX requests."""
        client = TestClient(app_with_data)
        
        response = client.get("/api/users/html", headers={"HX-Request": "true"})
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        
        content = response.text
        # Should NOT contain full HTML structure for fragments
        assert "<html" not in content
        assert "<head>" not in content
        assert "<body>" not in content
        # Should contain table data
        assert "alice" in content.lower()
        assert "bob" in content.lower()
        assert "rows:" in content.lower()
    
    def test_admin_table_context_includes_filter_form(self, app_with_data):
        """Test admin context includes filter form in API endpoint."""
        client = TestClient(app_with_data)
        
        response = client.get("/api/users/html?admin=true")
        
        assert response.status_code == 200
        content = response.text
        
        # Should contain filter form in admin context
        assert 'name="rql"' in content
        assert "Filter Data" in content
        assert 'action="/api/users/html"' in content
        assert 'name="admin" value="true"' in content
        
        # Should contain actual table data (immediate rendering, not HTMX loading)
        assert "<td>1</td>" in content.lower()
        assert "<td>alice</td>" in content.lower()
        assert "<td>bob</td>" in content.lower()
    
    def test_api_html_without_admin_context(self, app_with_data):
        """Test API HTML endpoint without admin context has no filter form."""
        client = TestClient(app_with_data)
        
        response = client.get("/api/users/html")
        
        assert response.status_code == 200
        content = response.text
        
        # Should NOT contain filter form in non-admin context
        assert "Filter Data" not in content
        assert 'name="rql"' not in content
        
        # Should still contain table data
        assert "<td>alice</td>" in content.lower()
        assert "<td>bob</td>" in content.lower()
    
    def test_admin_context_with_rql_filtering(self, app_with_data):
        """Test admin context with RQL filtering preserves admin state."""
        client = TestClient(app_with_data)
        
        response = client.get("/api/users/html?admin=true&rql=eq(active,true)")
        
        assert response.status_code == 200
        content = response.text
        
        # Should show filtered data (only active users)
        assert "<td>alice</td>" in content.lower()
        assert "<td>bob</td>" in content.lower()
        assert "<td>charlie</td>" not in content.lower()  # Charlie is inactive
        
        # Should preserve RQL query in filter form
        assert 'value="eq(active,true)"' in content
        # Should maintain admin context
        assert 'name="admin" value="true"' in content
    
    def test_api_html_empty_table(self, app_with_data):
        """Test API HTML endpoint handles empty tables correctly."""
        # Create empty table
        app_with_data.db_service.connection.execute("""
            CREATE TABLE empty_table (
                id INTEGER PRIMARY KEY,
                name VARCHAR(50)
            )
        """)
        
        # Refresh table discovery and routes
        app_with_data.db_service._discover_tables()
        app_with_data._setup_table_routes()
        
        client = TestClient(app_with_data)
        
        # Test standalone request
        response = client.get("/api/empty_table/html")
        assert response.status_code == 200
        assert "empty" in response.text.lower()
        
        # Test HTMX fragment request
        response = client.get("/api/empty_table/html", headers={"HX-Request": "true"})
        assert response.status_code == 200
        assert "empty" in response.text.lower()
    
    def test_admin_context_vs_regular_rendering(self, app_with_data):
        """Test admin context vs regular API access produces different content."""
        client = TestClient(app_with_data)
        
        # Test regular API access
        response = client.get("/api/users/html")
        assert response.status_code == 200
        regular_content = response.text
        
        # Should contain full HTML structure but no filter form
        assert "<html" in regular_content
        assert "<head>" in regular_content
        assert "Filter Data" not in regular_content
        
        # Test admin context API access
        response = client.get("/api/users/html?admin=true")
        assert response.status_code == 200
        admin_content = response.text
        
        # Should contain full HTML structure AND filter form
        assert "<html" in admin_content
        assert "<head>" in admin_content
        assert "Filter Data" in admin_content
        assert 'name="admin" value="true"' in admin_content


class TestHTMXIntegration:
    """Test end-to-end HTMX integration."""
    
    def test_admin_context_integrates_with_htmx_fragments(self, app_with_data):
        """Test that admin context works with HTMX fragment requests."""
        client = TestClient(app_with_data)
        
        # First, get the admin context page
        admin_response = client.get("/api/users/html?admin=true")
        assert admin_response.status_code == 200
        assert "Filter Data" in admin_response.text
        
        # Then simulate an HTMX fragment call
        fragment_response = client.get("/api/users/html", headers={"HX-Request": "true"})
        assert fragment_response.status_code == 200
        
        fragment_content = fragment_response.text
        # Fragment should contain table data but no full HTML structure
        assert "alice" in fragment_content.lower()
        assert "bob" in fragment_content.lower()
        assert "charlie" in fragment_content.lower()
        assert "<html" not in fragment_content
        assert "<head>" not in fragment_content
    
    def test_filtered_data_via_htmx(self, app_with_data):
        """Test that filtered queries work via HTMX."""
        client = TestClient(app_with_data)
        
        # Test filtering active users
        response = client.get(
            "/api/users/html?eq(active,true)", 
            headers={"HX-Request": "true"}
        )
        assert response.status_code == 200
        
        content = response.text
        # Should contain only active users
        assert "alice" in content.lower()
        assert "bob" in content.lower()
        assert "charlie" not in content.lower()  # Charlie is inactive
        assert "rows: 2" in content.lower()
    
    def test_error_handling_in_htmx_fragments(self, app_with_data):
        """Test error handling in HTMX fragment requests."""
        client = TestClient(app_with_data)
        
        # Test invalid table
        response = client.get("/api/nonexistent/html", headers={"HX-Request": "true"})
        assert response.status_code == 404  # Table doesn't exist
        
        # Test invalid RQL - system handles gracefully
        response = client.get(
            "/api/users/html?invalid_rql", 
            headers={"HX-Request": "true"}
        )
        assert response.status_code == 200  # System handles invalid RQL gracefully


@pytest.mark.slow
class TestHTMXPerformance:
    """Test performance characteristics of HTMX vs standalone rendering."""
    
    def test_fragment_response_smaller_than_standalone(self, app_with_data):
        """Test that HTMX fragments are smaller than standalone responses."""
        client = TestClient(app_with_data)
        
        # Get standalone response
        standalone_response = client.get("/api/users/html")
        standalone_size = len(standalone_response.text)
        
        # Get fragment response
        fragment_response = client.get("/api/users/html", headers={"HX-Request": "true"})
        fragment_size = len(fragment_response.text)
        
        # Fragment should be significantly smaller
        assert fragment_size < standalone_size
        # Should be at least 50% smaller due to no full HTML structure
        assert fragment_size < standalone_size * 0.5
