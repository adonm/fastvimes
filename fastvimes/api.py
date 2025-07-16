"""FastAPI app builder with dependency injection - thin wrapper over DatabaseService."""

from fastapi import FastAPI, Depends, HTTPException, Query
from typing import Dict, Any, List

from .config import FastVimesSettings
from .database_service import DatabaseService


def build_api(db_service: DatabaseService, settings: FastVimesSettings) -> FastAPI:
    """Build FastAPI app with dependency injection.
    
    All routes are thin wrappers over DatabaseService methods.
    """
    app = FastAPI(
        title="FastVimes API",
        description="Auto-generated API from DuckDB schema",
        version="0.2.0",
    )
    
    # Store db_service for dependency injection
    app.state.db_service = db_service
    
    def get_db() -> DatabaseService:
        """Dependency to get database service."""
        return app.state.db_service

    # META routes
    @app.get("/v1/meta/tables")
    async def list_tables(db: DatabaseService = Depends(get_db)) -> List[Dict[str, Any]]:
        """List all tables and views."""
        return db.list_tables()

    @app.get("/v1/meta/schema/{table_name}")
    async def get_table_schema(
        table_name: str, 
        db: DatabaseService = Depends(get_db)
    ) -> List[Dict[str, Any]]:
        """Get schema for a specific table."""
        try:
            return db.get_table_schema(table_name)
        except Exception as e:
            raise HTTPException(status_code=404, detail=str(e))

    # DATA routes
    @app.get("/v1/data/{table_name}")
    async def get_table_data(
        table_name: str,
        rql_query: str = Query(None, description="RQL query string"),
        limit: int = Query(100, description="Maximum number of records"),
        offset: int = Query(0, description="Number of records to skip"),
        format: str = Query("json", description="Output format: json, csv, parquet"),
        db: DatabaseService = Depends(get_db)
    ):
        """Get table data with RQL filtering."""
        try:
            return db.get_table_data(table_name, rql_query, limit, offset, format)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/v1/data/{table_name}")
    async def create_record(
        table_name: str,
        data: Dict[str, Any],
        db: DatabaseService = Depends(get_db)
    ) -> Dict[str, Any]:
        """Create a new record."""
        try:
            return db.create_record(table_name, data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.put("/v1/data/{table_name}")
    async def update_records(
        table_name: str,
        data: Dict[str, Any],
        rql_query: str = Query(None, description="RQL filter for which records to update"),
        db: DatabaseService = Depends(get_db)
    ) -> Dict[str, int]:
        """Update records matching the filter."""
        try:
            # Convert RQL to filters dict for update_records
            filters = {}  # TODO: Parse RQL query into filters
            updated_count = db.update_records(table_name, data, filters)
            return {"updated": updated_count}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.delete("/v1/data/{table_name}")
    async def delete_records(
        table_name: str,
        rql_query: str = Query(None, description="RQL filter for which records to delete"),
        db: DatabaseService = Depends(get_db)
    ) -> Dict[str, int]:
        """Delete records matching the filter."""
        try:
            # Convert RQL to filters dict for delete_records
            filters = {}  # TODO: Parse RQL query into filters
            deleted_count = db.delete_records(table_name, filters)
            return {"deleted": deleted_count}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    # QUERY route
    @app.post("/v1/query")
    async def execute_query(
        query: str,
        params: List[Any] = None,
        format: str = Query("json", description="Output format: json, csv, parquet"),
        db: DatabaseService = Depends(get_db)
    ):
        """Execute raw SQL query."""
        try:
            return db.execute_query(query, params or [])
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return app
