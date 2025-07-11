# FastVimes

Lightweight composition of FastAPI and Ibis for building data tools with automatic CLI, web API, and HTML interfaces.

## Design Philosophy

FastVimes is designed as a **lightweight composition** of stable, well-established libraries:

- **FastAPI** for HTTP framework and dependency injection
- **Ibis** for database abstraction and safe query building
- **Pydantic** for configuration and data validation
- **Typer** for CLI interface
- **DuckDB** as the primary database backend

The goal is to provide clean, inherited APIs from these dependencies while adding minimal abstraction.

## Features

- **Auto-generated APIs** from DuckDB schemas with RQL query language
- **Type-safe queries** using Ibis (no SQL injection vulnerabilities)
- **Admin interface** for Django-style table management
- **Multiple interfaces**: CLI, OpenAPI/Swagger, HTML forms
- **Instant setup**: Point at database + HTML folder and run
- **Clean architecture** with service-based design

## Quick Start

```python
from fastvimes import FastVimes

# Start with existing database - auto-generates APIs
app = FastVimes(db_path="data.db")

# Add custom endpoints using familiar FastAPI + Ibis patterns
@app.get("/users")
def get_users():
    return app.connection.table("users").execute()

# Run with convenience method or uvicorn (standard FastAPI)
if __name__ == "__main__":
    app.run()  # Simple: defaults to 127.0.0.1:8000
    # Or: app.run(host="0.0.0.0", port=8080, reload=True)
```

## Installation

Requires uv (which handles Python 3.13+ automatically)

```bash
uv add fastvimes
```

## Three Ways to Use

### 1. Instant App
```python
from fastvimes import FastVimes

# Point at database, get instant APIs
app = FastVimes(db_path="data.db")
# Generates: GET/POST /users, GET/POST /products, etc.
# Admin interface: /admin
# OpenAPI docs: /docs
```

### 2. Custom Configuration
```python
from fastvimes import FastVimes

app = FastVimes(
    db_path="data.db",
    extensions=["spatial", "httpfs"],
    read_only=False
)
# All tables writable, extensions loaded
```

### 3. Custom Endpoints (FastAPI-style)
```python
from fastvimes import FastVimes

app = FastVimes(db_path="data.db")

@app.get("/dashboard")
def dashboard():
    # Direct Ibis connection access
    return app.connection.table("sales").aggregate(
        total_sales=app.connection.table("sales").amount.sum()
    ).execute()

@app.get("/custom/{table_name}")
def custom_query(table_name: str):
    # Type-safe table access
    table = app.connection.table(table_name)
    return table.limit(100).execute()
```

## RQL Query Language

FastVimes uses RQL (Resource Query Language) for filtering and data access:

```bash
# Get all users
curl "http://localhost:8000/users"

# Get specific user
curl "http://localhost:8000/users?eq(id,1)"

# Advanced filtering
curl "http://localhost:8000/users?and(gt(age,25),eq(role,admin))"
curl "http://localhost:8000/users?contains(name,John)"
curl "http://localhost:8000/users?in(id,(1,2,3))"

# Update/Delete using filters
curl -X PUT "http://localhost:8000/users?eq(id,1)" -d '{"name": "New Name"}'
curl -X DELETE "http://localhost:8000/users?eq(id,1)"
```

## CLI Testing

Test API endpoints with automatic server management:

```bash
# Test with built-in curl command
fastvimes curl --db mydata.db "GET /users"
fastvimes curl --db mydata.db "GET /users?eq(id,1)"
fastvimes curl --db mydata.db "POST /users" --data '{"name": "Alice"}'
fastvimes curl --db mydata.db "PUT /users?eq(id,1)" --data '{"name": "Bob"}'
fastvimes curl --db mydata.db "DELETE /users?eq(id,1)"

# Other CLI commands
fastvimes serve --db mydata.db
fastvimes init --db mydata.db
fastvimes tables --db mydata.db
fastvimes query "SELECT * FROM users" --db mydata.db
```

## Documentation

- [Simple Tutorial](docs/simple.md) - Get started in 5 minutes
- [Advanced Usage](docs/advanced.md) - API extensions and complex configurations
- [Customization Guide](docs/customization.md) - HTMX fragments, styling, and UI customization
- [Manual Testing Guide](docs/manual-testing.md) - Step-by-step testing procedures

For a complete overview, see the [docs/README.md](docs/README.md).

## Development

See [AGENT.md](AGENT.md) for development commands.

### Backlog

DONE:

TODO:
- add an openapi page to the admin that includes the fastapi swagger ui using htmx, update design in agent.md
- improve overall admin html so that its wcag 2.2+ compliant, add relevant tests and update design in agent.md
- work out a way to report on complexity and test coverage
- review development methodology and see if we can improve to ensure maturity as we go