# Test Performance Guide

This document explains how to run tests efficiently with the optimized test suite.

## Fast Tests (Recommended for frequent runs)

Run only the fast, consolidated tests for quick feedback:

```bash
# Run fast tests only (~1.5 seconds)
uv run pytest tests/test_ui_components.py -m fast

# Run fast tests with verbose output
uv run pytest tests/test_ui_components.py -m fast -v

# Run fast tests with timing information
uv run pytest tests/test_ui_components.py -m fast --durations=10
```

## Test Performance Comparison

- **Fast tests**: 1.44s (5 tests, shared fixtures)
- **Full test suite**: 10.60s (32 tests, individual fixtures)
- **Performance improvement**: 6.5x faster for core functionality

## Test Organization

### Fast Test Classes (Use `@pytest.mark.fast`)
- `TestUIComponentsBasicFast` - Consolidated component initialization and basic functionality
- `TestUIComponentsAPIIntegrationFast` - Consolidated API integration tests

### Slow Test Classes (Use `@pytest.mark.slow`)
- `TestUIComponentsWithMultipleSchemas` - Multi-schema testing with external data

### Regular Test Classes (No marker)
- Individual component tests for detailed coverage

## Fixtures

### Session-scoped fixtures (shared across tests)
- `shared_db_service` - Shared database service for all tests
- `shared_api_client` - Shared API client for all tests  
- `shared_test_server` - Shared FastAPI test server for all tests

### Function-scoped fixtures (fresh for each test)
- `db_service` - Fresh database service per test
- `api_client` - Fresh API client per test
- `test_server` - Fresh FastAPI test server per test

## Usage Patterns

### For development (frequent runs)
```bash
# Quick validation of core functionality
uv run pytest tests/test_ui_components.py -m fast

# Full functionality verification
uv run pytest tests/test_ui_components.py -m "not slow"
```

### For CI/CD (comprehensive testing)
```bash
# Run all tests including slow multi-schema tests
uv run pytest tests/test_ui_components.py

# Run with coverage
uv run pytest tests/test_ui_components.py --cov=fastvimes
```

### For specific components
```bash
# Test specific component classes
uv run pytest tests/test_ui_components.py::TestUIComponentsBasicFast
uv run pytest tests/test_ui_components.py::TestUIComponentsAPIIntegrationFast
```

## Best Practices

1. **Use fast tests for frequent development cycles**
2. **Use full test suite before commits**
3. **Use slow tests for comprehensive validation**
4. **Monitor test performance with `--durations=10`**
5. **Add new tests to appropriate performance categories**

## Markers

- `@pytest.mark.fast` - Fast tests using shared fixtures
- `@pytest.mark.slow` - Slow tests with complex setup
- `@pytest.mark.xfail` - Expected failures with known issues
