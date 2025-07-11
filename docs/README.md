# FastVimes Documentation

This directory contains comprehensive documentation for FastVimes, a lightweight FastAPI + Ibis framework for building data tools.

## Quick Start

1. **[Simple Tutorial](simple.md)** - Get started in 5 minutes
2. **[Advanced Usage](advanced.md)** - Custom endpoints and complex configurations
3. **[Customization Guide](customization.md)** - HTMX fragments, styling, and UI customization
4. **[Manual Testing Guide](manual-testing.md)** - Step-by-step testing procedures

## Design Philosophy

FastVimes follows the principle of **lightweight composition over custom abstraction**:

- **FastAPI inheritance** - Full access to FastAPI features
- **Ibis integration** - Safe SQL operations and database portability
- **Zero-config startup** - Auto-generate everything from database schema
- **RQL query language** - Powerful query capabilities with `?eq(field,value)` syntax
- **HTMX fragments** - Modern web UX without heavy JavaScript frameworks

## Key Features

### 🚀 **Instant API Generation**
```bash
uv run fastvimes serve --db my_data.db
# Gets you REST API, admin interface, and HTML views instantly
```

### 🔍 **RQL Queries**
```bash
# Filter users by role
curl "http://localhost:8000/users?eq(role,admin)"

# Complex filters
curl "http://localhost:8000/users?and(gt(age,25),ne(role,guest))"
```

### 🎨 **HTMX Fragment Architecture**
- Full pages: `/admin`, `/dashboard`
- Fragments: `/users/html`, `/products/html`
- Built-in Bulma CSS + Font Awesome

### 🛠️ **Comprehensive CLI**
```bash
uv run fastvimes serve --db data.db
uv run fastvimes query "SELECT * FROM users" --format json
uv run fastvimes create users --data '{"name": "John", "email": "john@example.com"}'
```

## Architecture

```
FastVimes App
├── FastAPI (HTTP layer)
├── Ibis (Data layer)
├── Pydantic (Validation)
├── Auto-generated endpoints
├── HTML forms with FastHTML
├── Admin interface
└── CLI with Typer
```

## Getting Help

- **Issues**: Report bugs and request features on GitHub
- **Examples**: Check the `examples/` directory
- **Tests**: Run `uv run pytest` to verify functionality

## Contributing

1. Read the [AGENT.md](../AGENT.md) file for development guidelines
2. Run the manual tests: `docs/manual-testing.md`
3. Ensure all tests pass: `uv run pytest`
4. Follow the design patterns documented here
