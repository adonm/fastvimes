"""RQL (Resource Query Language) implementation using SQLGlot for FastVimes."""

import logging
from typing import Any, Dict, List, Optional, Union


import sqlglot
from sqlglot import exp, parse
from sqlglot.expressions import Select, Column, Table
from pyrql import parse as parse_rql

logger = logging.getLogger(__name__)


class RQLSQLGlotTranslator:
    """RQL translator that converts RQL queries to SQLGlot expressions."""

    # Core RQL operators mapping to SQLGlot expressions
    OPERATORS = {
        # Comparison operators
        "eq": lambda col, val: exp.EQ(this=col, expression=_value_to_literal(val)),
        "ne": lambda col, val: exp.NEQ(this=col, expression=_value_to_literal(val)),
        "gt": lambda col, val: exp.GT(this=col, expression=_value_to_literal(val)),
        "ge": lambda col, val: exp.GTE(this=col, expression=_value_to_literal(val)),
        "lt": lambda col, val: exp.LT(this=col, expression=_value_to_literal(val)),
        "le": lambda col, val: exp.LTE(this=col, expression=_value_to_literal(val)),
        
        # Set operations
        "in": lambda col, val: exp.In(
            this=col, 
            expressions=[_value_to_literal(v) for v in (val if isinstance(val, list) else [val])]
        ),
        "out": lambda col, val: exp.Not(
            this=exp.In(
                this=col, 
                expressions=[_value_to_literal(v) for v in (val if isinstance(val, list) else [val])]
            )
        ),
        "contains": lambda col, val: exp.Like(
            this=col, 
            expression=exp.Literal.string(f"%{val}%")
        ),
        "excludes": lambda col, val: exp.Not(
            this=exp.Like(
                this=col, 
                expression=exp.Literal.string(f"%{val}%")
            )
        ),
    }

    def __init__(self):
        pass

    def parse_rql_query(self, rql_string: str) -> Dict[str, Any]:
        """Parse RQL query string using pyrql and return structured data."""
        # Handle empty or whitespace-only queries
        if not rql_string or not rql_string.strip():
            return {
                "filters": [],
                "sort": [],
                "limit": None,
                "offset": None,
                "select": [],
                "count": False,
                "distinct": False
            }
            
        try:
            # Parse the RQL query using pyrql
            parsed = parse_rql(rql_string)
            
            # Extract filters and operations from parsed query
            result = {
                "filters": [],
                "sort": [],
                "limit": None,
                "offset": None,
                "select": [],
                "count": False,
                "distinct": False
            }
            
            # Process the parsed query tree
            self._process_query_node(parsed, result)
            
            return result
        except Exception as e:
            logger.warning(f"Failed to parse RQL query '{rql_string}': {e}")
            # If parsing fails, return empty result
            return {
                "filters": [],
                "sort": [],
                "limit": None,
                "offset": None,
                "select": [],
                "count": False,
                "distinct": False
            }

    def _process_query_node(self, node: Dict[str, Any], result: Dict[str, Any]):
        """Process a single query node from pyrql parse tree."""
        if not isinstance(node, dict) or "name" not in node:
            return
        
        name = node["name"]
        args = node.get("args", [])
        
        if name in ["and", "or"]:
            # Logical operations - recursively process args
            for arg in args:
                self._process_query_node(arg, result)
        elif name in self.OPERATORS:
            # Filter operation
            if len(args) >= 2:
                field = args[0]
                value = args[1]
                # Handle tuple values (e.g., from 'in' operator)
                if isinstance(value, tuple):
                    value = list(value)
                
                # Create SQLGlot filter expression
                column = Column(this=field)
                filter_func = self.OPERATORS[name]
                filter_expr = filter_func(column, value)
                result["filters"].append(filter_expr)
                
        elif name == "sort":
            # Sort operation - pyrql returns tuples like ('+', 'name') or ('-', 'age')
            if args:
                sorts = []
                for arg in args:
                    if isinstance(arg, tuple) and len(arg) == 2:
                        direction, field = arg
                        ascending = direction == "+"
                        if ascending:
                            sorts.append(exp.Ordered(this=Column(this=field)))
                        else:
                            sorts.append(exp.Ordered(this=Column(this=field), desc=True))
                    elif isinstance(arg, str):
                        # Handle simple field names (default ascending)
                        sorts.append(exp.Ordered(this=Column(this=arg)))
                result["sort"] = sorts
        elif name == "limit":
            # Limit operation
            if args:
                result["limit"] = args[0]
                if len(args) > 1:
                    result["offset"] = args[1]
        elif name == "select":
            # Select operation
            result["select"] = [Column(this=field) for field in args]
        elif name == "count":
            result["count"] = True
        elif name == "distinct":
            result["distinct"] = True

    def build_select_query(
        self, 
        table_name: str, 
        rql_data: Dict[str, Any]
    ) -> str:
        """Build a SELECT query from parsed RQL data."""
        
        # Create table expression
        table = Table(this=table_name)
        
        # Create select expression
        if rql_data["select"]:
            select_columns = rql_data["select"]
        elif rql_data["count"]:
            select_columns = [exp.Count(this=exp.Star())]
        else:
            select_columns = [exp.Star()]
        
        select_expr = Select(expressions=select_columns).from_(table)
        
        # Add WHERE conditions
        if rql_data["filters"]:
            combined_filter = rql_data["filters"][0]
            for filter_expr in rql_data["filters"][1:]:
                combined_filter = exp.And(this=combined_filter, expression=filter_expr)
            select_expr = select_expr.where(combined_filter)
        
        # Add ORDER BY
        if rql_data["sort"]:
            for order_expr in rql_data["sort"]:
                select_expr = select_expr.order_by(order_expr)
        
        # Add LIMIT
        if rql_data["limit"]:
            select_expr = select_expr.limit(rql_data["limit"])
        
        # Add OFFSET  
        if rql_data["offset"]:
            select_expr = select_expr.offset(rql_data["offset"])
        
        # Handle DISTINCT
        if rql_data["distinct"]:
            select_expr = select_expr.distinct()
        
        # Generate SQL for DuckDB
        return select_expr.sql(dialect="duckdb")

    def translate_rql_to_sql(self, table_name: str, rql_string: str) -> str:
        """Translate RQL query string to SQL."""
        rql_data = self.parse_rql_query(rql_string)
        return self.build_select_query(table_name, rql_data)

    def parse_query_params(self, query_params: Dict[str, Any]) -> str:
        """Parse FastAPI query parameters into RQL string."""
        parts = []
        
        # Special parameters that should not be treated as filters
        special_params = {"limit", "offset", "sort", "order"}
        
        for key, value in query_params.items():
            # Skip special parameters for now (handle them separately)
            if key in special_params:
                continue
                
            # Handle RQL function syntax in keys
            if "(" in key and ")" in key:
                parts.append(key)
            else:
                # Handle key=value pairs
                if isinstance(value, str) and "=" in value:
                    # FIQL syntax: field=operator=value
                    parts.append(f"{key}={value}")
                else:
                    # Direct syntax: field=value (implies eq)
                    parts.append(f"eq({key},{value})")
        
        # Handle special parameters
        if "limit" in query_params:
            limit_value = query_params["limit"]
            if "offset" in query_params:
                parts.append(f"limit({limit_value},{query_params['offset']})")
            else:
                parts.append(f"limit({limit_value})")
        
        if "sort" in query_params:
            sort_value = query_params["sort"]
            if isinstance(sort_value, str):
                # Parse sort=+field,-field format
                sort_fields = []
                for sort_spec in sort_value.split(','):
                    sort_spec = sort_spec.strip()
                    if sort_spec.startswith('+'):
                        sort_fields.append(('+', sort_spec[1:]))
                    elif sort_spec.startswith('-'):
                        sort_fields.append(('-', sort_spec[1:]))
                    else:
                        sort_fields.append(('+', sort_spec))
                
                if sort_fields:
                    sort_args = ','.join([f"({direction},{field})" for direction, field in sort_fields])
                    parts.append(f"sort({sort_args})")
        
        return "&".join(parts) if parts else ""


def _value_to_literal(value: Any) -> exp.Expression:
    """Convert Python value to SQLGlot literal expression."""
    if isinstance(value, str):
        return exp.Literal.string(value)
    elif isinstance(value, bool):
        return exp.Literal.number(str(value).lower())
    elif isinstance(value, (int, float)):
        return exp.Literal.number(str(value))
    elif value is None:
        return exp.Null()
    else:
        return exp.Literal.string(str(value))


def parse_rql_params(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Parse query parameters for RQL filters using SQLGlot.
    
    Args:
        query_params: All query parameters from request
        
    Returns:
        Dictionary containing parsed RQL data ready for SQL generation
    """
    translator = RQLSQLGlotTranslator()
    rql_string = translator.parse_query_params(query_params)
    return translator.parse_rql_query(rql_string)


def apply_rql_to_sql(table_name: str, query_params: Dict[str, Any]) -> str:
    """Apply RQL query parameters to generate SQL query.
    
    Args:
        table_name: Name of the table to query
        query_params: Query parameters from FastAPI request
        
    Returns:
        SQL query string for DuckDB
    """
    translator = RQLSQLGlotTranslator()
    rql_string = translator.parse_query_params(query_params)
    return translator.translate_rql_to_sql(table_name, rql_string)
