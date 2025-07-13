# FastVimes

**Auto-Generated Datasette-Style Apps with NiceGUI + DuckDB**

Zero-config reactive web apps from any database. Point at DuckDB → get instant Datasette-style interface with tables, forms, charts, and API → incrementally override components for custom functionality.

## ✨ Quick Start

```bash
# Instant demo with sample data (no setup required!)
uv run fastvimes serve

# Or point at your own DuckDB
uv run fastvimes serve --db my_data.db
```

**That's it!** Opens reactive web interface at `http://localhost:8000` with:
- 📊 Interactive table browser and data explorer
- 📝 Auto-generated forms for CRUD operations  
- 🔍 Advanced filtering and search
- 🌐 REST API with RQL query language
- 📖 Embedded API documentation

## 🎯 Core Concept

**Default Setup**: Uses in-memory DuckDB with sample data for zero-config startup.  
**Production**: Point at persistent DuckDB files or DuckLake with PostgreSQL/MySQL catalog for multi-user access.

## 🚀 Installation

Requires [uv](https://github.com/astral-sh/uv) (which handles Python 3.13+ automatically):

```bash
git clone https://github.com/adonm/fastvimes
cd fastvimes
uv sync
```

## 🎨 Incremental Customization

Start with auto-generated interface, selectively override components:

```python
from fastvimes import FastVimes

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

MyApp().serve()
```

## 🔧 CLI Commands

```bash
# Zero-config startup
uv run fastvimes serve                    # Instant demo with sample data
uv run fastvimes serve --db prod.db       # Production database

# Database operations  
uv run fastvimes meta tables              # List all tables
uv run fastvimes meta schema users        # Show table schema
uv run fastvimes data get users           # Get table data with RQL filtering
uv run fastvimes init newdb.db            # Create database with sample data

# API testing (automatic server lifecycle)
uv run fastvimes httpx "GET /api/v1/meta/tables"
uv run fastvimes httpx "GET /api/v1/data/users?eq(id,1)"
uv run fastvimes httpx "POST /api/v1/data/users" --data '{"name": "Alice"}'
```

## 🔍 RQL Query Language

Consistent, simple REST API querying:

```bash
# Basic filtering
GET /api/users?eq(id,123)           # id equals 123
GET /api/users?lt(age,30)           # age less than 30
GET /api/users?contains(name,alice) # name contains "alice"

# FIQL syntax sugar (alternative)
GET /api/users?id=eq=123            # Same as eq(id,123)

# Logical operations
GET /api/users?and(eq(active,true),gt(age,18))  # active AND age > 18

# Set operations and sorting
GET /api/users?in(id,(1,2,3))                  # id in [1,2,3]
GET /api/users?sort(+name,-created_at)         # Sort by name ASC, created_at DESC
GET /api/users?limit(10,20)                    # Skip 20, take 10 (pagination)
```

## 🏗️ Architecture

**Auto-generated reactive interfaces with incremental customization:**

- **NiceGUI**: Reactive Vue.js-based components for real-time updates
- **DuckDB**: High-performance analytical database for development/single-user
- **DuckLake**: Production multi-user capabilities with ACID guarantees
- **FastAPI**: Auto-generated REST endpoints with OpenAPI docs
- **SQLGlot**: Type-safe query building (prevents SQL injection)

**Data Flow:**
```
NiceGUI components → DatabaseService → RQL Parser → SQLGlot → DuckDB/DuckLake
```

## 📊 Features

### MVP (Phase 1)
- ✅ **Zero-config startup**: Instant demo with sample data
- ✅ **Auto-generated interface**: Tables, forms, navigation from schema
- ✅ **Basic CRUD**: Create, read, update, delete operations
- ✅ **CLI tools**: Database management and API testing

### Enhanced Features (Phase 2-4)
- ✅ **RQL filtering**: Advanced query language in API (Phase 2 complete)
- 🔄 **RQL UI integration**: Query builder components (Phase 3 in progress)
- 🎨 **Chart generation**: Auto-generated plots from data types (Phase 3)
- 🌐 **Multi-user**: Concurrent access via DuckLake with PostgreSQL/MySQL catalogs (Phase 4)

## 📈 Development Status

**Current**: Phase 2 (RQL Integration) Complete, Phase 3 (Enhanced NiceGUI) In Progress - See [BACKLOG.md](BACKLOG.md) for detailed roadmap

**Phase 2 Achievements**:
- ✅ RQL query language with pyrql + SQLGlot integration
- ✅ Single source of truth architecture via DatabaseService
- ✅ Comprehensive test coverage for core functionality
- ✅ Multi-format export support (JSON, CSV, Parquet)

## 🎯 Use Cases

**Perfect for:**
- 📊 Data exploration and analytics dashboards
- 🛠️ Internal admin tools and CRUD applications
- 🚀 Rapid prototyping with database-driven apps
- 👥 Small team collaboration on shared datasets

**Not ideal for:**
- 🏢 High-frequency trading or real-time systems
- 📱 Consumer-facing mobile applications
- 🎮 Complex business logic with multi-step workflows
- 🗄️ Non-tabular data (document stores, graph databases)

## 📚 Documentation

- [AGENT.md](AGENT.md) - Development commands and architecture details
- [BACKLOG.md](BACKLOG.md) - Detailed development roadmap and phases

## 🤝 Contributing

**Priority 1: Database API Core (80% of effort)**
- RQL query language enhancements
- SQLGlot type safety and query building
- DuckDB performance and schema introspection

**Priority 2: Developer Experience (15% of effort)**
- Error handling and debugging
- Testing infrastructure and CLI workflow
- Documentation and examples

**Priority 3: NiceGUI Interface (5% of effort)**
- Auto-generated components from schema
- Override patterns for customization
- Focus on functionality over visual polish

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.
