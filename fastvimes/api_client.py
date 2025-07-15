"""HTTP API client for NiceGUI components to consume FastAPI endpoints."""

from typing import Any
from urllib.parse import urlencode

import httpx


class FastVimesAPIClient:
    """Client for making HTTP requests to FastVimes FastAPI endpoints.

    This is designed for NiceGUI components to consume the same FastAPI endpoints
    that external clients use, ensuring API consistency.
    """

    def __init__(self, base_url: str = "http://localhost:8000", db_service=None):
        """Initialize API client with base URL.

        Args:
            base_url: Base URL for HTTP requests
            db_service: Optional database service for in-process calls (development mode)
        """
        self.base_url = base_url.rstrip("/")
        self.db_service = db_service  # For in-process development mode
        # Use synchronous client since NiceGUI runs synchronously
        self.client = httpx.Client(timeout=30.0) if not db_service else None

    def close(self):
        """Close the HTTP client."""
        if self.client:
            self.client.close()

    def list_tables(self) -> list[dict[str, Any]]:
        """Get list of all tables."""
        if self.db_service:
            # In-process call for development
            return self.db_service.list_tables()

        response = self.client.get(f"{self.base_url}/tables")
        response.raise_for_status()
        return response.json()["tables"]

    def get_table_data(
        self,
        table_name: str,
        rql_query: str | None = None,
        limit: int | None = 100,
        offset: int | None = 0,
    ) -> dict[str, Any]:
        """Get table data with optional RQL filtering."""
        if self.db_service:
            # In-process call for development
            return self.db_service.get_table_data(table_name, rql_query, limit, offset)

        params = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        url = f"{self.base_url}/{table_name}"
        if rql_query:
            # Combine RQL query with pagination params
            if params:
                query_string = f"{rql_query}&{urlencode(params)}"
            else:
                query_string = rql_query
            url = f"{url}?{query_string}"
        elif params:
            url = f"{url}?{urlencode(params)}"

        response = self.client.get(url)
        response.raise_for_status()
        return response.json()

    def create_record(
        self, table_name: str, record_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a new record in the specified table."""
        if self.db_service:
            # In-process call for development - return record directly like API does
            record = self.db_service.create_record(table_name, record_data)
            return {"message": "Record created successfully", "record": record}

        response = self.client.post(f"{self.base_url}/{table_name}", json=record_data)
        response.raise_for_status()
        return response.json()

    def get_table_schema(self, table_name: str) -> list[dict[str, Any]]:
        """Get schema information for a table."""
        if self.db_service:
            # In-process call for development
            return self.db_service.get_table_schema(table_name)

        response = self.client.get(f"{self.base_url}/{table_name}/schema")
        response.raise_for_status()
        return response.json()["schema"]
