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

from pathlib import Path
from typing import List, Dict, Any, Optional
import duckdb
from datetime import datetime, timedelta
import random

import pyrql
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
            (1, 'Alice Johnson', 'alice@example.com', 28, True, 'Engineering', '2024-01-15'),
            (2, 'Bob Smith', 'bob@example.com', 34, True, 'Marketing', '2024-02-20'),
            (3, 'Carol Davis', 'carol@example.com', 25, True, 'Engineering', '2024-03-10'),
            (4, 'David Wilson', 'david@example.com', 42, False, 'Sales', '2024-01-05'),
            (5, 'Eva Brown', 'eva@example.com', 31, True, 'Design', '2024-04-12'),
            (6, 'Frank Miller', 'frank@example.com', 29, True, 'Engineering', '2024-02-28'),
            (7, 'Grace Lee', 'grace@example.com', 36, True, 'Marketing', '2024-03-15'),
            (8, 'Henry Taylor', 'henry@example.com', 27, True, 'Engineering', '2024-01-20'),
        ]
        
        for user in users_data:
            self.connection.execute(
                "INSERT OR IGNORE INTO users (id, name, email, age, active, department, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                user
            )
        
        # Insert sample products
        products_data = [
            (1, 'Laptop Pro 15"', 'Electronics', 1299.99, 25, True, '2024-01-01'),
            (2, 'Wireless Mouse', 'Electronics', 29.99, 150, True, '2024-01-05'),
            (3, 'Standing Desk', 'Furniture', 399.99, 12, True, '2024-01-10'),
            (4, 'Ergonomic Chair', 'Furniture', 249.99, 8, True, '2024-01-15'),
            (5, 'USB-C Cable', 'Electronics', 19.99, 200, True, '2024-01-20'),
            (6, 'Monitor 27"', 'Electronics', 299.99, 18, True, '2024-02-01'),
            (7, 'Keyboard Mechanical', 'Electronics', 129.99, 45, True, '2024-02-05'),
            (8, 'Desk Lamp', 'Furniture', 79.99, 32, True, '2024-02-10'),
            (9, 'Notebook Pack', 'Office', 12.99, 100, False, '2024-02-15'),
            (10, 'Webcam HD', 'Electronics', 89.99, 22, True, '2024-03-01'),
        ]
        
        for product in products_data:
            self.connection.execute(
                "INSERT OR IGNORE INTO products (id, name, category, price, stock_quantity, active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                product
            )
        
        # Insert sample orders
        orders_data = [
            (1, 1, 1, 1, '2024-03-01', 'completed', 1299.99),
            (2, 2, 2, 2, '2024-03-02', 'completed', 59.98),
            (3, 3, 3, 1, '2024-03-03', 'pending', 399.99),
            (4, 1, 5, 3, '2024-03-04', 'completed', 59.97),
            (5, 4, 6, 1, '2024-03-05', 'cancelled', 299.99),
            (6, 5, 7, 1, '2024-03-06', 'completed', 129.99),
            (7, 2, 8, 2, '2024-03-07', 'pending', 159.98),
            (8, 6, 1, 1, '2024-03-08', 'completed', 1299.99),
            (9, 7, 10, 1, '2024-03-09', 'completed', 89.99),
            (10, 8, 4, 1, '2024-03-10', 'pending', 249.99),
        ]
        
        for order in orders_data:
            self.connection.execute(
                "INSERT OR IGNORE INTO orders (id, user_id, product_id, quantity, order_date, status, total_amount) VALUES (?, ?, ?, ?, ?, ?, ?)",
                order
            )
        
    # =============================================================================
    # PUBLIC API METHODS - Exposed via CLI/FastAPI/NiceGUI
    # =============================================================================
        
    def list_tables(self) -> List[Dict[str, Any]]:
        """List all tables and views in the database."""
        query = """
        SELECT table_name, table_type
        FROM information_schema.tables 
        WHERE table_schema = 'main'
        ORDER BY table_name
        """
        result = self.connection.execute(query).fetchall()
        return [
            {"name": row[0], "type": row[1].lower()}
            for row in result
        ]
        
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema information for a table."""
        query = f"DESCRIBE {table_name}"
        result = self.connection.execute(query).fetchall()
        return [
            {
                "name": row[0],
                "type": row[1],
                "nullable": row[2] == "YES",
                "key": row[3] if len(row) > 3 else None
            }
            for row in result
        ]
        
    def get_table_data(
        self, 
        table_name: str, 
        rql_query: Optional[str] = None,
        limit: Optional[int] = 100,
        offset: Optional[int] = 0,
        format: str = "json"
    ) -> Dict[str, Any] | bytes:
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
                count_query = sqlglot.select(sqlglot.func("COUNT", "*")).from_(table_name).where(where_clause.this)
            else:
                count_query = sqlglot.select(sqlglot.func("COUNT", "*")).from_(table_name)
                
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
            result = self.connection.execute(sql).fetchall()
            # Get column names from the result we just executed
            columns = [desc[0] for desc in self.connection.description]
            total_count = self._get_table_count(table_name)
        
        data = [dict(zip(columns, row)) for row in result]
        
        # Handle different output formats
        if format.lower() == "json":
            return {
                "columns": columns,
                "data": data,
                "total_count": total_count
            }
        elif format.lower() == "csv":
            return self._export_to_csv(columns, data)
        elif format.lower() == "parquet":
            return self._export_to_parquet(columns, data)
        else:
            raise ValueError(f"Unsupported format: {format}. Supported formats: json, csv, parquet")
    

        
    def _export_to_csv(self, columns: List[str], data: List[Dict[str, Any]]) -> bytes:
        """Export data to CSV format using DuckDB native functionality."""
        import tempfile
        import os
        
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
                
                create_sql = f"CREATE TEMP TABLE {temp_table} ({', '.join(column_defs)})"
                self.connection.execute(create_sql)
                
                # Insert data
                placeholders = ", ".join(["?" for _ in columns])
                insert_sql = f"INSERT INTO {temp_table} VALUES ({placeholders})"
                for row in data:
                    values = [row.get(col) for col in columns]
                    self.connection.execute(insert_sql, values)
                
                # Export to CSV using DuckDB
                with tempfile.NamedTemporaryFile(mode='w+b', suffix='.csv', delete=False) as f:
                    temp_file = f.name
                
                try:
                    export_sql = f"COPY {temp_table} TO '{temp_file}' (FORMAT CSV, HEADER)"
                    self.connection.execute(export_sql)
                    
                    # Read the file back
                    with open(temp_file, 'rb') as f:
                        return f.read()
                finally:
                    os.unlink(temp_file)
            else:
                # Empty data - return CSV header only
                header = ",".join(columns) + "\n"
                return header.encode('utf-8')
                
        finally:
            # Clean up temp table
            try:
                self.connection.execute(f"DROP TABLE IF EXISTS {temp_table}")
            except:
                pass
    
    def _export_to_parquet(self, columns: List[str], data: List[Dict[str, Any]]) -> bytes:
        """Export data to Parquet format using DuckDB native functionality."""
        import tempfile
        import os
        
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
                
                create_sql = f"CREATE TEMP TABLE {temp_table} ({', '.join(column_defs)})"
                self.connection.execute(create_sql)
                
                # Insert data
                placeholders = ", ".join(["?" for _ in columns])
                insert_sql = f"INSERT INTO {temp_table} VALUES ({placeholders})"
                for row in data:
                    values = [row.get(col) for col in columns]
                    self.connection.execute(insert_sql, values)
                
                # Export to Parquet using DuckDB
                with tempfile.NamedTemporaryFile(mode='w+b', suffix='.parquet', delete=False) as f:
                    temp_file = f.name
                
                try:
                    export_sql = f"COPY {temp_table} TO '{temp_file}' (FORMAT PARQUET)"
                    self.connection.execute(export_sql)
                    
                    # Read the file back
                    with open(temp_file, 'rb') as f:
                        return f.read()
                finally:
                    os.unlink(temp_file)
            else:
                # Empty data - create minimal Parquet with schema
                import pyarrow as pa
                import pyarrow.parquet as pq
                import io
                
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
            except:
                pass

    def _get_table_count(self, table_name: str) -> int:
        """Get total count of records in table."""
        import sqlglot
        query = sqlglot.select(sqlglot.func("COUNT", "*")).from_(table_name)
        sql = query.sql(dialect="duckdb")
        result = self.connection.execute(sql).fetchone()
        return result[0] if result else 0
        
    def create_record(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in the table."""
        if not data:
            raise ValueError("No data provided for record creation")
        
        import sqlglot
        from sqlglot import exp
        
        # Get the next available ID if not provided
        if 'id' not in data:
            max_query = sqlglot.select(
                sqlglot.func("COALESCE", sqlglot.func("MAX", exp.Column(this="id")), 0)
            ).from_(table_name)
            max_sql = max_query.sql(dialect="duckdb")
            max_id = self.connection.execute(max_sql).fetchone()[0]
            data['id'] = max_id + 1
            
        # Add created_at if not provided
        if 'created_at' not in data:
            from datetime import datetime
            data['created_at'] = datetime.now()
            
        # Get the table schema to ensure correct column order
        schema = self.get_table_schema(table_name)
        schema_columns = [col['name'] for col in schema]
        
        # Build columns and values in schema order, only including provided fields
        columns = []
        values = []
        for col_name in schema_columns:
            if col_name in data:
                columns.append(col_name)
                values.append(data[col_name])
        
        # Create INSERT with placeholders using proper SQLGlot expressions
        values_expr = exp.Values(
            expressions=[
                exp.Tuple(expressions=[exp.Placeholder() for _ in columns])
            ]
        )
        
        insert_query = exp.Insert(
            this=exp.to_identifier(table_name),
            expression=values_expr,
            columns=[exp.to_identifier(col) for col in columns]
        )
        sql = insert_query.sql(dialect="duckdb")
        
        try:
            self.connection.execute(sql, values)
            
            # Return the created record
            return self.get_record_by_id(table_name, data['id'])
        except Exception as e:
            raise RuntimeError(f"Failed to create record in {table_name}: {str(e)}")
    
    def get_record_by_id(self, table_name: str, record_id: int) -> Dict[str, Any]:
        """Get a single record by ID."""
        import sqlglot
        from sqlglot import exp
        
        query = sqlglot.select("*").from_(table_name).where(
            exp.EQ(this=exp.Column(this="id"), expression=exp.Placeholder())
        )
        sql = query.sql(dialect="duckdb")
        result = self.connection.execute(sql, [record_id]).fetchone()
        
        if not result:
            raise ValueError(f"Record with id {record_id} not found in {table_name}")
            
        columns = [desc[0] for desc in self.connection.description]
        return dict(zip(columns, result))
        
    def update_records(
        self, 
        table_name: str, 
        data: Dict[str, Any],
        rql_query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Update records in the table matching RQL query or simple filters."""
        if not data:
            raise ValueError("No data provided for record update")
        
        # Build SET clause
        set_clause = ', '.join([f"{col} = ?" for col in data.keys()])
        values = list(data.values())
        
        # Build WHERE clause
        where_clause = ""
        where_params = []
        
        if rql_query and rql_query.strip():
            # Use RQL for complex filtering
            from .rql_to_sql import convert_rql_to_sql
            import sqlglot
            
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
            parsed_where = sqlglot.parse_one(f"SELECT * FROM {table_name}{where_clause}", dialect="duckdb")
            if parsed_where.find(sqlglot.exp.Where):
                count_query = count_query.where(parsed_where.find(sqlglot.exp.Where).this)
        
        count_sql = count_query.sql(dialect="duckdb")
        count_before = self.connection.execute(count_sql, where_params).fetchone()[0] if where_params else self.connection.execute(count_sql).fetchone()[0]
        
        # Build UPDATE query using SQLGlot expressions
        from sqlglot import exp
        set_expressions = []
        for col in data.keys():
            set_expressions.append(
                exp.EQ(
                    this=exp.to_identifier(col),
                    expression=exp.Placeholder()
                )
            )
        
        update_query = exp.Update(
            this=exp.to_identifier(table_name),
            expressions=set_expressions
        )
        
        # Add WHERE clause if present
        if where_clause:
            parsed_where = sqlglot.parse_one(f"SELECT * FROM {table_name}{where_clause}", dialect="duckdb")
            if parsed_where.find(sqlglot.exp.Where):
                update_query = update_query.where(parsed_where.find(sqlglot.exp.Where).this)
        
        sql = update_query.sql(dialect="duckdb")
        all_values = values + where_params
        
        try:
            self.connection.execute(sql, all_values)
            # DuckDB rowcount is unreliable, return count_before as updated count
            return count_before
        except Exception as e:
            raise RuntimeError(f"Failed to update records in {table_name}: {str(e)}")
        
    def delete_records(
        self,
        table_name: str,
        rql_query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Delete records from the table matching RQL query or simple filters."""
        if not rql_query and not filters:
            # Prevent accidental deletion of all records
            raise ValueError("No filters or RQL query provided for deletion - this would delete all records")
        
        # Build WHERE clause
        where_clause = ""
        where_params = []
        
        if rql_query and rql_query.strip():
            # Use RQL for complex filtering
            from .rql_to_sql import convert_rql_to_sql
            import sqlglot
            
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
            parsed_where = sqlglot.parse_one(f"SELECT * FROM {table_name}{where_clause}", dialect="duckdb")
            if parsed_where.find(sqlglot.exp.Where):
                count_query = count_query.where(parsed_where.find(sqlglot.exp.Where).this)
        
        count_sql = count_query.sql(dialect="duckdb")
        count_before = self.connection.execute(count_sql, where_params).fetchone()[0] if where_params else self.connection.execute(count_sql).fetchone()[0]
        
        # Build DELETE query using SQLGlot expressions
        from sqlglot import exp
        delete_query = exp.Delete(this=exp.to_identifier(table_name))
        
        # Add WHERE clause if present
        if where_clause:
            parsed_where = sqlglot.parse_one(f"SELECT * FROM {table_name}{where_clause}", dialect="duckdb")
            if parsed_where.find(sqlglot.exp.Where):
                delete_query = delete_query.where(parsed_where.find(sqlglot.exp.Where).this)
        
        sql = delete_query.sql(dialect="duckdb")
        
        try:
            self.connection.execute(sql, where_params)
            # DuckDB rowcount is unreliable, return count_before as deleted count
            return count_before
        except Exception as e:
            raise RuntimeError(f"Failed to delete records from {table_name}: {str(e)}")
            
    def execute_query(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """Execute a raw SQL query and return results."""
        try:
            if params:
                result = self.connection.execute(query, params).fetchall()
            else:
                result = self.connection.execute(query).fetchall()
                
            columns = [desc[0] for desc in self.connection.description]
            return [dict(zip(columns, row)) for row in result]
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {str(e)}")
            
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
