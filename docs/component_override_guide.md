# Component Override Guide

FastVimes provides a simple page override system that allows you to customize the auto-generated UI pages for specific tables. This guide shows how to implement custom pages while maintaining the auto-generation benefits for other tables.

## Overview

The page override pattern in FastVimes allows you to:

1. **Selectively customize** specific pages for certain tables
2. **Maintain auto-generation** for tables that don't need customization  
3. **Create fully custom NiceGUI pages** when needed
4. **Use a simple inheritance model** for easy customization

## Available Override Methods

### In your FastVimes subclass, override these methods:

```python
from fastvimes import FastVimes
from nicegui import ui

class CustomFastVimes(FastVimes):
    def override_table_page(self, table_name: str):
        """Override table display page. Return None to use default."""
        if table_name == 'users':
            return self._custom_users_table()
        return None  # Use default auto-generated page for others
        
    def override_form_page(self, table_name: str):
        """Override form page. Return None to use default."""
        if table_name == 'products':
            return self._custom_products_form()
        return None  # Use default auto-generated form for others

    def _custom_users_table(self):
        """Custom table page for users with special functionality."""
        with ui.column().classes("w-full h-full p-8"):
            ui.label("Custom Users Management").classes("text-3xl font-bold mb-4")
            
            # Add custom widgets here
            with ui.card().classes("w-full"):
                ui.label("This is a custom users table page")
                # Add your custom table logic here
                
    def _custom_products_form(self):
        """Custom form page for products with validation."""
        with ui.column().classes("w-full max-w-2xl mx-auto p-8"):
            ui.label("Custom Product Form").classes("text-3xl font-bold mb-4")
            
            # Add custom form widgets here  
            with ui.card().classes("w-full p-6"):
                ui.label("This is a custom products form")
                # Add your custom form logic here
```

## Page Customization Patterns

### 1. Conditional Overrides

**Best Practice**: Override specific tables while keeping auto-generation for others:

```python
class MyApp(FastVimes):
    def override_table_page(self, table_name: str):
        """Custom table pages for specific tables only."""
        if table_name == 'users':
            return self._users_dashboard()
        elif table_name == 'orders':
            return self._orders_analytics()
        elif table_name == 'logs':
            return self._logs_viewer()
        
        return None  # Use auto-generated pages for other tables

    def _users_dashboard(self):
        """Custom users dashboard with analytics."""
        with ui.column().classes("w-full p-8"):
            ui.label("User Management Dashboard").classes("text-2xl font-bold mb-6")
            
            # Get user stats
            stats = self.db_service.execute_query(
                "SELECT COUNT(*) as total, COUNT(CASE WHEN active THEN 1 END) as active FROM users"
            )[0]
            
            # Display stats cards
            with ui.row().classes("gap-4 mb-6"):
                with ui.card().classes("p-4"):
                    ui.label("Total Users").classes("text-sm text-gray-500")
                    ui.label(str(stats['total'])).classes("text-2xl font-bold")
                    
                with ui.card().classes("p-4"):
                    ui.label("Active Users").classes("text-sm text-gray-500") 
                    ui.label(str(stats['active'])).classes("text-2xl font-bold")
            
            # Add custom user management widgets
            ui.label("User Actions").classes("text-lg font-medium mb-4")
            with ui.row().classes("gap-2"):
                ui.button("Export Users", icon="download")
                ui.button("Send Newsletter", icon="mail")
                ui.button("User Analytics", icon="analytics")
```

### 2. Global Page Overrides

Override pages for all tables with common customizations:

```python
class MyApp(FastVimes):
    def override_table_page(self, table_name: str):
        """Add custom header to all table pages."""
        return self._enhanced_table_page(table_name)
        
    def _enhanced_table_page(self, table_name: str):
        """Enhanced table page with custom navigation and branding."""
        with ui.column().classes("w-full h-full"):
            # Custom header
            with ui.card().classes("w-full mb-4 p-4"):
                with ui.row().classes("items-center justify-between"):
                    ui.label(f"🏢 Company Data - {table_name.title()}").classes("text-xl font-bold")
                    ui.button("Export All", icon="download")
            
            # Include default table content by calling original UI logic
            # You can replicate the table display logic from ui_pages.py here
            with ui.card().classes("w-full"):
                ui.label("Enhanced table view coming soon...")
                # Implement custom table display logic
```

## NiceGUI Integration

### Working with Database Service

Access the database service in your custom pages:

```python
class MyApp(FastVimes):
    def override_table_page(self, table_name: str):
        if table_name == 'analytics':
            return self._analytics_dashboard()
        return None
        
    def _analytics_dashboard(self):
        """Custom analytics dashboard."""
        with ui.column().classes("w-full p-8"):
            ui.label("Analytics Dashboard").classes("text-2xl font-bold mb-6")
            
            # Query data using database service
            daily_stats = self.db_service.execute_query("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as records
                FROM analytics 
                WHERE created_at >= CURRENT_DATE - INTERVAL 30 DAYS
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
            
            # Create chart with NiceGUI
            if daily_stats:
                chart_data = {
                    "title": {"text": "Daily Records"},
                    "xAxis": {"type": "category", "data": [row["date"] for row in daily_stats]},
                    "yAxis": {"type": "value"},
                    "series": [{
                        "type": "line",
                        "data": [row["records"] for row in daily_stats]
                    }]
                }
                ui.echart(chart_data).classes("w-full h-64")
```

## Form Customization Examples

### Custom Form with Validation

```python
class MyApp(FastVimes):
    def override_form_page(self, table_name: str):
        if table_name == 'users':
            return self._custom_user_form()
        return None
        
    def _custom_user_form(self):
        """Custom user form with enhanced validation."""
        with ui.column().classes("w-full max-w-2xl mx-auto p-8"):
            ui.label("Create New User").classes("text-2xl font-bold mb-6")
            
            with ui.card().classes("w-full p-6"):
                # Form fields
                name_input = ui.input("Full Name", placeholder="Enter full name").classes("w-full mb-4")
                email_input = ui.input("Email", placeholder="user@company.com").classes("w-full mb-4")
                role_select = ui.select(["admin", "user", "viewer"], label="Role").classes("w-full mb-4")
                
                # Custom validation
                def validate_and_submit():
                    if not name_input.value or len(name_input.value.strip()) < 2:
                        ui.notify("Name must be at least 2 characters", type="negative")
                        return
                        
                    if not email_input.value or "@" not in email_input.value:
                        ui.notify("Please enter a valid email", type="negative")
                        return
                    
                    # Create user with database service
                    try:
                        self.db_service.create_record("users", {
                            "name": name_input.value.strip(),
                            "email": email_input.value.strip(), 
                            "role": role_select.value,
                            "active": True
                        })
                        ui.notify("User created successfully!", type="positive")
                        ui.navigate.to("/table/users")
                    except Exception as e:
                        ui.notify(f"Error creating user: {e}", type="negative")
                
                ui.button("Create User", on_click=validate_and_submit, icon="person_add").props("color=primary").classes("w-full")
```

## Testing Override Pages

### Testing Custom Pages

```python
# Test your custom app
app = CustomFastVimes(db_path="test.db")

# Test specific overrides
users_page = app.override_table_page("users")
products_form = app.override_form_page("products")

# Verify overrides work
assert users_page is not None  # Should return custom page
assert app.override_table_page("orders") is None  # Should use default

app.serve()
```

## Best Practices

### 1. Keep Default Behavior for Most Tables
- Only override when you need specific customization
- Let FastVimes auto-generate standard CRUD interfaces
- Override selectively for special business logic

### 2. Use Database Service Methods
- Access data through `self.db_service` methods
- Don't bypass the database service layer
- Maintain data consistency and validation

### 3. Follow NiceGUI Patterns
- Use NiceGUI's built-in components (`ui.card`, `ui.button`, etc.)
- Follow responsive design patterns with proper CSS classes
- Handle errors gracefully with `ui.notify()`

### 4. Maintain Navigation
- Include navigation elements in custom pages
- Provide clear ways to return to table lists
- Keep the user experience consistent

## Architecture Summary

```
FastVimes App
├── override_table_page(table_name) → Custom NiceGUI Page or None
├── override_form_page(table_name) → Custom NiceGUI Page or None  
└── db_service → DatabaseService methods for data access

Default Behavior (when override returns None):
├── Auto-generated table pages with AGGrid
├── Auto-generated form pages with schema-based fields
└── Standard navigation and CRUD operations
```

## Common Patterns

### 1. Analytics Dashboard
```python
def override_table_page(self, table_name: str):
    if table_name in ['analytics', 'metrics', 'stats']:
        return self._analytics_dashboard(table_name)
    return None
```

### 2. Enhanced Forms  
```python
def override_form_page(self, table_name: str):
    if table_name in ['users', 'customers', 'orders']:
        return self._enhanced_form(table_name)
    return None
```

### 3. Read-only Displays
```python
def override_table_page(self, table_name: str):
    if table_name in ['logs', 'audit_trail']:
        return self._readonly_display(table_name)
    return None
```

---

**Next Steps**: Check out the [UI Walkthrough](UI_WALKTHROUGH.md) to see the default auto-generated interface, then experiment with custom overrides for your specific use cases.
