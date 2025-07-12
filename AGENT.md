# Agent Guide for FastVimes

Development commands and project info for AI assistants.

## Architecture Patterns

**Follow established patterns to minimize custom code:**

- **Frontend**: FastHTML generation + HTMX fragments + Bulma CSS
- **Python API**: SQLGlot + DuckDB direct connection + pydantic config
- **HTTP API**: FastAPI dependency injection + auto-generated endpoints with RQL query language
- **Services**: DatabaseService (clean separation)
- **CLI**: Typer commands inheriting from Python API + static-override for customization
- **FastAPI-first**: Use FastAPI's built-in parameter parsing, dependency injection, and validation instead of manual HTTP request parsing
- **Static-first HTML**: FastHTML generates static HTML, HTMX adds dynamic capabilities

## Admin UI Architecture

**The admin interface is a comprehensive single-page application that dogfoods the FastVimes API:**

### **Core Principle: Admin UI Uses Public API Structure**
- **Admin UI (FastHTML)** uses the same **services and logic (DatabaseService + RQL + Ibis)** that power the public API
- This ensures consistency and validates the public interface implementation through shared code paths
- Admin functionality is achieved through privileged endpoints under `/admin/*` routes

### **Admin UI Components**
1. **API Explorer**: Embedded OpenAPI/Swagger UI for interactive API documentation
2. **Table Management**: Datasette-style interface for browsing, filtering, and editing data
3. **Configuration Management**: Pydantic settings editor for runtime configuration
4. **HTML Fragment Viewer**: Preview HTML variants of API endpoints
5. **Schema Browser**: Interactive database schema exploration

### **Security Model**
- **Public API**: `/api/*` - Read-only by default, configurable per-table
- **Admin Privileged**: `/admin/*` - Write operations, configuration, system management
- **Path-based Security**: Simple URL pattern matching for access control policies

### **Data Flow Architecture**
```
Admin UI (FastHTML) → DatabaseService → RQL Parser → SQLGlot Queries → DuckDB
     ↓                      ↓
HTMX Fragments         FastAPI Routes (same services)
```

### **Admin Route Structure**
```
# Static HTML Interface (FastHTML-generated, overridable)
/admin/html/                      # Dashboard static HTML
/admin/html/schema                # Schema static page
/admin/html/config                # Configuration static page

# Dynamic API Endpoints  
/api/*                           # Public API (normal operations)
/api/{table}                     # Get/edit table or view data (tables and views treated identically)
/admin/api/*                     # Admin API (privileged operations)
/admin/api/schema                # Admin schema management API (create/drop tables/views)
/admin/api/config                # Admin configuration API

# HTMX Dynamic Loading
Admin HTML pages → HTMX calls → /api/* (normal data)
Admin HTML pages → HTMX calls → /admin/api/* (privileged operations)
```

### **View Management via Admin Schema API**
- **SQL Views**: Admin schema API enables creating/dropping SQL views via `/admin/api/schema`
- **DuckDB Integration**: Views are accessible through DuckDB connection like any table
- **Unified Access**: Views appear in `/api/{view_name}` endpoints same as tables
- **Admin UI**: Schema management interface provides view creation/editing capabilities

### **Static File Override Strategy**
- **FastHTML Generation**: All framework HTML generated using FastHTML
- **Static Override**: FastHTML outputs under `/admin/html/*` are static and overridable
- **User Customization**: Place custom HTML files in configured static directory to override defaults
- **Precedence**: User static files > Framework-generated FastHTML
- **CLI Export**: `static-override` command exports FastHTML output for customization

## Design Principles

**Core Philosophy: Lightweight composition over custom abstraction**

### 1. Introspection Over Configuration
- **Auto-generate everything**: Endpoints, models, forms, CLI commands from database schemas
- **Zero-config startup**: Point at database, get full API/admin interface instantly
- **Inheritance for customization**: Extend FastVimes class, override methods as needed
- **Minimal code required**: Single class inheritance should handle most use cases

### 2. Security and Safety First
- **SQLGlot for SQL safety**: Prevents SQL injection through safe query building and parameterization
- **FastAPI for HTTP security**: Built-in validation, dependency injection, automatic docs
- **Pydantic for data validation**: Type safety and automatic validation at runtime
- **Secure defaults**: Read-only by default, explicit opt-in for write operations

### 3. Composition Over Custom Code
- **Use library built-ins**: FastAPI's `Query()`, `Depends()`, `HTTPException` instead of custom equivalents
- **Combine stable tools**: FastAPI + SQLGlot + DuckDB + Pydantic rather than building custom abstractions
- **Extend through services**: Add functionality via dependency injection, not inheritance
- **Simple deployment**: Single Python file should be sufficient for basic apps

### 4. Modern Developer Experience
- **Better than existing conventions**: RQL-based filtering, auto-generated endpoints, OpenAPI compliance
- **Sensible defaults**: JSON by default, HTML fragments for HTMX, automatic schema introspection
- **Progressive enhancement**: Start with simple table access, add complexity as needed
- **Clear boundaries**: Database operations in services, HTTP logic in endpoints, CLI in separate module
- **API Dogfooding**: Admin interface validates the public API by consuming it internally

### 5. Testing and Development Workflow
- **RQL-based filtering**: All tests use RQL grammar (`?eq(id,1)` or `?id=eq=1`) for consistent, simple query patterns
- **Automated API testing**: Built-in `httpx` CLI command for testing endpoints with automatic server lifecycle
- **Consistent test patterns**: Use RQL operators throughout test suite for filtering, sorting, and aggregation
- **Fast feedback loop**: Server start/stop handled automatically for API testing

## Decision Framework

**When to choose different approaches:**

### When to Use FastVimes
- **Database-driven applications**: CRUD operations, admin interfaces, data APIs
- **Rapid prototyping**: Need instant API from existing database
- **Simple data tools**: Analytics dashboards, reporting interfaces
- **Team productivity**: Want to focus on business logic, not API boilerplate

### When NOT to Use FastVimes
- **Complex business logic**: Multi-step workflows, complex validation rules
- **High-performance requirements**: Real-time systems, high-frequency trading
- **Non-tabular data**: Document stores, graph databases, streaming data
- **Microservices**: When you need fine-grained service boundaries

### Implementation Choices
- **Use SQLGlot when**: Working with table data, need SQL safety, want safe query building
- **Add middleware when**: Cross-cutting concerns (auth, logging, rate limiting)
- **Use dependencies when**: Per-endpoint logic, parameter validation, request parsing
- **Extend FastVimes when**: Need to override default behavior, add global configuration
- **Create services when**: Business logic, external integrations, complex operations
- **Admin endpoints when**: Privileged operations (table management, configuration changes)
- **Public API when**: External access, read operations, standard CRUD

## CLI Architecture: Python vs HTTP API Testing

**FastVimes CLI provides two distinct patterns for different use cases:**

### 1. **Direct Python API Commands** (Efficient for daily use)
```bash
# These commands call Python methods directly, bypassing HTTP
uv run fastvimes tables --db demo.db              # Direct: app.list_tables_api()
uv run fastvimes get users --db demo.db           # Direct: app.get_table_data_api()
uv run fastvimes post users --data '{"name":"X"}' # Direct: app.create_record_api()
```
- **Purpose**: Fast, efficient operations for normal usage
- **Bypasses**: HTTP server, URL encoding, FastAPI dependencies
- **Use when**: Regular database operations, scripting, automation

### 2. **HTTP API Testing with `httpx` Command** (Tests full HTTP stack)
```bash
# These commands start a FastAPI server and make real HTTP requests with httpx
uv run fastvimes httpx --db demo.db "GET /api/users?eq(id,1)"
uv run fastvimes httpx --db demo.db "POST /api/users" --data '{"name":"Alice"}'
uv run fastvimes httpx --db demo.db --verbose "GET /api/users/html"
```
- **Purpose**: Test HTTP API consistency, URL encoding, RQL parsing, FastAPI dependencies
- **Tests**: Full HTTP stack including routing, middleware, dependency injection
- **Use when**: Verifying API behavior, testing RQL syntax, debugging HTTP issues

### 3. **Design Principle: API/CLI/HTML Consistency**
```python
# Same endpoints accessible three ways:
GET /api/users/                    # JSON API (FastAPI)
GET /api/users/html               # HTML fragments (FastHTML + HTMX)  
fastvimes get users               # CLI (direct Python calls)
fastvimes httpx "GET /api/users/"  # CLI HTTP testing (httpx)
```

## Development Workflow

**CRITICAL**: Always follow this exact order:

1. **Update Design** - Modify AGENT.md with new architecture/features/fixes
2. **Update Tests** - Write/modify tests to match the new design
3. **Implement Code** - Make the actual code changes to pass the tests
4. **Update Documentation** - Update user-facing docs and examples

## Development Commands

**CRITICAL**: All development commands use `uv run` to ensure consistent environment.

### Setup
```bash
# Install with uv (automatically handles Python 3.13+)
uv sync

# Install for development
uv sync --dev
```

**Requirements:**
- uv package manager (automatically handles Python 3.13+)

### Core Development Workflow

**Testing and Quality Assurance:**
```bash
# Run comprehensive automated tests (primary development command)
uv run pytest tests/test_core_functionality.py

# Run with coverage
uv run pytest tests/test_core_functionality.py --cov=fastvimes

# Format and lint (run before commits)
uv run ruff format
uv run ruff check --fix

# Type checking
uv run mypy fastvimes/

# Quick validation of core functionality
uv run fastvimes get users --eq "active,true" --db demo.db
```

**Local Development Server:**
```bash
# Start development server (most common)  
uv run fastvimes serve --db demo.db

# Initialize demo data for testing
uv run fastvimes init --db demo.db --force

# Check database schema during development
uv run fastvimes schema --db demo.db
uv run fastvimes tables --db demo.db

# Show configuration
uv run fastvimes config --db demo.db

# Export static HTML for customization
uv run fastvimes static-override /admin/html/tables --db demo.db
```

**Running Examples:**
```bash
# Run basic example
uv run python examples/basic_app.py serve

# Initialize example database
uv run python examples/basic_app.py init-db --force

# Get example info
uv run python examples/basic_app.py info
```

**Database Operations (for testing):**
```bash
# Execute SQL for testing
uv run fastvimes query "SELECT * FROM users LIMIT 5" --db demo.db

# Different output formats
uv run fastvimes query "SELECT COUNT(*) FROM users" --format json --db demo.db
uv run fastvimes query "SELECT * FROM users" --format csv --db demo.db
```

**HTTP API Testing with httpx:**
```bash
# Test HTTP endpoints with automatic server management using httpx
uv run fastvimes httpx --db demo.db "GET /api/users/"
uv run fastvimes httpx --db demo.db "GET /api/users/?eq(id,1)"
uv run fastvimes httpx --db demo.db "GET /api/users/?age=gt=25"
uv run fastvimes httpx --db demo.db "POST /api/users" --data '{"name": "Alice"}'
uv run fastvimes httpx --db demo.db "PUT /api/users?eq(id,1)" --data '{"name": "Bob"}'
uv run fastvimes httpx --db demo.db "DELETE /api/users?eq(id,1)"

# Test HTML endpoints for HTMX
uv run fastvimes httpx --db demo.db "GET /api/users/html"
uv run fastvimes httpx --db demo.db --headers "Accept: text/html" "GET /api/users/html"

# Advanced options with verbose output
uv run fastvimes httpx --db demo.db --port 8001 --verbose "GET /api/users/?limit=10"
```

### Development Best Practices

1. **Always use `uv run`** - ensures consistent Python environment
2. **Test frequently** - `uv run pytest` should pass before any commit
3. **Use demo database** - `demo.db` for development, `:memory:` for tests
4. **Format before commit** - `uv run ruff format && uv run ruff check --fix`
5. **Admin interface** - Access at `http://localhost:8000/admin` during development

## Key Dependencies

- **FastAPI**: HTTP framework and dependency injection
- **FastHTML (python-fasthtml)**: HTML generation
- **Typer**: CLI framework
- **SQLGlot**: SQL query building and parsing
- **DuckDB**: Database backend
- **pydantic-settings**: Configuration management with full-depth env vars
- **Uvicorn**: ASGI server

## Architecture Notes

**Implementation details specific to FastVimes:**

- **URL patterns**: Clear separation of API and UI endpoints
  - `/api/{table}` - JSON API endpoints for table data
  - `/api/{table}/html` - HTML table views for public access
- **Admin interface**: `/admin` with HTMX-powered WCAG compliant interface
- **DuckDB-only**: Backend can attach other databases and object stores via extensions

## Project Structure

```
fastvimes/
├── __init__.py          # Main FastVimes class export
├── app.py               # FastVimes class implementation
├── cli.py               # Typer CLI commands

├── forms.py             # Auto-generate FastHTML forms from DuckDB schemas
├── config.py            # pydantic-settings configuration schema
├── middleware.py        # Authentication and identity middleware
├── admin/               # Static admin HTML files (overridable by app devs)
│   ├── dashboard.html   # Main admin dashboard
│   ├── tables.html      # Table browser
│   ├── nav.html         # Navigation component
│   ├── schema.html      # Schema editor
│   └── config.html      # Configuration management
└── static/              # Default static files
    └── header_include.html  # Default empty header include
```

## RQL Query Language

**FastVimes uses RQL (Resource Query Language) for consistent, simple REST API querying:**

### Core RQL Operators
- **Comparison**: `eq(property,value)`, `lt(property,value)`, `gt(property,value)`, `le(property,value)`, `ge(property,value)`, `ne(property,value)`
- **Logical**: `and(query,query,...)`, `or(query,query,...)`
- **Set operations**: `in(property,array)`, `out(property,array)`, `contains(property,value)`, `excludes(property,value)`
- **Sorting**: `sort(+property,-property,...)` (+ for ascending, - for descending)
- **Limiting**: `limit(count,start,maxCount)`
- **Selection**: `select(property,property,...)`, `values(property)`
- **Aggregation**: `aggregate(property|function,...)`, `count()`, `distinct()`

### RQL Syntax Examples
```bash
# Basic filtering
GET /api/users?eq(id,123)           # id equals 123
GET /api/users?lt(age,30)           # age less than 30
GET /api/users?contains(name,alice) # name contains "alice"

# FIQL syntax sugar (alternative)
GET /api/users?id=eq=123            # Same as eq(id,123)
GET /api/users?age=lt=30            # Same as lt(age,30)

# Logical operations
GET /api/users?and(eq(active,true),gt(age,18))  # active AND age > 18
GET /api/users?or(eq(role,admin),eq(role,mod))  # role is admin OR mod

# Set operations
GET /api/users?in(id,(1,2,3))       # id in [1,2,3]
GET /api/users?out(status,(banned,deleted))    # status not in [banned,deleted]

# Sorting and limiting
GET /api/users?sort(+name,-created_at)         # Sort by name ASC, created_at DESC
GET /api/users?limit(10,20)                    # Skip 20, take 10 (pagination)

# Selection and aggregation
GET /api/users?select(id,name,email)           # Only return these fields
GET /api/users?count()                         # Return count only
GET /api/users?aggregate(department,count)     # Group by department with counts
```

### OpenAPI Integration
- **Automatic parameter documentation**: RQL operators become OpenAPI query parameters
- **Type safety**: FastAPI validates RQL syntax and parameter types
- **Schema generation**: Auto-generated OpenAPI spec includes all RQL operators
- **Interactive docs**: Swagger UI includes RQL query examples

## Implementation Patterns

**Configuration:**
```python
# pydantic-settings pattern
class FastVimesSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='FASTVIMES_',
        toml_file='fastvimes.toml'
    )
    db_path: str = "data.db"
    admin_enabled: bool = True
```

**Data Flow:**
```python
# SQLGlot + DuckDB connection pattern
app = FastVimes(db_path="data.db")
users = app.connection.table("users")

# FastAPI endpoint auto-generation
@app.get("/api/users")      # JSON API endpoint
@app.get("/api/users/html")     # HTML table view

# Admin UI uses the same services as the public API
# Admin FastHTML components use DatabaseService directly
# This validates the public API through shared implementation

# RQL-style query examples:
# GET /api/users?eq(id,123)
# GET /api/users?id=eq=123
# GET /api/users?contains(name,alice)
# GET /api/users?eq(active,true)
# GET /api/users?in(id,(1,2,3))
```

**Admin UI Implementation:**
```python
# Admin UI uses the same services as public API
# FastHTML components use DatabaseService directly, not HTTP requests

# Example: Admin static HTML page
@admin_router.get("/admin/html/tables")
def admin_tables_page():
    # Generate static FastHTML page (overridable by user)
    page = html_generator.generate_tables_page()
    return html_generator.render_to_string(page)

# Example: Admin privileged API endpoint  
@admin_router.get("/admin/api/tables")
def admin_tables_api(db_service: DatabaseService = Depends(get_db_service)):
    # Admin API uses the same service as public API
    tables = db_service.list_tables()  # Same method used by /api/tables
    return {"tables": tables}  # JSON for HTMX consumption

# Example: Admin config management API
@admin_router.post("/admin/api/config")
def admin_update_config(settings: FastVimesSettings):
    # Privileged operation: update runtime configuration
    app.config = settings
    return {"status": "updated"}

# Data flow:
# /admin/html/tables (static HTML) → HTMX calls → /admin/api/tables (JSON)
# /api/tables (public) and /admin/api/tables (privileged) use same service
```

## Code Style

- Use **ruff** for formatting and linting
- Type hints on public functions
- Keep functions small and focused
- Prefer composition over inheritance
