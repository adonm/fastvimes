# FastVimes

Lightweight composition of FastAPI and DuckDB for building data tools with automatic CLI, web API, and HTML interfaces.

## Design Philosophy

FastVimes is designed as a **lightweight composition** of stable, well-established libraries:

- **FastAPI** for HTTP framework and dependency injection
- **SQLGlot** for safe SQL query building and parsing
- **DuckDB** for high-performance analytics database
- **Pydantic** for configuration and data validation
- **Typer** for CLI interface

The goal is to provide clean, inherited APIs from these dependencies while adding minimal abstraction.

## Features

- **Auto-generated APIs** from DuckDB schemas with RQL query language
- **Type-safe queries** using SQLGlot (no SQL injection vulnerabilities)
- **Admin interface** with HTMX-powered table management at `/admin`
- **Multiple interfaces**: CLI, OpenAPI/Swagger, HTML forms
- **Instant setup**: Point at database + HTML folder and run
- **Clean architecture** with service-based design

## Quick Start

```python
from fastvimes import FastVimes

# Start with existing database - auto-generates APIs
app = FastVimes(db_path="data.db")

# Add custom endpoints using familiar FastAPI + DuckDB patterns
@app.get("/users")
def get_users():
    return app.db_service.execute_query("SELECT * FROM users")

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
    # Direct SQL query access
    return app.db_service.execute_query(
        "SELECT SUM(amount) as total_sales FROM sales"
    )

@app.get("/custom/{table_name}")
def custom_query(table_name: str):
    # Type-safe table access with SQLGlot
    from sqlglot import select
    from sqlglot.expressions import Table
    sql = select("*").from_(Table(this=table_name)).limit(100).sql(dialect="duckdb")
    return app.db_service.execute_query(sql)
```

## RQL Query Language

FastVimes uses RQL (Resource Query Language) for filtering and data access:

```bash
# Get all users (JSON API)
curl "http://localhost:8000/api/users"

# Get specific user
curl "http://localhost:8000/api/users?eq(id,1)"

# Advanced filtering
curl "http://localhost:8000/api/users?and(gt(age,25),eq(role,admin))"
curl "http://localhost:8000/api/users?contains(name,John)"
curl "http://localhost:8000/api/users?in(id,(1,2,3))"

# Update/Delete using filters
curl -X PUT "http://localhost:8000/api/users?eq(id,1)" -d '{"name": "New Name"}'
curl -X DELETE "http://localhost:8000/api/users?eq(id,1)"

# HTML table view
curl "http://localhost:8000/users/html"
```

## CLI Testing

Test API endpoints with automatic server management:

```bash
# Test with built-in curl command
fastvimes curl --db mydata.db "GET /api/users"
fastvimes curl --db mydata.db "GET /api/users?eq(id,1)"
fastvimes curl --db mydata.db "POST /api/users" --data '{"name": "Alice"}'
fastvimes curl --db mydata.db "PUT /api/users?eq(id,1)" --data '{"name": "Bob"}'
fastvimes curl --db mydata.db "DELETE /api/users?eq(id,1)"

# Other CLI commands
fastvimes serve --db mydata.db
fastvimes init --db mydata.db
fastvimes tables --db mydata.db
fastvimes query "SELECT * FROM users" --db mydata.db

# Export static HTML for customization
fastvimes static-override /admin/tables --db mydata.db
```

## Admin Interface

FastVimes includes a built-in admin interface at `/admin` with:

- **Dashboard**: Overview of your database and tables
- **Tables**: Browse, filter, and manage all database tables
- **Schema**: View and inspect table schemas
- **Configuration**: Manage application settings

### Admin Features

- **FastHTML-generated**: All HTML generated in Python using FastHTML
- **Static-first**: Base templates are static HTML, HTMX adds dynamic capabilities
- **Customizable**: Export any page as static HTML for customization
- **HTMX-powered**: Table views load as fragments without page refreshes
- **Interactive table management**: View data, HTML representations, and schemas
- **Responsive design**: Built with Bulma CSS framework

Access the admin interface by visiting `http://localhost:8000/admin` when your FastVimes application is running.

### Customizing Admin Interface

```bash
# Export any admin page as static HTML
fastvimes static-override /admin/tables --output ./my-templates
fastvimes static-override /admin --output ./my-templates
fastvimes static-override /admin/fragments/tables --output ./my-templates

# Customize the exported HTML files
# Place them in your static directory to override defaults
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
- ✅ Admin HTMX integration for table views
- ✅ Admin interface documentation
- ✅ Clarify URL patterns: Move to `/api/*` for JSON endpoints, clean up admin routes
- ✅ Standardize admin HTML fragments: `/admin/fragments/*` pattern
- ✅ Consistent endpoint naming: Remove `/data/{table}/html` confusion
- ✅ FastHTML-based HTML generation throughout
- ✅ Static-override CLI command for customization
- ✅ Static-first architecture with HTMX for dynamic capabilities

TODO:
**Design Improvements:**
- 🏗️ Separate admin fragments from public API endpoints (completed in URL restructure)
- Update bulma css to be themed like gruvbox with light/dark modes by default

**Features:**
- 📋 Add OpenAPI page to admin with FastAPI Swagger UI using HTMX
- 🗃️ Implement Datasette-style table management interface  
- ⚙️ Add Pydantic configuration editor for runtime settings
- 🔍 Add HTML fragment viewer for API endpoint previews
- 🎨 Improve admin HTML for WCAG 2.2+ compliance with tests
- 📊 Add complexity and test coverage reporting
- 🔍 Review development methodology for maturity improvements

**Architecture:**
- 🏗️ Separate admin fragments from public API endpoints (completed)
- 🔄 Update AGENT.md with clarified URL patterns (completed)
- 📝 Update documentation to match new URL structure (completed)
- 🔐 Implement admin UI consumption of public API endpoints (API dogfooding)
- 🔒 Implement path-based security for admin vs public routes