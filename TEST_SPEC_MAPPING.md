# Test-to-Spec Mapping Guide

## Overview

This document maps each test file and test class to specific design specifications in AGENT.md. This ensures that when design changes are made, it's clear which tests need to be updated.

## Core Architecture Tests

### Single Source of Truth Pattern
**Design Spec**: AGENT.md - Architecture Patterns - Single Source of Truth Flow
**Test Files**:
- `tests/test_database_service_complete.py` - DatabaseService public API methods
- `tests/test_rql_integration.py` - RQL parsing and SQL generation
- `tests/test_rql_to_sql.py` - SQLGlot integration for safety

**Test Classes**:
- `TestDatabaseServiceBasics` - Core public methods (list_tables, get_table_schema, get_table_data)
- `TestRQLFiltering` - RQL query parsing and filtering
- `TestRQLSorting` - RQL sort operations
- `TestRQLSelection` - RQL field selection
- `TestCRUDOperations` - Create, update, delete operations

### Multi-Schema Auto-Generation
**Design Spec**: AGENT.md - Testing Strategy - Multi-Schema Testing Requirements
**Test Files**:
- `tests/test_multi_schema_autogeneration.py` - Schema-agnostic functionality

**Test Classes**:
- `TestMultiSchemaAutogeneration` - Core functionality works with any schema
- `TestSchemaSpecificBehavior` - Schema-specific edge cases

## API Design Tests

### Namespaced API Structure
**Design Spec**: AGENT.md - API Namespacing - FastAPI URL Structure
**Test Files**:
- `tests/test_api_endpoints.py` (to be created)

**Expected Test Classes**:
- `TestMetaEndpoints` - `/api/v1/meta/*` endpoints
- `TestDataEndpoints` - `/api/v1/data/*` endpoints
- `TestQueryEndpoints` - `/api/v1/query` endpoint

### RQL Query Language
**Design Spec**: AGENT.md - RQL Query Language - Core RQL Operators
**Test Files**:
- `tests/test_rql_integration.py` - RQL parsing and execution
- `tests/test_rql_to_sql.py` - RQL to SQL conversion

**Test Classes**:
- `TestRQLOperators` - eq, lt, gt, contains, in operators
- `TestRQLLogical` - and, or operations
- `TestRQLSorting` - sort operations
- `TestRQLLimiting` - limit and pagination

## UI Component Tests

### Auto-Generated Components
**Design Spec**: AGENT.md - NiceGUI Exploratory Interface - Auto-Generated Components
**Test Files**:
- `tests/test_ui_components.py` - All UI component functionality

**Test Classes**:
- `TestUIComponentsBasic` - Component initialization and basic functionality
- `TestDataExplorerFunctionality` - Data grid with filtering, pagination, edit mode
- `TestFormGeneratorFunctionality` - CRUD forms from schema
- `TestQueryBuilderFunctionality` - Visual RQL query construction
- `TestTableBrowserFunctionality` - Table/view listing

### Component Override Pattern
**Design Spec**: AGENT.md - NiceGUI Integration Patterns - Override Strategy
**Test Files**:
- `tests/test_component_override.py` (to be created)

**Expected Test Classes**:
- `TestComponentOverrideBasic` - Basic override functionality
- `TestComponentOverrideAdvanced` - Complex override scenarios
- `TestComponentInheritance` - Extending existing components

## Authentication and Security Tests

### Authlib Integration
**Design Spec**: AGENT.md - Security and Safety First - Authlib for authentication
**Test Files**:
- `tests/test_auth_middleware.py` (to be created)

**Expected Test Classes**:
- `TestOAuthIntegration` - OAuth/OpenID Connect flows
- `TestAuthMiddleware` - Authentication middleware functionality
- `TestProtectedRoutes` - Route protection and authorization
- `TestAuthConfiguration` - Authentication configuration

### SQL Safety
**Design Spec**: AGENT.md - Security and Safety First - SQLGlot for SQL safety
**Test Files**:
- `tests/test_rql_to_sql.py` - SQL injection prevention

**Test Classes**:
- `TestSQLSafety` - SQL injection prevention tests
- `TestParameterBinding` - Safe parameter binding

## Configuration Tests

### Settings Management
**Design Spec**: AGENT.md - Implementation Patterns - Configuration
**Test Files**:
- `tests/test_config.py` (to be created)

**Expected Test Classes**:
- `TestSettingsValidation` - pydantic-settings configuration
- `TestEnvironmentVariables` - Environment variable handling
- `TestTOMLConfiguration` - TOML file configuration

## Performance Tests

### Query Performance
**Design Spec**: AGENT.md - Success Metrics - Performance Targets
**Test Files**:
- `tests/test_performance.py` (to be created)

**Expected Test Classes**:
- `TestRQLQueryPerformance` - <100ms query response time
- `TestUIResponseTime` - <50ms component interactions
- `TestMemoryUsage` - <100MB memory usage

## Test Organization Standards

### Test Naming Convention
- Test files: `test_[component]_[aspect].py`
- Test classes: `Test[Component][Aspect]`
- Test methods: `test_[specific_functionality]`

### Test Documentation
Each test class should include:
```python
class TestComponentName:
    """
    Tests for [Component Name] functionality.
    
    Design Spec: AGENT.md - [Section] - [Subsection]
    Coverage: [List of covered functionality]
    """
```

### Test Fixtures
- Use descriptive fixture names that indicate their purpose
- Group related fixtures in conftest.py
- Document fixture scope and purpose

### Test Data
- Use schema-agnostic test data where possible
- Include edge cases and error conditions
- Use parametrized tests for multiple schema types

## Maintenance Guidelines

### When Design Changes
1. **Update AGENT.md** with new design specification
2. **Check this mapping** to find affected tests
3. **Update test specifications** to match new design
4. **Update test implementations** to pass new requirements
5. **Update this mapping** if test structure changes

### When Adding New Features
1. **Add design specification** to AGENT.md
2. **Create test file and classes** following naming convention
3. **Update this mapping** with new test-to-spec relationships
4. **Implement tests** before implementing feature
5. **Verify tests** cover all aspects of design spec

### When Refactoring
1. **Identify affected design specifications**
2. **Update related tests** to match new structure
3. **Maintain test coverage** during refactoring
4. **Update this mapping** if test organization changes

## Coverage Targets by Component

### Core Components (Target: >90%)
- DatabaseService public methods
- RQL parsing and SQL generation
- Multi-schema compatibility

### UI Components (Target: >80%)
- Component initialization and basic functionality
- User interaction flows
- Error handling scenarios

### Security Components (Target: >95%)
- Authentication and authorization
- SQL injection prevention
- Input validation

### Configuration Components (Target: >70%)
- Settings validation
- Environment variable handling
- Error configuration scenarios

This mapping ensures that all tests are directly traceable to design specifications, making maintenance and updates more predictable and systematic.
