#!/usr/bin/env python3
"""
Basic FastVimes example application.

This example demonstrates the three main ways to use FastVimes:
1. Instant app from database
2. Custom app with configuration
3. FastAPI-style with custom endpoints

Run with:
  uv run python examples/basic_app.py --help
  uv run python examples/basic_app.py serve
  uv run python examples/basic_app.py serve --db demo.db --port 8080
"""

import sys
from pathlib import Path
from typing import Any

# Add the parent directory to the path so we can import fastvimes
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastvimes import FastVimes


def create_demo_database(db_path: str = "demo.db") -> None:
    """Create a demo database with sample data."""
    import ibis

    # Create connection and sample data
    con = ibis.duckdb.connect(db_path)

    # Create users table
    users_data = [
        {
            "id": 1,
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "age": 30,
            "role": "admin",
        },
        {
            "id": 2,
            "name": "Bob Smith",
            "email": "bob@example.com",
            "age": 25,
            "role": "user",
        },
        {
            "id": 3,
            "name": "Charlie Brown",
            "email": "charlie@example.com",
            "age": 35,
            "role": "user",
        },
    ]

    # Create products table
    products_data = [
        {
            "id": 1,
            "name": "Laptop",
            "price": 999.99,
            "category": "Electronics",
            "in_stock": True,
        },
        {
            "id": 2,
            "name": "Mouse",
            "price": 29.99,
            "category": "Electronics",
            "in_stock": True,
        },
        {
            "id": 3,
            "name": "Keyboard",
            "price": 79.99,
            "category": "Electronics",
            "in_stock": False,
        },
        {
            "id": 4,
            "name": "Monitor",
            "price": 299.99,
            "category": "Electronics",
            "in_stock": True,
        },
    ]

    # Create orders table
    orders_data = [
        {
            "id": 1,
            "user_id": 1,
            "product_id": 1,
            "quantity": 1,
            "order_date": "2023-11-01",
        },
        {
            "id": 2,
            "user_id": 2,
            "product_id": 2,
            "quantity": 2,
            "order_date": "2023-11-02",
        },
        {
            "id": 3,
            "user_id": 1,
            "product_id": 4,
            "quantity": 1,
            "order_date": "2023-11-03",
        },
    ]

    # Insert data
    con.create_table("users", users_data, overwrite=True)
    con.create_table("products", products_data, overwrite=True)
    con.create_table("orders", orders_data, overwrite=True)

    print(f"Created demo database: {db_path}")
    print("Tables created: users, products, orders")


def example_1_instant_app():
    """Example 1: Instant app from database"""
    # Create demo database if it doesn't exist
    if not Path("demo.db").exists():
        create_demo_database("demo.db")

    # Create instant app
    app = FastVimes(db_path="demo.db")

    return app


def example_2_custom_app():
    """Example 2: Custom app with detailed configuration"""
    # Create demo database if it doesn't exist
    if not Path("demo.db").exists():
        create_demo_database("demo.db")

    # Custom configuration
    app = FastVimes(
        db_path="demo.db",
        extensions=["json"],  # Enable JSON extension
        read_only=False,
    )

    return app


def example_3_fastapi_style():
    """Example 3: FastAPI-style with custom endpoints"""
    # Create demo database if it doesn't exist
    if not Path("demo.db").exists():
        create_demo_database("demo.db")

    # Start with basic FastVimes app
    app = FastVimes(db_path="demo.db")

    # Add custom endpoints
    @app.get("/dashboard")
    def dashboard() -> dict[str, Any]:
        """Custom dashboard endpoint with aggregated data."""
        users_count = app.connection.table("users").count().execute()
        products_count = app.connection.table("products").count().execute()
        orders_count = app.connection.table("orders").count().execute()

        # Get top users by order count
        top_users = (
            app.connection.table("orders")
            .join(app.connection.table("users"), "user_id", "id")
            .group_by("user_id")
            .aggregate(
                name=app.connection.table("users").name.first(),
                order_count=app.connection.table("orders").count(),
            )
            .order_by(app.connection.table("orders").count().desc())
            .limit(5)
            .execute()
        )

        return {
            "summary": {
                "users": users_count,
                "products": products_count,
                "orders": orders_count,
            },
            "top_users": top_users.to_dict("records")
            if hasattr(top_users, "to_dict")
            else [],
        }

    @app.get("/dashboard/html")
    def dashboard_html():
        """HTML version of dashboard."""
        data = dashboard()

        html = f"""
        <div class="container">
            <h1 class="title">Dashboard</h1>
            <div class="columns">
                <div class="column">
                    <div class="box">
                        <h2 class="subtitle">Users</h2>
                        <p class="is-size-2">{data["summary"]["users"]}</p>
                    </div>
                </div>
                <div class="column">
                    <div class="box">
                        <h2 class="subtitle">Products</h2>
                        <p class="is-size-2">{data["summary"]["products"]}</p>
                    </div>
                </div>
                <div class="column">
                    <div class="box">
                        <h2 class="subtitle">Orders</h2>
                        <p class="is-size-2">{data["summary"]["orders"]}</p>
                    </div>
                </div>
            </div>
        </div>
        """

        return app.form_generator.wrap_in_html(html, "Dashboard")

    @app.get("/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "database": "connected"}

    return app


def main():
    """Main function for CLI usage."""
    import typer

    app_cli = typer.Typer(help="FastVimes Basic Example")

    @app_cli.command()
    def serve(
        example: int = typer.Option(1, help="Example number (1, 2, or 3)"),
        host: str = typer.Option("127.0.0.1", help="Host to bind to"),
        port: int = typer.Option(8000, help="Port to bind to"),
        reload: bool = typer.Option(False, help="Enable auto-reload"),
        db: str = typer.Option("demo.db", help="Database path"),
    ):
        """Run the FastVimes example server."""
        import uvicorn

        # Update database path
        global DB_PATH
        DB_PATH = db

        # Choose example
        if example == 1:
            app = example_1_instant_app()
            print("Running Example 1: Instant App")
        elif example == 2:
            app = example_2_custom_app()
            print("Running Example 2: Custom App")
        elif example == 3:
            app = example_3_fastapi_style()
            print("Running Example 3: FastAPI-style")
        else:
            typer.echo("Invalid example number. Use 1, 2, or 3.")
            return

        print(f"Starting server on http://{host}:{port}")
        print(f"Using database: {db}")
        print("Available endpoints:")
        print("  - /docs (OpenAPI documentation)")
        print("  - /admin (Admin interface)")
        print("  - /users, /products, /orders (Auto-generated APIs)")
        if example == 3:
            print("  - /dashboard (Custom endpoint)")
            print("  - /health (Health check)")

        uvicorn.run(app, host=host, port=port, reload=reload)

    @app_cli.command()
    def init_db(
        db_path: str = typer.Option("demo.db", help="Database path"),
        force: bool = typer.Option(False, help="Overwrite existing database"),
    ):
        """Initialize demo database with sample data."""
        if Path(db_path).exists() and not force:
            typer.echo(f"Database {db_path} already exists. Use --force to overwrite.")
            return

        create_demo_database(db_path)
        typer.echo(f"Demo database initialized: {db_path}")

    @app_cli.command()
    def info():
        """Show information about the examples."""
        typer.echo("FastVimes Basic Examples:")
        typer.echo("")
        typer.echo("Example 1: Instant App")
        typer.echo("  - Auto-generated APIs from database schema")
        typer.echo("  - Admin interface enabled")
        typer.echo("  - All tables in readwrite mode")
        typer.echo("")
        typer.echo("Example 2: Custom App")
        typer.echo("  - Custom table configurations")
        typer.echo("  - Mixed readonly/readwrite modes")
        typer.echo("  - JSON extension enabled")
        typer.echo("")
        typer.echo("Example 3: FastAPI-style")
        typer.echo("  - Custom endpoints alongside auto-generated ones")
        typer.echo("  - Dashboard with aggregated data")
        typer.echo("  - Health check endpoint")

    app_cli()


if __name__ == "__main__":
    main()
