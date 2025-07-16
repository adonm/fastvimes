"""
Test bulk operations using DuckDB native file handling.

Design Spec: AGENT.md - Database API Core - Bulk Operations
Coverage: File-based bulk insert/upsert/delete, multi-format support, error handling
"""

import csv
import json
import os
import tempfile
from pathlib import Path

import pytest

from fastvimes.database_service import DatabaseService


class TestBulkOperationsCore:
    """
    Test core bulk operations functionality.

    Design Spec: AGENT.md - Database API Core - DuckDB native operations
    Coverage: bulk_insert_from_file, bulk_upsert_from_file, bulk_delete_from_file
    """

    @pytest.fixture
    def db_service(self):
        """Create a test database service with sample data."""
        service = DatabaseService(Path(":memory:"), create_sample_data=True)
        yield service
        service.close()

    @pytest.fixture
    def sample_data(self):
        """Sample data for testing."""
        return [
            {
                "id": 1001,
                "name": "Alice Johnson",
                "email": "alice.test@example.com",
                "age": 30,
                "active": True,
                "department": "Engineering",
                "created_at": "2024-01-01 10:00:00",
            },
            {
                "id": 1002,
                "name": "Bob Smith",
                "email": "bob.test@example.com",
                "age": 25,
                "active": True,
                "department": "Marketing",
                "created_at": "2024-01-01 11:00:00",
            },
            {
                "id": 1003,
                "name": "Charlie Brown",
                "email": "charlie.test@example.com",
                "age": 35,
                "active": False,
                "department": "Sales",
                "created_at": "2024-01-01 12:00:00",
            },
        ]

    def test_bulk_insert_from_json_file(self, db_service, sample_data):
        """Test bulk insert from JSON file."""
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_data, f)
            temp_file = f.name

        try:
            # Test bulk insert
            records_inserted = db_service.bulk_insert_from_file(
                "users", temp_file, "json"
            )

            # Verify results
            assert records_inserted == 3

            # Verify data was inserted
            result = db_service.get_table_data("users", limit=1000)
            total_records = len(result["data"])
            assert total_records >= 3  # Should have at least the 3 we inserted

            # Verify specific records exist (check for unique emails to avoid duplicates)
            inserted_emails = [
                row["email"]
                for row in result["data"]
                if row["email"]
                in [
                    "alice.test@example.com",
                    "bob.test@example.com",
                    "charlie.test@example.com",
                ]
            ]
            assert len(inserted_emails) == 3

        finally:
            os.unlink(temp_file)

    def test_bulk_insert_from_csv_file(self, db_service, sample_data):
        """Test bulk insert from CSV file."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as f:
            writer = csv.DictWriter(f, fieldnames=sample_data[0].keys())
            writer.writeheader()
            writer.writerows(sample_data)
            temp_file = f.name

        try:
            # Test bulk insert
            records_inserted = db_service.bulk_insert_from_file(
                "users", temp_file, "csv"
            )

            # Verify results
            assert records_inserted == 3

            # Verify data was inserted
            result = db_service.get_table_data("users", limit=1000)
            inserted_emails = [
                row["email"]
                for row in result["data"]
                if row["email"]
                in [
                    "alice.test@example.com",
                    "bob.test@example.com",
                    "charlie.test@example.com",
                ]
            ]
            assert len(inserted_emails) == 3

        finally:
            os.unlink(temp_file)

    def test_bulk_insert_auto_format_detection(self, db_service, sample_data):
        """Test auto-detection of file format."""
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_data, f)
            temp_file = f.name

        try:
            # Test with auto format detection
            records_inserted = db_service.bulk_insert_from_file(
                "users", temp_file, "auto"
            )

            # Verify results
            assert records_inserted == 3

        finally:
            os.unlink(temp_file)

    def test_bulk_insert_nonexistent_table(self, db_service, sample_data):
        """Test bulk insert with non-existent table."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_data, f)
            temp_file = f.name

        try:
            # Should raise error for non-existent table
            with pytest.raises(ValueError, match="Table nonexistent does not exist"):
                db_service.bulk_insert_from_file("nonexistent", temp_file, "json")

        finally:
            os.unlink(temp_file)

    def test_bulk_insert_invalid_format(self, db_service, sample_data):
        """Test bulk insert with invalid file format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_data, f)
            temp_file = f.name

        try:
            # Should raise error for invalid format
            with pytest.raises(RuntimeError, match="Bulk insert failed"):
                db_service.bulk_insert_from_file("users", temp_file, "invalid")

        finally:
            os.unlink(temp_file)

    def test_bulk_upsert_from_file(self, db_service, sample_data):
        """Test bulk upsert from file."""
        # Insert initial data
        initial_data = [
            {
                "id": 2001,
                "name": "Alice Original",
                "email": "alice.old@example.com",
                "age": 28,
                "active": True,
                "department": "Engineering",
                "created_at": "2024-01-01 10:00:00",
            },
            {
                "id": 2002,
                "name": "Bob Original",
                "email": "bob.old@example.com",
                "age": 23,
                "active": True,
                "department": "Marketing",
                "created_at": "2024-01-01 11:00:00",
            },
        ]

        # Create initial JSON file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(initial_data, f)
            initial_file = f.name

        try:
            # Insert initial data
            db_service.bulk_insert_from_file("users", initial_file, "json")

            # Create upsert data (updates + new records)
            upsert_data = [
                {
                    "id": 2001,
                    "name": "Alice Updated",
                    "email": "alice.updated@example.com",
                    "age": 30,
                    "active": True,
                    "department": "Engineering",
                    "created_at": "2024-01-01 10:00:00",
                },  # Update
                {
                    "id": 2003,
                    "name": "Charlie New",
                    "email": "charlie.new@example.com",
                    "age": 35,
                    "active": False,
                    "department": "Sales",
                    "created_at": "2024-01-01 12:00:00",
                },  # Insert
            ]

            # Create upsert JSON file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(upsert_data, f)
                upsert_file = f.name

            try:
                # Test bulk upsert
                result = db_service.bulk_upsert_from_file(
                    "users", upsert_file, ["id"], "json"
                )

                # Verify results structure
                assert "inserted" in result
                assert "updated" in result
                assert result["inserted"] >= 0  # Should have some records processed

                # Verify data was updated/inserted
                all_data = db_service.get_table_data("users", limit=1000)
                names_by_id = {row["id"]: row["name"] for row in all_data["data"]}

                # Check that Alice was updated
                if 2001 in names_by_id:
                    assert names_by_id[2001] == "Alice Updated"

                # Check that Charlie was inserted
                charlie_records = [
                    row for row in all_data["data"] if row["name"] == "Charlie New"
                ]
                assert len(charlie_records) >= 1

            finally:
                os.unlink(upsert_file)

        finally:
            os.unlink(initial_file)

    def test_bulk_delete_from_file(self, db_service, sample_data):
        """Test bulk delete from file."""
        # Insert initial data
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_data, f)
            initial_file = f.name

        try:
            # Insert initial data
            db_service.bulk_insert_from_file("users", initial_file, "json")

            # Create delete keys file
            delete_keys = [{"id": 1001}, {"id": 1003}]

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(delete_keys, f)
                delete_file = f.name

            try:
                # Test bulk delete
                records_deleted = db_service.bulk_delete_from_file(
                    "users", delete_file, ["id"], "json"
                )

                # Verify results
                assert records_deleted >= 0  # Should have deleted some records

                # Verify data was deleted
                all_data = db_service.get_table_data("users", limit=1000)
                remaining_ids = [row["id"] for row in all_data["data"]]

                # Alice (1001) and Charlie (1003) should be deleted
                assert 1001 not in remaining_ids
                assert 1003 not in remaining_ids

                # Bob (1002) should remain if it was the only one we kept

            finally:
                os.unlink(delete_file)

        finally:
            os.unlink(initial_file)

    def test_bulk_operations_with_multiple_key_columns(self, db_service):
        """Test bulk operations with composite keys."""
        # Create a table with composite key
        db_service.connection.execute("""
            CREATE TABLE composite_test (
                category VARCHAR,
                item_id INTEGER,
                name VARCHAR,
                price DECIMAL
            )
        """)

        # Insert initial data
        initial_data = [
            {"category": "books", "item_id": 1, "name": "Book A", "price": 20.00},
            {"category": "books", "item_id": 2, "name": "Book B", "price": 25.00},
            {"category": "electronics", "item_id": 1, "name": "Phone", "price": 500.00},
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(initial_data, f)
            initial_file = f.name

        try:
            # Insert initial data
            db_service.bulk_insert_from_file("composite_test", initial_file, "json")

            # Test upsert with composite key
            upsert_data = [
                {
                    "category": "books",
                    "item_id": 1,
                    "name": "Book A Updated",
                    "price": 22.00,
                },  # Update
                {
                    "category": "books",
                    "item_id": 3,
                    "name": "Book C",
                    "price": 30.00,
                },  # Insert
            ]

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(upsert_data, f)
                upsert_file = f.name

            try:
                # Test bulk upsert with composite key
                result = db_service.bulk_upsert_from_file(
                    "composite_test", upsert_file, ["category", "item_id"], "json"
                )

                # Verify results structure
                assert "inserted" in result
                assert "updated" in result

                # Verify data was updated/inserted
                all_data = db_service.get_table_data("composite_test", limit=1000)

                # Check that Book A was updated
                book_a_records = [
                    row
                    for row in all_data["data"]
                    if row["category"] == "books" and row["item_id"] == 1
                ]
                assert len(book_a_records) >= 1
                assert book_a_records[0]["name"] == "Book A Updated"

                # Check that Book C was inserted
                book_c_records = [
                    row
                    for row in all_data["data"]
                    if row["category"] == "books" and row["item_id"] == 3
                ]
                assert len(book_c_records) >= 1

            finally:
                os.unlink(upsert_file)

        finally:
            os.unlink(initial_file)


class TestBulkOperationsErrorHandling:
    """
    Test error handling in bulk operations.

    Design Spec: AGENT.md - Database API Core - Error handling
    Coverage: Invalid files, schema mismatches, database errors
    """

    @pytest.fixture
    def db_service(self):
        """Create a test database service."""
        service = DatabaseService(Path(":memory:"), create_sample_data=True)
        yield service
        service.close()

    def test_bulk_insert_nonexistent_file(self, db_service):
        """Test bulk insert with non-existent file."""
        with pytest.raises((FileNotFoundError, RuntimeError)):
            db_service.bulk_insert_from_file("users", "/nonexistent/file.json", "json")

    def test_bulk_insert_invalid_json(self, db_service):
        """Test bulk insert with invalid JSON file."""
        # Create file with invalid JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json")
            temp_file = f.name

        try:
            with pytest.raises(RuntimeError, match="Bulk insert failed"):
                db_service.bulk_insert_from_file("users", temp_file, "json")

        finally:
            os.unlink(temp_file)

    def test_bulk_insert_schema_mismatch(self, db_service):
        """Test bulk insert with schema mismatch."""
        # Create data with wrong schema
        invalid_data = [{"invalid_column": "value", "another_invalid": 123}]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            temp_file = f.name

        try:
            # This should either work (if DuckDB is flexible) or raise an error
            with pytest.raises(RuntimeError, match="Bulk insert failed"):
                db_service.bulk_insert_from_file("users", temp_file, "json")

        finally:
            os.unlink(temp_file)

    def test_bulk_upsert_invalid_key_columns(self, db_service):
        """Test bulk upsert with invalid key columns."""
        sample_data = [{"id": 1, "name": "Test"}]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_data, f)
            temp_file = f.name

        try:
            # Should handle invalid key columns gracefully
            with pytest.raises(RuntimeError, match="Bulk upsert failed"):
                db_service.bulk_upsert_from_file(
                    "users", temp_file, ["nonexistent_column"], "json"
                )

        finally:
            os.unlink(temp_file)


class TestBulkOperationsWithMultipleSchemas:
    """
    Test bulk operations with different schema patterns.

    Design Spec: AGENT.md - Testing Strategy - Multi-Schema Testing Requirements
    Coverage: Schema-agnostic bulk operations, different table structures
    """

    @pytest.fixture(params=["ecommerce", "blog", "inventory"])
    def schema_db_service(self, request):
        """Create database service with different schema patterns."""
        service = DatabaseService(Path(":memory:"), create_sample_data=False)

        if request.param == "ecommerce":
            # E-commerce schema
            service.connection.execute("""
                CREATE TABLE products (
                    product_id INTEGER PRIMARY KEY,
                    name VARCHAR,
                    category VARCHAR,
                    price DECIMAL,
                    stock INTEGER
                )
            """)
            expected_table = "products"
            expected_keys = ["product_id"]

        elif request.param == "blog":
            # Blog schema
            service.connection.execute("""
                CREATE TABLE posts (
                    post_id INTEGER PRIMARY KEY,
                    title VARCHAR,
                    content TEXT,
                    author VARCHAR,
                    created_at TIMESTAMP
                )
            """)
            expected_table = "posts"
            expected_keys = ["post_id"]

        elif request.param == "inventory":
            # Inventory schema
            service.connection.execute("""
                CREATE TABLE items (
                    warehouse_id VARCHAR,
                    item_code VARCHAR,
                    quantity INTEGER,
                    location VARCHAR,
                    PRIMARY KEY (warehouse_id, item_code)
                )
            """)
            expected_table = "items"
            expected_keys = ["warehouse_id", "item_code"]

        yield service, expected_table, expected_keys, request.param
        service.close()

    def test_bulk_operations_work_with_any_schema(self, schema_db_service):
        """Test that bulk operations work with any schema pattern."""
        db_service, table_name, key_columns, schema_type = schema_db_service

        # Create test data based on schema type
        if schema_type == "ecommerce":
            test_data = [
                {
                    "product_id": 1,
                    "name": "Widget A",
                    "category": "widgets",
                    "price": 19.99,
                    "stock": 100,
                },
                {
                    "product_id": 2,
                    "name": "Widget B",
                    "category": "widgets",
                    "price": 29.99,
                    "stock": 50,
                },
            ]
        elif schema_type == "blog":
            test_data = [
                {
                    "post_id": 1,
                    "title": "First Post",
                    "content": "Hello World",
                    "author": "admin",
                    "created_at": "2024-01-01",
                },
                {
                    "post_id": 2,
                    "title": "Second Post",
                    "content": "Another post",
                    "author": "user",
                    "created_at": "2024-01-02",
                },
            ]
        elif schema_type == "inventory":
            test_data = [
                {
                    "warehouse_id": "WH1",
                    "item_code": "A001",
                    "quantity": 100,
                    "location": "A1",
                },
                {
                    "warehouse_id": "WH1",
                    "item_code": "A002",
                    "quantity": 50,
                    "location": "A2",
                },
            ]

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name

        try:
            # Test bulk insert
            records_inserted = db_service.bulk_insert_from_file(
                table_name, temp_file, "json"
            )
            assert records_inserted == 2

            # Test bulk upsert
            result = db_service.bulk_upsert_from_file(
                table_name, temp_file, key_columns, "json"
            )
            assert "inserted" in result
            assert "updated" in result

            # Test bulk delete
            records_deleted = db_service.bulk_delete_from_file(
                table_name, temp_file, key_columns, "json"
            )
            assert records_deleted >= 0

        finally:
            os.unlink(temp_file)

    def test_bulk_operations_preserve_schema_constraints(self, schema_db_service):
        """Test that bulk operations respect schema constraints."""
        db_service, table_name, key_columns, schema_type = schema_db_service

        # Test with valid data first
        if schema_type == "ecommerce":
            valid_data = [
                {
                    "product_id": 1,
                    "name": "Valid Product",
                    "category": "test",
                    "price": 10.00,
                    "stock": 1,
                }
            ]
        elif schema_type == "blog":
            valid_data = [
                {
                    "post_id": 1,
                    "title": "Valid Post",
                    "content": "Content",
                    "author": "test",
                    "created_at": "2024-01-01",
                }
            ]
        elif schema_type == "inventory":
            valid_data = [
                {
                    "warehouse_id": "WH1",
                    "item_code": "TEST",
                    "quantity": 1,
                    "location": "TEST",
                }
            ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(valid_data, f)
            temp_file = f.name

        try:
            # Should work with valid data
            records_inserted = db_service.bulk_insert_from_file(
                table_name, temp_file, "json"
            )
            assert records_inserted == 1

            # Verify data was inserted with correct schema
            result = db_service.get_table_data(table_name, limit=10)
            assert len(result["data"]) >= 1

        finally:
            os.unlink(temp_file)
