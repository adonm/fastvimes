# Agent Guide for FastVimes

Development commands and project info for AI assistants.

## Development Commands

### Setup
```bash
# Install with uv
uv sync

# Install for development
uv sync --dev
```

### Testing
```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=fastvimes
```

### Linting and Formatting
```bash
# Format and lint with ruff
uv run ruff format
uv run ruff check --fix

# Type checking
uv run mypy fastvimes/
```

### Running Examples
```bash
# Run basic example
uv run python examples/basic_app.py

# As CLI
uv run python examples/basic_app.py --help

# As server
uv run python examples/basic_app.py serve
```

## Key Dependencies

- **FastAPI**: HTTP framework and dependency injection
- **FastHTML**: HTML generation and form system
- **Typer**: CLI framework
- **Ibis**: Data abstraction layer
- **DuckDB**: Database backend
- **pydantic-settings**: Configuration management with full-depth env vars
- **Uvicorn**: ASGI server

## Architecture Notes

- Keep it simple and flexible
- Auto-generate APIs from database schemas (PostgREST style)
- Use Ibis for data operations, dynamic validation at runtime
- FastAPI for HTTP, FastHTML for HTML generation
- Typer CLI introspects same Ibis models as FastAPI endpoints
- Clean URLs: `/{table}` for JSON, `/{table}/html` for forms
- Admin interface with table management (enabled by default, configurable)
- Support POST upserts, PUT/PATCH updates, DELETE with query filters
- Auto-detect primary keys, fallback to rowid (configurable)
- Simple query syntax: `?id=123` vs `?id=eq.123`
- All mutations return the affected record
- pydantic-settings for full-depth env vars (`FASTVIMES_TABLES_USERS_MODE=readwrite`)
- HTML introspection for instant app setup from database + HTML folder
- Views for complex queries instead of complex API parameters
- HTMX-first architecture: all HTML as composable fragments
- Built-in static file serving (Bulma + HTMX from unpkg by default)
- DuckDB-only backend with extension support for other databases
- FastAPI dependency injection for auth (external auth stack + trusted headers)
- HTML errors embedded in same response with Bulma styling
- Minimal custom HTML files for admin interface (HTML-dev friendly)

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
│   ├── html             # Main admin dashboard
│   ├── tables.html      # Table browser
│   ├── nav.html         # Navigation component
│   ├── schema.html      # Schema editor
│   └── config.html      # Configuration management
└── static/              # Default static files
    └── header_include.html  # Default empty header include
```

## Configuration Schema

```python
# fastvimes/config.py
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, Optional

class TableConfig(BaseModel):
    mode: str = "readonly"  # readonly, readwrite
    html: bool = True
    primary_key: Optional[str] = None
    use_rowid: bool = True

class AdminConfig(BaseModel):
    enabled: bool = True

class FastVimesSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='FASTVIMES_',
        env_nested_delimiter='_'
    )
    
    # Database connection
    db_path: str = "data.db"
    extensions: list[str] = []
    read_only: bool = False
    
    # HTML static files
    html_path: Optional[str] = None
    
    # Defaults for all tables
    default: TableConfig = TableConfig()
    
    # Per-table overrides
    tables: Dict[str, TableConfig] = {}
    
    # Admin interface
    admin: AdminConfig = AdminConfig()
    
    def model_post_init(self, __context):
        """Validate configuration consistency"""
        if self.read_only:
            # If database is read-only, all tables must be readonly
            if self.default.mode == "readwrite":
                raise ValueError("Cannot use readwrite mode when database is read_only=True")
            for table_name, config in self.tables.items():
                if config.mode == "readwrite":
                    raise ValueError(f"Table '{table_name}' cannot use readwrite mode when database is read_only=True")

# Environment variables:
# FASTVIMES_DB_PATH=data.db
# FASTVIMES_EXTENSIONS=spatial,httpfs
# FASTVIMES_READ_ONLY=false
# FASTVIMES_HTML_PATH=./static
# FASTVIMES_DEFAULT_MODE=readonly
# FASTVIMES_TABLES_USERS_MODE=readwrite
# FASTVIMES_TABLES_USERS_PRIMARY_KEY=email
# FASTVIMES_ADMIN_ENABLED=false
```

## Data Flow & Implementation Details

```python
# Database connection with Ibis (uses FastVimesSettings)
app = FastVimes()  # Uses default config from pydantic-settings
# Or with explicit config:
app = FastVimes(config=FastVimesSettings(
    db_path="data.db",
    extensions=["spatial", "httpfs"], 
    read_only=False,
    default=TableConfig(mode="readwrite")
))
# Internally: config loaded via pydantic-settings from env vars/files

# Schema introspection: Runtime dynamic dataclass generation
@app.get("/users/new")
def new_user_form():
    User = app.get_table_dataclass("users")  # Dynamic from Ibis schema
    form = app.generate_form(User, action="/users")
    return form

# Standard FastAPI middleware for identity/auth
@app.middleware("http")
async def identity_middleware(request: Request, call_next):
    user_id = request.headers.get("X-User-ID")
    role = request.headers.get("X-User-Role")
    # Apply filtering logic
    response = await call_next(request)
    return response

# Admin interface: Static HTML files served from fastvimes/admin/
# /admin/html -> serves fastvimes/admin/html (overridable in static/admin/html)
# HTMX endpoints like /admin/nav load fastvimes/admin/nav.html
```

## Code Style

- Use **ruff** for formatting and linting
- Type hints on public functions
- Keep functions small and focused
- Prefer composition over inheritance
