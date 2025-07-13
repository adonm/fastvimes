# Agent Guide for FastVimes

Development commands and project info for AI assistants.

## Project Vision

**FastVimes: Auto-Generated Datasette-Style Apps with NiceGUI + DuckDB**

Generate Datasette-like exploratory interfaces automatically from DuckDB schemas using NiceGUI's reactive components, with incremental override capabilities for custom form/database applications.

**Core Concept**: `fastvimes serve` → instant reactive web app with sample data, tables, forms, charts, and API. Use DuckDB for high-performance analytics, with DuckLake as a production target for multi-user capabilities.

**Default Setup**: Uses in-memory DuckDB with sample data for zero-config startup. Production: point at persistent DuckDB files or DuckLake with PostgreSQL/MySQL catalog for multi-user access.

## Schema Introspection Verbs

**META OPERATIONS** (database introspection):
- list_tables() -> List[Dict[str, Any]]
- get_table_schema(table_name: str) -> List[Dict[str, Any]]
- execute_query(query: str, params: List[Any]) -> List[Dict[str, Any]]

**DATA OPERATIONS** (table CRUD, work on any table):
- get_table_data(table_name, rql_query, limit, offset, format) -> Dict[str, Any] | bytes
- create_record(table_name: str, data: Dict[str, Any]) -> Dict[str, Any]
- update_records(table_name: str, data: Dict[str, Any], filters: Dict[str, Any]) -> int
- delete_records(table_name: str, filters: Dict[str, Any]) -> int

**SUPPORTED OUTPUT FORMATS:**
- **Python objects** (fetchall) → JSON in HTTP APIs
- **Parquet files** (DuckDB native: `duckdb.sql().write_parquet()`)  
- **CSV files** (DuckDB native: `duckdb.sql().write_csv()`)

**SUPPORTED INPUT FORMATS** (future bulk operations):
- **JSON** (single records and arrays)
- **Parquet files** (DuckDB native: `INSERT INTO table SELECT * FROM 'file.parquet'`)
- **CSV files** (DuckDB native: `INSERT INTO table SELECT * FROM 'file.csv'`)

## DuckLake Production Target

**FastVimes primarily uses DuckDB** for development and single-user scenarios, with **DuckLake as the first-class production target** for scaling to multi-user concurrent access:

- **Development**: DuckDB files provide high-performance analytics with simple file-based storage
- **Production**: DuckLake enables concurrent multi-user access with ACID guarantees via PostgreSQL/MySQL catalogs
- **Migration Path**: Seamless upgrade from DuckDB to DuckLake for production deployments
- **Multi-Catalog Support**: DuckLake supports multiple database catalogs for complex production environments

## API Namespacing

**FastAPI URL Structure** (prevents table name collisions):
```
/api/v1/meta/tables              # List tables
/api/v1/meta/schema/{table}      # Get table schema
/api/v1/data/{table}             # CRUD operations (GET/POST/PUT/DELETE)
/api/v1/data/{table}?format=json # JSON (default)
/api/v1/data/{table}?format=parquet # Parquet file download
/api/v1/data/{table}?format=csv  # CSV file download
/api/v1/query                    # Raw SQL execution
```

**CLI Command Structure** (prevents table name collisions):
```bash
fastvimes meta tables            # List tables
fastvimes meta schema {table}    # Get table schema
fastvimes data get {table}       # Get table data with RQL (JSON default)
fastvimes data get {table} --format json    # JSON output
fastvimes data get {table} --format parquet # Parquet file
fastvimes data get {table} --format csv     # CSV file
fastvimes data create {table}    # Create record in table
fastvimes data update {table}    # Update records in table
fastvimes data delete {table}    # Delete records from table
fastvimes data bulk-insert {table} --file data.parquet  # Future: bulk insert
fastvimes data bulk-upsert {table} --file data.csv      # Future: bulk upsert
fastvimes query "SQL..." --format csv       # Execute raw SQL with CSV output
fastvimes httpx "GET /api/v1/..." # Test HTTP endpoints
```

## Architecture Patterns

**CRITICAL: Single Source of Truth Flow**

```
DuckDB/DuckLake (system of record) 
    ↓ SQLGlot (safe SQL generation)
    ↓ PyRQL (query language) 
    ↓ DatabaseService Public Methods (business logic, validation, RQL support)
    ↓ FastAPI (light wrapper) + Typer CLI (light wrapper) + NiceGUI (direct calls)
```

**Follow established patterns to minimize custom code:**

- **Database Layer**: DuckDB/DuckLake + SQLGlot for safety + PyRQL for queries
- **DatabaseService**: Public methods with business logic, validation, RQL support
  - **Public methods**: API surface exposed via CLI/FastAPI/NiceGUI (well-tested)
  - **Private methods**: Internal implementation details (prefixed with `_`)
- **FastAPI**: Light wrappers over DatabaseService public methods (auto-exposed as HTTP/OpenAPI)
- **CLI**: Light wrappers over DatabaseService public methods (not HTTP calls)
  - **Regular commands**: Direct DatabaseService method calls (efficient)
  - **httpx command**: Test FastAPI endpoints with automatic server lifecycle
- **NiceGUI**: Calls DatabaseService public methods directly
- **Validation**: All validation happens in DatabaseService public methods - FastAPI/CLI/NiceGUI inherit it
- **Exploratory UI**: Auto-generated Datasette-style interface with incremental customization
- **Override Pattern**: Start with auto-generated NiceGUI components, selectively override for custom functionality
- **Production**: DuckLake enables concurrent multi-user access with ACID guarantees

**This ensures:**
- Single source of truth through DatabaseService public methods
- API consistency across CLI/HTTP/NiceGUI (1:1 method mapping)
- All features available via machine-friendly HTTP API
- NiceGUI validates public API by using it directly
- No HTTP overhead in CLI layer
- Clear separation: public API vs internal implementation

## NiceGUI Exploratory Interface

**Auto-generated Datasette-style interface with incremental override capabilities:**

### **Core Principle: Schema-Driven UI Generation**
- **Auto-generation**: NiceGUI components generated automatically from DuckLake schema
- **Incremental Override**: Start with generated interface, selectively replace components for custom functionality
- **Reactive Components**: Use NiceGUI's Vue.js-based reactive system for real-time data updates
- **API Integration**: All UI components consume the same RQL-based FastAPI endpoints
- **Embedded UIs**: DuckDB UI extension and FastAPI docs accessible within NiceGUI interface (iframe integration)

### **Auto-Generated Components**
1. **Table Browser**: Interactive table/view listing with search and filtering
2. **Data Explorer**: Sortable, filterable data grids with inline editing capabilities
3. **Form Generator**: CRUD forms automatically created from table schemas

### **Planned Components**
4. **Query Builder**: Visual RQL query construction interface (Phase 3)
5. **Chart Generator**: Auto-generated plots based on column types and data patterns (Phase 3)
6. **Relationship Navigator**: Follow foreign keys between related tables (Phase 5)

### **Schema Generation Scope (MVP)**
- **Basic tables**: Simple column types (text, number, date, boolean)
- **No joins/relations**: Ignore foreign keys and complex relationships initially
- **Views as enhancement**: Use database views to handle complex queries and relationships
- **Progressive enhancement**: Add relationship support after core functionality is solid

### **Override Strategy**
```python
# Auto-generated base interface
app = FastVimes(db_path="data.db")
app.serve()  # Gets full Datasette-style interface

# Incremental customization
class MyApp(FastVimes):
    def table_component(self, table_name: str):
        if table_name == "users":
            return custom_user_table()  # Custom component
        return super().table_component(table_name)  # Default for others
        
    def form_component(self, table_name: str):
        if table_name == "orders":
            return custom_order_form()  # Custom form logic
        return super().form_component(table_name)  # Auto-generated forms
```

### **NiceGUI Integration Patterns**
```python
# Example auto-generated table view
@ui.page('/table/{table_name}')
def table_view(table_name: str):
    columns = app.get_table_schema(table_name)
    
    # Auto-generated filter controls
    filters = ui.row()
    for col in columns:
        create_filter_widget(col, filters)
    
    # Auto-generated data grid  
    table = ui.table(columns=columns, rows=[])
    table.bind_value_from(app.get_table_data, table_name)
    
    # Auto-generated action buttons
    ui.button('Add Record', on_click=lambda: show_add_form(table_name))
```

## Design Principles

**Core Philosophy: Auto-generated reactive interfaces with incremental customization**

### 1. Schema-Driven Auto-Generation
- **Auto-generate everything**: NiceGUI components, FastAPI endpoints, CLI commands from DuckLake schemas
- **Zero-config startup**: Point at DuckLake, get instant Datasette-style reactive interface
- **Override methods**: Start with full interface, selectively replace components as needed
- **Minimal code required**: Single method override should handle most customizations

### 2. Security and Safety First
- **SQLGlot for SQL safety**: Prevents SQL injection through safe query building and parameterization
- **FastAPI for HTTP security**: Built-in validation, dependency injection, automatic docs
- **Pydantic for data validation**: Type safety and automatic validation at runtime
- **Secure defaults**: Read-only by default, explicit opt-in for write operations

### 3. Composition Over Custom Code
- **Use library built-ins**: NiceGUI's reactive components, FastAPI's dependency injection
- **Combine stable tools**: NiceGUI + FastAPI + SQLGlot + DuckLake + Pydantic
- **Extend through services**: Add functionality via dependency injection, not inheritance
- **Simple deployment**: Single Python file should be sufficient for basic apps

### 4. Modern Developer Experience
- **Better than Datasette**: Reactive components, incremental customization, auto-generated forms
- **Sensible defaults**: Reactive UI by default, automatic schema introspection
- **Progressive enhancement**: Start with auto-generated interface, incrementally override for custom needs
- **Clear boundaries**: Database operations in services, HTTP logic in endpoints, UI in NiceGUI components
- **API Integration**: NiceGUI interface validates the public API by consuming it directly

### 5. Testing and Development Workflow
- **RQL-based filtering**: All tests use RQL grammar (`?eq(id,1)` or `?id=eq=1`) for consistent, simple query patterns
- **Automated API testing**: Built-in `httpx` CLI command for testing endpoints with automatic server lifecycle
- **Consistent test patterns**: Use RQL operators throughout test suite for filtering, sorting, and aggregation
- **Fast feedback loop**: Server start/stop handled automatically for API testing

## Core Focus Areas for Contributors

**Priority 1: Database API Core (80% of effort)**
- RQL query language enhancements
- SQLGlot type safety and query building
- DuckLake performance and schema introspection
- Auto-generation from database schemas

**Priority 2: Developer Experience (15% of effort)**  
- Error handling and debugging
- Testing infrastructure and CLI workflow
- Documentation and examples
- FastAPI integration patterns

**Priority 3: NiceGUI Interface (5% of effort)**
- Auto-generated components from schema
- Override patterns for customization
- Focus on functionality over visual polish

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
- **Override NiceGUI components when**: Need custom UI behavior, specialized forms, custom visualizations
- **Use auto-generated components when**: Standard CRUD operations, data exploration, rapid prototyping

## CLI Architecture: Python vs HTTP API Testing

**FastVimes CLI provides two distinct patterns for different use cases:**

### 1. **Direct Python API Commands** (Efficient for daily use)
```bash
# These commands call DatabaseService methods directly, bypassing HTTP
uv run fastvimes meta tables              # Direct: db_service.list_tables()
uv run fastvimes meta schema users        # Direct: db_service.get_table_schema()
uv run fastvimes data get users --format json     # Direct: db_service.get_table_data()
uv run fastvimes data get users --format parquet  # Direct: DuckDB native export
uv run fastvimes query "SELECT * FROM users LIMIT 5" --format csv  # Direct: DuckDB CSV export
```
- **Purpose**: Fast, efficient operations for normal usage
- **Bypasses**: HTTP server, URL encoding, FastAPI dependencies
- **Use when**: Regular database operations, scripting, automation

### 2. **HTTP API Testing with `httpx` Command** (Tests full HTTP stack)
```bash
# These commands start a FastAPI server and make real HTTP requests with httpx
uv run fastvimes httpx "GET /api/v1/meta/tables"
uv run fastvimes httpx "GET /api/v1/data/users?eq(active,true)&format=json"
uv run fastvimes httpx "GET /api/v1/data/users?format=parquet"
uv run fastvimes httpx "POST /api/v1/data/users" --data '{"name":"Alice"}'
uv run fastvimes httpx --verbose "GET /api/v1/meta/schema/users"
```
- **Purpose**: Test HTTP API consistency, URL encoding, RQL parsing, FastAPI dependencies
- **Tests**: Full HTTP stack including routing, middleware, dependency injection
- **Use when**: Verifying API behavior, testing RQL syntax, debugging HTTP issues

### 3. **Design Principle: API/CLI/NiceGUI Consistency**
```python
# Same endpoints accessible three ways:
GET /api/v1/data/users             # JSON API (FastAPI)
NiceGUI reactive components        # Auto-generated UI consuming DatabaseService directly  
fastvimes data get users           # CLI (direct Python calls)
fastvimes httpx "GET /api/v1/data/users"  # CLI HTTP testing (httpx)
```

## Development Workflow

**CRITICAL**: Always follow this exact order:

1. **Update Design** - Modify AGENT.md with new architecture/features/fixes
2. **Update Tests** - Write/modify tests to match the new design
3. **Implement Code** - Make the actual code changes to pass the tests
4. **Update Documentation** - Update user-facing docs and examples

**Architecture Compliance**: All new features must follow the single source of truth pattern:
- Business logic goes in DatabaseService public methods
- FastAPI endpoints are light wrappers over DatabaseService methods
- CLI commands are light wrappers over DatabaseService methods  
- NiceGUI calls DatabaseService methods directly
- All validation happens once in DatabaseService methods

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

### Quick Start (Zero Configuration)
```bash
# Instant demo with in-memory database and sample data
uv run fastvimes serve                  # No arguments needed!

# Or specify custom data
uv run fastvimes serve     # Point to existing DuckLake
```

### Core Development Workflow

**Testing and Quality Assurance:**
```bash
# Fast checks for regular development (recommended)
uv run pytest -m fast                    # Run only fast tests (~10 seconds)
uv run ruff format && uv run ruff check  # Format and lint

# Full test suite (run before commits)
uv run pytest                           # All tests including slow CLI tests (~20 seconds)
uv run pytest --cov=fastvimes          # With coverage report

# Specific test categories
uv run pytest -m python_api            # Python API tests only
uv run pytest -m http                  # HTTP API tests only 
uv run pytest -m "not slow"            # Skip slow subprocess tests

# Type checking (optional)
uv run mypy fastvimes/

# Quick validation of core functionality (NEW NAMESPACED COMMANDS)
uv run fastvimes meta tables
uv run fastvimes data get users --eq "active,true"
```

**Local Development Server:**
```bash
# Start development server (most common)  
uv run fastvimes serve

# Initialize demo data for testing
uv run fastvimes init --force

# Check database schema during development
uv run fastvimes schema
uv run fastvimes tables

# Show configuration
uv run fastvimes config

# Run development server (most common)  
uv run fastvimes serve
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
uv run fastvimes query "SELECT * FROM users LIMIT 5"

# Different output formats
uv run fastvimes query "SELECT COUNT(*) FROM users" --format json
uv run fastvimes query "SELECT * FROM users" --format csv
```

**HTTP API Testing with httpx:**
```bash
# Test HTTP endpoints with automatic server management using httpx
uv run fastvimes httpx "GET /api/v1/meta/tables"
uv run fastvimes httpx "GET /api/v1/data/users?eq(id,1)&format=json"
uv run fastvimes httpx "GET /api/v1/data/users?age=gt=25&format=parquet"
uv run fastvimes httpx "GET /api/v1/data/users?format=csv"
uv run fastvimes httpx "POST /api/v1/data/users" --data '{"name": "Alice"}'
uv run fastvimes httpx "PUT /api/v1/data/users?eq(id,1)" --data '{"name": "Bob"}'
uv run fastvimes httpx "DELETE /api/v1/data/users?eq(id,1)"

# Test with different query patterns and formats
uv run fastvimes httpx "GET /api/v1/data/users?limit=5&sort(+name)&format=json"
uv run fastvimes httpx "GET /api/v1/data/users?select(id,name,email)&format=csv"

# Advanced options with verbose output
uv run fastvimes httpx --port 8001 --verbose "GET /api/v1/data/users?limit=10&format=parquet"
```

### Development Best Practices

1. **Always use `uv run`** - ensures consistent Python environment
2. **Test frequently** - `uv run pytest` should pass before any commit
3. **Use demo database** - `demo.db` for development, `:memory:` for tests
4. **Format before commit** - `uv run ruff format && uv run ruff check --fix`
5. **NiceGUI interface** - Access at `http://localhost:8000` during development

## Key Dependencies

- **FastAPI**: HTTP framework and dependency injection
  - Docs: https://fastapi.tiangolo.com/
  - Usage: REST API endpoints, dependency injection, automatic OpenAPI docs
- **NiceGUI**: Python-based reactive UI framework  
  - Docs: https://nicegui.io/
  - Usage: Auto-generated reactive web interface, component override system
- **Typer**: CLI framework
  - Docs: https://typer.tiangolo.com/
  - Usage: Command-line interface with subcommands (meta, data, httpx)
- **SQLGlot**: SQL query building and parsing
  - Docs: https://sqlglot.com/
  - Usage: Safe SQL generation, RQL to SQL conversion, prevents injection
  - **Important**: Use `exp.Insert()`, `exp.Update()`, `exp.Delete()` from expressions module
  - **Note**: UPDATE SET clauses use `exp.EQ()` expressions, not SetExpression
- **PyRQL**: RQL (Resource Query Language) parser
  - GitHub: https://github.com/pjwerneck/pyrql
  - Usage: Parse RQL queries for REST API filtering
  - **Note**: Returns parsed AST, parameter binding handled separately  
- **DuckDB**: Database backend
  - Docs: https://duckdb.org/
  - Usage: High-performance analytics database with file-based storage
- **pydantic-settings**: Configuration management with full-depth env vars
  - Docs: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
  - Usage: Environment variable configuration with TOML file support
- **Uvicorn**: ASGI server
  - Docs: https://www.uvicorn.org/
  - Usage: Development server for FastAPI application

## Architecture Notes

**Implementation details specific to FastVimes:**

- **URL patterns**: Clear separation of API and UI endpoints
  - `/api/{table}` - JSON API endpoints for table data
- **NiceGUI interface**: Auto-generated reactive components from DuckLake schema
- **DuckLake backend**: Enables concurrent multi-user access with ACID guarantees via PostgreSQL/MySQL catalogs

## Project Structure

```
fastvimes/
├── __init__.py          # Main FastVimes class export
├── app.py               # FastVimes class implementation
├── cli.py               # Typer CLI commands
├── config.py            # pydantic-settings configuration schema
├── database_service.py  # DatabaseService public API (single source of truth)
├── rql_to_sql.py        # RQL to SQL conversion using pyrql + SQLGlot
├── api_client.py        # API client for NiceGUI components
└── components/          # Auto-generated NiceGUI components (overridable)
    ├── __init__.py
    ├── table_browser.py # Table/view listing component  
    ├── data_explorer.py # Data grid with filtering/sorting
    └── form_generator.py # CRUD forms from schema
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
# DatabaseService as single source of truth
app = FastVimes(db_path="data.db")
db_service = app.db_service

# FastAPI endpoints are light wrappers
@app.api.get("/users")
async def get_users(rql_query: str = None, limit: int = 100, offset: int = 0):
    return db_service.get_table_data("users", rql_query, limit, offset)

# CLI commands are light wrappers  
@cli.command()
def tables():
    tables = db_service.list_tables()
    for table in tables:
        print(f"{table['name']} ({table['type']})")

# NiceGUI components use DatabaseService directly
# This validates the public API through shared implementation
data_explorer = DataExplorer(db_service, "users")

# RQL-style query examples:
# GET /users?eq(id,123)
# GET /users?id=eq=123
# GET /users?contains(name,alice)
# GET /users?eq(active,true)
# GET /users?in(id,(1,2,3))
```

**NiceGUI Implementation:**
```python
# NiceGUI components use the same services as public API
# Components use DatabaseService directly, not HTTP requests

# Example: Auto-generated table browser
@ui.page('/tables')
def tables_page():
    # Auto-generated table listing from schema
    tables = db_service.list_tables()
    for table in tables:
        ui.button(table.name, on_click=lambda t=table: navigate_to_table(t.name))

# Example: Auto-generated data explorer
@ui.page('/table/{table_name}')
def table_page(table_name: str):
    # Auto-generated reactive data grid
    columns = db_service.get_table_schema(table_name)
    data_grid = ui.table(columns=columns, rows=[])
    data_grid.bind_value_from(lambda: db_service.get_table_data(table_name))

# Data flow:
# NiceGUI components → DatabaseService → RQL Parser → SQLGlot → DuckLake
# Same service used by /api/{table} endpoints
```

## Code Style

- Use **ruff** for formatting and linting
- Type hints on public functions
- Keep functions small and focused
- Prefer composition over inheritance
