"""RQL (Resource Query Language) implementation for FastVimes using pyrql."""

from typing import Any, Dict, List, Optional, Union
from urllib.parse import unquote_plus

import ibis
from pyrql import parse, Query


class RQLFilter:
    """RQL (Resource Query Language) filter parser and applier using pyrql."""

    # Core RQL operators mapping to Ibis operations
    OPERATORS = {
        # Comparison operators
        "eq": lambda col, val: col == val,
        "ne": lambda col, val: col != val,
        "gt": lambda col, val: col > val,
        "ge": lambda col, val: col >= val,
        "lt": lambda col, val: col < val,
        "le": lambda col, val: col <= val,
        
        # Set operations
        "in": lambda col, val: col.isin(val) if isinstance(val, list) else col.isin([val]),
        "out": lambda col, val: ~col.isin(val) if isinstance(val, list) else ~col.isin([val]),
        "contains": lambda col, val: col.contains(val),
        "excludes": lambda col, val: ~col.contains(val),
    }

    def __init__(self):
        pass

    def parse_query_string(self, query_string: str) -> Dict[str, Any]:
        """Parse RQL query string using pyrql."""
        try:
            # Parse the RQL query using pyrql
            parsed = parse(query_string)
            
            # Extract filters and operations from parsed query
            result = {
                "filters": {},
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
            # If parsing fails, return empty result
            return {
                "filters": {},
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
                result["filters"][f"{field}__{name}"] = value
        elif name == "sort":
            # Sort operation - pyrql returns tuples like ('+', 'name') or ('-', 'age')
            if args:
                sorts = []
                for arg in args:
                    if isinstance(arg, tuple) and len(arg) == 2:
                        direction, field = arg
                        ascending = direction == "+"
                        sorts.append((field, ascending))
                    elif isinstance(arg, str):
                        # Handle simple field names (default ascending)
                        sorts.append((arg, True))
                result["sort"] = sorts
        elif name == "limit":
            # Limit operation
            if args:
                result["limit"] = args[0]
                if len(args) > 1:
                    result["offset"] = args[1]
        elif name == "select":
            # Select operation
            result["select"] = args
        elif name == "count":
            result["count"] = True
        elif name == "distinct":
            result["distinct"] = True

    def apply_filters(self, table: ibis.Table, filters: Dict[str, Any]) -> ibis.Table:
        """Apply RQL filters to an Ibis table."""
        for filter_key, value in filters.items():
            try:
                # Parse field__operator format
                if "__" in filter_key:
                    field_name, operator = filter_key.rsplit("__", 1)
                else:
                    field_name, operator = filter_key, "eq"
                
                if hasattr(table, field_name) and operator in self.OPERATORS:
                    column = getattr(table, field_name)
                    filter_func = self.OPERATORS[operator]
                    table = table.filter(filter_func(column, value))
                    
            except (ValueError, AttributeError):
                # Skip invalid filters rather than erroring
                continue
        
        return table

    def apply_rql_to_data(self, data: List[Dict[str, Any]], rql_string: str) -> List[Dict[str, Any]]:
        """Apply RQL query directly to data using pyrql Query engine."""
        try:
            query_engine = Query(data)
            result = query_engine.query(rql_string)
            return result.all()
        except Exception as e:
            # If query fails, return original data
            return data


def parse_rql_params(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Parse query parameters for RQL filters.
    
    Args:
        query_params: All query parameters from request
        
    Returns:
        Dictionary containing parsed RQL filters and operators
    """
    # Convert query params to RQL string
    rql_string = _build_rql_string(query_params)
    
    parser = RQLFilter()
    return parser.parse_query_string(rql_string)


def _build_rql_string(query_params: Dict[str, Any]) -> str:
    """Build RQL query string from query parameters."""
    parts = []
    
    # Special parameters that should not be treated as filters
    special_params = {"limit", "offset", "sort", "order"}
    
    for key, value in query_params.items():
        # Skip special parameters
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
                parts.append(f"{key}={value}")
    
    return "&".join(parts) if parts else ""


def apply_rql_to_table(table: ibis.Table, rql_string: str) -> ibis.Table:
    """Apply RQL query to Ibis table (convenience function)."""
    parser = RQLFilter()
    parsed = parser.parse_query_string(rql_string)
    
    # Apply filters
    if parsed["filters"]:
        table = parser.apply_filters(table, parsed["filters"])
    
    # Apply sorting
    if parsed["sort"]:
        for field, ascending in parsed["sort"]:
            if hasattr(table, field):
                column = getattr(table, field)
                table = table.order_by(column.asc() if ascending else column.desc())
    
    # Apply limit/offset
    if parsed["limit"]:
        if parsed["offset"]:
            table = table.limit(parsed["limit"], offset=parsed["offset"])
        else:
            table = table.limit(parsed["limit"])
    
    # Apply select
    if parsed["select"]:
        select_fields = [field for field in parsed["select"] if hasattr(table, field)]
        if select_fields:
            table = table.select(*select_fields)
    
    return table
