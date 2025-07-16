# Testing Guide for FastVimes

## Overview

FastVimes uses a comprehensive testing strategy with four layers to ensure the simple pgweb-style interface works reliably across different scenarios and browsers.

## Testing Architecture

### 1. **DatabaseService Unit Tests** (tests/test_database_service_complete.py)
- **Purpose**: Test core business logic with multiple database schemas
- **Speed**: Fast (~2-3 seconds)
- **Focus**: Data operations, RQL parsing, SQLGlot safety
- **Coverage**: Multi-schema validation, edge cases, error handling

### 2. **API Integration Tests** (tests/test_phase2_features.py)
- **Purpose**: Test HTTP API endpoints via `httpx` command
- **Speed**: Medium (~5-10 seconds)
- **Focus**: RQL query parsing, FastAPI routing, OpenAPI docs
- **Coverage**: All CRUD operations, format exports, error responses

### 3. **NiceGUI UI Tests** (tests/test_lean_structure.py)
- **Purpose**: Test UI components using native NiceGUI testing
- **Speed**: Fast (~3-5 seconds)
- **Focus**: Component rendering, state management, navigation
- **Coverage**: Page loads, form interactions, reactive updates

### 4. **Playwright MCP Browser Tests** (tests/test_playwright_ui_workflows.py)
- **Purpose**: Test complete user workflows in real browsers
- **Speed**: Slow (~30-60 seconds)
- **Focus**: End-to-end user journeys, visual validation, cross-browser compatibility
- **Coverage**: Complete pgweb-style workflows

## Playwright MCP Testing for pgweb-Style Interface

### **What Should Be Tested**

#### **Core pgweb Features**
1. **Table Browsing**
   - Navigation sidebar with table listing
   - Search and filter tables by name
   - Click table to view data
   - Responsive table layout

2. **Data Exploration**
   - AGGrid data display with pagination
   - Column sorting and filtering
   - Row selection and navigation
   - Export functionality (CSV/Parquet)

3. **Simple CRUD Operations**
   - Add record form with validation
   - Edit existing records inline
   - Delete records with confirmation
   - Success/error feedback

4. **DuckDB UI Integration**
   - "Advanced SQL" button/tab
   - Iframe embedding of DuckDB UI
   - Context passing (selected table)
   - Seamless handoff experience

#### **User Experience Testing**
1. **Navigation Workflows**
   - Homepage → table listing → table view → record details
   - Breadcrumb navigation and back buttons
   - Sidebar persistence across page changes
   - Mobile-responsive drawer behavior

2. **Data Interaction Patterns**
   - Search tables → filter data → export results
   - Browse data → click row → edit form → save changes
   - Add record → fill form → validate → submit → confirm
   - Table view → advanced SQL → DuckDB UI handoff

3. **Error Handling**
   - Nonexistent table URLs show friendly errors
   - Network failures display retry options
   - Form validation errors with clear feedback
   - Graceful degradation when DuckDB UI unavailable

#### **Performance and Reliability**
1. **Loading States**
   - Tables load within 3 seconds for 1000+ rows
   - Charts render within 5 seconds
   - Forms respond instantly to user input
   - Export operations complete within 10 seconds

2. **Visual Consistency**
   - Screenshots for baseline comparison
   - Responsive design across viewport sizes
   - Consistent styling and theming
   - Accessibility compliance (ARIA labels, keyboard navigation)

3. **Cross-Browser Support**
   - Core functionality in Chrome, Firefox, Safari
   - Mobile responsiveness on various devices
   - JavaScript compatibility across browser versions

### **Test Structure Examples**

#### **Simple Table Browsing Flow**
```python
async def test_simple_table_browsing():
    """Test the core pgweb-style table browsing experience."""
    # 1. Navigate to homepage
    await browser_navigate("http://localhost:8000")
    await browser_wait_for(text="Welcome to FastVimes")
    
    # 2. Use sidebar to browse tables
    await browser_click("Tables section", "label:contains('Tables')")
    await browser_wait_for(text="users")
    
    # 3. Search for specific table
    await browser_type("Search input", "input[placeholder='Search tables...']", "users")
    await browser_wait_for(text="users")
    
    # 4. Click to view table data
    await browser_click("Users table", "row:contains('users')")
    await browser_wait_for(text="Table: users")
    
    # 5. Verify data loads in AGGrid
    await browser_wait_for_element(".ag-root-wrapper")
    await browser_wait_for(text="Alice Johnson")
```

#### **CRUD Operations Flow**
```python
async def test_simple_crud_operations():
    """Test basic CRUD operations like pgweb."""
    # Navigate to table
    await browser_navigate("http://localhost:8000/table/users")
    
    # Add record
    await browser_click("Add Record", "button:contains('Add Record')")
    await browser_type("Name field", "input[label='name']", "Test User")
    await browser_type("Email field", "input[label='email']", "test@example.com")
    await browser_click("Submit", "button:contains('Create Record')")
    
    # Verify record appears
    await browser_wait_for(text="Record created successfully")
    await browser_wait_for(text="Test User")
    
    # Edit record (inline or form)
    await browser_click("Edit button", "button[aria-label='Edit Test User']")
    await browser_type("Name field", "input[value='Test User']", "Updated User")
    await browser_click("Save", "button:contains('Save')")
    
    # Verify update
    await browser_wait_for(text="Updated User")
```

#### **DuckDB UI Integration Flow**
```python
async def test_duckdb_ui_handoff():
    """Test smooth handoff to DuckDB UI for advanced features."""
    # Start in table view
    await browser_navigate("http://localhost:8000/table/users")
    await browser_wait_for(text="Table: users")
    
    # Click Advanced SQL button
    await browser_click("Advanced SQL", "button:contains('Advanced SQL')")
    
    # Verify DuckDB UI loads
    await browser_wait_for(text="DuckDB SQL Editor")
    await browser_wait_for_element("iframe[src*='duckdb-ui']")
    
    # Verify context is passed (selected table)
    await browser_wait_for(text="SELECT * FROM users")
```

### **Writing Effective Playwright Tests**

#### **Best Practices**
1. **Use descriptive element names**: "Search input" not just "input"
2. **Wait for content to load**: Always use `browser_wait_for` before interactions
3. **Take snapshots for debugging**: Use `browser_snapshot` at key points
4. **Test error scenarios**: Invalid inputs, network failures, edge cases
5. **Verify API integration**: Ensure UI changes persist in database

#### **Test Organization**
- **One workflow per test**: Don't combine unrelated user journeys
- **Clear test names**: Describe the exact user workflow being tested
- **Setup/teardown**: Clean database state between tests
- **Parallel execution**: Design tests to run independently

#### **Performance Considerations**
- **Measure key interactions**: Login, table load, chart render times
- **Set reasonable timeouts**: 3s for tables, 5s for charts, 10s for exports
- **Test with realistic data**: Use datasets similar to production size
- **Monitor resource usage**: Memory, CPU during intensive operations

## Running Tests

### **Development Workflow**
```bash
# Fast feedback loop (unit tests only)
uv run pytest -m fast

# Medium feedback (API tests)
uv run pytest -m "not slow"

# Full test suite (includes Playwright)
uv run pytest

# Playwright tests only
uv run pytest -m playwright
```

### **CI/CD Integration**
```bash
# Headless browser testing
uv run pytest -m playwright --headless

# Visual regression testing
uv run pytest -m visual --update-snapshots

# Cross-browser testing
uv run pytest -m playwright --browser=chrome,firefox
```

## Test Maintenance

### **Updating Tests**
- **Schema changes**: Update multi-schema test fixtures
- **UI changes**: Update element selectors and expected text
- **New features**: Add corresponding Playwright workflows
- **Performance**: Update timeout expectations

### **Debugging Failures**
- **Screenshots**: Check saved screenshots in test output
- **Console logs**: Examine browser console for JavaScript errors
- **Network requests**: Verify API calls are working correctly
- **Element inspection**: Use browser developer tools for selector validation

This testing approach ensures FastVimes delivers a reliable pgweb-style experience while maintaining the clear separation between simple UI operations and advanced SQL features handled by DuckDB UI.
