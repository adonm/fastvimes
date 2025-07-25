"""Database service for DuckLake operations with RQL support.

This service provides the core business logic with a clear public API.

SCHEMA INTROSPECTION VERBS:

META OPERATIONS (exposed via /api/v1/meta/* and fastvimes meta):
- list_tables() -> List[Dict[str, Any]]
- get_table_schema(table_name: str) -> List[Dict[str, Any]]
- execute_query(query: str, params: List[Any]) -> List[Dict[str, Any]]

DATA OPERATIONS (exposed via /api/v1/data/* and fastvimes data):
- get_table_data(table_name, rql_query, limit, offset, format) -> Dict[str, Any] | bytes
- create_record(table_name: str, data: Dict[str, Any]) -> Dict[str, Any]
- update_records(table_name: str, data: Dict[str, Any], filters: Dict[str, Any]) -> int
- delete_records(table_name: str, filters: Dict[str, Any]) -> int

SUPPORTED OUTPUT FORMATS:
- Python objects (fetchall) → JSON in HTTP APIs
- Parquet files (DuckDB native: duckdb.sql().write_parquet())
- CSV files (DuckDB native: duckdb.sql().write_csv())

SUPPORTED INPUT FORMATS (future bulk operations):
- JSON (single records and arrays)
- Parquet files (DuckDB native: INSERT INTO table SELECT * FROM 'file.parquet')
- CSV files (DuckDB native: INSERT INTO table SELECT * FROM 'file.csv')

PRIVATE METHODS (internal implementation):
- _create_connection() -> duckdb.DuckDBPyConnection
- _create_sample_data() -> None
- _get_table_count(table_name: str) -> int
- _get_table_data_fallback(...) -> Dict[str, Any]
"""

import time
from pathlib import Path
from typing import Any

import duckdb

from .rql_to_sql import convert_rql_to_sql


class DatabaseService:
    """Service for database operations using DuckLake backend.

    Public methods provide the API surface exposed via CLI/FastAPI/NiceGUI.
    Private methods (prefixed with _) are internal implementation details.
    """

    def __init__(self, db_path: Path, create_sample_data: bool = False):
        """Initialize database service with DuckLake connection."""
        self.db_path = db_path
        self.connection = self._create_connection()

        if create_sample_data:
            self._create_sample_data()

    # =============================================================================
    # PRIVATE METHODS - Internal implementation details
    # =============================================================================

    def _create_connection(self) -> duckdb.DuckDBPyConnection:
        """Create DuckLake connection.

        For now, this uses DuckDB directly. Will be upgraded to DuckLake
        once the Python SDK is available.
        """
        if self.db_path == Path(":memory:"):
            return duckdb.connect(":memory:")
        else:
            return duckdb.connect(str(self.db_path))

    def _create_sample_data(self):
        """Create sample tables with realistic demo data."""
        # Create users table
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                age INTEGER,
                active BOOLEAN DEFAULT true,
                department VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create products table
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                category VARCHAR(50),
                price DECIMAL(10,2),
                stock_quantity INTEGER DEFAULT 0,
                active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create orders table
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'pending',
                total_amount DECIMAL(10,2),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # Insert sample users
        users_data = [
            (
                1,
                "Alice Johnson",
                "alice@example.com",
                28,
                True,
                "Engineering",
                "2024-01-15",
            ),
            (2, "Bob Smith", "bob@example.com", 34, True, "Marketing", "2024-02-20"),
            (
                3,
                "Carol Davis",
                "carol@example.com",
                25,
                True,
                "Engineering",
                "2024-03-10",
            ),
            (4, "David Wilson", "david@example.com", 42, False, "Sales", "2024-01-05"),
            (5, "Eva Brown", "eva@example.com", 31, True, "Design", "2024-04-12"),
            (
                6,
                "Frank Miller",
                "frank@example.com",
                29,
                True,
                "Engineering",
                "2024-02-28",
            ),
            (7, "Grace Lee", "grace@example.com", 36, True, "Marketing", "2024-03-15"),
            (
                8,
                "Henry Taylor",
                "henry@example.com",
                27,
                True,
                "Engineering",
                "2024-01-20",
            ),
        ]

        for user in users_data:
            self.connection.execute(
                "INSERT OR IGNORE INTO users (id, name, email, age, active, department, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                user,
            )

        # Insert sample products
        products_data = [
            (1, 'Laptop Pro 15"', "Electronics", 1299.99, 25, True, "2024-01-01"),
            (2, "Wireless Mouse", "Electronics", 29.99, 150, True, "2024-01-05"),
            (3, "Standing Desk", "Furniture", 399.99, 12, True, "2024-01-10"),
            (4, "Ergonomic Chair", "Furniture", 249.99, 8, True, "2024-01-15"),
            (5, "USB-C Cable", "Electronics", 19.99, 200, True, "2024-01-20"),
            (6, 'Monitor 27"', "Electronics", 299.99, 18, True, "2024-02-01"),
            (7, "Keyboard Mechanical", "Electronics", 129.99, 45, True, "2024-02-05"),
            (8, "Desk Lamp", "Furniture", 79.99, 32, True, "2024-02-10"),
            (9, "Notebook Pack", "Office", 12.99, 100, False, "2024-02-15"),
            (10, "Webcam HD", "Electronics", 89.99, 22, True, "2024-03-01"),
        ]

        for product in products_data:
            self.connection.execute(
                "INSERT OR IGNORE INTO products (id, name, category, price, stock_quantity, active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                product,
            )

        # Insert sample orders
        orders_data = [
            (1, 1, 1, 1, "2024-03-01", "completed", 1299.99),
            (2, 2, 2, 2, "2024-03-02", "completed", 59.98),
            (3, 3, 3, 1, "2024-03-03", "pending", 399.99),
            (4, 1, 5, 3, "2024-03-04", "completed", 59.97),
            (5, 4, 6, 1, "2024-03-05", "cancelled", 299.99),
            (6, 5, 7, 1, "2024-03-06", "completed", 129.99),
            (7, 2, 8, 2, "2024-03-07", "pending", 159.98),
            (8, 6, 1, 1, "2024-03-08", "completed", 1299.99),
            (9, 7, 10, 1, "2024-03-09", "completed", 89.99),
            (10, 8, 4, 1, "2024-03-10", "pending", 249.99),
        ]

        for order in orders_data:
            self.connection.execute(
                "INSERT OR IGNORE INTO orders (id, user_id, product_id, quantity, order_date, status, total_amount) VALUES (?, ?, ?, ?, ?, ?, ?)",
                order,
            )

    # =============================================================================
    # PUBLIC API METHODS - Exposed via CLI/FastAPI/NiceGUI
    # =============================================================================

    def list_tables(self) -> list[dict[str, Any]]:
        """List all tables and views in the database."""
        query = """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = 'main'
        ORDER BY table_name
        """
        result = self.connection.execute(query).fetchall()
        return [{"name": row[0], "type": row[1].lower()} for row in result]

    def get_table_schema(self, table_name: str) -> list[dict[str, Any]]:
        """Get schema information for a table."""
        query = f"DESCRIBE {table_name}"
        result = self.connection.execute(query).fetchall()
        return [
            {
                "name": row[0],
                "type": row[1],
                "nullable": row[2] == "YES",
                "key": row[3] if len(row) > 3 else None,
            }
            for row in result
        ]

    def get_table_data(
        self,
        table_name: str,
        rql_query: str | None = None,
        limit: int | None = 100,
        offset: int | None = 0,
        format: str = "json",
    ) -> dict[str, Any] | bytes:
        """Get table data with optional RQL filtering using safe SQL generation."""
        import sqlglot
        from sqlglot import exp

        sql_params = None
        if rql_query and rql_query.strip():
            # Use RQL to SQL converter for complex queries
            try:
                sql, params = convert_rql_to_sql(table_name, rql_query)

                # Check if RQL query already has LIMIT/OFFSET
                parsed_query = sqlglot.parse_one(sql, dialect="duckdb")
                has_rql_limit = parsed_query.find(exp.Limit) is not None
                has_rql_offset = parsed_query.find(exp.Offset) is not None

                # Only apply function-level pagination if RQL doesn't have its own
                if limit and not has_rql_limit:
                    parsed_query = parsed_query.limit(limit)
                if offset and not has_rql_offset:
                    parsed_query = parsed_query.offset(offset)

                final_sql = parsed_query.sql(dialect="duckdb")
                result = self.connection.execute(final_sql, params).fetchall()
                # Get column names from the result we just executed
                columns = [desc[0] for desc in self.connection.description]
                sql_params = (final_sql, params)  # Mark that RQL was successful

            except (ValueError, Exception) as e:
                # Fallback to basic query without RQL if parsing fails
                print(f"Warning: RQL parsing failed, falling back to basic query: {e}")
                sql_params = None  # Fall through to basic query logic

        if sql_params is not None:
            # RQL was successful, get count from the same query
            final_sql, params = sql_params

            # Get count without pagination for total_count
            count_sql, count_params = convert_rql_to_sql(table_name, rql_query)
            count_query = sqlglot.parse_one(count_sql, dialect="duckdb")

            # Build COUNT query properly
            if count_query.find(exp.Where):
                where_clause = count_query.find(exp.Where)
                count_query = (
                    sqlglot.select(sqlglot.func("COUNT", "*"))
                    .from_(table_name)
                    .where(where_clause.this)
                )
            else:
                count_query = sqlglot.select(sqlglot.func("COUNT", "*")).from_(
                    table_name
                )

            count_sql = count_query.sql(dialect="duckdb")
            total_count = self.connection.execute(count_sql, count_params).fetchone()[0]

        else:
            # RQL failed or not provided, use basic query
            query = sqlglot.select("*").from_(table_name)
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)

            sql = query.sql(dialect="duckdb")
            try:
                result = self.connection.execute(sql).fetchall()
                # Get column names from the result we just executed
                columns = [desc[0] for desc in self.connection.description]
                total_count = self._get_table_count(table_name)
            except Exception as e:
                raise ValueError(
                    f"Table '{table_name}' not found or query failed: {e}"
                ) from e

        data = [dict(zip(columns, row, strict=False)) for row in result]

        # Handle different output formats
        if format.lower() == "json":
            return {"columns": columns, "data": data, "total_count": total_count}
        elif format.lower() == "csv":
            return self._export_to_csv(columns, data)
        elif format.lower() == "parquet":
            return self._export_to_parquet(columns, data)
        else:
            raise ValueError(
                f"Unsupported format: {format}. Supported formats: json, csv, parquet"
            )

    def _export_to_csv(self, columns: list[str], data: list[dict[str, Any]]) -> bytes:
        """Export data to CSV format using DuckDB native functionality."""
        import os
        import tempfile

        # Create temporary table with the data
        temp_table = f"temp_export_{id(data)}"

        try:
            # Create temp table
            if data:
                # Create table from first row to get schema
                sample_row = data[0]
                column_defs = []
                for col in columns:
                    value = sample_row.get(col)
                    if isinstance(value, int):
                        col_type = "INTEGER"
                    elif isinstance(value, float):
                        col_type = "DOUBLE"
                    elif isinstance(value, bool):
                        col_type = "BOOLEAN"
                    else:
                        col_type = "VARCHAR"
                    column_defs.append(f"{col} {col_type}")

                create_sql = (
                    f"CREATE TEMP TABLE {temp_table} ({', '.join(column_defs)})"
                )
                self.connection.execute(create_sql)

                # Insert data
                placeholders = ", ".join(["?" for _ in columns])
                insert_sql = f"INSERT INTO {temp_table} VALUES ({placeholders})"
                for row in data:
                    values = [row.get(col) for col in columns]
                    self.connection.execute(insert_sql, values)

                # Export to CSV using DuckDB
                with tempfile.NamedTemporaryFile(
                    mode="w+b", suffix=".csv", delete=False
                ) as f:
                    temp_file = f.name

                try:
                    export_sql = (
                        f"COPY {temp_table} TO '{temp_file}' (FORMAT CSV, HEADER)"
                    )
                    self.connection.execute(export_sql)

                    # Read the file back
                    with open(temp_file, "rb") as f:
                        return f.read()
                finally:
                    os.unlink(temp_file)
            else:
                # Empty data - return CSV header only
                header = ",".join(columns) + "\n"
                return header.encode("utf-8")

        finally:
            # Clean up temp table
            try:
                self.connection.execute(f"DROP TABLE IF EXISTS {temp_table}")
            except Exception:
                pass

    def _export_to_parquet(
        self, columns: list[str], data: list[dict[str, Any]]
    ) -> bytes:
        """Export data to Parquet format using DuckDB native functionality."""
        import os
        import tempfile

        # Create temporary table with the data
        temp_table = f"temp_export_{id(data)}"

        try:
            if data:
                # Create table from first row to get schema
                sample_row = data[0]
                column_defs = []
                for col in columns:
                    value = sample_row.get(col)
                    if isinstance(value, int):
                        col_type = "INTEGER"
                    elif isinstance(value, float):
                        col_type = "DOUBLE"
                    elif isinstance(value, bool):
                        col_type = "BOOLEAN"
                    else:
                        col_type = "VARCHAR"
                    column_defs.append(f"{col} {col_type}")

                create_sql = (
                    f"CREATE TEMP TABLE {temp_table} ({', '.join(column_defs)})"
                )
                self.connection.execute(create_sql)

                # Insert data
                placeholders = ", ".join(["?" for _ in columns])
                insert_sql = f"INSERT INTO {temp_table} VALUES ({placeholders})"
                for row in data:
                    values = [row.get(col) for col in columns]
                    self.connection.execute(insert_sql, values)

                # Export to Parquet using DuckDB
                with tempfile.NamedTemporaryFile(
                    mode="w+b", suffix=".parquet", delete=False
                ) as f:
                    temp_file = f.name

                try:
                    export_sql = f"COPY {temp_table} TO '{temp_file}' (FORMAT PARQUET)"
                    self.connection.execute(export_sql)

                    # Read the file back
                    with open(temp_file, "rb") as f:
                        return f.read()
                finally:
                    os.unlink(temp_file)
            else:
                # Empty data - create minimal Parquet with schema
                import io

                import pyarrow as pa
                import pyarrow.parquet as pq

                # Create empty schema
                schema_fields = []
                for col in columns:
                    schema_fields.append(pa.field(col, pa.string()))
                schema = pa.schema(schema_fields)

                # Create empty table
                table = pa.table([], schema=schema)

                # Write to bytes
                buffer = io.BytesIO()
                pq.write_table(table, buffer)
                return buffer.getvalue()

        finally:
            # Clean up temp table
            try:
                self.connection.execute(f"DROP TABLE IF EXISTS {temp_table}")
            except Exception:
                pass

    def _get_table_count(self, table_name: str) -> int:
        """Get total count of records in table."""
        import sqlglot

        query = sqlglot.select(sqlglot.func("COUNT", "*")).from_(table_name)
        sql = query.sql(dialect="duckdb")
        result = self.connection.execute(sql).fetchone()
        return result[0] if result else 0

    def create_record(self, table_name: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new record in the table."""
        if not data:
            raise ValueError("No data provided for record creation")

        import sqlglot
        from sqlglot import exp

        # Get table schema to find primary key columns
        schema = self.get_table_schema(table_name)

        # Find primary key column (look for common patterns: id, *_id, primary key constraint)
        primary_key_col = None
        for col in schema:
            col_name = col["name"].lower()
            col_type = col["type"].upper()
            if col_name == "id" or col_name.endswith("_id"):
                # Skip UUID columns as they need special handling
                if "UUID" not in col_type:
                    primary_key_col = col["name"]
                    break

        # Generate next available ID if primary key column exists and not provided
        if primary_key_col and primary_key_col not in data:
            max_query = sqlglot.select(
                sqlglot.func(
                    "COALESCE", sqlglot.func("MAX", exp.Column(this=primary_key_col)), 0
                )
            ).from_(table_name)
            max_sql = max_query.sql(dialect="duckdb")
            max_id = self.connection.execute(max_sql).fetchone()[0]
            data[primary_key_col] = max_id + 1

        # Add timestamp column if exists and not provided
        timestamp_col = None
        for col in schema:
            col_name = col["name"].lower()
            if col_name in ["created_at", "timestamp", "created", "date_created"]:
                timestamp_col = col["name"]
                break

        if timestamp_col and timestamp_col not in data:
            from datetime import datetime

            data[timestamp_col] = datetime.now()

        # Use already retrieved schema for column order
        schema_columns = [col["name"] for col in schema]

        # Build columns and values in schema order, only including provided fields
        columns = []
        values = []
        for col_name in schema_columns:
            if col_name in data:
                columns.append(col_name)
                values.append(data[col_name])

        # Create INSERT with placeholders using proper SQLGlot expressions
        values_expr = exp.Values(
            expressions=[exp.Tuple(expressions=[exp.Placeholder() for _ in columns])]
        )

        insert_query = exp.Insert(
            this=exp.to_identifier(table_name),
            expression=values_expr,
            columns=[exp.to_identifier(col) for col in columns],
        )
        sql = insert_query.sql(dialect="duckdb")

        try:
            self.connection.execute(sql, values)

            # Return the created record if we have a primary key
            if primary_key_col and primary_key_col in data:
                return self.get_record_by_id(table_name, data[primary_key_col])
            else:
                # Return success message if no primary key
                return {"message": "Record created successfully", "data": data}
        except Exception as e:
            raise RuntimeError(
                f"Failed to create record in {table_name}: {str(e)}"
            ) from e

    def get_record_by_id(self, table_name: str, record_id: int) -> dict[str, Any]:
        """Get a single record by ID."""
        import sqlglot
        from sqlglot import exp

        # Get table schema to find primary key column
        schema = self.get_table_schema(table_name)
        primary_key_col = None
        for col in schema:
            col_name = col["name"].lower()
            col_type = col["type"].upper()
            if col_name == "id" or col_name.endswith("_id"):
                # Skip UUID columns as they need special handling
                if "UUID" not in col_type:
                    primary_key_col = col["name"]
                    break

        if not primary_key_col:
            raise ValueError(
                f"No suitable primary key column found in table {table_name}"
            )

        query = (
            sqlglot.select("*")
            .from_(table_name)
            .where(
                exp.EQ(
                    this=exp.Column(this=primary_key_col), expression=exp.Placeholder()
                )
            )
        )
        sql = query.sql(dialect="duckdb")
        result = self.connection.execute(sql, [record_id]).fetchone()

        if not result:
            raise ValueError(
                f"Record with {primary_key_col} {record_id} not found in {table_name}"
            )

        columns = [desc[0] for desc in self.connection.description]
        return dict(zip(columns, result, strict=False))

    def update_records(
        self,
        table_name: str,
        data: dict[str, Any],
        rql_query: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> int:
        """Update records in the table matching RQL query or simple filters."""
        if not data:
            raise ValueError("No data provided for record update")

        # Build SET clause
        values = list(data.values())

        # Build WHERE clause
        where_clause = ""
        where_params = []

        if rql_query and rql_query.strip():
            # Use RQL for complex filtering
            import sqlglot

            from .rql_to_sql import convert_rql_to_sql

            # Convert RQL to SQL WHERE clause
            select_sql, rql_params = convert_rql_to_sql(table_name, rql_query)

            # Extract WHERE clause from the generated SELECT
            parsed = sqlglot.parse_one(select_sql, dialect="duckdb")
            where_clause = ""
            if parsed.find(sqlglot.exp.Where):
                where_clause = " WHERE " + str(parsed.find(sqlglot.exp.Where).this)
                where_params = rql_params

        elif filters:
            # Simple equality filters for backward compatibility
            where_conditions = []
            for key, value in filters.items():
                where_conditions.append(f"{key} = ?")
                where_params.append(value)
            where_clause = " WHERE " + " AND ".join(where_conditions)

        # Count matching records before update using SQLGlot
        import sqlglot

        count_query = sqlglot.select(sqlglot.func("COUNT", "*")).from_(table_name)
        if where_clause:
            # Parse and apply the WHERE clause
            parsed_where = sqlglot.parse_one(
                f"SELECT * FROM {table_name}{where_clause}", dialect="duckdb"
            )
            if parsed_where.find(sqlglot.exp.Where):
                count_query = count_query.where(
                    parsed_where.find(sqlglot.exp.Where).this
                )

        count_sql = count_query.sql(dialect="duckdb")
        count_before = (
            self.connection.execute(count_sql, where_params).fetchone()[0]
            if where_params
            else self.connection.execute(count_sql).fetchone()[0]
        )

        # Build UPDATE query using SQLGlot expressions
        from sqlglot import exp

        set_expressions = []
        for col in data.keys():
            set_expressions.append(
                exp.EQ(this=exp.to_identifier(col), expression=exp.Placeholder())
            )

        update_query = exp.Update(
            this=exp.to_identifier(table_name), expressions=set_expressions
        )

        # Add WHERE clause if present
        if where_clause:
            parsed_where = sqlglot.parse_one(
                f"SELECT * FROM {table_name}{where_clause}", dialect="duckdb"
            )
            if parsed_where.find(sqlglot.exp.Where):
                update_query = update_query.where(
                    parsed_where.find(sqlglot.exp.Where).this
                )

        sql = update_query.sql(dialect="duckdb")
        all_values = values + where_params

        try:
            self.connection.execute(sql, all_values)
            # DuckDB rowcount is unreliable, return count_before as updated count
            return count_before
        except Exception as e:
            raise RuntimeError(
                f"Failed to update records in {table_name}: {str(e)}"
            ) from e

    def delete_records(
        self,
        table_name: str,
        rql_query: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> int:
        """Delete records from the table matching RQL query or simple filters."""
        if not rql_query and not filters:
            # Prevent accidental deletion of all records
            raise ValueError(
                "No filters or RQL query provided for deletion - this would delete all records"
            )

        # Build WHERE clause
        where_clause = ""
        where_params = []

        if rql_query and rql_query.strip():
            # Use RQL for complex filtering
            import sqlglot

            from .rql_to_sql import convert_rql_to_sql

            # Convert RQL to SQL WHERE clause
            select_sql, rql_params = convert_rql_to_sql(table_name, rql_query)

            # Extract WHERE clause from the generated SELECT
            parsed = sqlglot.parse_one(select_sql, dialect="duckdb")
            where_clause = ""
            if parsed.find(sqlglot.exp.Where):
                where_clause = " WHERE " + str(parsed.find(sqlglot.exp.Where).this)
                where_params = rql_params

        elif filters:
            # Simple equality filters for backward compatibility
            where_conditions = []
            for key, value in filters.items():
                where_conditions.append(f"{key} = ?")
                where_params.append(value)
            where_clause = " WHERE " + " AND ".join(where_conditions)

        # Count matching records before deletion using SQLGlot
        import sqlglot

        count_query = sqlglot.select(sqlglot.func("COUNT", "*")).from_(table_name)
        if where_clause:
            # Parse and apply the WHERE clause
            parsed_where = sqlglot.parse_one(
                f"SELECT * FROM {table_name}{where_clause}", dialect="duckdb"
            )
            if parsed_where.find(sqlglot.exp.Where):
                count_query = count_query.where(
                    parsed_where.find(sqlglot.exp.Where).this
                )

        count_sql = count_query.sql(dialect="duckdb")
        count_before = (
            self.connection.execute(count_sql, where_params).fetchone()[0]
            if where_params
            else self.connection.execute(count_sql).fetchone()[0]
        )

        # Build DELETE query using SQLGlot expressions
        from sqlglot import exp

        delete_query = exp.Delete(this=exp.to_identifier(table_name))

        # Add WHERE clause if present
        if where_clause:
            parsed_where = sqlglot.parse_one(
                f"SELECT * FROM {table_name}{where_clause}", dialect="duckdb"
            )
            if parsed_where.find(sqlglot.exp.Where):
                delete_query = delete_query.where(
                    parsed_where.find(sqlglot.exp.Where).this
                )

        sql = delete_query.sql(dialect="duckdb")

        try:
            self.connection.execute(sql, where_params)
            # DuckDB rowcount is unreliable, return count_before as deleted count
            return count_before
        except Exception as e:
            raise RuntimeError(
                f"Failed to delete records from {table_name}: {str(e)}"
            ) from e

    def execute_query(
        self, query: str, params: list[Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a raw SQL query and return results."""
        try:
            if params:
                result = self.connection.execute(query, params).fetchall()
            else:
                result = self.connection.execute(query).fetchall()

            columns = [desc[0] for desc in self.connection.description]
            return [dict(zip(columns, row, strict=False)) for row in result]
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {str(e)}") from e

    def get_chart_data(self, table_name: str) -> dict[str, Any]:
        """Analyze table data and suggest appropriate chart visualizations."""
        schema = self.get_table_schema(table_name)

        # Find numeric columns for charts
        numeric_columns = [
            col
            for col in schema
            if any(
                t in col["type"].lower()
                for t in ["int", "float", "double", "decimal", "number"]
            )
        ]

        # Find categorical columns for grouping
        categorical_columns = [
            col
            for col in schema
            if any(
                t in col["type"].lower()
                for t in ["varchar", "text", "string", "char", "bool"]
            )
            and col["name"] not in ["id", "created_at", "updated_at"]
        ]

        chart_suggestions = []

        # Count by categorical columns (bar charts)
        for cat_col in categorical_columns[
            :3
        ]:  # Limit to first 3 to avoid too many charts
            try:
                query = f"SELECT {cat_col['name']}, COUNT(*) as count FROM {table_name} GROUP BY {cat_col['name']} ORDER BY count DESC LIMIT 10"
                data = self.execute_query(query, [])
                if data:
                    chart_suggestions.append(
                        {
                            "type": "bar",
                            "title": f"Count by {cat_col['name'].title()}",
                            "data": data,
                            "x_key": cat_col["name"],
                            "y_key": "count",
                        }
                    )
            except Exception:
                pass

        # Distribution of numeric columns (histograms)
        for num_col in numeric_columns[:2]:  # Limit to first 2 numeric columns
            try:
                query = f"SELECT {num_col['name']} FROM {table_name} WHERE {num_col['name']} IS NOT NULL ORDER BY {num_col['name']}"
                raw_data = self.execute_query(query, [])
                if raw_data:
                    # Create histogram bins
                    values = [row[num_col["name"]] for row in raw_data]
                    if values:
                        min_val, max_val = min(values), max(values)
                        if max_val > min_val:
                            bin_count = min(10, len(set(values)))  # Max 10 bins
                            bin_size = (max_val - min_val) / bin_count
                            bins = {}
                            for val in values:
                                bin_key = (
                                    int((val - min_val) // bin_size)
                                    if bin_size > 0
                                    else 0
                                )
                                bin_key = min(
                                    bin_key, bin_count - 1
                                )  # Ensure within range
                                bin_label = f"{min_val + bin_key * bin_size:.1f}-{min_val + (bin_key + 1) * bin_size:.1f}"
                                bins[bin_label] = bins.get(bin_label, 0) + 1

                            histogram_data = [
                                {"range": k, "count": v} for k, v in bins.items()
                            ]
                            chart_suggestions.append(
                                {
                                    "type": "bar",
                                    "title": f"Distribution of {num_col['name'].title()}",
                                    "data": histogram_data,
                                    "x_key": "range",
                                    "y_key": "count",
                                }
                            )
            except Exception:
                pass

        # Time series if there's a date column
        date_columns = [
            col
            for col in schema
            if any(t in col["type"].lower() for t in ["date", "timestamp", "time"])
        ]

        if date_columns and numeric_columns:
            date_col = date_columns[0]
            num_col = numeric_columns[0]
            try:
                query = f"""
                    SELECT DATE_TRUNC('day', {date_col["name"]}) as date,
                           AVG({num_col["name"]}) as avg_value,
                           COUNT(*) as count
                    FROM {table_name}
                    WHERE {date_col["name"]} IS NOT NULL AND {num_col["name"]} IS NOT NULL
                    GROUP BY DATE_TRUNC('day', {date_col["name"]})
                    ORDER BY date
                    LIMIT 30
                """
                data = self.execute_query(query, [])
                if data:
                    chart_suggestions.append(
                        {
                            "type": "line",
                            "title": f"{num_col['name'].title()} Over Time",
                            "data": data,
                            "x_key": "date",
                            "y_key": "avg_value",
                        }
                    )
            except Exception:
                pass

        return {
            "table_name": table_name,
            "charts": chart_suggestions,
            "numeric_columns": [col["name"] for col in numeric_columns],
            "categorical_columns": [col["name"] for col in categorical_columns],
            "date_columns": [col["name"] for col in date_columns],
        }

    # Bulk Operations using DuckDB native file handling
    def bulk_insert_from_file(
        self, table_name: str, file_path: str, file_format: str = "auto"
    ) -> int:
        """
        Bulk insert records from file using DuckDB native operations.

        Args:
            table_name: Target table name
            file_path: Path to the file (supports Parquet, CSV, JSON)
            file_format: File format ('parquet', 'csv', 'json', 'auto')

        Returns:
            Number of records inserted
        """
        # Validate table exists
        if not self._table_exists(table_name):
            raise ValueError(f"Table {table_name} does not exist")

        # Auto-detect format if needed
        if file_format == "auto":
            if file_path.endswith(".parquet"):
                file_format = "parquet"
            elif file_path.endswith(".csv"):
                file_format = "csv"
            elif file_path.endswith(".json"):
                file_format = "json"
            else:
                raise ValueError(f"Cannot auto-detect format for {file_path}")

        # Get count before insertion
        count_before = self.connection.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]

        try:
            # Use DuckDB native file reading
            if file_format == "parquet":
                sql = f"INSERT INTO {table_name} SELECT * FROM read_parquet('{file_path}')"
            elif file_format == "csv":
                sql = f"INSERT INTO {table_name} SELECT * FROM read_csv_auto('{file_path}')"
            elif file_format == "json":
                sql = f"INSERT INTO {table_name} SELECT * FROM read_json_auto('{file_path}')"
            else:
                raise ValueError(f"Unsupported file format: {file_format}")

            self.connection.execute(sql)

            # Get count after insertion
            count_after = self.connection.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            ).fetchone()[0]
            return count_after - count_before

        except Exception as e:
            raise RuntimeError(f"Bulk insert failed for {table_name}: {str(e)}") from e

    def bulk_upsert_from_file(
        self,
        table_name: str,
        file_path: str,
        key_columns: list[str],
        file_format: str = "auto",
    ) -> dict[str, int]:
        """
        Bulk upsert (insert or update) records from file.

        Args:
            table_name: Target table name
            file_path: Path to the file
            key_columns: Columns to match for updates
            file_format: File format ('parquet', 'csv', 'json', 'auto')

        Returns:
            Dictionary with 'inserted' and 'updated' counts
        """
        # Validate table exists
        if not self._table_exists(table_name):
            raise ValueError(f"Table {table_name} does not exist")

        # Auto-detect format if needed
        if file_format == "auto":
            if file_path.endswith(".parquet"):
                file_format = "parquet"
            elif file_path.endswith(".csv"):
                file_format = "csv"
            elif file_path.endswith(".json"):
                file_format = "json"
            else:
                raise ValueError(f"Cannot auto-detect format for {file_path}")

        # Get initial count
        count_before = self.connection.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]

        try:
            # Create temporary table for new data
            temp_table = f"temp_{table_name}_{int(time.time())}"

            # Load data into temporary table
            if file_format == "parquet":
                sql = f"CREATE TABLE {temp_table} AS SELECT * FROM read_parquet('{file_path}')"
            elif file_format == "csv":
                sql = f"CREATE TABLE {temp_table} AS SELECT * FROM read_csv_auto('{file_path}')"
            elif file_format == "json":
                sql = f"CREATE TABLE {temp_table} AS SELECT * FROM read_json_auto('{file_path}')"
            else:
                raise ValueError(f"Unsupported file format: {file_format}")

            self.connection.execute(sql)

            # Get all column names for the table
            schema = self.get_table_schema(table_name)
            all_columns = [col["name"] for col in schema]

            # Build key matching condition
            key_conditions = []
            for key_col in key_columns:
                key_conditions.append(
                    f"{table_name}.{key_col} = {temp_table}.{key_col}"
                )
            key_condition = " AND ".join(key_conditions)

            # Update existing records
            non_key_columns = [col for col in all_columns if col not in key_columns]
            if non_key_columns:
                set_clauses = []
                for col in non_key_columns:
                    set_clauses.append(f"{col} = {temp_table}.{col}")
                set_clause = ", ".join(set_clauses)

                update_sql = f"""
                    UPDATE {table_name}
                    SET {set_clause}
                    FROM {temp_table}
                    WHERE {key_condition}
                """
                self.connection.execute(update_sql)

            # Insert new records
            column_list = ", ".join(all_columns)
            insert_sql = f"""
                INSERT INTO {table_name} ({column_list})
                SELECT {column_list}
                FROM {temp_table}
                WHERE NOT EXISTS (
                    SELECT 1 FROM {table_name}
                    WHERE {key_condition}
                )
            """
            self.connection.execute(insert_sql)

            # Get final count
            count_after = self.connection.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            ).fetchone()[0]

            # Clean up temporary table
            self.connection.execute(f"DROP TABLE {temp_table}")

            # Calculate rough estimates (exact tracking would require more complex logic)
            total_processed = count_after - count_before
            return {
                "inserted": total_processed,
                "updated": 0,  # Simplified - actual implementation would track this
            }

        except Exception as e:
            # Clean up temporary table on error
            try:
                self.connection.execute(f"DROP TABLE IF EXISTS {temp_table}")
            except Exception:
                pass
            raise RuntimeError(f"Bulk upsert failed for {table_name}: {str(e)}") from e

    def bulk_delete_from_file(
        self,
        table_name: str,
        file_path: str,
        key_columns: list[str],
        file_format: str = "auto",
    ) -> int:
        """
        Bulk delete records based on keys from file.

        Args:
            table_name: Target table name
            file_path: Path to the file containing keys to delete
            key_columns: Columns to match for deletion
            file_format: File format ('parquet', 'csv', 'json', 'auto')

        Returns:
            Number of records deleted
        """
        # Validate table exists
        if not self._table_exists(table_name):
            raise ValueError(f"Table {table_name} does not exist")

        # Auto-detect format if needed
        if file_format == "auto":
            if file_path.endswith(".parquet"):
                file_format = "parquet"
            elif file_path.endswith(".csv"):
                file_format = "csv"
            elif file_path.endswith(".json"):
                file_format = "json"
            else:
                raise ValueError(f"Cannot auto-detect format for {file_path}")

        # Get count before deletion
        count_before = self.connection.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]

        try:
            # Create temporary table for keys to delete
            temp_table = f"temp_delete_{table_name}_{int(time.time())}"

            # Load keys into temporary table
            if file_format == "parquet":
                sql = f"CREATE TABLE {temp_table} AS SELECT * FROM read_parquet('{file_path}')"
            elif file_format == "csv":
                sql = f"CREATE TABLE {temp_table} AS SELECT * FROM read_csv_auto('{file_path}')"
            elif file_format == "json":
                sql = f"CREATE TABLE {temp_table} AS SELECT * FROM read_json_auto('{file_path}')"
            else:
                raise ValueError(f"Unsupported file format: {file_format}")

            self.connection.execute(sql)

            # Build key matching condition
            key_conditions = []
            for key_col in key_columns:
                key_conditions.append(
                    f"{table_name}.{key_col} = {temp_table}.{key_col}"
                )
            key_condition = " AND ".join(key_conditions)

            # Delete matching records
            delete_sql = f"""
                DELETE FROM {table_name}
                WHERE EXISTS (
                    SELECT 1 FROM {temp_table}
                    WHERE {key_condition}
                )
            """
            self.connection.execute(delete_sql)

            # Get count after deletion
            count_after = self.connection.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            ).fetchone()[0]

            # Clean up temporary table
            self.connection.execute(f"DROP TABLE {temp_table}")

            return count_before - count_after

        except Exception as e:
            # Clean up temporary table on error
            try:
                self.connection.execute(f"DROP TABLE IF EXISTS {temp_table}")
            except Exception:
                pass
            raise RuntimeError(f"Bulk delete failed for {table_name}: {str(e)}") from e

    def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        try:
            tables = self.list_tables()
            return any(table["name"] == table_name for table in tables)
        except Exception:
            return False

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
