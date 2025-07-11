# Agent Guide for FastVimes

Development commands and project info for AI assistants.

## Architecture Patterns

**Follow established patterns to minimize custom code:**

- **Frontend**: HTMX fragments + Bulma CSS + static files
- **Python API**: Ibis connection patterns + pydantic config
- **HTTP API**: FastAPI dependency injection + auto-generated endpoints with RQL query language
- **Services**: DatabaseService, AdminService (clean separation)
- **CLI**: Typer commands inheriting from Python API
- **FastAPI-first**: Use FastAPI's built-in parameter parsing, dependency injection, and validation instead of manual HTTP request parsing

## Design Principles

**Core Philosophy: Lightweight composition over custom abstraction**

### 1. Introspection Over Configuration
- **Auto-generate everything**: Endpoints, models, forms, CLI commands from database schemas
- **Zero-config startup**: Point at database, get full API/admin interface instantly
- **Inheritance for customization**: Extend FastVimes class, override methods as needed
- **Minimal code required**: Single class inheritance should handle most use cases

### 2. Security and Safety First
- **Ibis for SQL safety**: Prevents SQL injection through safe query building
- **FastAPI for HTTP security**: Built-in validation, dependency injection, automatic docs
- **Pydantic for data validation**: Type safety and automatic validation at runtime
- **Secure defaults**: Read-only by default, explicit opt-in for write operations

### 3. Composition Over Custom Code
- **Use library built-ins**: FastAPI's `Query()`, `Depends()`, `HTTPException` instead of custom equivalents
- **Combine stable tools**: FastAPI + Ibis + Pydantic rather than building custom abstractions
- **Extend through services**: Add functionality via dependency injection, not inheritance
- **Simple deployment**: Single Python file should be sufficient for basic apps

### 4. Modern Developer Experience
- **Better than existing conventions**: RQL-based filtering, auto-generated endpoints, OpenAPI compliance
- **Sensible defaults**: JSON by default, HTML fragments for HTMX, automatic schema introspection
- **Progressive enhancement**: Start with simple table access, add complexity as needed
- **Clear boundaries**: Database operations in services, HTTP logic in endpoints, CLI in separate module

### 5. Testing and Development Workflow
- **RQL-based filtering**: All tests use RQL grammar (`?eq(id,1)` or `?id=eq=1`) for consistent, simple query patterns
- **Automated API testing**: Built-in `curl` CLI command for testing endpoints with automatic server lifecycle
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
- **Use Ibis when**: Working with table data, need SQL safety, want database portability
- **Add middleware when**: Cross-cutting concerns (auth, logging, rate limiting)
- **Use dependencies when**: Per-endpoint logic, parameter validation, request parsing
- **Extend FastVimes when**: Need to override default behavior, add global configuration
- **Create services when**: Business logic, external integrations, complex operations

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
# Run tests (primary development command)
uv run pytest

# Run with coverage
uv run pytest --cov=fastvimes

# Format and lint (run before commits)
uv run ruff format
uv run ruff check --fix

# Type checking
uv run mypy fastvimes/
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

**API Testing with curl:**
```bash
# Test API endpoints with automatic server management
uv run fastvimes curl --db demo.db "GET /users"
uv run fastvimes curl --db demo.db "GET /users?eq(id,1)"
uv run fastvimes curl --db demo.db "POST /users" --data '{"name": "Alice"}'
uv run fastvimes curl --db demo.db "PUT /users?eq(id,1)" --data '{"name": "Bob"}'
uv run fastvimes curl --db demo.db "DELETE /users?eq(id,1)"

# Advanced curl options
uv run fastvimes curl --db demo.db --port 8001 --verbose "GET /users?limit(10)"
uv run fastvimes curl --db demo.db --headers "Accept: text/html" "GET /users/html"
```

### Development Best Practices

1. **Always use `uv run`** - ensures consistent Python environment
2. **Test frequently** - `uv run pytest` should pass before any commit
3. **Use demo database** - `demo.db` for development, `:memory:` for tests
4. **Format before commit** - `uv run ruff format && uv run ruff check --fix`
5. **Admin interface** - Access at `http://localhost:8000/admin` during development

## Key Dependencies

- **FastAPI**: HTTP framework and dependency injection
- **FastHTML (python-fasthtml)**: HTML generation and form system (auto-generated from Pydantic models)
- **Typer**: CLI framework
- **Ibis**: Data abstraction layer
- **DuckDB**: Database backend
- **pydantic-settings**: Configuration management with full-depth env vars
- **Uvicorn**: ASGI server

## Architecture Notes

**Implementation details specific to FastVimes:**

- **URL patterns**: `/{table}` for JSON, `/{table}/html` for HTML fragments
- **Primary key handling**: Auto-detect from schema, fallback to rowid if configurable
- **Environment variables**: Full-depth nesting (`FASTVIMES_TABLES_USERS_MODE=readwrite`)
- **HTML introspection**: Instant app setup from database + HTML folder structure
- **CDN dependencies**: Bulma 1.0.4, HTMX 2.0.6, Font Awesome 5.15.4 via unpkg
- **DuckDB-only**: Backend with extension support for other databases
- **HTML error handling**: Errors embedded in HTML response with Bulma styling (JSON/CLI use FastAPI/Typer defaults)
- **Customization**: Override via `static/header_include.html` and CSS files
- **Views pattern**: Use database views for complex queries vs complex API parameters

## Project Structure

```
fastvimes/
├── __init__.py          # Main FastVimes class export
├── app.py               # FastVimes class implementation
├── cli.py               # Typer CLI commands
├── endpoints.py         # Auto-generated API endpoints
├── forms.py             # Auto-generate FastHTML forms from Ibis schemas
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
GET /users?eq(id,123)           # id equals 123
GET /users?lt(age,30)           # age less than 30
GET /users?contains(name,alice) # name contains "alice"

# FIQL syntax sugar (alternative)
GET /users?id=eq=123            # Same as eq(id,123)
GET /users?age=lt=30            # Same as lt(age,30)

# Logical operations
GET /users?and(eq(active,true),gt(age,18))  # active AND age > 18
GET /users?or(eq(role,admin),eq(role,mod))  # role is admin OR mod

# Set operations
GET /users?in(id,(1,2,3))       # id in [1,2,3]
GET /users?out(status,(banned,deleted))    # status not in [banned,deleted]

# Sorting and limiting
GET /users?sort(+name,-created_at)         # Sort by name ASC, created_at DESC
GET /users?limit(10,20)                    # Skip 20, take 10 (pagination)

# Selection and aggregation
GET /users?select(id,name,email)           # Only return these fields
GET /users?count()                         # Return count only
GET /users?aggregate(department,count)     # Group by department with counts
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
# Ibis connection pattern
app = FastVimes(db_path="data.db")
users = app.connection.table("users")

# FastAPI endpoint auto-generation
@app.get("/users")  # JSON response
@app.get("/users/html")  # HTML fragment

# RQL-style query examples:
# GET /users?eq(id,123)
# GET /users?id=eq=123
# GET /users?contains(name,alice)
# GET /users?eq(active,true)
# GET /users?in(id,(1,2,3))
```

## Code Style

- Use **ruff** for formatting and linting
- Type hints on public functions
- Keep functions small and focused
- Prefer composition over inheritance
