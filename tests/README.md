# FastVimes Testing Guide

## Quick Start for Developers

### Daily Development Workflow

```bash
# Fast checks during development (recommended)
uv run pytest -m fast                    # Run only fast tests (~10 seconds)
uv run ruff format && uv run ruff check  # Format and lint code
```

### Before Committing

```bash
# Full test suite
uv run pytest                           # All tests including CLI (~20 seconds)
uv run pytest --cov=fastvimes          # With coverage report
```

## Test Categories

### By Speed
- **Fast tests** (`-m fast`): Python API + HTTP tests (~10 seconds)
- **Slow tests** (`-m slow`): CLI tests using subprocess (~10 seconds) 
- **All tests**: Complete suite (~20 seconds)

### By Interface
- **Python API** (`-m python_api`): Direct FastVimes class usage
- **HTTP API** (`-m http`): FastAPI TestClient tests
- **CLI Interface** (`-m cli`): Command-line interface via subprocess

## Test Commands

```bash
# Fast development checks
uv run pytest -m fast                    # Fast tests only
uv run pytest -m "not slow"             # Skip slow subprocess tests

# Specific interfaces  
uv run pytest -m python_api             # Python API only
uv run pytest -m http                   # HTTP API only
uv run pytest -m cli                    # CLI interface only

# Full test suite
uv run pytest                           # All tests
uv run pytest tests/test_interfaces.py  # Consolidated test file
uv run pytest --cov=fastvimes          # With coverage

# Specific test classes
uv run pytest tests/test_interfaces.py::TestPythonAPI
uv run pytest tests/test_interfaces.py::TestHTTPInterface 
uv run pytest tests/test_interfaces.py::TestCLIInterface
```

## Test Architecture

All tests use **shared scenarios** from `TestScenarios` class to ensure consistency across interfaces:

- **`TestPythonAPI`**: Tests direct Python API calls
- **`TestCLIInterface`**: Tests CLI commands via subprocess  
- **`TestHTTPInterface`**: Tests HTTP endpoints via TestClient

Each interface tests the same functionality to verify API/CLI/HTML consistency.

## Markers

- `@pytest.mark.fast`: Fast tests for regular development
- `@pytest.mark.slow`: Slow tests using subprocess/file operations
- `@pytest.mark.python_api`: Python API interface tests
- `@pytest.mark.http`: HTTP interface tests
- `@pytest.mark.cli`: CLI interface tests

## Recommended Workflow

1. **During development**: `uv run pytest -m fast`
2. **Before commits**: `uv run pytest`
3. **Debugging specific interface**: `uv run pytest -m python_api` (or `http`/`cli`)
4. **Coverage analysis**: `uv run pytest --cov=fastvimes`
