"""FastAPI app builder with dependency injection - thin wrapper over DatabaseService."""

from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, UploadFile

from .config import FastVimesSettings
from .database_service import DatabaseService


def build_api(db_service: DatabaseService, settings: FastVimesSettings) -> FastAPI:
    """Build FastAPI app with dependency injection.

    All routes are thin wrappers over DatabaseService methods.
    """
    app = FastAPI(
        title="FastVimes API",
        description="""
## FastVimes Auto-Generated Database API

Automatically generated REST API for DuckDB databases with RQL query support.

### Features
- **Auto-generated endpoints** from database schema
- **RQL query language** for filtering and sorting
- **Multiple output formats** (JSON, CSV, Parquet)
- **Bulk operations** with file upload support
- **Health monitoring** for production deployments

### RQL Query Examples
- `?eq(id,123)` - Filter where id equals 123
- `?lt(age,30)` - Filter where age less than 30
- `?sort(+name,-created_at)` - Sort by name ASC, created_at DESC
- `?limit(10,20)` - Skip 20 records, take 10 (pagination)
- `?select(id,name,email)` - Only return specified fields

### Bulk Operations
Upload CSV, Parquet, or JSON files for efficient bulk insert/upsert/delete operations.
        """,
        version="0.2.0",
        docs_url="/docs",  # Available at /api/docs when mounted
        redoc_url="/redoc",  # Available at /api/redoc when mounted
        contact={
            "name": "FastVimes",
            "url": "https://github.com/adonm/fastvimes",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    # Store db_service for dependency injection
    app.state.db_service = db_service

    def get_db() -> DatabaseService:
        """Dependency to get database service."""
        return app.state.db_service

    # HEALTH endpoint
    @app.get(
        "/health",
        summary="Health Check",
        description="Health check endpoint for monitoring, load balancers, and service discovery.",
        tags=["Health"],
        response_description="Service health status with database connectivity information"
    )
    async def health_check(db: DatabaseService = Depends(get_db)) -> dict[str, Any]:
        """Health check endpoint for monitoring and load balancers."""
        try:
            # Test database connectivity
            tables = db.list_tables()
            table_count = len(tables)
            
            # Test a simple query
            result = db.execute_query("SELECT 1 as health_check")
            db_connected = len(result) == 1 and result[0]["health_check"] == 1
            
            status = "healthy" if db_connected else "unhealthy"
            
            return {
                "status": status,
                "database": {
                    "connected": db_connected,
                    "table_count": table_count,
                },
                "version": "0.2.0",
                "service": "FastVimes"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "database": {
                    "connected": False,
                    "table_count": 0,
                },
                "version": "0.2.0",
                "service": "FastVimes"
            }

    # META routes
    @app.get(
        "/v1/meta/tables",
        summary="List Tables",
        description="List all tables and views in the database with metadata.",
        tags=["Metadata"],
        response_description="Array of table information including name and type"
    )
    async def list_tables(
        db: DatabaseService = Depends(get_db),
    ) -> list[dict[str, Any]]:
        """List all tables and views."""
        return db.list_tables()

    @app.get(
        "/v1/meta/schema/{table_name}",
        summary="Get Table Schema",
        description="Get detailed schema information for a specific table including column names, types, and constraints.",
        tags=["Metadata"],
        response_description="Array of column definitions with name, type, nullable, and key information"
    )
    async def get_table_schema(
        table_name: str, db: DatabaseService = Depends(get_db)
    ) -> list[dict[str, Any]]:
        """Get schema for a specific table."""
        try:
            return db.get_table_schema(table_name)
        except Exception as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

    # DATA routes
    @app.get(
        "/v1/data/{table_name}",
        summary="Get Table Data",
        description="""
Get table data with optional RQL filtering, sorting, and pagination.

**RQL Examples:**
- `?eq(id,123)` - Filter where id equals 123
- `?lt(age,30)&sort(+name)` - Age < 30, sorted by name
- `?limit(10,20)&format=csv` - Skip 20, take 10, CSV format
        """,
        tags=["Data Operations"],
        response_description="Table data in specified format (JSON, CSV, or Parquet)"
    )
    async def get_table_data(
        table_name: str,
        rql_query: str = Query(None, description="RQL query string for filtering and sorting"),
        limit: int = Query(100, description="Maximum number of records to return"),
        offset: int = Query(0, description="Number of records to skip for pagination"),
        format: str = Query("json", description="Output format: json, csv, parquet"),
        db: DatabaseService = Depends(get_db),
    ):
        """Get table data with RQL filtering."""
        try:
            return db.get_table_data(table_name, rql_query, limit, offset, format)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.post("/v1/data/{table_name}")
    async def create_record(
        table_name: str, data: dict[str, Any], db: DatabaseService = Depends(get_db)
    ) -> dict[str, Any]:
        """Create a new record."""
        try:
            return db.create_record(table_name, data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.put("/v1/data/{table_name}")
    async def update_records(
        table_name: str,
        data: dict[str, Any],
        rql_query: str = Query(
            None, description="RQL filter for which records to update"
        ),
        db: DatabaseService = Depends(get_db),
    ) -> dict[str, int]:
        """Update records matching the filter."""
        try:
            # Convert RQL to filters dict for update_records
            filters = {}  # TODO: Parse RQL query into filters
            updated_count = db.update_records(table_name, data, filters)
            return {"updated": updated_count}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.delete("/v1/data/{table_name}")
    async def delete_records(
        table_name: str,
        rql_query: str = Query(
            None, description="RQL filter for which records to delete"
        ),
        db: DatabaseService = Depends(get_db),
    ) -> dict[str, int]:
        """Delete records matching the filter."""
        try:
            # Convert RQL to filters dict for delete_records
            filters = {}  # TODO: Parse RQL query into filters
            deleted_count = db.delete_records(table_name, filters)
            return {"deleted": deleted_count}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    # QUERY route
    @app.post("/v1/query")
    async def execute_query(
        query: str,
        params: list[Any] = None,
        format: str = Query("json", description="Output format: json, csv, parquet"),
        db: DatabaseService = Depends(get_db),
    ):
        """Execute raw SQL query."""
        try:
            return db.execute_query(query, params or [])
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    # BULK operation routes
    @app.post("/v1/data/{table_name}/bulk-insert")
    async def bulk_insert(
        table_name: str,
        file: UploadFile,
        format: str = Query(default="auto", description="File format: json, csv, parquet, auto"),
        db: DatabaseService = Depends(get_db),
    ):
        """Bulk insert records from uploaded file."""
        try:
            # Save uploaded file temporarily
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1] if '.' in file.filename else 'tmp'}") as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                records_inserted = db.bulk_insert_from_file(table_name, tmp_path, format)
                return {
                    "message": "Bulk insert completed successfully",
                    "records_inserted": records_inserted,
                    "table_name": table_name
                }
            finally:
                os.unlink(tmp_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.post("/v1/data/{table_name}/bulk-upsert")
    async def bulk_upsert(
        table_name: str,
        file: UploadFile,
        key_columns: str = Query(description="Comma-separated list of key columns for upsert"),
        format: str = Query(default="auto", description="File format: json, csv, parquet, auto"),
        db: DatabaseService = Depends(get_db),
    ):
        """Bulk upsert records from uploaded file."""
        try:
            # Save uploaded file temporarily
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1] if '.' in file.filename else 'tmp'}") as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                key_list = [k.strip() for k in key_columns.split(",")]
                upsert_result = db.bulk_upsert_from_file(table_name, tmp_path, key_list, format)
                return {
                    "message": "Bulk upsert completed successfully",
                    "records_inserted": upsert_result["inserted"],
                    "records_updated": upsert_result["updated"],
                    "table_name": table_name,
                    "key_columns": key_list
                }
            finally:
                os.unlink(tmp_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.post("/v1/data/{table_name}/bulk-delete")
    async def bulk_delete(
        table_name: str,
        file: UploadFile,
        key_columns: str = Query(description="Comma-separated list of key columns for deletion"),
        format: str = Query(default="auto", description="File format: json, csv, parquet, auto"),
        db: DatabaseService = Depends(get_db),
    ):
        """Bulk delete records based on uploaded file."""
        try:
            # Save uploaded file temporarily
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1] if '.' in file.filename else 'tmp'}") as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                key_list = [k.strip() for k in key_columns.split(",")]
                records_deleted = db.bulk_delete_from_file(table_name, tmp_path, key_list, format)
                return {
                    "message": "Bulk delete completed successfully",
                    "records_deleted": records_deleted,
                    "table_name": table_name,
                    "key_columns": key_list
                }
            finally:
                os.unlink(tmp_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    return app
