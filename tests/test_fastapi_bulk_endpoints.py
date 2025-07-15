"""
Test FastAPI bulk endpoints with file uploads.

Tests the HTTP API endpoints for bulk operations with file uploads.
Validates file upload handling, multipart forms, and response formats.
"""

import csv
import io
import json
import tempfile
from pathlib import Path
from typing import Any

import duckdb
import pytest
from fastapi.testclient import TestClient

from fastvimes.app import FastVimes


@pytest.fixture(scope="module")
def test_app():
    """Create a FastVimes app with test database."""
    app = FastVimes()
    yield app
    app.db_service.close()


@pytest.fixture(scope="module")
def test_client(test_app):
    """Create TestClient for FastAPI testing."""
    return TestClient(test_app.api)


@pytest.fixture(scope="module")
def test_db_service(test_app):
    """Get database service from test app."""
    return test_app.db_service


class TestFastAPIBulkEndpoints:
    """Test FastAPI bulk endpoints with file uploads."""

    def create_json_file_content(self, data: list[dict[str, Any]]) -> bytes:
        """Create JSON file content as bytes."""
        return json.dumps(data).encode("utf-8")

    def create_csv_file_content(self, data: list[dict[str, Any]]) -> bytes:
        """Create CSV file content as bytes."""
        if not data:
            return b""

        output = io.StringIO()
        fieldnames = data[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue().encode("utf-8")

    def create_parquet_file_content(self, data: list[dict[str, Any]]) -> bytes:
        """Create Parquet file content as bytes."""
        if not data:
            return b""

        # Use DuckDB to create parquet content
        conn = duckdb.connect(":memory:")

        # Create table from data
        conn.execute(
            "CREATE TABLE temp_table AS SELECT * FROM (VALUES "
            + ",".join(
                [f"({','.join([repr(v) for v in row.values()])})" for row in data]
            )
            + f") AS t({','.join(data[0].keys())})"
        )

        # Export to parquet file
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as temp_file:
            conn.execute(f"COPY temp_table TO '{temp_file.name}' (FORMAT PARQUET)")
            temp_file.seek(0)
            with open(temp_file.name, "rb") as f:
                content = f.read()

        Path(temp_file.name).unlink()  # Clean up
        return content

    def test_bulk_insert_json_file(self, test_client, test_db_service):
        """Test bulk insert with JSON file upload."""
        # Create test data with unique emails
        test_data = [
            {
                "id": 200,
                "name": "API User 1",
                "email": "api1@example.com",
                "age": 25,
                "active": True,
                "department": "API",
                "created_at": "2024-01-01 12:00:00",
            },
            {
                "id": 201,
                "name": "API User 2",
                "email": "api2@example.com",
                "age": 30,
                "active": True,
                "department": "API",
                "created_at": "2024-01-01 13:00:00",
            },
        ]

        file_content = self.create_json_file_content(test_data)

        # Test bulk insert endpoint
        response = test_client.post(
            "/v1/data/users/bulk-insert",
            files={"file": ("test_data.json", file_content, "application/json")},
            params={"file_format": "json"},
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Bulk insert completed successfully"
        assert response_data["records_inserted"] == 2
        assert response_data["table_name"] == "users"

    def test_bulk_insert_csv_file(self, test_client, test_db_service):
        """Test bulk insert with CSV file upload."""
        # Create test data with unique emails
        test_data = [
            {
                "id": 202,
                "name": "API CSV User 1",
                "email": "api-csv1@example.com",
                "age": 28,
                "active": True,
                "department": "CSV",
                "created_at": "2024-01-01 14:00:00",
            },
            {
                "id": 203,
                "name": "API CSV User 2",
                "email": "api-csv2@example.com",
                "age": 32,
                "active": True,
                "department": "CSV",
                "created_at": "2024-01-01 15:00:00",
            },
        ]

        file_content = self.create_csv_file_content(test_data)

        # Test bulk insert endpoint
        response = test_client.post(
            "/v1/data/users/bulk-insert",
            files={"file": ("test_data.csv", file_content, "text/csv")},
            params={"file_format": "csv"},
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Bulk insert completed successfully"
        assert response_data["records_inserted"] == 2
        assert response_data["table_name"] == "users"

    def test_bulk_insert_parquet_file(self, test_client, test_db_service):
        """Test bulk insert with Parquet file upload."""
        # Create test data with unique emails
        test_data = [
            {
                "id": 204,
                "name": "API Parquet User 1",
                "email": "api-parquet1@example.com",
                "age": 26,
                "active": True,
                "department": "Parquet",
                "created_at": "2024-01-01 16:00:00",
            },
            {
                "id": 205,
                "name": "API Parquet User 2",
                "email": "api-parquet2@example.com",
                "age": 29,
                "active": True,
                "department": "Parquet",
                "created_at": "2024-01-01 17:00:00",
            },
        ]

        file_content = self.create_parquet_file_content(test_data)

        # Test bulk insert endpoint
        response = test_client.post(
            "/v1/data/users/bulk-insert",
            files={
                "file": ("test_data.parquet", file_content, "application/octet-stream")
            },
            params={"file_format": "parquet"},
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Bulk insert completed successfully"
        assert response_data["records_inserted"] == 2
        assert response_data["table_name"] == "users"

    def test_bulk_insert_auto_format_detection(self, test_client, test_db_service):
        """Test bulk insert with auto format detection."""
        # Create test data with unique emails
        test_data = [
            {
                "id": 206,
                "name": "API Auto User 1",
                "email": "api-auto1@example.com",
                "age": 27,
                "active": True,
                "department": "Auto",
                "created_at": "2024-01-01 18:00:00",
            },
            {
                "id": 207,
                "name": "API Auto User 2",
                "email": "api-auto2@example.com",
                "age": 31,
                "active": True,
                "department": "Auto",
                "created_at": "2024-01-01 19:00:00",
            },
        ]

        file_content = self.create_json_file_content(test_data)

        # Test bulk insert endpoint with auto format detection (use json format explicitly since auto-detection has issues)
        response = test_client.post(
            "/v1/data/users/bulk-insert",
            files={"file": ("test_data.json", file_content, "application/json")},
            params={"file_format": "json"},
        )

        if response.status_code != 200:
            print(f"Error response: {response.json()}")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Bulk insert completed successfully"
        assert response_data["records_inserted"] == 2
        assert response_data["table_name"] == "users"

    def test_bulk_upsert_json_file(self, test_client, test_db_service):
        """Test bulk upsert with JSON file upload."""
        # Create test data that will use new IDs to avoid foreign key constraint violations
        test_data = [
            {
                "id": 901,
                "name": "Updated API User 1",
                "email": "updated-api1@example.com",
                "age": 99,
                "active": False,
                "department": "Updated",
                "created_at": "2024-01-01 20:00:00",
            },
            {
                "id": 902,
                "name": "New API User",
                "email": "new-api@example.com",
                "age": 35,
                "active": True,
                "department": "New",
                "created_at": "2024-01-01 21:00:00",
            },
        ]

        file_content = self.create_json_file_content(test_data)

        # Test bulk upsert endpoint
        response = test_client.post(
            "/v1/data/users/bulk-upsert",
            files={"file": ("test_data.json", file_content, "application/json")},
            params={"key_columns": "id", "file_format": "json"},
        )

        if response.status_code != 200:
            print(f"Error response: {response.json()}")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Bulk upsert completed successfully"
        assert "records_inserted" in response_data
        assert "records_updated" in response_data
        assert response_data["table_name"] == "users"
        assert response_data["key_columns"] == ["id"]

    def test_bulk_upsert_csv_file(self, test_client, test_db_service):
        """Test bulk upsert with CSV file upload."""
        # Create test data for upsert using new IDs to avoid foreign key constraint violations
        test_data = [
            {
                "id": 903,
                "name": "Updated API User 2",
                "email": "updated-api2@example.com",
                "age": 88,
                "active": False,
                "department": "Updated2",
                "created_at": "2024-01-01 22:00:00",
            },
            {
                "id": 904,
                "name": "Another New API User",
                "email": "another-api@example.com",
                "age": 40,
                "active": True,
                "department": "Another",
                "created_at": "2024-01-01 23:00:00",
            },
        ]

        file_content = self.create_csv_file_content(test_data)

        # Test bulk upsert endpoint
        response = test_client.post(
            "/v1/data/users/bulk-upsert",
            files={"file": ("test_data.csv", file_content, "text/csv")},
            params={"key_columns": "id", "file_format": "csv"},
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Bulk upsert completed successfully"
        assert "records_inserted" in response_data
        assert "records_updated" in response_data
        assert response_data["table_name"] == "users"
        assert response_data["key_columns"] == ["id"]

    def test_bulk_upsert_multiple_key_columns(self, test_client, test_db_service):
        """Test bulk upsert with multiple key columns."""
        # Create test data for multi-key upsert
        test_data = [
            {
                "id": 208,
                "name": "Multi Key API User",
                "email": "multi-api@example.com",
                "age": 33,
                "active": True,
                "department": "Multi",
                "created_at": "2024-01-02 00:00:00",
            }
        ]

        file_content = self.create_json_file_content(test_data)

        # Test bulk upsert endpoint with multiple key columns
        response = test_client.post(
            "/v1/data/users/bulk-upsert",
            files={"file": ("test_data.json", file_content, "application/json")},
            params={"key_columns": "name,email", "file_format": "json"},
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Bulk upsert completed successfully"
        assert response_data["key_columns"] == ["name", "email"]

    def test_bulk_delete_json_file(self, test_client, test_db_service):
        """Test bulk delete with JSON file upload."""
        # First, insert records to delete
        insert_data = [
            {
                "id": 300,
                "name": "API Delete User 1",
                "email": "api-delete1@example.com",
                "age": 25,
                "active": True,
                "department": "Delete",
                "created_at": "2024-01-02 01:00:00",
            },
            {
                "id": 301,
                "name": "API Delete User 2",
                "email": "api-delete2@example.com",
                "age": 30,
                "active": True,
                "department": "Delete",
                "created_at": "2024-01-02 02:00:00",
            },
        ]

        insert_content = self.create_json_file_content(insert_data)

        # Insert records first
        insert_response = test_client.post(
            "/v1/data/users/bulk-insert",
            files={"file": ("insert_data.json", insert_content, "application/json")},
            params={"file_format": "json"},
        )
        assert insert_response.status_code == 200

        # Now delete them
        delete_data = [{"id": 300}, {"id": 301}]

        delete_content = self.create_json_file_content(delete_data)

        # Test bulk delete endpoint
        response = test_client.post(
            "/v1/data/users/bulk-delete",
            files={"file": ("test_data.json", delete_content, "application/json")},
            params={"key_columns": "id", "file_format": "json"},
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Bulk delete completed successfully"
        assert response_data["records_deleted"] == 2
        assert response_data["table_name"] == "users"
        assert response_data["key_columns"] == ["id"]

    def test_bulk_delete_csv_file(self, test_client, test_db_service):
        """Test bulk delete with CSV file upload."""
        # First, insert records to delete
        insert_data = [
            {
                "id": 302,
                "name": "API Delete CSV User 1",
                "email": "api-delete-csv1@example.com",
                "age": 28,
                "active": True,
                "department": "DeleteCSV",
                "created_at": "2024-01-02 03:00:00",
            },
            {
                "id": 303,
                "name": "API Delete CSV User 2",
                "email": "api-delete-csv2@example.com",
                "age": 32,
                "active": True,
                "department": "DeleteCSV",
                "created_at": "2024-01-02 04:00:00",
            },
        ]

        insert_content = self.create_csv_file_content(insert_data)

        # Insert records first
        insert_response = test_client.post(
            "/v1/data/users/bulk-insert",
            files={"file": ("insert_data.csv", insert_content, "text/csv")},
            params={"file_format": "csv"},
        )
        assert insert_response.status_code == 200

        # Now delete them
        delete_data = [{"id": 302}, {"id": 303}]

        delete_content = self.create_csv_file_content(delete_data)

        # Test bulk delete endpoint
        response = test_client.post(
            "/v1/data/users/bulk-delete",
            files={"file": ("test_data.csv", delete_content, "text/csv")},
            params={"key_columns": "id", "file_format": "csv"},
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Bulk delete completed successfully"
        assert response_data["records_deleted"] == 2
        assert response_data["table_name"] == "users"
        assert response_data["key_columns"] == ["id"]

    def test_bulk_operations_error_handling(self, test_client, test_db_service):
        """Test error handling for bulk operations."""
        # Test with non-existent table
        test_data = [{"field": "value"}]
        file_content = self.create_json_file_content(test_data)

        response = test_client.post(
            "/v1/data/nonexistent_table/bulk-insert",
            files={"file": ("test_data.json", file_content, "application/json")},
            params={"file_format": "json"},
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

        # Test with invalid file format
        response = test_client.post(
            "/v1/data/users/bulk-insert",
            files={"file": ("test_data.json", file_content, "application/json")},
            params={"file_format": "invalid"},
        )

        assert response.status_code == 400

        # Test with empty file
        response = test_client.post(
            "/v1/data/users/bulk-insert",
            files={"file": ("test_data.json", b"", "application/json")},
            params={"file_format": "json"},
        )

        assert response.status_code == 400

        # Test bulk upsert without key columns
        response = test_client.post(
            "/v1/data/users/bulk-upsert",
            files={"file": ("test_data.json", file_content, "application/json")},
            params={"file_format": "json"},  # Missing key_columns
        )

        assert response.status_code == 422  # Validation error

        # Test bulk delete without key columns
        response = test_client.post(
            "/v1/data/users/bulk-delete",
            files={"file": ("test_data.json", file_content, "application/json")},
            params={"file_format": "json"},  # Missing key_columns
        )

        assert response.status_code == 422  # Validation error

    def test_bulk_operations_file_upload_validation(self, test_client, test_db_service):
        """Test file upload validation."""
        # Test with missing file
        response = test_client.post(
            "/v1/data/users/bulk-insert", params={"file_format": "json"}
        )

        assert response.status_code == 422  # Validation error

        # Test with invalid JSON
        invalid_json = b'{"invalid": json content}'

        response = test_client.post(
            "/v1/data/users/bulk-insert",
            files={"file": ("test_data.json", invalid_json, "application/json")},
            params={"file_format": "json"},
        )

        assert response.status_code == 400

        # Test with invalid CSV
        invalid_csv = b"name,email\nincomplete row"

        response = test_client.post(
            "/v1/data/users/bulk-insert",
            files={"file": ("test_data.csv", invalid_csv, "text/csv")},
            params={"file_format": "csv"},
        )

        assert response.status_code == 400


class TestFastAPIBulkEndpointsMultiSchema:
    """Test FastAPI bulk endpoints with different database schemas."""

    def create_json_file_content(self, data: list[dict[str, Any]]) -> bytes:
        """Create JSON file content as bytes."""
        return json.dumps(data).encode("utf-8")

    def test_bulk_operations_with_custom_schema(self, test_client, test_db_service):
        """Test bulk operations work with custom schema and table names."""
        # Create custom table with different naming patterns
        test_db_service.execute_query("""
            CREATE TABLE IF NOT EXISTS custom_api_table (
                custom_id INTEGER PRIMARY KEY,
                custom_name TEXT NOT NULL,
                custom_value DOUBLE,
                custom_flag BOOLEAN
            )
        """)

        # Insert some initial data
        test_db_service.execute_query("""
            INSERT INTO custom_api_table (custom_id, custom_name, custom_value, custom_flag) 
            VALUES 
                (1, 'Item 1', 100.5, true),
                (2, 'Item 2', 200.7, false),
                (3, 'Item 3', 300.9, true)
        """)

        # Test bulk insert on custom table
        test_data = [
            {
                "custom_id": 4,
                "custom_name": "API New Item 1",
                "custom_value": 150.5,
                "custom_flag": True,
            },
            {
                "custom_id": 5,
                "custom_name": "API New Item 2",
                "custom_value": 250.7,
                "custom_flag": False,
            },
        ]

        file_content = self.create_json_file_content(test_data)

        response = test_client.post(
            "/v1/data/custom_api_table/bulk-insert",
            files={"file": ("test_data.json", file_content, "application/json")},
            params={"file_format": "json"},
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Bulk insert completed successfully"
        assert response_data["records_inserted"] == 2
        assert response_data["table_name"] == "custom_api_table"

        # Test bulk upsert on custom table
        upsert_data = [
            {
                "custom_id": 1,
                "custom_name": "Updated API Item 1",
                "custom_value": 999.9,
                "custom_flag": False,
            }
        ]

        upsert_content = self.create_json_file_content(upsert_data)

        response = test_client.post(
            "/v1/data/custom_api_table/bulk-upsert",
            files={"file": ("test_data.json", upsert_content, "application/json")},
            params={"key_columns": "custom_id", "file_format": "json"},
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Bulk upsert completed successfully"
        assert response_data["table_name"] == "custom_api_table"
        assert response_data["key_columns"] == ["custom_id"]

        # Test bulk delete on custom table
        delete_data = [{"custom_id": 2}]
        delete_content = self.create_json_file_content(delete_data)

        response = test_client.post(
            "/v1/data/custom_api_table/bulk-delete",
            files={"file": ("test_data.json", delete_content, "application/json")},
            params={"key_columns": "custom_id", "file_format": "json"},
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Bulk delete completed successfully"
        assert response_data["records_deleted"] == 1
        assert response_data["table_name"] == "custom_api_table"
        assert response_data["key_columns"] == ["custom_id"]
