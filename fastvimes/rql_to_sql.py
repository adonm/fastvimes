"""
RQL to SQL converter using pyrql for parsing and SQLGlot for safe SQL generation.

This module provides a bridge between RQL queries and safe SQL generation,
following the FastVimes architecture requirement for SQLGlot usage.
"""

from typing import Any

import pyrql
import sqlglot
from sqlglot import exp


class RQLToSQLConverter:
    """Converts RQL queries to safe SQL using SQLGlot."""

    def __init__(self, dialect: str = "duckdb"):
        self.dialect = dialect

    def convert_to_sql(self, table_name: str, rql_query: str) -> tuple[str, list[Any]]:
        """
        Convert an RQL query to safe SQL with parameters.

        Args:
            table_name: Target table name
            rql_query: RQL query string

        Returns:
            Tuple of (sql_string, parameters_list)
        """
        # Parse RQL query using pyrql
        try:
            parsed_rql = pyrql.parse(rql_query)
        except Exception as e:
            raise ValueError(f"Invalid RQL query: {e}") from e

        # Start with basic SELECT
        query = sqlglot.select("*").from_(table_name)
        params = []

        # Convert RQL to SQL components
        if isinstance(parsed_rql, dict):
            query, params = self._apply_rql_to_query(query, parsed_rql, params)
        elif isinstance(parsed_rql, list):
            # Handle list of conditions (implicit AND)
            conditions = []
            for condition_node in parsed_rql:
                condition, params = self._convert_rql_condition(condition_node, params)
                if condition:
                    conditions.append(condition)

            if conditions:
                where_condition = conditions[0]
                for condition in conditions[1:]:
                    where_condition = exp.And(
                        this=where_condition, expression=condition
                    )
                query = query.where(where_condition)

        # Generate final SQL
        sql = query.sql(dialect=self.dialect, pretty=True)

        return sql, params

    def _apply_rql_to_query(self, query, rql_node, params: list[Any]):
        """Apply RQL node to SQLGlot query."""
        if isinstance(rql_node, dict):
            operator = rql_node.get("name")
            args = rql_node.get("args", [])

            if operator == "and":
                # Handle AND operations - process both filter conditions and other operations
                conditions = []
                for arg in args:
                    if isinstance(arg, dict):
                        # Check if this is a non-filter operation (select, sort, limit)
                        arg_op = arg.get("name")
                        if arg_op in ("select", "sort", "limit"):
                            # Apply non-filter operations directly to query
                            query, params = self._apply_rql_to_query(query, arg, params)
                        else:
                            # This is a filter condition
                            condition, params = self._convert_rql_condition(arg, params)
                            if condition:
                                conditions.append(condition)
                    else:
                        # Handle other condition types
                        condition, params = self._convert_rql_condition(arg, params)
                        if condition:
                            conditions.append(condition)

                # Apply WHERE conditions if any
                if conditions:
                    where_condition = conditions[0]
                    for condition in conditions[1:]:
                        where_condition = exp.And(
                            this=where_condition, expression=condition
                        )
                    query = query.where(where_condition)

            elif operator == "or":
                # Handle OR operations
                conditions = []
                for arg in args:
                    condition, params = self._convert_rql_condition(arg, params)
                    if condition:
                        conditions.append(condition)

                if conditions:
                    where_condition = conditions[0]
                    for condition in conditions[1:]:
                        where_condition = exp.Or(
                            this=where_condition, expression=condition
                        )
                    query = query.where(where_condition)

            elif operator == "select":
                # Handle field selection
                if args:
                    query = sqlglot.select(*args).from_(query.find(exp.Table))

            elif operator == "sort":
                # Handle sorting
                for arg in args:
                    if isinstance(arg, tuple) and len(arg) == 2:
                        # Handle ('-', 'field') or ('+', 'field') tuples
                        direction, field = arg
                        if direction == "-":
                            query = query.order_by(exp.Ordered(this=field, desc=True))
                        else:
                            query = query.order_by(field)
                    elif isinstance(arg, str):
                        # Handle string format like "-field" or "+field"
                        if arg.startswith("-"):
                            query = query.order_by(exp.Ordered(this=arg[1:], desc=True))
                        elif arg.startswith("+"):
                            query = query.order_by(arg[1:])
                        else:
                            query = query.order_by(arg)
                    else:
                        # Default to ascending
                        query = query.order_by(str(arg))

            elif operator == "limit":
                # Handle limiting
                if args:
                    limit_val = args[0]
                    query = query.limit(limit_val)
                    if len(args) > 1:
                        offset_val = args[1]
                        query = query.offset(offset_val)

            elif operator in [
                "eq",
                "ne",
                "lt",
                "le",
                "gt",
                "ge",
                "contains",
                "in",
                "out",
            ]:
                # Handle comparison operations
                condition, params = self._convert_rql_condition(rql_node, params)
                if condition:
                    query = query.where(condition)

        return query, params

    def _convert_rql_condition(
        self, rql_node, params: list[Any]
    ) -> tuple[exp.Expression | None, list[Any]]:
        """Convert a single RQL condition to SQLGlot expression."""
        if not isinstance(rql_node, dict):
            return None, params

        operator = rql_node.get("name")
        args = rql_node.get("args", [])

        if len(args) < 2:
            return None, params

        field_name = args[0]
        value = args[1]

        column = exp.Column(this=field_name)

        if operator == "eq":
            params.append(value)
            return exp.EQ(this=column, expression=exp.Placeholder()), params

        elif operator == "ne":
            params.append(value)
            return exp.NEQ(this=column, expression=exp.Placeholder()), params

        elif operator == "lt":
            params.append(value)
            return exp.LT(this=column, expression=exp.Placeholder()), params

        elif operator == "le":
            params.append(value)
            return exp.LTE(this=column, expression=exp.Placeholder()), params

        elif operator == "gt":
            params.append(value)
            return exp.GT(this=column, expression=exp.Placeholder()), params

        elif operator == "ge":
            params.append(value)
            return exp.GTE(this=column, expression=exp.Placeholder()), params

        elif operator == "contains":
            params.append(f"%{value}%")
            return exp.Like(this=column, expression=exp.Placeholder()), params

        elif operator == "in":
            if isinstance(value, list | tuple):
                in_params = []
                for val in value:
                    params.append(val)
                    in_params.append(exp.Placeholder())
                return exp.In(this=column, expressions=in_params), params

        elif operator == "out":
            if isinstance(value, list | tuple):
                in_params = []
                for val in value:
                    params.append(val)
                    in_params.append(exp.Placeholder())
                return exp.Not(this=exp.In(this=column, expressions=in_params)), params

        return None, params


def convert_rql_to_sql(
    table_name: str, rql_query: str, dialect: str = "duckdb"
) -> tuple[str, list[Any]]:
    """Convenience function to convert RQL to SQL."""
    converter = RQLToSQLConverter(dialect=dialect)
    return converter.convert_to_sql(table_name, rql_query)
