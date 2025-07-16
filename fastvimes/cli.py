"""FastVimes CLI using Typer with namespaced commands."""

import json
from pathlib import Path

import typer

from .app import FastVimes
from .config import FastVimesSettings

# Main app
app = typer.Typer(
    name="fastvimes",
    help="FastVimes: Auto-Generated Datasette-Style Apps with NiceGUI + DuckDB",
)

# Subcommands
meta_app = typer.Typer(help="Database metadata operations")
data_app = typer.Typer(help="Table data operations (CRUD)")
user_app = typer.Typer(help="User management operations")

app.add_typer(meta_app, name="meta")
app.add_typer(data_app, name="data")
app.add_typer(user_app, name="user")


def _serve_main(db: str | None, host: str, port: int, debug: bool):
    """Main function for serve command - needed for NiceGUI proper initialization."""

    settings = FastVimesSettings(host=host, port=port, debug=debug)

    # Create FastVimes app
    fastvimes = FastVimes(db_path=db, settings=settings)

    print("Starting FastVimes server...")
    if db:
        print(f"Database: {db}")
    else:
        print("Database: In-memory with sample data")
    print(f"Server: http://{host}:{port}")

    # Start the server (don't auto-launch browser)
    fastvimes.serve(host=host, port=port, show=False)


@app.command()
def serve(
    db: str | None = typer.Option(
        None,
        help="Path to DuckDB database. If not provided, uses in-memory database with sample data.",
    ),
    host: str = typer.Option("127.0.0.1", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    debug: bool = typer.Option(False, help="Enable debug mode"),
):
    """Start the FastVimes server with NiceGUI interface."""
    _serve_main(db, host, port, debug)


@app.command()
def init(
    db: str = typer.Argument(..., help="Path to DuckDB database to create"),
    force: bool = typer.Option(False, help="Overwrite existing database"),
):
    """Initialize a new DuckDB database with sample data."""
    db_path = Path(db)

    if db_path.exists() and not force:
        typer.echo(f"Database {db} already exists. Use --force to overwrite.")
        raise typer.Exit(1)

    # Create new database with sample data
    from .database_service import DatabaseService

    db_service = DatabaseService(db_path, create_sample_data=True)

    typer.echo(f"Initialized database: {db}")
    typer.echo("Sample tables created:")

    tables = db_service.list_tables()
    for table in tables:
        typer.echo(f"  {table['name']}")


@app.command()
def httpx(
    request: str = typer.Argument(
        ..., help="HTTP request in format 'METHOD /path' or just '/path' for GET"
    ),
    data: str | None = typer.Option(None, help="JSON data for POST/PUT requests"),
    port: int = typer.Option(8000, help="Port to connect to"),
    host: str = typer.Option("127.0.0.1", help="Host to connect to"),
    verbose: bool = typer.Option(False, help="Show detailed output"),
):
    """Test HTTP API endpoints with automatic server lifecycle."""
    import json
    import subprocess
    import sys
    import time
    import urllib.parse
    import urllib.request
    from urllib.error import HTTPError, URLError

    # Parse request
    parts = request.strip().split(" ", 1)
    if len(parts) == 1:
        method = "GET"
        path = parts[0]
    else:
        method, path = parts

    method = method.upper()

    # Ensure path starts with /
    if not path.startswith("/"):
        path = "/" + path

    # Start server in background
    server_process = None
    try:
        # Start FastVimes server
        server_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "fastvimes.cli",
                "serve",
                "--host",
                host,
                "--port",
                str(port),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to start
        base_url = f"http://{host}:{port}"
        for _ in range(30):  # Wait up to 30 seconds
            try:
                urllib.request.urlopen(f"{base_url}/api/v1/meta/tables", timeout=1)
                break
            except (URLError, OSError):
                time.sleep(1)
        else:
            typer.echo("Failed to start server", err=True)
            return

        # Make the request
        url = f"{base_url}{path}"

        if verbose:
            typer.echo(f"Making {method} request to {url}")

        # Prepare request
        headers = {"Content-Type": "application/json"} if data else {}
        req_data = data.encode("utf-8") if data else None

        request_obj = urllib.request.Request(
            url, data=req_data, headers=headers, method=method
        )

        try:
            with urllib.request.urlopen(request_obj) as response:
                response_data = response.read().decode("utf-8")

                if verbose:
                    typer.echo(f"Status: {response.status}")
                    typer.echo(f"Headers: {dict(response.headers)}")

                # Pretty print JSON response
                try:
                    json_data = json.loads(response_data)
                    typer.echo(json.dumps(json_data, indent=2))
                except json.JSONDecodeError:
                    typer.echo(response_data)

        except HTTPError as e:
            typer.echo(f"HTTP Error {e.code}: {e.reason}", err=True)
            error_data = e.read().decode("utf-8")
            try:
                json_error = json.loads(error_data)
                typer.echo(json.dumps(json_error, indent=2), err=True)
            except json.JSONDecodeError:
                typer.echo(error_data, err=True)

    finally:
        # Clean up server
        if server_process:
            server_process.terminate()
            server_process.wait(timeout=5)


# =============================================================================
# META COMMANDS - Database introspection
# =============================================================================


@meta_app.command()
def tables(db: str | None = typer.Option(None, help="Path to DuckDB database")):
    """List all tables in the database."""
    fastvimes = FastVimes(db_path=db)
    tables = fastvimes.db_service.list_tables()

    if not tables:
        typer.echo("No tables found.")
        return

    typer.echo("Tables:")
    for table in tables:
        typer.echo(f"  {table['name']} ({table['type']})")


@meta_app.command()
def schema(
    table: str = typer.Argument(..., help="Table name"),
    db: str | None = typer.Option(None, help="Path to DuckDB database"),
):
    """Show schema for a specific table."""
    fastvimes = FastVimes(db_path=db)
    schema = fastvimes.db_service.get_table_schema(table)

    typer.echo(f"Schema for table '{table}':")
    for column in schema:
        nullable = "NULL" if column.get("nullable") else "NOT NULL"
        key = f" ({column['key']})" if column.get("key") else ""
        typer.echo(f"  {column['name']}: {column['type']} {nullable}{key}")


# =============================================================================
# DATA COMMANDS - Table CRUD operations
# =============================================================================


@data_app.command()
def get(
    table: str = typer.Argument(..., help="Table name"),
    rql: str | None = typer.Option(None, help="RQL query filter"),
    limit: int | None = typer.Option(100, help="Maximum number of records"),
    offset: int | None = typer.Option(0, help="Number of records to skip"),
    format: str = typer.Option("json", help="Output format: json, csv, parquet"),
    db: str | None = typer.Option(None, help="Path to DuckDB database"),
):
    """Get table data with RQL filtering and multi-format output."""
    fastvimes = FastVimes(db_path=db)

    try:
        result = fastvimes.db_service.get_table_data(
            table_name=table, rql_query=rql, limit=limit, offset=offset, format=format
        )

        if format.lower() == "json":
            typer.echo(json.dumps(result, indent=2, default=str))
        else:
            # For CSV/Parquet, write to stdout as bytes
            import sys

            sys.stdout.buffer.write(result)

    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1) from e


@data_app.command()
def create(
    table: str = typer.Argument(..., help="Table name"),
    data: str = typer.Option(..., help="JSON data for the new record"),
    db: str | None = typer.Option(None, help="Path to DuckDB database"),
):
    """Create a new record in the specified table."""
    fastvimes = FastVimes(db_path=db)

    try:
        record_data = json.loads(data)
        result = fastvimes.db_service.create_record(table, record_data)
        typer.echo(
            json.dumps(
                {"message": "Record created successfully", "record": result},
                indent=2,
                default=str,
            )
        )
    except json.JSONDecodeError:
        typer.echo("Error: Invalid JSON data", err=True)
        raise typer.Exit(1) from None
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1) from e


@data_app.command()
def update(
    table: str = typer.Argument(..., help="Table name"),
    data: str = typer.Option(..., help="JSON data for updating records"),
    rql: str | None = typer.Option(None, help="RQL query to filter records"),
    db: str | None = typer.Option(None, help="Path to DuckDB database"),
):
    """Update records in the specified table."""
    fastvimes = FastVimes(db_path=db)

    try:
        update_data = json.loads(data)
        count = fastvimes.db_service.update_records(
            table_name=table, data=update_data, rql_query=rql
        )
        typer.echo(
            json.dumps(
                {"message": f"Updated {count} records", "count": count},
                indent=2,
                default=str,
            )
        )
    except json.JSONDecodeError:
        typer.echo("Error: Invalid JSON data", err=True)
        raise typer.Exit(1) from None
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1) from e


@data_app.command()
def delete(
    table: str = typer.Argument(..., help="Table name"),
    rql: str = typer.Option(..., help="RQL query to filter records for deletion"),
    db: str | None = typer.Option(None, help="Path to DuckDB database"),
):
    """Delete records from the specified table."""
    fastvimes = FastVimes(db_path=db)

    try:
        count = fastvimes.db_service.delete_records(table_name=table, rql_query=rql)
        typer.echo(
            json.dumps(
                {"message": f"Deleted {count} records", "count": count},
                indent=2,
                default=str,
            )
        )
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1) from e


# =============================================================================
# QUERY COMMAND - Raw SQL execution
# =============================================================================


@app.command()
def query(
    sql: str = typer.Argument(..., help="SQL query to execute"),
    format: str = typer.Option("json", help="Output format: json, csv, parquet"),
    db: str | None = typer.Option(None, help="Path to DuckDB database"),
):
    """Execute a raw SQL query and return results."""
    fastvimes = FastVimes(db_path=db)

    try:
        result = fastvimes.db_service.execute_query(sql)

        if format.lower() == "json":
            typer.echo(json.dumps(result, indent=2, default=str))
        elif format.lower() == "csv":
            # Convert to CSV format
            if result:
                import csv
                import io

                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=result[0].keys())
                writer.writeheader()
                writer.writerows(result)
                typer.echo(output.getvalue())
            else:
                typer.echo("")
        elif format.lower() == "parquet":
            # Convert to Parquet format
            if result:
                columns = list(result[0].keys())
                data = result
                parquet_bytes = fastvimes.db_service._export_to_parquet(columns, data)
                import sys

                sys.stdout.buffer.write(parquet_bytes)
            else:
                typer.echo("")
        else:
            typer.echo(
                f"Error: Unsupported format '{format}'. Use: json, csv, parquet",
                err=True,
            )
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1) from e


# =============================================================================
# BULK OPERATIONS COMMANDS - File-based bulk operations
# =============================================================================


@data_app.command()
def bulk_insert(
    table: str = typer.Argument(..., help="Table name"),
    file: str = typer.Option(
        ..., "--file", help="Path to data file (Parquet, CSV, or JSON)"
    ),
    file_format: str = typer.Option(
        "auto", help="File format: auto, parquet, csv, json"
    ),
    db: str | None = typer.Option(None, help="Path to DuckDB database"),
):
    """Bulk insert records from file."""
    try:
        fastvimes = FastVimes(db_path=db)

        # Verify file exists
        if not Path(file).exists():
            typer.echo(f"Error: File '{file}' not found", err=True)
            raise typer.Exit(1)

        # Perform bulk insert
        records_inserted = fastvimes.db_service.bulk_insert_from_file(
            table, file, file_format
        )

        typer.echo(
            f"Successfully inserted {records_inserted} records into table '{table}'"
        )
        typer.echo(f"Source file: {file}")
        typer.echo(f"Format: {file_format}")

    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1) from e


@data_app.command()
def bulk_upsert(
    table: str = typer.Argument(..., help="Table name"),
    file: str = typer.Option(
        ..., "--file", help="Path to data file (Parquet, CSV, or JSON)"
    ),
    key_columns: str = typer.Option(
        ..., "--key-columns", help="Comma-separated list of key columns for matching"
    ),
    file_format: str = typer.Option(
        "auto", help="File format: auto, parquet, csv, json"
    ),
    db: str | None = typer.Option(None, help="Path to DuckDB database"),
):
    """Bulk upsert (insert or update) records from file."""
    try:
        fastvimes = FastVimes(db_path=db)

        # Verify file exists
        if not Path(file).exists():
            typer.echo(f"Error: File '{file}' not found", err=True)
            raise typer.Exit(1)

        # Parse key columns
        key_columns_list = [col.strip() for col in key_columns.split(",")]

        # Perform bulk upsert
        result = fastvimes.db_service.bulk_upsert_from_file(
            table, file, key_columns_list, file_format
        )

        typer.echo(f"Successfully processed records in table '{table}':")
        typer.echo(f"  Records inserted: {result['inserted']}")
        typer.echo(f"  Records updated: {result['updated']}")
        typer.echo(f"Source file: {file}")
        typer.echo(f"Key columns: {key_columns_list}")
        typer.echo(f"Format: {file_format}")

    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1) from e


@data_app.command()
def bulk_delete(
    table: str = typer.Argument(..., help="Table name"),
    file: str = typer.Option(
        ..., "--file", help="Path to file containing keys to delete"
    ),
    key_columns: str = typer.Option(
        ..., "--key-columns", help="Comma-separated list of key columns for matching"
    ),
    file_format: str = typer.Option(
        "auto", help="File format: auto, parquet, csv, json"
    ),
    db: str | None = typer.Option(None, help="Path to DuckDB database"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
):
    """Bulk delete records based on keys from file."""
    try:
        fastvimes = FastVimes(db_path=db)

        # Verify file exists
        if not Path(file).exists():
            typer.echo(f"Error: File '{file}' not found", err=True)
            raise typer.Exit(1)

        # Parse key columns
        key_columns_list = [col.strip() for col in key_columns.split(",")]

        # Confirmation prompt
        if not confirm:
            typer.echo(
                f"This will delete records from table '{table}' based on keys in '{file}'"
            )
            typer.echo(f"Key columns: {key_columns_list}")
            if not typer.confirm("Are you sure you want to proceed?"):
                typer.echo("Operation cancelled")
                raise typer.Exit(0)

        # Perform bulk delete
        records_deleted = fastvimes.db_service.bulk_delete_from_file(
            table, file, key_columns_list, file_format
        )

        typer.echo(
            f"Successfully deleted {records_deleted} records from table '{table}'"
        )
        typer.echo(f"Source file: {file}")
        typer.echo(f"Key columns: {key_columns_list}")
        typer.echo(f"Format: {file_format}")

    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1) from e


# User management commands
@user_app.command("create")
def create_user(
    username: str = typer.Argument(..., help="Username for the new user"),
    email: str = typer.Option(..., help="Email address for the new user"),
    password: str = typer.Option(..., help="Password for the new user"),
    name: str = typer.Option("", help="Full name for the new user"),
    admin: bool = typer.Option(False, help="Grant admin privileges to the user"),
    db: str | None = typer.Option(
        None,
        help="Path to DuckDB database. If not provided, uses in-memory database.",
    ),
):
    """Create a new user account."""
    try:
        settings = FastVimesSettings(db_path=db or ":memory:")

        # Import here to avoid circular imports
        from pathlib import Path

        from .database_service import DatabaseService
        from .middleware.auth_authlib import AuthMiddleware

        db_service = DatabaseService(
            db_path=Path(settings.db_path), create_sample_data=False
        )

        # Create auth middleware to access user management methods
        auth_middleware = AuthMiddleware(
            app=None,  # We don't need the app for user creation
            settings=settings,
            db_service=db_service,
        )

        # Initialize users table
        auth_middleware._init_users_table()

        # Set roles
        roles = ["user"]
        if admin:
            roles.append("admin")

        # Create user
        user_id = auth_middleware._create_user(
            username=username,
            email=email,
            password=password,
            name=name or username,
            roles=roles,
        )

        typer.echo("User created successfully!")
        typer.echo(f"User ID: {user_id}")
        typer.echo(f"Username: {username}")
        typer.echo(f"Email: {email}")
        typer.echo(f"Roles: {', '.join(roles)}")

    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1) from e


@user_app.command("list")
def list_users(
    db: str | None = typer.Option(
        None,
        help="Path to DuckDB database. If not provided, uses in-memory database.",
    ),
):
    """List all users."""
    try:
        settings = FastVimesSettings(db_path=db or ":memory:")

        # Import here to avoid circular imports
        from pathlib import Path

        from .database_service import DatabaseService

        db_service = DatabaseService(
            db_path=Path(settings.db_path), create_sample_data=False
        )

        # Query users table
        with db_service._create_connection() as conn:
            result = conn.execute("""
                SELECT id, username, email, name, roles, created_at
                FROM fastvimes_users
                ORDER BY created_at DESC
            """).fetchall()

        if not result:
            typer.echo("No users found.")
            return

        typer.echo("Users:")
        typer.echo("-" * 80)
        for row in result:
            user_id, username, email, name, roles, created_at = row
            typer.echo(f"ID: {user_id}")
            typer.echo(f"Username: {username}")
            typer.echo(f"Email: {email}")
            typer.echo(f"Name: {name}")
            typer.echo(f"Roles: {', '.join(roles)}")
            typer.echo(f"Created: {created_at}")
            typer.echo("-" * 80)

    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1) from e


if __name__ in {"__main__", "__mp_main__"}:
    app()
