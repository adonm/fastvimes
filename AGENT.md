# Agent Guide for FastVimes

Development commands and project info for AI assistants.

## Project Vision

**FastVimes: Auto-Generated pgweb-Style Apps with NiceGUI + DuckDB**

Generate pgweb-like exploratory interfaces automatically from DuckDB schemas using NiceGUI's reactive components, with incremental override capabilities for custom form/database applications.

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

**SUPPORTED INPUT FORMATS** (bulk operations):
- **JSON** (single records and arrays)
- **Parquet files** (DuckDB native: `INSERT INTO table SELECT * FROM 'file.parquet'`)
- **CSV files** (DuckDB native: `INSERT INTO table SELECT * FROM 'file.csv'`)
- **Bulk operations**: insert, upsert, delete with file upload support

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
fastvimes data bulk-insert {table} --file data.parquet  # Bulk insert
fastvimes data bulk-upsert {table} --file data.csv      # Bulk upsert  
fastvimes data bulk-delete {table} --file data.json     # Bulk delete
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
- **Exploratory UI**: Auto-generated pgweb-style interface with incremental customization
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

**Auto-generated pgweb style interface with incremental override capabilities:**

### **Core Principle: Schema-Driven UI Generation**
- **Auto-generation**: NiceGUI components generated automatically from schema
- **Incremental Override**: Start with generated interface, selectively replace components for custom functionality
- **Reactive State Management**: Use NiceGUI's `ui.state()` for automatic data binding and updates
- **API Integration**: All UI components consume the same RQL-based FastAPI endpoints
- **Advanced SQL Features**: Delegate complex queries to embedded DuckDB UI extension (iframe integration)

### **Role Separation: FastVimes vs DuckDB UI**
- **FastVimes Focus**: Auto-generated exploratory UI (tables, forms, charts) with CRUD operations
- **DuckDB UI Extension**: Advanced SQL editor, query analysis, performance tuning, complex joins
- **Integration**: DuckDB UI embedded as iframe tab within FastVimes interface
- **Handoff**: One-click transition from FastVimes table view to DuckDB UI query editor

### **Auto-Generated Components (pgweb-inspired)**
1. **Table Browser**: Interactive table/view listing with search and filtering
2. **Data Explorer**: Sortable, filterable data grids with inline editing capabilities
3. **Form Generator**: CRUD forms automatically created from table schemas
4. **DuckDB UI Tab**: Embedded iframe for advanced SQL features

### **Planned Components**
5. **Query Builder**: Visual RQL query construction interface (Phase 3)
6. **Chart Generator**: Auto-generated plots based on column types and data patterns (Phase 3)
7. **Relationship Navigator**: Follow foreign keys between related tables (Phase 5)

### **Schema Generation Scope (MVP)**
- **Basic tables**: Simple column types (text, number, date, boolean)
- **No joins/relations**: Ignore foreign keys and complex relationships initially
- **Views as enhancement**: Use database views to handle complex queries and relationships
- **Progressive enhancement**: Add relationship support after core functionality is solid

### **Override Strategy**
```python
# Auto-generated base interface
app = FastVimes(db_path="data.db")
app.serve()  # Gets full pgweb-style interface

# Incremental customization
class MyApp(FastVimes):
    def override_table_page(self, table_name: str):
        if table_name == "users":
            return custom_user_table()  # Custom page
        return None  # Use default for others
        
    def override_form_page(self, table_name: str):
        if table_name == "orders":
            return custom_order_form()  # Custom form page
        return None  # Use auto-generated forms
```

### **NiceGUI Built-in Usage Patterns**
```python
# CORRECT: Use NiceGUI built-ins directly in ui_pages.py
@ui.page("/table/{table_name}")
def table_page(table_name: str):
    with ui.column().classes("w-full h-full"):
        # Get data from database service
        data = app.db_service.get_table_data(table_name, limit=1000)
        schema = app.db_service.get_table_schema(table_name)
        
        # Use NiceGUI's built-in AGGrid with full feature set
        grid = ui.aggrid({
            "columnDefs": [{"field": col["name"], "sortable": True, "filter": True} for col in schema],
            "rowData": data["records"] if isinstance(data, dict) else data,
            "pagination": True,
            "paginationPageSize": 50,
        }).classes("w-full h-96")

# AVOID: Custom component wrappers
class CustomDataExplorer:  # Don't do this anymore
    def __init__(self, db_service, table_name):
        # This adds unnecessary complexity over ui.aggrid
```

### **Component Composition Patterns**
```python
# CORRECT: Small, focused functions in ui_pages.py
def filter_panel(db_service, table_name):
    """Filter controls using NiceGUI built-ins."""
    with ui.row():
        ui.input("Search", on_change=lambda e: apply_filter(e.value))
        ui.select(["active", "inactive"], label="Status")
        
def data_table(db_service, table_name):
    """Data grid using ui.aggrid built-in."""
    data = db_service.get_table_data(table_name)
    schema = db_service.get_table_schema(table_name)
    return ui.aggrid({
        "columnDefs": [{"field": col["name"]} for col in schema],
        "rowData": data
    })

# Compose pages from functions
@ui.page("/table/{table_name}")
def table_page(table_name: str):
    with ui.column():
        filter_panel(app.db_service, table_name)
        data_table(app.db_service, table_name)
```

### **DuckDB UI Integration Pattern**
```python
# Embedded DuckDB UI for advanced features
@ui.page('/duckdb-ui')
def duckdb_ui_page():
    """Embedded DuckDB UI for advanced SQL features."""
    if app.settings.duckdb_ui_enabled:
        ui.html(f'''
            <iframe 
                src="http://localhost:{app.settings.duckdb_ui_port}" 
                width="100%" 
                height="800px"
                style="border: none;">
            </iframe>
        ''').classes("w-full h-full")
    else:
        ui.label("DuckDB UI is not enabled").classes("text-gray-500")
```

## Design Principles

**Core Philosophy: Auto-generated reactive interfaces with incremental customization**

### 1. Schema-Driven Auto-Generation
- **Auto-generate everything**: NiceGUI components, FastAPI endpoints, CLI commands from DuckLake schemas
- **Zero-config startup**: Point at DuckLake, get instant pgweb-style reactive interface
- **Override methods**: Start with full interface, selectively replace components as needed
- **Minimal code required**: Single method override should handle most customizations

### 2. Security and Safety First
- **SQLGlot for SQL safety**: Prevents SQL injection through safe query building and parameterization
- **Authlib for authentication**: OAuth/OpenID Connect integration using Authlib for FastAPI
- **FastAPI for HTTP security**: Built-in validation, dependency injection, automatic docs
- **Pydantic for data validation**: Type safety and automatic validation at runtime
- **Secure defaults**: Read-only by default, explicit opt-in for write operations

### 3. Composition Over Custom Code
- **Use library built-ins**: NiceGUI's reactive components, FastAPI's dependency injection
- **Combine stable tools**: NiceGUI + FastAPI + SQLGlot + DuckLake + Pydantic
- **Extend through services**: Add functionality via dependency injection, not inheritance
- **Simple deployment**: Single Python file should be sufficient for basic apps

### 4. Modern Developer Experience
- **pgweb style with incremental customisation**: Reactive components, incremental customisation, auto-generated forms
- **Sensible defaults**: Reactive UI by default, automatic schema introspection
- **Progressive enhancement**: Start with auto-generated interface, incrementally override for custom needs
- **Clear boundaries**: Database operations in services, HTTP logic in endpoints, UI in NiceGUI components
- **API Integration**: NiceGUI interface validates the public API by consuming it directly

### 5. NiceGUI Reactive Architecture
- **Use `ui.state()` for reactive data**: Automatic UI updates when state changes
- **Component composition**: Small, focused components that compose into larger interfaces
- **Avoid manual DOM manipulation**: Use data binding instead of `.props()` and `.refresh()`
- **Event-driven architecture**: State changes trigger UI updates automatically
- **Performance optimization**: Use targeted updates instead of full component rebuilds

### 6. Testing and Development Workflow
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

**CRITICAL**: Always follow this exact order based on spec-driven development principles:

1. **Update Design Spec** - Modify AGENT.md with new architecture/features/fixes (acts as our spec)
2. **Define Test Requirements** - Write/modify tests to match the new design spec before implementation
3. **Implement Code** - Make the actual code changes to pass the tests
4. **Update Documentation** - Update user-facing docs and examples

**Architecture Compliance**: All new features must follow the single source of truth pattern:
- Business logic goes in DatabaseService public methods
- FastAPI endpoints are light wrappers over DatabaseService methods
- CLI commands are light wrappers over DatabaseService methods  
- NiceGUI calls DatabaseService methods directly
- All validation happens once in DatabaseService methods

## Spec-Driven Development Process

**Inspired by Kiro.dev's approach to mature agent contributions:**

### 1. Spec as Source of Truth
- **AGENT.md serves as our living spec** - Contains architecture, patterns, and requirements
- **Explicit requirements** - Every feature must have clear, testable requirements
- **System design documentation** - Architecture diagrams and component relationships
- **Discrete tasks** - Break down complex features into manageable implementation tasks

### 2. Agent Contribution Guidelines
- **Follow the spec strictly** - All code changes must align with AGENT.md architecture
- **Test-first approach** - Write tests before implementing features
- **Multi-schema validation** - Ensure autogeneration works with any schema structure
- **Consistent patterns** - Use established patterns to minimize custom code

### 3. Steering Files for AI Agents
- **AGENT.md** - Primary steering document with architecture and patterns
- **Test requirements** - Multi-schema testing patterns and validation rules
- **Code style** - Ruff formatting, type hints, composition over inheritance
- **Security practices** - Never expose secrets, use SQLGlot for safety

## Testing Strategy

### NiceGUI Testing Patterns

**Four-Layer Testing Approach:**
1. **DatabaseService Unit Tests**: Direct method testing with multiple schemas
2. **API Integration Tests**: HTTP API via `httpx` command with server lifecycle management
3. **NiceGUI UI Tests**: Using `from nicegui.testing import User` fixture  
4. **Playwright MCP UI Tests**: Full browser testing with real user interactions

#### **Native NiceGUI Testing (Lightweight)**
```python
from nicegui.testing import User

async def test_basic_functionality(user: User) -> None:
    await user.open("/")
    # Test UI interactions: user.click(), user.type(), user.select()
    # Assert UI state: await user.wait_for_element()
```

#### **Playwright MCP Testing (Comprehensive)**

**When to use Playwright MCP:**
- **Complete UI workflows**: Multi-step user journeys (navigation → table → form → charts)
- **Cross-browser testing**: Ensure compatibility across different browsers
- **Real interaction testing**: Mouse movements, drag-drop, complex gestures
- **Visual regression testing**: Screenshot comparisons, layout validation
- **Performance testing**: Page load times, chart rendering performance
- **Integration testing**: Full stack testing including DuckDB backend

**Playwright MCP Testing Patterns:**
```python
# Start server in background for testing
def setup_test_server():
    """Start FastVimes server for Playwright testing."""
    # Use mcp__playwright__browser_navigate to http://localhost:8000
    # Server automatically started with show=False
    
# Test navigation sidebar
async def test_navigation_sidebar():
    await mcp__playwright__browser_navigate("http://localhost:8000")
    await mcp__playwright__browser_snapshot()  # Get page structure
    await mcp__playwright__browser_click("Table search input", "input[placeholder='Search tables...']")
    await mcp__playwright__browser_type("Search tables", "input[placeholder='Search tables...']", "users")
    await mcp__playwright__browser_click("Users table", "row containing 'users'")
    
# Test AGGrid functionality
async def test_data_grid_interaction():
    await mcp__playwright__browser_navigate("http://localhost:8000/table/users")
    await mcp__playwright__browser_wait_for(text="Table: users")
    await mcp__playwright__browser_snapshot()  # Verify grid loaded
    await mcp__playwright__browser_click("Column filter", "[col-id='name'] .ag-header-icon")
    await mcp__playwright__browser_type("Filter input", ".ag-filter-text-input", "Alice")
    
# Test charts rendering
async def test_charts_display():
    await mcp__playwright__browser_navigate("http://localhost:8000/table/users")
    await mcp__playwright__browser_click("Charts tab", "div[role='tab']:contains('Charts')")
    await mcp__playwright__browser_wait_for(text="Auto-generated Charts")
    await mcp__playwright__browser_snapshot()  # Verify charts rendered
    
# Test form submission
async def test_form_workflow():
    await mcp__playwright__browser_navigate("http://localhost:8000/table/users")
    await mcp__playwright__browser_click("Add Record", "button:contains('Add Record')")
    await mcp__playwright__browser_wait_for(text="Add Record to users")
    await mcp__playwright__browser_type("Name field", "input[label='name']", "Test User")
    await mcp__playwright__browser_type("Email field", "input[label='email']", "test@example.com")
    await mcp__playwright__browser_click("Submit", "button:contains('Create Record')")
    await mcp__playwright__browser_wait_for(text="Record created successfully")
```

**Playwright MCP Best Practices:**
- **Use descriptive element names**: "Search input" not just "input"
- **Wait for content**: Use `browser_wait_for` for dynamic content loading
- **Take snapshots**: Use `browser_snapshot` for debugging and verification
- **Test error scenarios**: Invalid inputs, network failures, empty states
- **Verify API integration**: Check that UI changes persist in database

**UI Component Testing Requirements:**
- **Navigation Sidebar**: Test search functionality, table selection, responsive behavior
- **Data Tables (AGGrid)**: Test sorting, filtering, pagination, row selection, export
- **Charts (ECharts)**: Test chart rendering, data updates, interaction, tooltips
- **Forms**: Test field validation, submission, error handling, success feedback
- **Error Boundaries**: Test graceful error handling and user feedback

**Component Testing Standards:**
- **Method Coverage**: Test all public methods and user interaction flows
- **State Management**: Test component state changes and UI updates
- **Error Handling**: Test error scenarios and user feedback
- **API Integration**: Test component-to-API communication patterns
- **Multi-Schema Support**: Test with different table structures and column types
- **Cross-Browser Support**: Test core functionality in Chrome, Firefox, Safari
- **Mobile Responsiveness**: Test navigation drawer and components on mobile viewports

**Key Testing Principles:**
- **Multi-Schema Testing**: Test with different table names, column types, and structures
- **Avoid Hardcoding**: Use schema introspection to generate tests dynamically
- **API Consistency**: Same endpoints accessible via CLI/FastAPI/NiceGUI
- **Autogeneration Validation**: Ensure endpoints/UI components work with any schema

### Multi-Schema Testing Requirements

**CRITICAL**: Tests must verify autogeneration works with any schema structure:

```python
# Test with multiple different schemas
@pytest.fixture(params=[
    'ecommerce_schema',    # users, products, orders
    'blog_schema',         # posts, comments, authors  
    'inventory_schema',    # items, warehouses, suppliers
    'custom_schema'        # arbitrary table/column names
])
def multi_schema_db(request):
    """Test with multiple schema patterns to avoid hardcoded assumptions."""
    schema_name = request.param
    return create_test_db_with_schema(schema_name)
```

**Schema Diversity Requirements:**
- Different table names (not just users/products/orders)
- Different column names and types
- Different foreign key relationships
- Edge cases: reserved words, special characters, long names

## Contributor Guidelines for AI Agents

**Based on Kiro.dev's approach to mature agent contributions:**

### Pre-Implementation Checklist
1. **Spec Review** - Read AGENT.md thoroughly, understand architecture patterns
2. **Test Requirements** - Identify what tests need to be written/modified
3. **Multi-Schema Validation** - Ensure changes work with any schema structure
4. **Architecture Compliance** - Follow single source of truth pattern

### Implementation Process
1. **Update AGENT.md** - Add/modify spec for new features
2. **Write Tests First** - Create tests that validate the spec requirements
3. **Implement Code** - Make minimal changes to pass tests
4. **Run Full Test Suite** - Ensure no regressions across all schemas
5. **Update Documentation** - Add user-facing docs and examples

### Code Quality Standards
- **Follow established patterns** - Use existing DatabaseService patterns
- **Minimize custom code** - Prefer composition over inheritance
- **Security first** - Never expose secrets, use SQLGlot for safety
- **Type safety** - Use type hints on all public functions
- **Ruff compliance** - Format with ruff, fix all linting issues

### Testing Requirements
- **Multi-schema tests** - Every feature must work with different schemas
- **API consistency** - Same endpoints via CLI/FastAPI/NiceGUI
- **Performance validation** - Ensure changes don't degrade performance
- **Edge case handling** - Test with reserved words, special characters

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
# Note: Browser won't auto-launch, manually visit http://localhost:8000

# Or specify custom data  
uv run fastvimes serve demo.db          # Point to existing DuckDB file
```

### Core Development Workflow

**Git Workflow (CRITICAL):**
```bash
# Commit frequently - every few hours of meaningful work
git add -A && git commit -m "feat: implement user table filtering"

# Remove old code instead of commenting out (git history preserves it)
rm old_components.py  # Don't comment out, just delete
git add -A && git commit -m "refactor: remove legacy component system"

# Clean up as you go - don't accumulate dead code
git clean -fd  # Remove untracked files
```

**Development Principles:**
- **Commit every 2-3 hours** of focused work, even if incomplete
- **Delete old code immediately** - git history preserves everything
- **No commented-out code** - if you need it later, check git history
- **Clean working directory** - no old backup files or unused modules
- **Descriptive commit messages** - explain what and why, not how
- **Use mature tools** - DuckDB CLI instead of custom shells, NiceGUI built-ins instead of custom components

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

# Interactive SQL shell (uses mature DuckDB CLI)
# Note: Only works with file databases, not in-memory
uv run fastvimes duckdb --db demo.db       # Connect to SAME database as FastVimes app
```

**Local Development Server:**
```bash
# Start development server (browser won't auto-launch)
uv run fastvimes serve

# Initialize demo data for testing
uv run fastvimes init demo.db --force

# Check database schema during development
uv run fastvimes meta tables
uv run fastvimes meta schema users

# Show configuration
uv run fastvimes config

# Access server manually at: http://localhost:8000
# API docs available at: http://localhost:8000/api/docs
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
- **Authlib**: OAuth and OpenID Connect library
  - Docs: https://docs.authlib.org/en/stable/client/fastapi.html
  - Usage: OAuth/OpenID Connect authentication integration with FastAPI
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

**Lean Structure: 7 Core Files + Optional Overrides**

```
fastvimes/
├── __init__.py          # Export FastVimes class
├── app.py               # FastVimes class (~150 lines: DB + API + UI setup)
├── db_service.py        # DatabaseService public API (single source of truth)
├── api.py               # build_api(db_service) - thin FastAPI wrapper with DI
├── ui_pages.py          # @ui.page functions using NiceGUI built-ins
├── cli.py               # Typer commands calling db_service directly
├── config.py            # pydantic-settings configuration
└── overrides/           # Optional: drop-in files to override default pages
    ├── custom_table.py
    └── custom_form.py
```

**Mature Dependencies Handle Everything Else:**
- **NiceGUI**: `ui.aggrid`, `ui.tree`, `ui.dark_mode`, Quasar layout/theming
- **FastAPI**: Dependency injection, routing, security scopes  
- **Authlib**: OAuth/OIDC integration (only if auth enabled)
- **DuckDB UI**: Advanced SQL IDE via iframe embedding
- **Python stdlib**: `logging.basicConfig()` for logging

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

## What's Next

**FastVimes lean architecture is complete!** 🎉 See [ROADMAP.md](ROADMAP.md) for detailed next steps.

**Phase 3 Complete: Developer Experience**
1. **Native DuckDB CLI integration** - `fastvimes duckdb` connects to same database as app (file databases only)
2. **Health endpoint** - `/api/health` for production monitoring  
3. **Enhanced OpenAPI docs** - Rich documentation with RQL examples and proper tagging
4. **Mature dependency usage** - Leverage existing tools instead of custom implementations

**Key Design Decision:** DuckDB CLI connects to the exact same database file that FastVimes uses, ensuring data consistency. In-memory databases cannot be shared between processes, so CLI is only available for file-based databases.

**Implementation approach:**
- **Use NiceGUI built-ins** - `ui.chart`, `ui.tree`, `ui.upload`
- **Extend DatabaseService** - Add methods for chart data, validation
- **Test-first development** - Define behavior before implementation
- **Commit frequently** - Every 2-3 hours, delete old code immediately

## Code Style

- Use **ruff** for formatting and linting
- Type hints on public functions  
- Keep functions small and focused
- Prefer composition over inheritance
- **Delete old code** - don't comment out (git history preserves it)
