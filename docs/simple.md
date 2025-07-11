# Simple Tutorial - Get Started in 5 Minutes

## 1. Instant App from Database

```bash
# Install FastVimes
uv add fastvimes

# Point at any DuckDB database (use uv run for all commands)
uv run fastvimes serve --db my_data.db

# Visit http://localhost:8000/admin for table management
```

You now have:
- REST API at `/{table}` endpoints (use `/{schema.table}` for schemas)
- HTML forms at `/{table}/html`
- Admin interface at `/admin` (table management)
- OpenAPI docs at `/docs`

### CLI Commands
```bash
# Main actions (use uv run for all commands)
uv run fastvimes serve --db data.db
uv run fastvimes init --db data.db --force                 # Initialize database
uv run fastvimes schema --db data.db                       # Show all tables
uv run fastvimes tables --db data.db                       # List table configs
uv run fastvimes query "SELECT * FROM users LIMIT 10" --db data.db

# Different output formats
uv run fastvimes query "SELECT COUNT(*) FROM users" --format json --db data.db
uv run fastvimes query "SELECT * FROM users" --format csv --db data.db

# Custom app file
uv run python myapp.py serve
uv run python myapp.py init-db --force
```

## 2. Add Custom Styles

Create `static/header_include.html`:
```html
<style>
.my-table { background: #f5f5f5; }
</style>
```

Run with static files:
```bash
uv run fastvimes serve --db my_data.db --html static/
```

## 3. Configure Tables

Create `fastvimes.toml`:
```toml
# Database settings
db_path = "my_data.db"
read_only = false

# Default settings for all tables
default_mode = "readonly"
default_html = true

# Per-table overrides
[tables.users]
mode = "readwrite"
primary_key = "email"

[tables.orders]
mode = "readwrite"
html = false
```

Run with config:
```bash
uv run fastvimes serve --config fastvimes.toml
```

## 4. Configuration Management

Use TOML, env vars, or Python config (see AGENT.md for complete schema):

```bash
# Environment variables (pydantic-settings format)
export FASTVIMES_DB_PATH=my_data.db
export FASTVIMES_DEFAULT_MODE=readwrite
export FASTVIMES_TABLES_USERS_PRIMARY_KEY=email
export FASTVIMES_ADMIN_ENABLED=true

# CLI with config file
uv run fastvimes serve --config fastvimes.toml
```

## 5. Export Configuration from Admin

Visit `/admin` to manage configuration:

```toml
# Generated fastvimes.toml (click "Export Config" in admin)
db_path = "my_data.db"
admin_enabled = true
default_mode = "readwrite"
default_html = true

[tables.users]
mode = "readonly"
primary_key = "email"

[tables.orders]
mode = "readwrite"
html = false
```

## 6. Create a Python App

Create `app.py`:
```python
from fastvimes import FastVimes

app = FastVimes(
    db_path="my_data.db",
    html_path="static/"
)

if __name__ == "__main__":
    app.run()
```

Run: `uv run python app.py`

## Next Steps

- [Customization Guide](customization.md) - Style your interface
- [Advanced Usage](advanced.md) - Add custom endpoints
