# FastVimes

**Instant database APIs** - Point at any DuckDB database and get automatic REST APIs, CLI tools, and admin interface.

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

## Features

- **Auto-generated APIs** from DuckDB schemas with RQL query language
- **Type-safe queries** using SQLGlot (no SQL injection vulnerabilities)  
- **Admin interface** with HTMX-powered table management at `/admin`
- **Multiple interfaces**: CLI, OpenAPI/Swagger, HTML forms
- **Instant setup**: Point at database and run

## Usage Patterns

### 1. Instant App
```python
# Point at database, get instant APIs
app = FastVimes(db_path="data.db")
# Auto-generates: GET/POST /api/users, /api/products, etc.
# Admin interface: /admin | OpenAPI docs: /docs
```

### 2. Custom Configuration  
```python
app = FastVimes(
    db_path="data.db",
    extensions=["spatial", "httpfs"],
    read_only=False
)
```

### 3. Custom Endpoints (Standard FastAPI)
```python
app = FastVimes(db_path="data.db")

@app.get("/dashboard")
def dashboard():
    return app.db_service.execute_query(
        "SELECT SUM(amount) as total_sales FROM sales"
    )
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

## Admin Interface

Built-in admin interface at `/admin` for database management:

- **Table Browser**: View, filter, and manage all database tables
- **SQL Query**: Direct database access with syntax highlighting  
- **API Explorer**: Embedded OpenAPI/Swagger documentation
- **Configuration**: Runtime settings management

## CLI & Testing

```bash
# Start server
fastvimes serve --db mydata.db

# Test API endpoints (automatic server management)
fastvimes curl --db mydata.db "GET /api/users?eq(id,1)"
fastvimes curl --db mydata.db "POST /api/users" --data '{"name": "Alice"}'

# Database operations
fastvimes tables --db mydata.db
fastvimes query "SELECT * FROM users" --db mydata.db
```

## Architecture

FastVimes is a **lightweight composition** of stable libraries:

- **FastAPI** - HTTP framework and dependency injection
- **SQLGlot** - Safe SQL query building and parsing  
- **DuckDB** - High-performance analytics database
- **Pydantic** - Configuration and data validation
- **Typer** - CLI interface

**Goal**: Clean, inherited APIs with minimal abstraction.

## Documentation

See [AGENT.md](AGENT.md) for development commands and detailed architecture.

## Contributing

FastVimes follows these core priorities for new contributors:

### Priority 1: Core Database API Functionality
- **RQL query language** enhancements and new operators
- **Type safety** improvements with SQLGlot integration  
- **Performance** optimizations for DuckDB operations
- **Schema introspection** and auto-generation features

### Priority 2: Developer Experience
- **Error handling** and debugging capabilities
- **Testing** infrastructure and example applications
- **Documentation** for API patterns and extensions
- **CLI** command improvements and workflow optimization

### Priority 3: Admin Interface (when needed)
- **Security** path-based access control
- **Data management** core functionality only
- **Configuration** runtime settings management

### Not Currently Prioritized
- CSS/styling enhancements (use Bulma defaults)
- Mobile responsive design (desktop-first for data tools)
- Complex UI animations or visual polish
- WCAG compliance beyond basic accessibility

New contributors should focus on **database API functionality** and **developer experience** rather than UI polish.

## Stability & Versioning

FastVimes follows **semantic versioning** with these compatibility guarantees:

- **Major versions** (1.x → 2.x): Breaking changes to core APIs
- **Minor versions** (1.1 → 1.2): New features, backwards compatible
- **Patch versions** (1.1.1 → 1.1.2): Bug fixes only

**Stable APIs** (will not change without major version bump):
- `FastVimes` class constructor parameters
- Core HTTP endpoints (`/api/{table}`, `/admin`)
- RQL query language operators
- CLI command interface

**Extension-safe patterns** (guaranteed stable):
```python
# Safe: Inherit and override methods
class MyApp(FastVimes):
    def get_custom_endpoint(self):
        return self.db_service.execute_query("SELECT ...")

# Safe: Add routes using FastAPI patterns  
@app.get("/dashboard")
def dashboard(db_service: DatabaseService = Depends(app.get_db_service)):
    return db_service.execute_query("SELECT ...")
```

## Production Use

**Error Handling:**
```python
from fastvimes import FastVimes
from fastvimes.exceptions import DatabaseError, ValidationError

app = FastVimes(db_path="prod.db")

@app.exception_handler(DatabaseError)
def handle_db_error(request, exc):
    return {"error": "Database unavailable", "code": 500}
```

**Testing Extensions:**
```python
def test_custom_endpoint():
    app = FastVimes(db_path=":memory:")
    client = TestClient(app)
    response = client.get("/dashboard")
    assert response.status_code == 200
```