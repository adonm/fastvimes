# Simple Tutorial - Get Started in 5 Minutes

## 1. Instant App from Database

```bash
# Install FastVimes
uv add fastvimes

# Point at any DuckDB database
uv run fastvimes serve --db my_data.db

# Visit http://localhost:8000/admin/html
```

You now have:
- REST API at `/{table}` endpoints (use `/{schema.table}` for schemas)
- HTML forms at `/{table}/html`
- Admin interface at `/admin/html` (table management)
- OpenAPI docs at `/docs`

### CLI Commands
```bash
# Main actions (match API endpoints)
uv run fastvimes serve --db data.db
uv run fastvimes query users --limit 10                    # GET /users
uv run fastvimes create users --name "John" --email "john@example.com"  # POST /users
uv run fastvimes update users --id 1 --name "Jane"         # PUT /users?id=1
uv run fastvimes delete users --id 1                       # DELETE /users?id=1

# Schema support
uv run fastvimes query schema.users --select name,email

# Custom app file
uv run myapp.py serve
uv run myapp.py query users --limit 10
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

Create `config.toml`:
```toml
[default]
mode = "readonly"
html = true

[tables.users]
mode = "readwrite"
primary_key = "email"

[tables.orders]
mode = "readwrite"
```

Run with config:
```bash
uv run fastvimes serve --db my_data.db --config config.toml
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
uv run fastvimes serve --config config.toml
```

## 5. Export Configuration from Admin

Visit `/admin/html` to manage configuration:

```toml
# Generated config.toml (click "Export Config" in admin)
[default]
mode = "readwrite"
html = true

[tables.users]
mode = "readonly"
primary_key = "email"

[tables.orders]
mode = "readwrite"
```

## 6. Create a Python App

Create `app.py`:
```python
from fastvimes import FastVimes, FastVimesSettings

app = FastVimes(config=FastVimesSettings(
    db_path="my_data.db",
    html_path="static/"
))

if __name__ == "__main__":
    app.run()
```

Run: `uv run python app.py serve`

## Next Steps

- [Customization Guide](customization.md) - Style your interface
- [Advanced Usage](advanced.md) - Add custom endpoints
