# Component Override Guide

FastVimes provides a powerful component override system that allows you to customize the auto-generated UI components for specific tables or globally. This guide shows how to implement custom components while maintaining the auto-generation benefits.

## Overview

The component override pattern in FastVimes allows you to:

1. **Selectively customize** specific components for certain tables
2. **Maintain auto-generation** for tables that don't need customization
3. **Extend existing components** rather than replacing them entirely
4. **Use a simple inheritance model** for easy customization

## Available Override Methods

### In your FastVimes subclass, override these methods:

```python
class CustomFastVimes(FastVimes):
    def table_component(self, table_name: str):
        """Override table display component (DataExplorer)."""
        if table_name == 'users':
            return CustomDataExplorer(self.api_client, table_name)
        return super().table_component(table_name)  # Default for others
        
    def form_component(self, table_name: str):
        """Override form component (FormGenerator)."""
        if table_name == 'products':
            return CustomFormGenerator(self.api_client, table_name)
        return super().form_component(table_name)
        
    def query_component(self, table_name: str):
        """Override query builder component (QueryBuilder)."""
        if table_name == 'orders':
            return CustomQueryBuilder(self.api_client, table_name)
        return super().query_component(table_name)
        
    def table_browser_component(self):
        """Override table browser component (TableBrowser)."""
        return CustomTableBrowser(self.api_client)
```

## Component Customization Patterns

### 1. Extending Existing Components

**Best Practice**: Extend existing components rather than replacing them:

```python
class CustomDataExplorer(DataExplorer):
    """Custom data explorer with additional features."""
    
    def _render_header(self):
        """Override header with custom buttons."""
        with ui.row().classes('w-full justify-between items-center mb-4'):
            ui.label(f'Custom: {self.table_name}').classes('text-h6 text-blue-600')
            
            with ui.row().classes('gap-2'):
                # Add custom buttons
                ui.button('Custom Action', icon='star', on_click=self._custom_action)
                # Call parent method for standard buttons
                super()._render_header()
                
    def _custom_action(self):
        """Custom action implementation."""
        ui.notify('Custom action triggered!', type='info')
```

### 2. Conditional Component Selection

**Pattern**: Use table-specific logic to choose components:

```python
def table_component(self, table_name: str):
    """Different components for different table types."""
    if table_name == 'users':
        return UserDataExplorer(self.api_client, table_name)
    elif table_name.startswith('log_'):
        return LogDataExplorer(self.api_client, table_name)
    elif table_name in ['products', 'inventory']:
        return ProductDataExplorer(self.api_client, table_name)
    else:
        return super().table_component(table_name)  # Default
```

### 3. Global Component Replacement

**Pattern**: Replace components globally:

```python
def table_component(self, table_name: str):
    """Use custom component for all tables."""
    return EnhancedDataExplorer(self.api_client, table_name)
```

## Real-World Examples

### Example 1: User Management Component

```python
class UserDataExplorer(DataExplorer):
    """Specialized component for user management."""
    
    def _render_header(self):
        """Custom header with user-specific actions."""
        with ui.row().classes('w-full justify-between items-center mb-4'):
            ui.label(f'User Management: {self.table_name}').classes('text-h6')
            
            with ui.row().classes('gap-2'):
                ui.button('Invite User', icon='person_add', on_click=self._invite_user)
                ui.button('Export Users', icon='download', on_click=self._export_users)
                ui.button('Refresh', icon='refresh', on_click=self._refresh_data)
                
    def _invite_user(self):
        """Open invite user dialog."""
        with ui.dialog() as dialog:
            with ui.card():
                ui.label('Invite New User').classes('text-h6 mb-4')
                email_input = ui.input('Email').classes('w-full')
                role_select = ui.select(['admin', 'user', 'viewer'], label='Role').classes('w-full')
                
                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('Cancel', on_click=dialog.close).props('outline')
                    ui.button('Send Invite', on_click=lambda: self._send_invite(dialog, email_input, role_select))
        dialog.open()
        
    def _send_invite(self, dialog, email_input, role_select):
        """Send user invitation."""
        # Custom invitation logic
        ui.notify(f'Invitation sent to {email_input.value}', type='positive')
        dialog.close()
```

### Example 2: Product Catalog Component

```python
class ProductDataExplorer(DataExplorer):
    """Specialized component for product catalog."""
    
    def _render_bulk_operations(self):
        """Custom bulk operations for products."""
        if not self.selected_rows:
            return
            
        with ui.row().classes('w-full p-2 bg-blue-50 rounded mb-2'):
            ui.label(f'{len(self.selected_rows)} products selected').classes('text-sm')
            with ui.row().classes('gap-2 ml-auto'):
                ui.button('Update Prices', icon='attach_money', on_click=self._bulk_update_prices)
                ui.button('Change Category', icon='category', on_click=self._bulk_change_category)
                ui.button('Mark Sale', icon='local_offer', on_click=self._bulk_mark_sale)
                # Call parent for standard operations
                super()._render_bulk_operations()
                
    def _bulk_update_prices(self):
        """Bulk price update dialog."""
        with ui.dialog() as dialog:
            with ui.card():
                ui.label('Update Prices').classes('text-h6 mb-4')
                
                price_input = ui.number('New Price', prefix='$').classes('w-full')
                discount_input = ui.number('Discount %', suffix='%').classes('w-full')
                
                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('Cancel', on_click=dialog.close).props('outline')
                    ui.button('Update', on_click=lambda: self._apply_price_update(dialog, price_input, discount_input))
        dialog.open()
```

### Example 3: Analytics Dashboard Component

```python
class AnalyticsQueryBuilder(QueryBuilder):
    """Query builder with analytics presets."""
    
    def render(self):
        """Render with analytics presets."""
        with ui.card().classes('w-full'):
            ui.label('Analytics Dashboard').classes('text-h6 text-purple-600 mb-4')
            
            # Analytics presets
            with ui.row().classes('mb-4'):
                ui.label('Quick Analytics:').classes('text-sm font-bold')
                ui.button('Daily Report', on_click=self._daily_report).props('dense')
                ui.button('Weekly Trends', on_click=self._weekly_trends).props('dense')
                ui.button('Monthly Summary', on_click=self._monthly_summary).props('dense')
            
            # Call parent render
            super().render()
            
    def _daily_report(self):
        """Generate daily report query."""
        self.filters = [{"column": "created_at", "operator": "gt", "value": "TODAY()"}]
        self._execute_query()
```

## Best Practices

### 1. **Extend, Don't Replace**
```python
# ✅ Good: Extend existing functionality
class CustomDataExplorer(DataExplorer):
    def _render_header(self):
        # Add custom elements
        ui.button('Custom Action', on_click=self._custom_action)
        # Call parent for standard functionality
        super()._render_header()

# ❌ Avoid: Complete replacement loses auto-generation benefits
class CustomDataExplorer(DataExplorer):
    def render(self):
        # Completely custom render loses all auto-generation
        with ui.card():
            ui.label('Custom Component')
```

### 2. **Use Conditional Logic**
```python
# ✅ Good: Selective customization
def table_component(self, table_name: str):
    if table_name == 'users':
        return CustomDataExplorer(self.api_client, table_name)
    return super().table_component(table_name)  # Auto-generation for others

# ❌ Avoid: Global replacement loses flexibility
def table_component(self, table_name: str):
    return CustomDataExplorer(self.api_client, table_name)  # All tables
```

### 3. **Maintain API Consistency**
```python
# ✅ Good: Custom components use same API
class CustomDataExplorer(DataExplorer):
    def __init__(self, api_client: FastVimesAPIClient, table_name: str):
        super().__init__(api_client, table_name)
        # Custom initialization

# ❌ Avoid: Breaking API contracts
class CustomDataExplorer(DataExplorer):
    def __init__(self, custom_param, api_client, table_name):
        # Changes API contract
```

### 4. **Progressive Enhancement**
```python
# ✅ Good: Start simple, add complexity gradually
class CustomDataExplorer(DataExplorer):
    def _render_header(self):
        """Start with one custom button."""
        super()._render_header()
        ui.button('Custom Action', on_click=self._custom_action)

# Then later enhance:
class CustomDataExplorer(DataExplorer):
    def _render_header(self):
        """Add more custom features over time."""
        super()._render_header()
        ui.button('Custom Action', on_click=self._custom_action)
        ui.button('Another Action', on_click=self._another_action)
```

## Component Architecture

### Component Hierarchy
```
FastVimes
├── table_browser_component() → TableBrowser
├── table_component(table_name) → DataExplorer
├── form_component(table_name) → FormGenerator
└── query_component(table_name) → QueryBuilder
```

### Override Points
Each component has specific override points:

**DataExplorer**:
- `_render_header()` - Header with action buttons
- `_render_filters()` - Filter controls
- `_render_bulk_operations()` - Bulk operation toolbar
- `_render_data_table()` - Main data table
- `_render_pagination()` - Pagination controls

**FormGenerator**:
- `render()` - Main form render
- `_render_field()` - Individual field rendering
- `_validate_form()` - Form validation logic

**QueryBuilder**:
- `render()` - Main query builder interface
- `_render_filters()` - Filter configuration
- `_execute_query()` - Query execution logic

**TableBrowser**:
- `render()` - Main table listing
- `_render_table_list()` - Table list rendering
- `_render_table_item()` - Individual table items

## Testing Custom Components

```python
# Test component override
def test_custom_component_override():
    app = CustomFastVimes()
    
    # Test that custom component is used
    custom_component = app.table_component('users')
    assert isinstance(custom_component, CustomDataExplorer)
    
    # Test that default component is used for other tables
    default_component = app.table_component('products')
    assert isinstance(default_component, DataExplorer)
```

## Migration Guide

### From Manual UI to Component Override

**Before** (Manual UI):
```python
@ui.page('/users')
def users_page():
    # Manual UI construction
    with ui.card():
        ui.label('Users')
        # Manual table creation
        ui.table(columns=columns, rows=rows)
```

**After** (Component Override):
```python
class UserDataExplorer(DataExplorer):
    def _render_header(self):
        ui.label('Users').classes('text-h6')
        super()._render_header()

class CustomFastVimes(FastVimes):
    def table_component(self, table_name: str):
        if table_name == 'users':
            return UserDataExplorer(self.api_client, table_name)
        return super().table_component(table_name)
```

**Benefits**:
- Keeps auto-generation for schema changes
- Maintains API consistency
- Easier to test and maintain
- Progressive enhancement path

This override pattern provides the perfect balance between auto-generation benefits and customization flexibility.
