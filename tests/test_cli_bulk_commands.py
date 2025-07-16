"""
Test CLI bulk commands: bulk-insert, bulk-upsert, bulk-delete

Tests the CLI interface for bulk operations using subprocess calls.
Marked as slow since they use subprocess execution.
"""

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

from fastvimes.database_service import DatabaseService


@pytest.mark.slow
@pytest.mark.cli
class TestCLIBulkCommands:
    """Test CLI bulk commands through subprocess execution."""

    def run_cli_command(self, cmd: list[str]) -> subprocess.CompletedProcess:
        """Helper to run CLI commands and return result."""
        full_cmd = [sys.executable, "-m", "fastvimes.cli"] + cmd
        return subprocess.run(full_cmd, capture_output=True, text=True, timeout=30)

    def create_test_json_file(self, data: list[dict[str, Any]], temp_dir: Path) -> Path:
        """Create a temporary JSON file with test data."""
        json_file = temp_dir / "test_data.json"
        with open(json_file, "w") as f:
            json.dump(data, f)
        return json_file

    def create_test_csv_file(self, data: list[dict[str, Any]], temp_dir: Path) -> Path:
        """Create a temporary CSV file with test data."""
        csv_file = temp_dir / "test_data.csv"
        if data:
            fieldnames = data[0].keys()
            with open(csv_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
        return csv_file

    def create_test_parquet_file(
        self, data: list[dict[str, Any]], temp_dir: Path
    ) -> Path:
        """Create a temporary Parquet file with test data."""
        parquet_file = temp_dir / "test_data.parquet"
        # Use DuckDB to create parquet files since we don't have pandas/pyarrow
        import duckdb

        conn = duckdb.connect(":memory:")

        if data:
            # Create table from data
            conn.execute(
                "CREATE TABLE temp_table AS SELECT * FROM (VALUES "
                + ",".join(
                    [f"({','.join([repr(v) for v in row.values()])})" for row in data]
                )
                + f") AS t({','.join(data[0].keys())})"
            )

            # Export to parquet
            conn.execute(f"COPY temp_table TO '{parquet_file}' (FORMAT PARQUET)")

        return parquet_file

    def setup_test_database(self, temp_dir: Path) -> Path:
        """Set up a test database with sample data."""
        db_path = temp_dir / "test_bulk.db"

        # Initialize database with sample data
        result = self.run_cli_command(["init", str(db_path), "--force"])
        assert result.returncode == 0, f"Database init failed: {result.stderr}"

        return db_path

    def test_bulk_insert_json_file(self):
        """Test bulk-insert command with JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = self.setup_test_database(temp_path)

            # Create test data with unique emails (not conflicting with existing data)
            new_users = [
                {
                    "id": 100,
                    "name": "Alice Johnson New",
                    "email": "alice.bulk.new@example.com",
                    "age": 28,
                    "active": True,
                    "department": "Engineering",
                    "created_at": "2024-01-01 10:00:00",
                },
                {
                    "id": 101,
                    "name": "Bob Smith New",
                    "email": "bob.bulk.new@example.com",
                    "age": 35,
                    "active": True,
                    "department": "Marketing",
                    "created_at": "2024-01-01 11:00:00",
                },
            ]
            json_file = self.create_test_json_file(new_users, temp_path)

            # Run bulk-insert command
            result = self.run_cli_command(
                [
                    "data",
                    "bulk-insert",
                    "users",
                    "--file",
                    str(json_file),
                    "--db",
                    str(db_path),
                ]
            )

            assert result.returncode == 0, f"bulk-insert failed: {result.stderr}"
            assert "Successfully inserted 2 records" in result.stdout

    def test_bulk_insert_csv_file(self):
        """Test bulk-insert command with CSV file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = self.setup_test_database(temp_path)

            # Create test data (matching users schema with all 7 columns)
            new_users = [
                {
                    "id": 102,
                    "name": "Charlie Brown",
                    "email": "charlie.bulk.csv@example.com",
                    "age": 42,
                    "active": True,
                    "department": "Sales",
                    "created_at": "2024-01-01 12:00:00",
                },
                {
                    "id": 103,
                    "name": "Diana Prince",
                    "email": "diana.bulk.csv@example.com",
                    "age": 30,
                    "active": True,
                    "department": "HR",
                    "created_at": "2024-01-01 13:00:00",
                },
            ]
            csv_file = self.create_test_csv_file(new_users, temp_path)

            # Run bulk-insert command
            result = self.run_cli_command(
                [
                    "data",
                    "bulk-insert",
                    "users",
                    "--file",
                    str(csv_file),
                    "--db",
                    str(db_path),
                ]
            )

            assert result.returncode == 0, f"bulk-insert failed: {result.stderr}"
            assert "Successfully inserted 2 records" in result.stdout

    def test_bulk_insert_parquet_file(self):
        """Test bulk-insert command with Parquet file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = self.setup_test_database(temp_path)

            # Create test data (matching users schema with all 7 columns)
            new_users = [
                {
                    "id": 104,
                    "name": "Eve Adams",
                    "email": "eve.bulk.parquet@example.com",
                    "age": 26,
                    "active": True,
                    "department": "Design",
                    "created_at": "2024-01-01 14:00:00",
                },
                {
                    "id": 105,
                    "name": "Frank Wilson",
                    "email": "frank.bulk.parquet@example.com",
                    "age": 38,
                    "active": True,
                    "department": "Support",
                    "created_at": "2024-01-01 15:00:00",
                },
            ]
            parquet_file = self.create_test_parquet_file(new_users, temp_path)

            # Run bulk-insert command
            result = self.run_cli_command(
                [
                    "data",
                    "bulk-insert",
                    "users",
                    "--file",
                    str(parquet_file),
                    "--db",
                    str(db_path),
                ]
            )

            assert result.returncode == 0, f"bulk-insert failed: {result.stderr}"
            assert "Successfully inserted 2 records" in result.stdout

    def test_bulk_upsert_json_file(self):
        """Test bulk-upsert command with JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = self.setup_test_database(temp_path)

            # Create test data that will insert new records (avoiding existing IDs to prevent foreign key constraints)
            upsert_data = [
                {
                    "id": 901,
                    "name": "Updated User 1",
                    "email": "updated1.bulk.upsert@example.com",
                    "age": 99,
                    "active": False,
                    "department": "Updated",
                    "created_at": "2024-01-01 16:00:00",
                },
                {
                    "id": 902,
                    "name": "New User",
                    "email": "new.bulk.upsert@example.com",
                    "age": 25,
                    "active": True,
                    "department": "New",
                    "created_at": "2024-01-01 17:00:00",
                },
            ]
            json_file = self.create_test_json_file(upsert_data, temp_path)

            # Run bulk-upsert command
            result = self.run_cli_command(
                [
                    "data",
                    "bulk-upsert",
                    "users",
                    "--file",
                    str(json_file),
                    "--key-columns",
                    "id",
                    "--db",
                    str(db_path),
                ]
            )

            assert result.returncode == 0, f"bulk-upsert failed: {result.stderr}"
            assert "Successfully processed records" in result.stdout

    def test_bulk_upsert_csv_file(self):
        """Test bulk-upsert command with CSV file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = self.setup_test_database(temp_path)

            # Create test data for upsert (avoiding existing IDs to prevent foreign key constraints)
            upsert_data = [
                {
                    "id": 903,
                    "name": "Updated User 2",
                    "email": "updated2.bulk.csv@example.com",
                    "age": 88,
                    "active": False,
                    "department": "Updated2",
                    "created_at": "2024-01-01 18:00:00",
                },
                {
                    "id": 904,
                    "name": "Another New User",
                    "email": "another.bulk.csv@example.com",
                    "age": 33,
                    "active": True,
                    "department": "Another",
                    "created_at": "2024-01-01 19:00:00",
                },
            ]
            csv_file = self.create_test_csv_file(upsert_data, temp_path)

            # Run bulk-upsert command
            result = self.run_cli_command(
                [
                    "data",
                    "bulk-upsert",
                    "users",
                    "--file",
                    str(csv_file),
                    "--key-columns",
                    "id",
                    "--db",
                    str(db_path),
                ]
            )

            assert result.returncode == 0, f"bulk-upsert failed: {result.stderr}"
            assert "Successfully processed records" in result.stdout

    def test_bulk_delete_json_file(self):
        """Test bulk-delete command with JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = self.setup_test_database(temp_path)

            # First, add some records to delete (to ensure they exist without foreign key references)
            insert_data = [
                {
                    "id": 501,
                    "name": "Delete Me 1",
                    "email": "delete1.bulk@example.com",
                    "age": 30,
                    "active": True,
                    "department": "Temp",
                    "created_at": "2024-01-01 23:00:00",
                },
                {
                    "id": 502,
                    "name": "Delete Me 2",
                    "email": "delete2.bulk@example.com",
                    "age": 31,
                    "active": True,
                    "department": "Temp",
                    "created_at": "2024-01-01 23:01:00",
                },
            ]
            insert_file = self.create_test_json_file(insert_data, temp_path)

            # Insert the records first
            insert_result = self.run_cli_command(
                [
                    "data",
                    "bulk-insert",
                    "users",
                    "--file",
                    str(insert_file),
                    "--db",
                    str(db_path),
                ]
            )
            assert insert_result.returncode == 0, (
                f"bulk-insert failed: {insert_result.stderr}"
            )

            # Now create test data with IDs to delete
            delete_data = [{"id": 501}, {"id": 502}]
            json_file = self.create_test_json_file(delete_data, temp_path)

            # Run bulk-delete command
            result = self.run_cli_command(
                [
                    "data",
                    "bulk-delete",
                    "users",
                    "--file",
                    str(json_file),
                    "--key-columns",
                    "id",
                    "--confirm",
                    "--db",
                    str(db_path),
                ]
            )

            assert result.returncode == 0, f"bulk-delete failed: {result.stderr}"
            assert "Successfully deleted 2 records" in result.stdout

    def test_bulk_delete_csv_file(self):
        """Test bulk-delete command with CSV file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = self.setup_test_database(temp_path)

            # First, add some records to delete (to ensure they exist without foreign key references)
            insert_data = [
                {
                    "id": 503,
                    "name": "Delete Me 3",
                    "email": "delete3.bulk@example.com",
                    "age": 32,
                    "active": True,
                    "department": "Temp",
                    "created_at": "2024-01-01 23:02:00",
                },
                {
                    "id": 504,
                    "name": "Delete Me 4",
                    "email": "delete4.bulk@example.com",
                    "age": 33,
                    "active": True,
                    "department": "Temp",
                    "created_at": "2024-01-01 23:03:00",
                },
            ]
            insert_csv_file = self.create_test_csv_file(insert_data, temp_path)

            # Insert the records first
            insert_result = self.run_cli_command(
                [
                    "data",
                    "bulk-insert",
                    "users",
                    "--file",
                    str(insert_csv_file),
                    "--db",
                    str(db_path),
                ]
            )
            assert insert_result.returncode == 0, (
                f"bulk-insert failed: {insert_result.stderr}"
            )

            # Now create test data with IDs to delete
            delete_data = [{"id": 503}, {"id": 504}]
            csv_file = self.create_test_csv_file(delete_data, temp_path)

            # Run bulk-delete command
            result = self.run_cli_command(
                [
                    "data",
                    "bulk-delete",
                    "users",
                    "--file",
                    str(csv_file),
                    "--key-columns",
                    "id",
                    "--confirm",
                    "--db",
                    str(db_path),
                ]
            )

            assert result.returncode == 0, f"bulk-delete failed: {result.stderr}"
            assert "Successfully deleted 2 records" in result.stdout

    def test_bulk_insert_auto_format_detection(self):
        """Test that bulk-insert automatically detects file format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = self.setup_test_database(temp_path)

            # Create test data without specifying format (matching users schema with all 7 columns)
            new_users = [
                {
                    "id": 106,
                    "name": "Auto User 1",
                    "email": "auto1.bulk.format@example.com",
                    "age": 29,
                    "active": True,
                    "department": "Auto1",
                    "created_at": "2024-01-01 20:00:00",
                },
                {
                    "id": 107,
                    "name": "Auto User 2",
                    "email": "auto2.bulk.format@example.com",
                    "age": 31,
                    "active": True,
                    "department": "Auto2",
                    "created_at": "2024-01-01 21:00:00",
                },
            ]
            json_file = self.create_test_json_file(new_users, temp_path)

            # Run bulk-insert without format specification
            result = self.run_cli_command(
                [
                    "data",
                    "bulk-insert",
                    "users",
                    "--file",
                    str(json_file),
                    "--db",
                    str(db_path),
                ]
            )

            assert result.returncode == 0, f"bulk-insert failed: {result.stderr}"
            assert "Successfully inserted 2 records" in result.stdout

    def test_bulk_operations_error_handling(self):
        """Test error handling for bulk operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = self.setup_test_database(temp_path)

            # Test with non-existent file
            result = self.run_cli_command(
                [
                    "data",
                    "bulk-insert",
                    "users",
                    "--file",
                    "non_existent_file.json",
                    "--db",
                    str(db_path),
                ]
            )

            assert result.returncode != 0
            assert "Error" in result.stderr or "not found" in result.stderr.lower()

    def test_bulk_operations_with_multiple_key_columns(self):
        """Test bulk operations with multiple key columns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = self.setup_test_database(temp_path)

            # Create test data for multi-key upsert (matching users schema with all 7 columns)
            upsert_data = [
                {
                    "id": 108,
                    "name": "Multi Key User",
                    "email": "multi.bulk.keys@example.com",
                    "age": 40,
                    "active": True,
                    "department": "Multi",
                    "created_at": "2024-01-01 22:00:00",
                }
            ]
            json_file = self.create_test_json_file(upsert_data, temp_path)

            # Run bulk-upsert with multiple key columns
            result = self.run_cli_command(
                [
                    "data",
                    "bulk-upsert",
                    "users",
                    "--file",
                    str(json_file),
                    "--key-columns",
                    "name,email",
                    "--db",
                    str(db_path),
                ]
            )

            assert result.returncode == 0, f"bulk-upsert failed: {result.stderr}"
            assert "Successfully processed records" in result.stdout

    def test_bulk_operations_with_nonexistent_table(self):
        """Test bulk operations with non-existent table."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = self.setup_test_database(temp_path)

            # Create test data
            test_data = [{"field": "value"}]
            json_file = self.create_test_json_file(test_data, temp_path)

            # Run bulk-insert on non-existent table
            result = self.run_cli_command(
                [
                    "data",
                    "bulk-insert",
                    "nonexistent_table",
                    "--file",
                    str(json_file),
                    "--db",
                    str(db_path),
                ]
            )

            assert result.returncode != 0
            assert "Error" in result.stderr or "not found" in result.stderr.lower()


@pytest.mark.slow
@pytest.mark.cli
class TestCLIBulkCommandsMultiSchema:
    """Test CLI bulk commands with different database schemas."""

    def run_cli_command(self, cmd: list[str]) -> subprocess.CompletedProcess:
        """Helper to run CLI commands and return result."""
        full_cmd = [sys.executable, "-m", "fastvimes.cli"] + cmd
        return subprocess.run(full_cmd, capture_output=True, text=True, timeout=30)

    def create_test_json_file(self, data: list[dict[str, Any]], temp_dir: Path) -> Path:
        """Create a temporary JSON file with test data."""
        json_file = temp_dir / "test_data.json"
        with open(json_file, "w") as f:
            json.dump(data, f)
        return json_file

    def setup_custom_database(
        self, temp_dir: Path, schema_type: str = "custom"
    ) -> Path:
        """Set up a custom database schema for testing."""
        db_path = temp_dir / f"test_bulk_{schema_type}.db"

        # Create a database with custom schema
        db_service = DatabaseService(str(db_path))

        if schema_type == "custom":
            # Create custom tables with different naming patterns
            db_service.execute_query("""
                CREATE TABLE custom_table (
                    custom_id INTEGER PRIMARY KEY,
                    custom_name TEXT NOT NULL,
                    custom_value DOUBLE,
                    custom_flag BOOLEAN
                )
            """)

            db_service.execute_query("""
                INSERT INTO custom_table (custom_id, custom_name, custom_value, custom_flag)
                VALUES
                    (1, 'Item 1', 100.5, true),
                    (2, 'Item 2', 200.7, false),
                    (3, 'Item 3', 300.9, true)
            """)

        return db_path

    def test_bulk_operations_with_custom_schema(self):
        """Test bulk operations work with custom schema and table names."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = self.setup_custom_database(temp_path, "custom")

            # Create test data matching custom schema
            new_data = [
                {
                    "custom_id": 10,
                    "custom_name": "New Item 1",
                    "custom_value": 150.5,
                    "custom_flag": True,
                },
                {
                    "custom_id": 11,
                    "custom_name": "New Item 2",
                    "custom_value": 250.7,
                    "custom_flag": False,
                },
            ]
            json_file = self.create_test_json_file(new_data, temp_path)

            # Run bulk-insert on custom table
            result = self.run_cli_command(
                [
                    "data",
                    "bulk-insert",
                    "custom_table",
                    "--file",
                    str(json_file),
                    "--db",
                    str(db_path),
                ]
            )

            assert result.returncode == 0, f"bulk-insert failed: {result.stderr}"
            assert "Successfully inserted 2 records" in result.stdout

            # Test bulk-upsert on custom table
            upsert_data = [
                {
                    "custom_id": 1,
                    "custom_name": "Updated Item 1",
                    "custom_value": 999.9,
                    "custom_flag": False,
                }
            ]
            upsert_file = self.create_test_json_file(upsert_data, temp_path)

            result = self.run_cli_command(
                [
                    "data",
                    "bulk-upsert",
                    "custom_table",
                    "--file",
                    str(upsert_file),
                    "--key-columns",
                    "custom_id",
                    "--db",
                    str(db_path),
                ]
            )

            assert result.returncode == 0, f"bulk-upsert failed: {result.stderr}"
            assert "Successfully processed records" in result.stdout

            # Test bulk-delete on custom table
            delete_data = [{"custom_id": 2}]
            delete_file = self.create_test_json_file(delete_data, temp_path)

            result = self.run_cli_command(
                [
                    "data",
                    "bulk-delete",
                    "custom_table",
                    "--file",
                    str(delete_file),
                    "--key-columns",
                    "custom_id",
                    "--confirm",
                    "--db",
                    str(db_path),
                ]
            )

            assert result.returncode == 0, f"bulk-delete failed: {result.stderr}"
            assert "Successfully deleted 1 records" in result.stdout
