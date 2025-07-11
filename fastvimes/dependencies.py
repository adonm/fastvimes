"""FastAPI dependencies for query parameter parsing."""

from typing import Any

from fastapi import Depends, Query, Request

from .rql import RQLFilter, parse_rql_params


class QueryParams:
    """Dependency to parse query parameters with FastAPI."""

    def __init__(self, request: Request):
        self.request = request
        self.filter_parser = RQLFilter()

    @property
    def filters(self) -> dict[str, Any]:
        """Get RQL-style filters from query parameters."""
        return parse_rql_params(dict(self.request.query_params))

    def get_pagination(self) -> tuple[int | None, int | None]:
        """Get pagination parameters."""
        limit = self.request.query_params.get("limit")
        offset = self.request.query_params.get("offset")

        try:
            limit = int(limit) if limit else None
        except ValueError:
            limit = None

        try:
            offset = int(offset) if offset else None
        except ValueError:
            offset = None

        return limit, offset

    def get_sorting(self) -> str | None:
        """Get sorting parameter."""
        return self.request.query_params.get("sort")

    def get_ordering(self) -> str | None:
        """Get ordering parameter (alias for sort)."""
        return self.request.query_params.get("order") or self.get_sorting()


def get_query_params(request: Request) -> QueryParams:
    """FastAPI dependency to inject query parameters."""
    return QueryParams(request)


def get_filters(
    query_params: QueryParams = Depends(get_query_params),
) -> dict[str, Any]:
    """FastAPI dependency to inject RQL-style filters."""
    return query_params.filters["filters"]


def get_pagination(
    query_params: QueryParams = Depends(get_query_params),
) -> tuple[int | None, int | None]:
    """FastAPI dependency to inject pagination parameters."""
    return query_params.get_pagination()


def get_sorting(query_params: QueryParams = Depends(get_query_params)) -> str | None:
    """FastAPI dependency to inject sorting parameter."""
    return query_params.get_sorting()


# More specific dependencies for common patterns using Query
def get_limit(limit: int | None = Query(None)) -> int | None:
    """FastAPI dependency for limit parameter."""
    return limit


def get_offset(offset: int | None = Query(None)) -> int | None:
    """FastAPI dependency for offset parameter."""
    return offset


def get_sort(sort: str | None = Query(None)) -> str | None:
    """FastAPI dependency for sort parameter."""
    return sort
