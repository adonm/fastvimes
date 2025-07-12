"""RQL-aligned CLI for FastVimes - mirrors API endpoints exactly."""

import typer
import json
import threading
import time
import httpx
from typing import Optional, Any
from pathlib import Path

app = typer.Typer(help="FastVimes CLI - RQL-enabled database operations")


def _get_app(db: str):
    """Get FastVimes app instance."""
    from fastvimes.app import FastVimes
    # Configure for read-write access for testing
    return FastVimes(db_path=db, default_mode="readwrite")


def _format_output(data: Any) -> None:
    """Format and print output as JSON."""
    if data is None:
        return
    print(json.dumps(data, indent=2, default=str))


# Core table operations mirroring /api/* endpoints

@app.command("tables")
def list_tables(
    db: str = typer.Option(..., "--db", help="Database file path"),
):
    """List all tables (mirrors GET /api/tables)."""
    fv = _get_app(db)
    tables = fv.list_tables_api()
    _format_output({"tables": tables})


@app.command("schema")
def show_schema(
    db: str = typer.Option(..., "--db", help="Database file path"),
    table: Optional[str] = typer.Option(None, "--table", help="Specific table to show"),
):
    """Show database schema information."""
    fv = _get_app(db)
    
    if table:
        # Show specific table schema
        try:
            schema = fv.db_service.get_table_schema(table)
            _format_output(schema)
        except Exception as e:
            typer.echo(f"Error getting schema for table '{table}': {e}", err=True)
            raise typer.Exit(1)
    else:
        # Show all tables with basic info
        tables = fv.list_tables_api()
        schemas = {}
        for table_name in tables:
            try:
                schemas[table_name] = fv.db_service.get_table_schema(table_name)
            except Exception as e:
                schemas[table_name] = {"error": str(e)}
        _format_output({"schemas": schemas})


@app.command("config")
def show_config(
    db: str = typer.Option(..., "--db", help="Database file path"),
):
    """Show current configuration."""
    fv = _get_app(db)
    config_dict = {
        "db_path": fv.config.db_path,
        "read_only": fv.config.read_only,
        "admin_enabled": fv.config.admin_enabled,
        "default_mode": fv.config.default_mode,
        "default_html": fv.config.default_html,
        "extensions": fv.config.extensions,
        "tables": {name: config.model_dump() for name, config in fv.config.tables.items()}
    }
    _format_output(config_dict)


@app.command("get")
def get_table_data(
    table: str,
    db: str = typer.Option(..., "--db", help="Database file path"),
    # RQL-style parameters matching API endpoints
    eq: Optional[str] = typer.Option(None, help="Equal filter: eq(field,value)"),
    lt: Optional[str] = typer.Option(None, help="Less than: lt(field,value)"),
    gt: Optional[str] = typer.Option(None, help="Greater than: gt(field,value)"),
    contains: Optional[str] = typer.Option(None, help="Contains: contains(field,value)"),
    sort: Optional[str] = typer.Option(None, help="Sort: +field,-field"),
    limit: Optional[int] = typer.Option(None, help="Limit results"),
    offset: Optional[int] = typer.Option(None, help="Offset results"),
    # Raw RQL query string (most flexible)
    rql: Optional[str] = typer.Option(None, help="Raw RQL query string"),
):
    """Get data from table with RQL filters (mirrors GET /api/{table})."""
    fv = _get_app(db)
    
    # Build RQL query string from parameters
    rql_parts = []
    
    # Handle individual RQL parameters
    if eq:
        rql_parts.append(f"eq({eq})")
    if lt:
        rql_parts.append(f"lt({lt})")
    if gt:
        rql_parts.append(f"gt({gt})")
    if contains:
        rql_parts.append(f"contains({contains})")
    if sort:
        # Parse sort format: +field,-field becomes sort(+field,-field)
        rql_parts.append(f"sort({sort})")
    if limit:
        if offset:
            rql_parts.append(f"limit({limit},{offset})")
        else:
            rql_parts.append(f"limit({limit})")
    
    # Build final RQL string
    if rql:
        # Use provided raw RQL
        final_rql = rql
    elif rql_parts:
        # Combine individual parts with AND
        if len(rql_parts) == 1:
            final_rql = rql_parts[0]
        else:
            filters = [part for part in rql_parts if not part.startswith(('sort(', 'limit('))]
            non_filters = [part for part in rql_parts if part.startswith(('sort(', 'limit('))]
            if len(filters) > 1:
                filter_part = f"and({','.join(filters)})"
            elif len(filters) == 1:
                filter_part = filters[0]
            else:
                filter_part = ""
            
            all_parts = ([filter_part] if filter_part else []) + non_filters
            final_rql = "&".join(all_parts)
    else:
        final_rql = ""
    
    # Convert individual parameters to proper query parameters dict
    query_params = {}
    
    if eq:
        query_params[f"eq({eq})"] = None
    if lt:
        query_params[f"lt({lt})"] = None
    if gt:
        query_params[f"gt({gt})"] = None
    if contains:
        query_params[f"contains({contains})"] = None
    if sort:
        query_params[f"sort({sort})"] = None
    if limit:
        if offset:
            query_params[f"limit({limit},{offset})"] = None
        else:
            query_params[f"limit({limit})"] = None
    
    # Handle raw RQL if provided
    if rql:
        # Parse raw RQL and add to query_params
        for param in rql.split('&'):
            if param.strip():
                query_params[param.strip()] = None
    
    try:
        # Use same RQL processing as API endpoints
        results = fv.get_table_data_api(table, query_params)
        _format_output(results)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command("post")
def create_record(
    table: str,
    db: str = typer.Option(..., "--db", help="Database file path"),
    data: str = typer.Option(..., "--data", help="JSON data for the record"),
):
    """Create record in table (mirrors POST /api/{table})."""
    fv = _get_app(db)
    
    try:
        data_dict = json.loads(data)
        result = fv.create_record_api(table, data_dict)
        _format_output(result)
    except json.JSONDecodeError:
        typer.echo("Invalid JSON data", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command("put")  
def update_records(
    table: str,
    db: str = typer.Option(..., "--db", help="Database file path"),
    data: str = typer.Option(..., "--data", help="JSON data for the record"),
    # RQL filters for which records to update
    eq: Optional[str] = typer.Option(None, help="Update where: eq(field,value)"),
    rql: Optional[str] = typer.Option(None, help="Update where: RQL query"),
):
    """Update records in table (mirrors PUT /api/{table})."""
    fv = _get_app(db)
    
    try:
        data_dict = json.loads(data)
        query_params = {}
        if eq:
            query_params[f"eq({eq})"] = None
        if rql:
            for param in rql.split('&'):
                if param.strip():
                    query_params[param.strip()] = None
        
        result = fv.update_records_api(table, data_dict, query_params)
        _format_output(result)
    except json.JSONDecodeError:
        typer.echo("Invalid JSON data", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command("delete")
def delete_records(
    table: str,
    db: str = typer.Option(..., "--db", help="Database file path"),
    # RQL filters for which records to delete
    eq: Optional[str] = typer.Option(None, help="Delete where: eq(field,value)"),
    rql: Optional[str] = typer.Option(None, help="Delete where: RQL query"),
):
    """Delete records from table (mirrors DELETE /api/{table})."""
    fv = _get_app(db)
    
    try:
        query_params = {}
        if eq:
            query_params[f"eq({eq})"] = None
        if rql:
            for param in rql.split('&'):
                if param.strip():
                    query_params[param.strip()] = None
        
        result = fv.delete_records_api(table, query_params)
        _format_output(result)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


# Server and utility commands

@app.command()
def serve(
    db: str = typer.Option(..., "--db", help="Database file path"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
):
    """Start the FastVimes server."""
    import uvicorn
    from fastvimes.app import FastVimes
    
    app_instance = FastVimes(db_path=db)
    
    typer.echo(f"Starting FastVimes server with RQL support...")
    typer.echo(f"Database: {db}")
    typer.echo(f"Tables: {', '.join(app_instance.list_tables_api())}")
    typer.echo(f"API: http://{host}:{port}/api/")
    typer.echo(f"Admin: http://{host}:{port}/admin")
    
    uvicorn.run(
        app_instance,
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def init(
    db: str = typer.Option(..., "--db", help="Database file path"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing database"),
):
    """Initialize database with sample data."""
    if Path(db).exists() and not force:
        typer.echo(f"Database {db} already exists. Use --force to overwrite.")
        raise typer.Exit(1)
    
    # Remove existing file if force is specified
    if force and Path(db).exists():
        Path(db).unlink()
    
    try:
        # Create FastVimes app to properly initialize database
        fv = _get_app(db)
        
        # Create sample tables through FastVimes to ensure compatibility
        fv.db_service._connection.execute("""
            CREATE TABLE users (
                id INTEGER,
                name VARCHAR,
                email VARCHAR,
                age INTEGER,
                active BOOLEAN
            )
        """)
        
        fv.db_service._connection.execute("""
            INSERT INTO users VALUES 
            (1, 'Alice', 'alice@example.com', 25, true),
            (2, 'Bob', 'bob@example.com', 30, true),
            (3, 'Charlie', 'charlie@example.com', 35, false)
        """)
        
        # Refresh table routes so FastVimes recognizes the new table
        fv.refresh_table_routes()
        
        typer.echo(f"Initialized database: {db} with sample users table")
        typer.echo(f"Tables available: {', '.join(fv.list_tables_api())}")
        
    except Exception as e:
        typer.echo(f"Failed to initialize database: {e}", err=True)
        # Clean up partially created file
        if Path(db).exists():
            Path(db).unlink()
        raise typer.Exit(1)


@app.command()
def query(
    sql: str,
    db: str = typer.Option(..., "--db", help="Database file path"),
    format_output: str = typer.Option("json", "--format", help="Output format"),
):
    """Execute raw SQL query."""
    fv = _get_app(db)
    
    try:
        result = fv.execute_raw_sql(sql)
        if format_output == "json":
            _format_output(result.to_dict('records'))
        elif format_output == "csv":
            print(result.to_csv())
        else:
            print(result)
    except Exception as e:
        typer.echo(f"Query failed: {e}", err=True)
        raise typer.Exit(1)


@app.command("httpx")
def httpx_cmd(
    url: str = typer.Argument(..., help="URL path to request (e.g., 'GET /api/users')"),
    db: str = typer.Option(..., "--db", help="Database path"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", help="Port to bind to"),
    data: Optional[str] = typer.Option(None, "--data", help="JSON data for POST/PUT"),
    headers: Optional[str] = typer.Option(None, "--headers", help="Headers"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
):
    """Test FastAPI HTTP endpoints using httpx (tests URL encoding, RQL parsing, etc.)."""
    # Parse URL
    parts = url.strip().split(None, 1)
    if len(parts) == 2:
        method, path = parts
        method = method.upper()
    else:
        method = "GET"
        path = parts[0]

    if not path.startswith('/'):
        path = '/' + path

    # Start server in background
    from fastvimes.app import FastVimes
    import uvicorn
    
    # Configure for read-write access for testing (same as CLI)
    app_instance = FastVimes(db_path=db, default_mode="readwrite")
    
    def run_server():
        uvicorn.run(
            app_instance,
            host=host,
            port=port,
            log_level="error",
            access_log=False
        )

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    try:
        # Build request
        base_url = f"http://{host}:{port}"
        
        # Parse headers
        request_headers = {}
        if headers:
            for header in headers.split(','):
                if ':' in header:
                    key, value = header.split(':', 1)
                    request_headers[key.strip()] = value.strip()
        
        # Parse JSON data
        json_data = None
        if data:
            try:
                json_data = json.loads(data)
                request_headers["Content-Type"] = "application/json"
            except json.JSONDecodeError:
                typer.echo(f"Invalid JSON data: {data}", err=True)
                raise typer.Exit(1)

        if verbose:
            typer.echo(f"Making {method} request to: {base_url}{path}")
            if json_data:
                typer.echo(f"Data: {json.dumps(json_data)}")
            if request_headers:
                typer.echo(f"Headers: {request_headers}")

        # Make HTTP request using httpx
        with httpx.Client() as client:
            response = client.request(
                method=method,
                url=f"{base_url}{path}",
                json=json_data,
                headers=request_headers
            )
            
            if verbose:
                typer.echo(f"Status: {response.status_code}")
                typer.echo(f"Response headers: {dict(response.headers)}")
            
            # Print response body
            print(response.text)
            
            # Exit with non-zero code for HTTP errors
            if response.status_code >= 400:
                raise typer.Exit(1)

    except httpx.RequestError as e:
        typer.echo(f"Request error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
