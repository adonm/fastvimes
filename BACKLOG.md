# FastVimes Development Backlog

## Current Status: Phase 2 Complete, Phase 3 In Progress ✅

**Completed**: RQL/SQLGlot integration, comprehensive testing, single source of truth architecture
**In Progress**: Enhanced NiceGUI components with namespaced CLI/API
**Next**: Complete namespaced structure, then advanced UI components

## Phase 2.1: Architecture Consistency (COMPLETED ✅)

### Single Source of Truth Architecture
**COMPLETED**: Architecture implemented with proper flow:

```
DuckDB/DuckLake → SQLGlot → PyRQL → DatabaseService → FastAPI/CLI/NiceGUI
```

**✅ Achievements:**
1. **DatabaseService Public API** - Clear public vs private methods implemented
   - ✅ Public methods (exposed via CLI/FastAPI/NiceGUI) - no `_` prefix
   - ✅ Private methods (internal implementation) - `_` prefix
   - ✅ Public methods contain all business logic, validation, RQL support
   - ✅ 1:1 mapping between public methods and CLI commands/FastAPI endpoints

2. **Architecture Implementation Status:**
   - ✅ **DatabaseService**: Single source of truth with public API methods
   - ✅ **RQL Integration**: pyrql + SQLGlot for safe query processing
   - ✅ **FastAPI**: Light wrappers over DatabaseService methods (flat structure)
   - ✅ **CLI**: Light wrappers over DatabaseService methods (flat structure)
   - ✅ **NiceGUI**: Components call DatabaseService methods directly
   - ✅ **Testing**: Comprehensive coverage across all layers

3. **Remaining Work for Namespaced Structure:**
   - 🔄 Implement proper API namespacing: `/api/v1/meta/*` and `/api/v1/data/*`
   - 🔄 Implement proper CLI namespacing: `meta` and `data` subcommands
   - 🔄 Support multiple output formats: JSON, Parquet, CSV via `?format=` parameter
   - ✅ Keep existing `httpx` command for FastAPI testing (automatic server lifecycle)

## Phase 3: Enhanced NiceGUI Components (In Progress)

### Auto-Generated Components Priority
1. **Query Builder Component** - Visual RQL query construction interface
   - Drag-and-drop filter building
   - Real-time preview of results
   - Save/load query presets
   
2. **Enhanced Data Explorer** - Advanced table component
   - Inline editing capabilities  
   - Sortable/filterable columns with RQL integration
   - Bulk operations (edit, delete multiple rows)
   - Export functionality (CSV, JSON)
   
3. **Chart Generator** - Auto-generated visualizations
   - Column type detection for appropriate chart types
   - Interactive charts with drill-down
   - Real-time data updates
   
4. **Advanced Form Generator** - Smart CRUD forms
   - Field validation based on schema
   - Relationship handling (foreign keys)
   - Multi-step forms for complex data

### Override Pattern Implementation  
5. **Component Override System** - Allow custom component substitution
   - Base class with overridable methods
   - Component registry for custom implementations
   - Hot-swapping for development

## Phase 4: Production Features

### Performance & Scalability
1. **Bulk Operations** - High-performance data import/export
   - Bulk insert/upsert APIs with Parquet/CSV file upload
   - DuckDB native: `INSERT INTO table SELECT * FROM 'file.parquet'`
   - Support multipart file uploads in FastAPI endpoints
   - CLI commands: `fastvimes data bulk-insert users --file data.parquet`
2. **Connection Pooling** - Database connection management
3. **Query Caching** - Cache frequent RQL queries  
4. **Async Support** - Non-blocking database operations
5. **Streaming Results** - Handle large datasets efficiently

### Security & Authentication
1. **Authentication Middleware** - User login/session management
2. **Authorization Rules** - Table/column-level permissions
3. **Audit Logging** - Track data changes and access
4. **Rate Limiting** - Prevent API abuse

### DuckLake Integration  
1. **Multi-Catalog Support** - PostgreSQL/MySQL catalogs
2. **Concurrent Access** - Multi-user ACID guarantees
3. **Schema Migration** - Version control for database schemas
4. **Backup/Restore** - Data protection capabilities

## Phase 5: Advanced Features

### Relationship Support
1. **Foreign Key Navigation** - Follow relationships between tables
2. **Join Query Builder** - Visual relationship query construction  
3. **Nested Data Display** - Show related data inline
4. **Cascade Operations** - Handle related record updates/deletes

### Advanced Querying
1. **OR Logic Support** - Complete RQL logical operators
2. **Aggregation Functions** - COUNT, SUM, AVG, etc.
3. **Date/Time Operations** - Specialized temporal queries
4. **Full-Text Search** - Search across text columns
5. **Geospatial Queries** - Location-based filtering (if needed)

### Developer Experience  
1. **Hot Reload** - Development server with auto-refresh
2. **Component Inspector** - Debug UI component state
3. **Query Profiler** - Performance analysis tools
4. **API Documentation** - Auto-generated OpenAPI docs
5. **Example Gallery** - Sample applications and patterns

## Phase 6: Ecosystem Integration

### External Integrations
1. **CSV/Excel Import** - Data loading utilities
2. **REST API Sync** - Sync with external APIs
3. **Webhook Support** - Event-driven data updates  
4. **ETL Pipeline** - Data transformation capabilities

### Deployment & Operations
1. **Docker Container** - Containerized deployment
2. **Cloud Deployment** - AWS/GCP/Azure support
3. **Monitoring** - Health checks and metrics
4. **Configuration Management** - Environment-based config

## Immediate Next Steps (Week 1)

### High Priority
1. **Fix Test Failures** - Resolve pagination and CRUD operation issues
2. **Query Builder Component** - Start visual RQL builder
3. **Enhanced Data Explorer** - Add inline editing and bulk operations
4. **HTTP API Testing** - Verify RQL works correctly via httpx commands

### Medium Priority  
1. **Component Override Pattern** - Implement base class with overridable methods
2. **Authentication Middleware** - Basic login/session support
3. **Documentation** - Usage examples and API reference
4. **Error Handling** - Improve user-facing error messages

### Low Priority
1. **Chart Generator** - Basic visualization component
2. **Performance Optimization** - Query caching and connection pooling
3. **Docker Setup** - Containerized development environment

## Architecture Decisions Made

### ✅ Confirmed Patterns
- **RQL + SQLGlot**: Hybrid parsing/generation for safety and performance
- **pyrql Integration**: Standard library for RQL parsing  
- **FastAPI + NiceGUI**: HTTP API with reactive UI components
- **DuckDB Backend**: High-performance analytical database
- **Fallback Strategy**: Graceful degradation for complex queries

### 🔄 Pending Decisions  
- **Authentication Provider**: Built-in vs. external (OAuth, LDAP)
- **UI Framework**: Pure NiceGUI vs. hybrid with other frameworks
- **Deployment Strategy**: Single binary vs. microservices
- **Data Validation**: Schema-based vs. runtime validation

## Success Metrics

### Phase 3 Goals
- [ ] Query Builder: Visual RQL construction without writing code
- [ ] Data Explorer: Inline editing with real-time validation  
- [ ] Chart Generator: Auto-generate 3+ chart types from data
- [ ] Override Pattern: Custom component replacement in <10 lines of code

### Performance Targets
- [ ] RQL Query Response: <100ms for typical queries (<10k records)
- [ ] UI Responsiveness: <50ms for component interactions
- [ ] Memory Usage: <100MB for typical datasets
- [ ] Test Coverage: >90% for core functionality

### Developer Experience Goals
- [ ] Zero-Config Startup: `fastvimes serve` works immediately
- [ ] Auto-Generation: Full UI from schema in <1 minute
- [ ] Override Simplicity: Custom components with minimal boilerplate
- [ ] Documentation: Complete examples for all major features

This backlog reflects the current architecture and focuses on delivering the Datasette-style auto-generation promise while maintaining the incremental override capability that makes FastVimes unique.
