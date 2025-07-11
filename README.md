# FastVimes

FastAPI-inspired library for building data tools with automatic CLI, web API, and HTML interfaces.

## Features

- **Auto-generated APIs** from DuckDB schemas (PostgREST style)
- **Admin interface** for Django-style table management
- **Multiple interfaces**: CLI, OpenAPI/Swagger, HTML forms
- **Instant setup**: Point at database + HTML folder and run

## Quick Start

```python
from fastvimes import FastVimes, FastVimesSettings

# Custom endpoints
app = FastVimes()

@app.get("/users")
def get_users():
    return app.db.table("users").to_pandas()

# Or instant app from existing database
app = FastVimes(config=FastVimesSettings(
    db_path="data.db", 
    html_path="./static/"
))
app.run()
```

## Installation

```bash
uv add fastvimes
```

## Three Ways to Use

### 1. Instant App
```bash
uv run fastvimes serve --db data.db --html ./static/
```

### 2. Custom App
```python
from fastvimes import FastVimes, FastVimesSettings, TableConfig

app = FastVimes(config=FastVimesSettings(
    db_path="data.db",
    extensions=["spatial", "httpfs"],
    read_only=False,
    default=TableConfig(mode="readwrite")
))
# Admin interface enabled by default
app.run()
```

### 3. FastAPI-style
```python
@app.get("/dashboard")
def dashboard():
    return app.db.table("sales").aggregate(...)

if __name__ == "__main__":
    app.run()  # Use: uv run myapp.py serve
```

## Documentation

- [Simple Tutorial](docs/simple.md) - Get started in 5 minutes
- [Customization Guide](docs/customization.md) - Styling and interface customization
- [Advanced Usage](docs/advanced.md) - API extensions and complex configurations

## Development

See [AGENT.md](AGENT.md) for development commands.
