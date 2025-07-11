# FastVimes Manual Testing Guide

This document covers manual testing for features that require human judgment and aren't covered by automated tests.

## Prerequisites

Install uv (handles Python 3.13+ automatically):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup

```bash
# Install dependencies
uv sync

# Create test database with sample data
uv run python examples/basic_app.py init-db --db-path test_manual.db --force

# Start development server
uv run fastvimes serve --db test_manual.db --port 8000
```

## Admin Interface Testing

### 1. Dashboard Access
- Visit: http://localhost:8000/admin
- Verify admin dashboard loads with navigation
- Check all nav links work (Tables, Schema, Config)

### 2. Table Browser
- Navigate to Tables section
- Verify all tables are listed (users, products, orders)
- Click on each table to view data
- Test pagination controls if more than 10 records
- Try filtering with different operators (eq, gt, like, etc.)
- Test sorting by clicking column headers

### 3. Schema Viewer
- Navigate to Schema section
- Verify table schemas display correctly
- Check column names, types, and constraints
- Test switching between different tables

### 4. Configuration Display
- Navigate to Config section
- Verify current configuration is displayed
- Check table-specific configurations are shown
- Test different configuration files if available

### 5. HTML Table Views
- Visit: http://localhost:8000/users/html
- Verify HTML table renders with Bulma styling
- Test responsive design by resizing browser
- Check pagination controls work
- Try filter parameters in URL: `?eq(role,admin)`

### 6. Error Handling
- Visit non-existent table: http://localhost:8000/nonexistent/html
- Verify error page displays properly with Bulma styling
- Check error message is user-friendly
- Test with invalid filter parameters

### 7. HTMX Integration
- Open browser dev tools
- Navigate admin interface
- Verify HTMX requests are working (check Network tab)
- Test that page fragments load without full page refresh

## Visual Design Testing

### 1. Styling Consistency
- Verify Bulma CSS loads correctly
- Check Font Awesome icons display
- Test consistent spacing and typography
- Verify color scheme matches Bulma theme

### 2. Responsive Design
- Test on different screen sizes
- Check mobile menu functionality
- Verify tables remain readable on small screens
- Test tablet and desktop layouts

### 3. Form Elements
- Check form inputs are styled consistently
- Verify buttons follow Bulma button styles
- Test form validation display
- Check accessibility with keyboard navigation

## Performance Testing

### 1. Large Dataset Handling
- Create database with large tables (use test_large_dataset.py)
- Test pagination performance with thousands of records
- Verify filtering doesn't timeout
- Check memory usage stays reasonable

### 2. Concurrent Access
- Open multiple browser tabs to same admin interface
- Test simultaneous filtering/sorting operations
- Verify no race conditions or conflicts

## Browser Compatibility

Test in different browsers:
- Chrome/Chromium
- Firefox
- Safari (if available)
- Edge (if available)

Check for:
- CSS rendering differences
- JavaScript functionality
- HTMX behavior
- Font loading

## Cleanup

```bash
rm test_manual.db test_config.toml
```

## What NOT to Test Manually

These are covered by automated tests:
- API endpoints and responses
- CLI commands and output
- Configuration parsing
- Database connections
- Query execution
- Error handling logic
- Performance benchmarks

Focus manual testing on visual elements, user experience, and browser-specific behavior that automated tests cannot verify.
