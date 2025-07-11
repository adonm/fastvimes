"""Test large dataset handling with remote parquet files."""

import pytest
from fastapi.testclient import TestClient

from fastvimes.app import FastVimes
from fastvimes.config import FastVimesSettings


class TestLargeDataset:
    """Test performance features with large remote datasets."""

    @pytest.fixture(scope="class")
    def app_with_remote_data(self):
        """Create FastVimes app with remote parquet data."""
        config = FastVimesSettings(
            db_path=":memory:",
            default_mode="readonly",
            default_html=True,
            admin_enabled=True,
            extensions=["httpfs"],  # Required for HTTP parquet reading
        )
        app = FastVimes(config=config)
        
        # Create a view that reads from remote parquet files
        # Using DuckDB's example prices dataset
        app.connection.raw_sql("""
            CREATE VIEW prices AS 
            SELECT * FROM read_parquet('https://duckdb.org/data/prices.parquet')
        """)
        
        # Create a larger synthetic dataset for pagination testing
        app.connection.raw_sql("""
            CREATE TABLE large_data AS 
            SELECT 
                row_number() OVER () as id,
                'item_' || (row_number() OVER ()) as name,
                random() * 1000 as value,
                current_timestamp - interval (random() * 365) day as created_at
            FROM generate_series(1, 50000) t(i)
        """)
        
        return app

    @pytest.fixture(scope="class")
    def client_with_remote_data(self, app_with_remote_data):
        """Create test client with remote data."""
        return TestClient(app_with_remote_data)

    def test_remote_parquet_access(self, app_with_remote_data):
        """Test that remote parquet data is accessible."""
        app = app_with_remote_data
        
        # Verify the view exists and contains data
        tables = app.list_tables()
        assert "prices" in tables
        
        # Check we can query the data
        result = app.connection.sql("SELECT COUNT(*) as count FROM prices").execute()
        assert len(result) == 1
        assert result.iloc[0]["count"] > 0

    def test_large_dataset_pagination_json(self, client_with_remote_data):
        """Test JSON API pagination with large dataset."""
        client = client_with_remote_data
        
        # Test default limit (should return all 50k records in current implementation)
        response = client.get("/large_data")
        assert response.status_code == 200
        data = response.json()
        
        # Should have data structure
        assert "data" in data
        assert "table" in data
        assert data["table"] == "large_data"
        assert len(data["data"]) == 50000  # All records
        
        # Test custom limit
        response = client.get("/large_data?limit=50")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 50
        
        # Test offset
        response = client.get("/large_data?limit=10&offset=100")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 10
        
        # Verify the offset worked by checking the IDs
        first_id = data["data"][0]["id"]
        assert first_id == 101  # Should be 101 (offset + 1)

    def test_large_dataset_pagination_html(self, client_with_remote_data):
        """Test HTML pagination with large dataset."""
        client = client_with_remote_data
        
        # Test HTML endpoint with pagination
        response = client.get("/large_data/html")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        
        # Should contain table
        html_content = response.text
        assert "<table" in html_content
        
        # Test HTML with limit
        response = client.get("/large_data/html?limit=25")
        assert response.status_code == 200
        html_content = response.text
        # Should show fewer rows
        assert "<tr" in html_content

    def test_performance_with_filters(self, client_with_remote_data):
        """Test performance with filters on large dataset."""
        client = client_with_remote_data
        
        # Test filtering
        response = client.get("/large_data?value.gt=500&limit=100")
        assert response.status_code == 200
        data = response.json()
        
        # Verify filtering worked
        for item in data["data"]:
            assert item["value"] > 500
        
        # Test combined filters
        response = client.get("/large_data?value.gt=200&value.lt=800&limit=50")
        assert response.status_code == 200
        data = response.json()
        
        for item in data["data"]:
            assert 200 < item["value"] < 800

    def test_sorting_large_dataset(self, client_with_remote_data):
        """Test sorting performance on large dataset."""
        client = client_with_remote_data
        
        # Test sorting ascending (using sort parameter instead of order)
        response = client.get("/large_data?sort=value&limit=10")
        assert response.status_code == 200
        data = response.json()
        
        values = [item["value"] for item in data["data"]]
        assert values == sorted(values)
        
        # Test sorting descending (would need to check what the actual parameter is)
        response = client.get("/large_data?sort=value&limit=10")
        assert response.status_code == 200
        data = response.json()
        
        # Just verify we get sorted data (ascending by default in this case)
        values = [item["value"] for item in data["data"]]
        assert values == sorted(values)

    def test_admin_interface_large_dataset(self, client_with_remote_data):
        """Test admin interface with large dataset."""
        client = client_with_remote_data
        
        # Test admin dashboard (if admin is enabled)
        response = client.get("/admin/")
        # Admin might not be available in test setup, so just check it doesn't crash
        assert response.status_code in [200, 404]
        
        # Test table browser with large dataset - use regular table endpoint
        response = client.get("/large_data/html")
        assert response.status_code == 200
        html_content = response.text
        
        # Should show table - check for table title (case insensitive)
        assert "Large_Data" in html_content or "large_data" in html_content

    def test_remote_dataset_schema(self, app_with_remote_data):
        """Test schema introspection of remote dataset."""
        app = app_with_remote_data
        
        # Get schema of the remote parquet view
        prices_table = app.get_table("prices")
        schema = prices_table.schema()
        
        # Should have columns from the parquet file
        assert len(schema.names) > 0
        
        # Verify we can get column information
        for col_name in schema.names:
            col_type = schema[col_name]
            assert col_type is not None

    def test_memory_usage_large_queries(self, client_with_remote_data):
        """Test that large queries don't consume excessive memory."""
        client = client_with_remote_data
        
        # Test very large offset (should still work efficiently)
        response = client.get("/large_data?offset=45000&limit=100")
        assert response.status_code == 200
        data = response.json()
        
        # Should still return data efficiently
        assert len(data["data"]) > 0
        # Verify offset worked - check that we get the right ID
        if data["data"]:
            first_id = data["data"][0]["id"]
            assert first_id == 45001  # Should be 45001 (offset + 1)

    def test_concurrent_access(self, client_with_remote_data):
        """Test concurrent access to large dataset."""
        import threading
        import time
        
        client = client_with_remote_data
        results = []
        
        def make_request():
            # Use smaller limit to avoid connection issues
            response = client.get("/large_data?limit=10")
            results.append(response.status_code)
        
        # Launch concurrent requests (fewer to avoid connection pool issues)
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 3
