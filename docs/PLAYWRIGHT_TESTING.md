# FastVimes Playwright Testing Guide

Simple and effective Playwright testing for FastVimes UI.

## Overview

FastVimes includes a streamlined Playwright testing setup:

1. **Consolidated Tests** - Single working test file (`tests/test_playwright.py`)
2. **Screenshot Capture** - Automated screenshot tool (`scripts/demo_screenshots.py`)
3. **Container Support** - Works in GitHub Codespaces and Docker containers

## Setup & Installation

### 1. Install Dependencies
```bash
# Install all dependencies including Playwright
uv sync --dev

# Install Playwright browsers
uv run playwright install

# Install system dependencies (Linux containers)
uv run playwright install-deps
```

### 2. Verify Installation
```bash
# Quick verification
uv run python tests/test_playwright.py

# Check directory setup
ls -la test-results/
```

## Tests

### Single Test File: `tests/test_playwright.py`

All Playwright functionality is consolidated into one working test file:

```python
async def test_homepage_loads(self, page, server):
    await page.goto("http://localhost:8050")
    await page.screenshot(path="test-results/screenshots/homepage.png")
    assert "FastVimes" in await page.content()
```

**Run Tests**:
```bash
# All tests
uv run pytest tests/test_playwright.py -v

# Specific test
uv run pytest tests/test_playwright.py::TestFastVimesUI::test_homepage_loads -s

# All Playwright tests
uv run pytest -m playwright -v
```

## Screenshot Capture

### Automated Screenshot Demo

**File**: `scripts/demo_screenshots.py`

Captures screenshots of all major FastVimes interfaces:

```bash
# Run interactive demo
uv run python scripts/demo_screenshots.py

# Options:
# 1. Capture new screenshots
# 2. Create baseline from existing  
# 3. Both
```

**Screenshots Captured**:
- Homepage (`homepage.png`)
- API Documentation (`api-docs.png`)
- Users Table (`table-view.png`)
- Add User Form (`form-view.png`)
- Mobile View (`mobile-view.png`)

### Manual Screenshot Capture

```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch(
        args=["--no-sandbox", "--disable-dev-shm-usage"]
    )
    page = await browser.new_page(viewport={"width": 1280, "height": 720})
    
    await page.goto("http://localhost:8000")
    await page.screenshot(path="screenshot.png")
    
    await browser.close()
```

## Configuration

### Playwright Config

**File**: `playwright.config.py`

```python
config = {
    "browsers": ["chromium"],
    "headless": True,
    "viewport": {"width": 1280, "height": 720},
    "base_url": "http://localhost:8000",
    "screenshot_on_failure": True,
}

# Directory structure
test_config = {
    "screenshot_dir": "test-results/screenshots",
    "baseline_dir": "test-results/baselines",
}
```

### Container Settings

**File**: `.devcontainer.json`

```json
{
    "runArgs": [
        "--shm-size=2gb",
        "--cap-add=SYS_ADMIN"
    ],
    "containerEnv": {
        "PLAYWRIGHT_BROWSERS_PATH": "/ms-playwright"
    }
}
```

## Visual Regression Testing

### 1. Create Baselines
```bash
# Capture current interface as baseline
uv run python scripts/demo_screenshots.py
# Choose option 2: "Create baseline from existing"
```

### 2. Compare Changes
```bash
# After making UI changes, capture new screenshots
uv run python scripts/demo_screenshots.py  
# Choose option 1: "Capture new screenshots"

# Compare manually or use image diff tools
diff test-results/baselines/ test-results/screenshots/
```

### 3. Automated Comparison
```python
# Example visual regression test
async def test_visual_regression(self, page):
    await page.goto("http://localhost:8000")
    
    # Take current screenshot
    await page.screenshot(path="test-results/current.png")
    
    # Compare with baseline (implement comparison logic)
    baseline = Path("test-results/baselines/homepage.png")
    current = Path("test-results/current.png")
    
    assert images_match(baseline, current, threshold=0.95)
```

## Running Tests

### All Tests
```bash
# All Playwright tests
uv run pytest -m playwright -v

# Specific test file
uv run pytest tests/test_playwright.py -v

# Single test
uv run pytest tests/test_playwright.py::TestFastVimesUI::test_homepage_loads -s
```

### With Coverage
```bash
uv run pytest tests/test_playwright.py --cov=fastvimes
```

## Troubleshooting

### Browser Installation Issues
```bash
# Reinstall browsers
uv run playwright install --force

# Check browser status
uv run playwright install-deps
```

### Container Permission Issues
```bash
# Add to .devcontainer.json:
"runArgs": ["--cap-add=SYS_ADMIN", "--shm-size=2gb"]
```

### Server Connection Issues
```bash
# Check server status
curl http://localhost:8000/api/health

# Manual server start
uv run fastvimes serve --port 8000
```

### Screenshot Directory Issues
```bash
# Create directories manually
mkdir -p test-results/screenshots test-results/baselines

# Check permissions
ls -la test-results/
```

## Best Practices

### 1. Test Isolation
- Start fresh server for each test class
- Use unique ports for parallel testing
- Clean up processes in fixtures

### 2. Container Compatibility
- Use `--no-sandbox` for container environments
- Disable GPU acceleration with `--disable-gpu`
- Set appropriate `--shm-size` for shared memory

### 3. Screenshot Consistency
- Use fixed viewport sizes
- Wait for content to load (`page.wait_for_timeout()`)
- Disable animations for consistent captures

### 4. Visual Testing
- Establish clear baselines
- Use meaningful filenames
- Document expected visual changes

## Integration with FastVimes

### UI Component Testing
```python
async def test_data_table_functionality(self, page):
    """Test AGGrid data table interactions."""
    await page.goto("http://localhost:8000/table/users")
    
    # Test sorting
    await page.click(".ag-header-cell[col-id='name']")
    await page.screenshot(path="test-results/table-sorted.png")
    
    # Test filtering
    await page.click(".ag-header-icon[ref='eMenu']")
    await page.fill(".ag-filter-text-input", "Alice")
    await page.screenshot(path="test-results/table-filtered.png")
```

### API Integration Testing
```python
async def test_api_integration_via_ui(self, page):
    """Test that UI properly calls API endpoints."""
    responses = []
    
    page.on("response", lambda resp: responses.append(resp) 
             if "/api/" in resp.url else None)
    
    await page.goto("http://localhost:8000/table/users")
    
    # Verify API calls were made
    api_calls = [r.url for r in responses]
    assert any("/api/v1/data/users" in url for url in api_calls)
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Playwright Tests
  run: |
    uv run playwright install --with-deps
    uv run pytest -m playwright --screenshot=on
    
- name: Upload Screenshots
  uses: actions/upload-artifact@v3
  with:
    name: playwright-screenshots
    path: test-results/screenshots/
```

This testing setup provides comprehensive coverage of FastVimes UI functionality with both automated testing and visual verification capabilities.
