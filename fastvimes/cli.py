"""Command line interface for FastVimes."""

import json
import shlex
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

import typer
import uvicorn
from rich.console import Console
from rich.json import JSON
from rich.table import Table

from .app import FastVimes
from .config import FastVimesSettings

console = Console()
app = typer.Typer(name="fastvimes", help="FastVimes CLI")


@app.command()
def serve(
    db: str | None = typer.Option(None, "--db", help="Database path"),
    config: str | None = typer.Option(None, "--config", help="Configuration file path"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", help="Port to bind to"),
    reload: bool = typer.Option(
        False, "--reload/--no-reload", help="Enable auto-reload"
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
):
    """Start the FastVimes server."""
    if verbose:
        console.print("Starting FastVimes server...")

    # Create configuration
    if config:
        # Load from config file
        settings = FastVimesSettings.from_toml(config)
        # Override with CLI args
        if db:
            settings.db_path = db
    else:
        # Create from CLI args and env vars
        config_kwargs = {}
        if db:
            config_kwargs["db_path"] = db
        settings = FastVimesSettings(**config_kwargs)

    # Create app
    fastvimes_app = FastVimes(config=settings)

    if verbose:
        console.print(f"Database: {settings.db_path}")
        console.print(f"Server: http://{host}:{port}")

    # Start server - disable reload if not supported
    if reload:
        console.print("⚠️  Reload mode not supported with FastVimes CLI. Use --no-reload or run with uvicorn directly.")
        console.print("   For development with reload, use: uvicorn your_app:app --reload")
        reload = False
    
    uvicorn.run(fastvimes_app, host=host, port=port, reload=reload, access_log=verbose)


@app.command()
def config(
    db: str | None = typer.Option(None, "--db", help="Database path"),
    config: str | None = typer.Option(None, "--config", help="Configuration file path"),
    verbose: bool = typer.Option(
        False, "--verbose", help="Show detailed configuration"
    ),
):
    """Show configuration information."""
    # Create configuration
    if config:
        settings = FastVimesSettings.from_toml(config)
        if db:
            settings.db_path = db
    else:
        config_kwargs = {}
        if db:
            config_kwargs["db_path"] = db
        settings = FastVimesSettings(**config_kwargs)

    console.print("Current configuration:")
    console.print(f"  Database path: {settings.db_path}")
    console.print(f"  HTML path: {settings.html_path}")
    console.print(f"  Read-only: {settings.read_only}")
    console.print(f"  Extensions: {settings.extensions}")
    console.print(f"  Default table mode: {settings.default_mode}")
    console.print(f"  Admin enabled: {settings.admin_enabled}")

    if verbose:
        console.print("\nTable configurations:")
        for table_name, table_config in settings.tables.items():
            console.print(f"  {table_name}: {table_config.mode}")


@app.command()
def create(
    table: str = typer.Argument(..., help="Table name"),
    db: str | None = typer.Option(None, "--db", help="Database path"),
    config: str | None = typer.Option(None, "--config", help="Configuration file path"),
    data: str | None = typer.Option(None, "--data", help="JSON data to insert"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
):
    """Create new records in a table."""
    if verbose:
        console.print(f"Creating record in table: {table}")

    # Create configuration
    if config:
        settings = FastVimesSettings.from_toml(config)
        if db:
            settings.db_path = db
    else:
        config_kwargs = {}
        if db:
            config_kwargs["db_path"] = db
        settings = FastVimesSettings(**config_kwargs)

    # Create app
    fastvimes_app = FastVimes(config=settings)

    try:
        # Parse JSON data if provided
        if data:
            import json

            record_data = json.loads(data)
        else:
            console.print("No data provided. Use --data with JSON format.")
            raise typer.Exit(1)

        # Get table model
        table_model = fastvimes_app.get_table_dataclass(table)

        # Validate data
        validated_record = table_model(**record_data)

        # Insert into database
        table_ref = fastvimes_app.get_table(table)
        insert_data = validated_record.model_dump()

        # Use raw SQL for insertion since Ibis insert can be complex
        columns = ", ".join(insert_data.keys())
        placeholders = ", ".join(["?" for _ in insert_data.values()])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        fastvimes_app.connection.raw_sql(sql, list(insert_data.values()))

        console.print(f"Record created successfully in {table}")
        if verbose:
            console.print(f"Data: {insert_data}")

    except Exception as e:
        console.print(f"Error creating record: {e}")
        raise typer.Exit(1)
    finally:
        fastvimes_app.close()


@app.command()
def init(
    db: str | None = typer.Option("data.db", "--db", help="Database path"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files"),
):
    """Initialize a new FastVimes project."""
    console.print("Initializing FastVimes project...")

    # Create database
    import ibis

    if not Path(db).exists() or force:
        conn = ibis.duckdb.connect(database=db)
        conn.disconnect()
        console.print(f"Created database: {db}")

    # Create configuration file
    config_file = Path("fastvimes.toml")
    if not config_file.exists() or force:
        config_content = f"""# Database settings
db_path = "{db}"
extensions = []
read_only = false

# Interface settings
html_path = "./static"
admin_enabled = true

# Default table settings
default_mode = "readonly"
default_html = true
default_use_rowid = true

# Per-table overrides
# [tables.users]
# mode = "readwrite"
# primary_key = "email"
"""
        config_file.write_text(config_content.strip())
        console.print(f"Created configuration: {config_file}")

    console.print("Project initialized successfully!")


@app.command()
def schema(
    db: str | None = typer.Option(None, "--db", help="Database path"),
    table: str | None = typer.Option(
        None, "--table", help="Show schema for specific table"
    ),
):
    """Show database schema."""
    config_kwargs = {}
    if db:
        config_kwargs["db_path"] = db

    settings = FastVimesSettings(**config_kwargs)

    try:
        fastvimes_app = FastVimes(config=settings)

        if table:
            # Show specific table schema
            try:
                table_obj = fastvimes_app.get_table(table)
                schema = table_obj.schema()

                console.print(f"Schema for table '{table}':")
                schema_table = Table(show_header=True, header_style="bold magenta")
                schema_table.add_column("Column", style="cyan")
                schema_table.add_column("Type", style="green")

                for field_name, field_type in schema.items():
                    schema_table.add_row(field_name, str(field_type))

                console.print(schema_table)

            except Exception as e:
                console.print(f"Error: {e}", style="red")
        else:
            # Show all tables
            tables = fastvimes_app.list_tables()

            console.print("Available tables:")
            for table_name, table_config in tables.items():
                console.print(f"  {table_name} (mode: {table_config.mode})")

        fastvimes_app.close()

    except Exception as e:
        console.print(f"Error: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def tables(
    db: str | None = typer.Option(None, "--db", help="Database path"),
    config: str | None = typer.Option(None, "--config", help="Configuration file path"),
):
    """List all tables in the database."""
    if config:
        # Load from config file
        settings = FastVimesSettings.from_toml(config)
        # Override with CLI args
        if db:
            settings.db_path = db
    else:
        # Create from CLI args and env vars
        config_kwargs = {}
        if db:
            config_kwargs["db_path"] = db
        settings = FastVimesSettings(**config_kwargs)

    try:
        fastvimes_app = FastVimes(config=settings)

        tables = fastvimes_app.list_tables()

        if tables:
            table_display = Table(show_header=True, header_style="bold magenta")
            table_display.add_column("Table", style="cyan")
            table_display.add_column("Mode", style="green")
            table_display.add_column("HTML", style="yellow")
            table_display.add_column("Primary Key", style="blue")

            for table_name, table_config in tables.items():
                table_display.add_row(
                    table_name,
                    table_config.mode,
                    "Yes" if table_config.html else "No",
                    table_config.primary_key or "Auto",
                )

            console.print(table_display)
        else:
            console.print("No tables found in database.")

        fastvimes_app.close()

    except Exception as e:
        console.print(f"Error: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def query(
    sql: str = typer.Argument(..., help="SQL query to execute"),
    db: str | None = typer.Option(None, "--db", help="Database path"),
    format: str = typer.Option(
        "table", "--format", help="Output format: table, json, csv"
    ),
):
    """Execute a SQL query."""
    config_kwargs = {}
    if db:
        config_kwargs["db_path"] = db

    settings = FastVimesSettings(**config_kwargs)

    try:
        fastvimes_app = FastVimes(config=settings)

        result = fastvimes_app.execute_query(sql)

        if format == "json":
            # Convert to JSON
            if hasattr(result, "to_pandas"):
                df = result.to_pandas()
                data = df.to_dict(orient="records")
                console.print(JSON.from_data(data))
            elif isinstance(result, dict):
                console.print(JSON.from_data(result))
            else:
                console.print(JSON.from_data(str(result)))

        elif format == "csv":
            # Convert to CSV
            if hasattr(result, "to_pandas"):
                df = result.to_pandas()
                console.print(df.to_csv(index=False))
            else:
                console.print(str(result))

        else:
            # Default table format
            if hasattr(result, "to_pandas"):
                df = result.to_pandas()
                if not df.empty:
                    # Create table
                    table = Table(show_header=True, header_style="bold magenta")

                    # Add columns
                    for col in df.columns:
                        table.add_column(str(col), style="cyan")

                    # Add rows
                    for _, row in df.iterrows():
                        table.add_row(*[str(val) for val in row])

                    console.print(table)
                else:
                    console.print("No results.")
            elif isinstance(result, dict):
                # For DDL results
                console.print(JSON.from_data(result))
            else:
                console.print(str(result))

        fastvimes_app.close()

    except Exception as e:
        console.print(f"Error: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def curl(
    url: str = typer.Argument(..., help="URL path to request (e.g., 'GET /users')"),
    db: str | None = typer.Option(None, "--db", help="Database path"),
    config: str | None = typer.Option(None, "--config", help="Configuration file path"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", help="Port to bind to"),
    data: str | None = typer.Option(None, "--data", help="JSON data for POST/PUT requests"),
    headers: str | None = typer.Option(None, "--headers", help="Additional headers (e.g., 'Accept: text/html')"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose curl output"),
):
    """Test API endpoints with automatic server management."""
    # Parse URL - expect format like "GET /users" or "/users?eq(id,1)"
    parts = url.strip().split(None, 1)
    if len(parts) == 2:
        method, path = parts
        method = method.upper()
    else:
        method = "GET"
        path = parts[0]
    
    # Ensure path starts with /
    if not path.startswith('/'):
        path = '/' + path
    
    # Create configuration
    if config:
        settings = FastVimesSettings.from_toml(config)
        if db:
            settings.db_path = db
    else:
        config_kwargs = {}
        if db:
            config_kwargs["db_path"] = db
        settings = FastVimesSettings(**config_kwargs)

    # Create app
    fastvimes_app = FastVimes(config=settings)
    
    # Server management
    server_process = None
    server_thread = None
    
    def run_server():
        """Run the server in a separate thread."""
        try:
            uvicorn.run(
                fastvimes_app, 
                host=host, 
                port=port, 
                log_level="error" if not verbose else "info",
                access_log=False
            )
        except Exception as e:
            if verbose:
                console.print(f"Server error: {e}")
    
    try:
        # Start server in background thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        
        # Build curl command
        base_url = f"http://{host}:{port}"
        full_url = f"{base_url}{path}"
        
        curl_cmd = ["curl", "-X", method]
        
        if data:
            curl_cmd.extend(["-d", data])
            curl_cmd.extend(["-H", "Content-Type: application/json"])
        
        if headers:
            for header in headers.split(','):
                curl_cmd.extend(["-H", header.strip()])
        
        if verbose:
            curl_cmd.append("-v")
        
        curl_cmd.append(full_url)
        
        if verbose:
            console.print(f"Running: {' '.join(shlex.quote(arg) for arg in curl_cmd)}")
        
        # Execute curl
        result = subprocess.run(curl_cmd, capture_output=True, text=True)
        
        # Print output
        if result.stdout:
            console.print(result.stdout)
        if result.stderr and verbose:
            console.print(f"[red]stderr: {result.stderr}[/red]")
        
        # Exit with curl's exit code
        if result.returncode != 0:
            raise typer.Exit(result.returncode)
            
    except KeyboardInterrupt:
        console.print("\nInterrupted by user")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"Error: {e}", style="red")
        raise typer.Exit(1)
    finally:
        # Server cleanup happens automatically when main process exits
        fastvimes_app.close()


@app.callback()
def main(
    db: str | None = typer.Option(None, "--db", help="Database path"),
    config: str | None = typer.Option(None, "--config", help="Configuration file path"),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
    version: bool = typer.Option(False, "--version", help="Show version"),
):
    """FastVimes: FastAPI-inspired framework for building data tools."""
    if version:
        console.print("FastVimes version 0.1.0")
        raise typer.Exit(0)

    if verbose:
        console.print("FastVimes CLI")


if __name__ == "__main__":
    app()
