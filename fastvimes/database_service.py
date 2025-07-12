"""Core database service for FastVimes using DuckDB directly with SQLGlot."""

import logging
from typing import Dict, Any, List, Optional
import duckdb
from sqlglot import transpile
from sqlglot.expressions import Select, Column, Table

from .config import FastVimesSettings, TableConfig


logger = logging.getLogger(__name__)


class DatabaseService:
    """Core database service handling connections, table discovery, and query execution."""

    def __init__(self, config: FastVimesSettings):
        self.config = config
        self._connection = None
        self._tables: Dict[str, Dict[str, Any]] = {}
        self._table_configs: Dict[str, TableConfig] = {}


        self._setup_database()
        self._discover_tables()

    def _setup_database(self) -> None:
        """Initialize DuckDB connection with extensions."""
        try:
            self._connection = duckdb.connect(
                database=self.config.db_path,
                read_only=self.config.read_only
            )

            # Load configured extensions
            for extension in self.config.extensions:
                try:
                    self._connection.execute(f"INSTALL {extension}")
                    self._connection.execute(f"LOAD {extension}")
                    logger.info(f"Loaded DuckDB extension: {extension}")
                except Exception as e:
                    logger.warning(f"Failed to load extension {extension}: {e}")

        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise RuntimeError(f"Database initialization failed: {e}")

    def _discover_tables(self) -> None:
        """Discover available tables and setup configurations."""
        try:
            # Query for tables
            result = self._connection.execute("SHOW TABLES").fetchall()
            table_names = [row[0] for row in result]
            
            for table_name in table_names:
                # Get table schema information
                schema_result = self._connection.execute(f"DESCRIBE {table_name}").fetchall()
                
                columns = {}
                for row in schema_result:
                    col_name = row[0]
                    col_type = row[1]
                    nullable = row[2] == 'YES'
                    columns[col_name] = {
                        'type': col_type,
                        'nullable': nullable
                    }
                
                self._tables[table_name] = {
                    'name': table_name,
                    'columns': columns
                }

                # Create table configuration using the settings method
                table_config = self.config.get_table_config(table_name)
                self._table_configs[table_name] = table_config
                
                logger.info(f"Discovered table: {table_name} (mode: {table_config.mode})")

        except Exception as e:
            logger.error(f"Failed to discover tables: {e}")
            raise RuntimeError(f"Table discovery failed: {e}")

    @property
    def connection(self):
        """Access to underlying DuckDB connection."""
        return self._connection

    @property
    def tables(self) -> Dict[str, Dict[str, Any]]:
        """Access to discovered tables with schema info."""
        return self._tables

    def list_tables(self) -> Dict[str, TableConfig]:
        """List all available tables with their configurations."""
        return self._table_configs.copy()

    def get_table_schema(self, name: str) -> Dict[str, Any]:
        """Get table schema information by name."""
        if name not in self._tables:
            raise ValueError(f"Table '{name}' not found")
        return self._tables[name]

    def get_table_config(self, name: str) -> TableConfig:
        """Get table configuration by name."""
        if name not in self._table_configs:
            raise ValueError(f"Table configuration for '{name}' not found")
        return self._table_configs[name]

    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results as list of dicts."""
        try:
            # Use fetchall() to get raw results and column names to avoid pandas dependency
            result = self._connection.execute(sql)
            columns = [desc[0] for desc in result.description]
            rows = result.fetchall()
            
            # Convert to list of dicts
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise RuntimeError(f"Query execution failed: {e}")

    def execute_rql_query(self, table_name: str, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute an RQL query and return results."""
        try:
            from .rql_sqlglot import apply_rql_to_sql, RQLSQLGlotTranslator
            
            # Check if we have a direct RQL string
            if "_rql_string" in query_params:
                translator = RQLSQLGlotTranslator()
                sql = translator.translate_rql_to_sql(table_name, query_params["_rql_string"])
            else:
                sql = apply_rql_to_sql(table_name, query_params)
            
            logger.debug(f"Generated SQL: {sql}")
            return self.execute_query(sql)
        except Exception as e:
            logger.error(f"RQL query execution failed: {e}")
            raise RuntimeError(f"RQL query execution failed: {e}")



    def insert_record(self, table_name: str, data: Dict[str, Any]) -> None:
        """Insert a new record into a table."""
        if table_name not in self._tables:
            raise ValueError(f"Table '{table_name}' not found")
        
        schema = self._tables[table_name]
        columns = list(data.keys())
        values = list(data.values())
        
        # Validate columns exist
        for col in columns:
            if col not in schema['columns']:
                raise ValueError(f"Column '{col}' does not exist in table '{table_name}'")
        
        # Build parameterized query
        placeholders = ', '.join(['?' for _ in values])
        column_list = ', '.join(columns)
        sql = f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})"
        
        try:
            self._connection.execute(sql, values)
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            raise RuntimeError(f"Insert failed: {e}")

    def update_record(self, table_name: str, data: Dict[str, Any], where_params: Dict[str, Any]) -> int:
        """Update record(s) in a table. Returns number of affected rows."""
        if table_name not in self._tables:
            raise ValueError(f"Table '{table_name}' not found")
        
        schema = self._tables[table_name]
        
        # Validate columns exist
        for col in data.keys():
            if col not in schema['columns']:
                raise ValueError(f"Column '{col}' does not exist in table '{table_name}'")
        
        # Build SET clause
        set_clauses = []
        set_values = []
        for col, value in data.items():
            set_clauses.append(f"{col} = ?")
            set_values.append(value)
        
        # Handle RQL WHERE clause if RQL string is provided
        if "_rql_string" in where_params:
            from .rql_sqlglot import RQLSQLGlotTranslator
            rql_string = where_params["_rql_string"]
            translator = RQLSQLGlotTranslator()
            rql_data = translator.parse_rql_query(rql_string)
            
            if rql_data["filters"]:
                # Build WHERE clause from RQL filters
                combined_filter = rql_data["filters"][0]
                for filter_expr in rql_data["filters"][1:]:
                    from sqlglot.expressions import And
                    combined_filter = And(this=combined_filter, expression=filter_expr)
                where_clause = combined_filter.sql(dialect="duckdb")
            else:
                raise ValueError("WHERE conditions are required for UPDATE operations")
        else:
            # Build simple WHERE clause from key-value pairs
            where_clauses = []
            where_values = []
            for col, value in where_params.items():
                if col not in schema['columns']:
                    raise ValueError(f"Where column '{col}' does not exist in table '{table_name}'")
                where_clauses.append(f"{col} = ?")
                where_values.append(value)
            
            if not where_clauses:
                raise ValueError("WHERE conditions are required for UPDATE operations")
            
            where_clause = ' AND '.join(where_clauses)
            set_values.extend(where_values)
        
        sql = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {where_clause}"
        
        try:
            result = self._connection.execute(sql, set_values)
            return result.rowcount if hasattr(result, 'rowcount') else 0
        except Exception as e:
            logger.error(f"Update failed: {e}")
            raise RuntimeError(f"Update failed: {e}")

    def delete_record(self, table_name: str, where_params: Dict[str, Any]) -> int:
        """Delete record(s) from a table. Returns number of affected rows."""
        if table_name not in self._tables:
            raise ValueError(f"Table '{table_name}' not found")
        
        schema = self._tables[table_name]
        
        # Handle RQL WHERE clause if RQL string is provided
        if "_rql_string" in where_params:
            from .rql_sqlglot import RQLSQLGlotTranslator
            rql_string = where_params["_rql_string"]
            translator = RQLSQLGlotTranslator()
            rql_data = translator.parse_rql_query(rql_string)
            
            if rql_data["filters"]:
                # Build WHERE clause from RQL filters
                combined_filter = rql_data["filters"][0]
                for filter_expr in rql_data["filters"][1:]:
                    from sqlglot.expressions import And
                    combined_filter = And(this=combined_filter, expression=filter_expr)
                where_clause = combined_filter.sql(dialect="duckdb")
                sql = f"DELETE FROM {table_name} WHERE {where_clause}"
                query_values = []
            else:
                raise ValueError("WHERE conditions are required for DELETE operations")
        else:
            # Build simple WHERE clause from key-value pairs
            where_clauses = []
            where_values = []
            for col, value in where_params.items():
                if col not in schema['columns']:
                    raise ValueError(f"Where column '{col}' does not exist in table '{table_name}'")
                where_clauses.append(f"{col} = ?")
                where_values.append(value)
            
            if not where_clauses:
                raise ValueError("WHERE conditions are required for DELETE operations")
            
            sql = f"DELETE FROM {table_name} WHERE {' AND '.join(where_clauses)}"
            query_values = where_values
        
        try:
            result = self._connection.execute(sql, query_values)
            return result.rowcount if hasattr(result, 'rowcount') else 0
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise RuntimeError(f"Delete failed: {e}")

    def get_table_dataclass(self, table_name: str):
        """Generate a Pydantic dataclass for a table schema.
        
        This creates a dynamic Pydantic model based on the table's schema
        that can be used for request/response validation in FastAPI endpoints.
        """
        from pydantic import create_model
        from typing import Optional, Any

        if table_name not in self._tables:
            raise ValueError(f"Table '{table_name}' not found")

        schema = self._tables[table_name]
        columns = schema['columns']
        
        # Build field definitions for Pydantic
        field_definitions = {}
        
        for name, col_info in columns.items():
            # Convert DuckDB types to Python types
            python_type = self._duckdb_to_python_type(col_info['type'])
            
            # Make fields optional based on nullability
            if col_info['nullable']:
                field_definitions[name] = (Optional[python_type], None)
            else:
                field_definitions[name] = (python_type, ...)

        # Create dynamic Pydantic model
        model_name = f"{table_name.title()}Model"
        return create_model(model_name, **field_definitions)

    def _duckdb_to_python_type(self, duckdb_type: str) -> type:
        """Convert DuckDB data type to Python type for Pydantic."""
        duckdb_type = duckdb_type.upper()
        
        type_mapping = {
            'BIGINT': int,
            'INTEGER': int,
            'SMALLINT': int,
            'TINYINT': int,
            'DOUBLE': float,
            'REAL': float,
            'FLOAT': float,
            'VARCHAR': str,
            'TEXT': str,
            'BOOLEAN': bool,
            'DATE': str,  # Could use datetime.date
            'TIMESTAMP': str,  # Could use datetime.datetime
            'TIME': str,
        }
        
        # Handle type patterns
        for duck_pattern, python_type in type_mapping.items():
            if duck_pattern in duckdb_type:
                return python_type
        
        # Default to str for unknown types
        return str

    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
