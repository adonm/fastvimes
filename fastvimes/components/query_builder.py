"""Simple visual RQL query builder component."""

from typing import List, Dict, Any, Optional
from nicegui import ui

from ..api_client import FastVimesAPIClient


class QueryBuilder:
    """Minimal, intuitive RQL query builder component."""
    
    def __init__(self, api_client: FastVimesAPIClient, table_name: str):
        """Initialize query builder for a specific table."""
        self.api_client = api_client
        self.table_name = table_name
        self.filters = []
        self.sort_column = None
        self.sort_direction = "asc"
        self.limit_value = 100
        self.selected_columns = []
        
    def render(self):
        """Render the query builder interface."""
        try:
            schema = self.api_client.get_table_schema(self.table_name)
            columns = [col["name"] for col in schema]
        except Exception as e:
            ui.label(f"Error loading schema: {e}").classes('text-red-500')
            return
        
        with ui.card().classes('w-full'):
            ui.label('Query Builder').classes('text-h6 mb-4')
            
            # Simple query controls in a compact layout
            with ui.row().classes('w-full gap-4'):
                # Column selection (SELECT)
                self._render_column_selection(columns)
                
                # Sorting (ORDER BY)
                self._render_sort_controls(columns)
                
                # Limit (LIMIT)
                self._render_limit_control()
            
            # Filters (WHERE)
            self._render_filter_controls(schema)
            
            # Query preview and execute
            self._render_query_controls()
    
    def _render_column_selection(self, columns: List[str]):
        """Render column selection dropdown."""
        with ui.column().classes('min-w-48'):
            ui.label('Select Columns').classes('text-sm font-bold')
            ui.select(
                columns,
                multiple=True,
                value=self.selected_columns,
                on_change=lambda value: setattr(self, 'selected_columns', value.value)
            ).classes('w-full').props('use-chips')
    
    def _render_sort_controls(self, columns: List[str]):
        """Render sorting controls."""
        with ui.column().classes('min-w-48'):
            ui.label('Sort By').classes('text-sm font-bold')
            with ui.row().classes('w-full'):
                ui.select(
                    columns,
                    value=self.sort_column,
                    on_change=lambda value: setattr(self, 'sort_column', value.value)
                ).classes('flex-grow')
                ui.select(
                    ['asc', 'desc'],
                    value=self.sort_direction,
                    on_change=lambda value: setattr(self, 'sort_direction', value.value)
                ).classes('w-20')
    
    def _render_limit_control(self):
        """Render limit control."""
        with ui.column().classes('min-w-32'):
            ui.label('Limit').classes('text-sm font-bold')
            ui.number(
                value=self.limit_value,
                on_change=lambda value: setattr(self, 'limit_value', value.value or 100)
            ).classes('w-full')
    
    def _render_filter_controls(self, schema: List[Dict[str, Any]]):
        """Render filter controls."""
        with ui.expansion('Filters', icon='filter_list').classes('w-full'):
            with ui.column().classes('w-full'):
                # Add filter button
                ui.button(
                    'Add Filter',
                    icon='add',
                    on_click=lambda: self._add_filter(schema)
                ).props('dense outline')
                
                # Render existing filters
                for i, filter_config in enumerate(self.filters):
                    self._render_filter_row(i, filter_config, schema)
    
    def _render_filter_row(self, index: int, filter_config: Dict[str, Any], schema: List[Dict[str, Any]]):
        """Render a single filter row."""
        columns = [col["name"] for col in schema]
        
        with ui.row().classes('w-full items-center gap-2'):
            # Column selection
            ui.select(
                columns,
                value=filter_config.get('column'),
                on_change=lambda value, idx=index: self._update_filter(idx, 'column', value.value)
            ).classes('w-40')
            
            # Operator selection
            operators = ['eq', 'ne', 'gt', 'lt', 'contains', 'in']
            ui.select(
                operators,
                value=filter_config.get('operator', 'eq'),
                on_change=lambda value, idx=index: self._update_filter(idx, 'operator', value.value)
            ).classes('w-32')
            
            # Value input
            ui.input(
                value=filter_config.get('value', ''),
                placeholder='Value',
                on_change=lambda value, idx=index: self._update_filter(idx, 'value', value.value)
            ).classes('flex-grow')
            
            # Remove filter button
            ui.button(
                icon='remove',
                on_click=lambda idx=index: self._remove_filter(idx)
            ).props('dense flat color=negative')
    
    def _render_query_controls(self):
        """Render query preview and execute controls."""
        with ui.row().classes('w-full items-center gap-4 mt-4'):
            # Query preview
            rql_query = self._build_rql_query()
            ui.input(
                value=rql_query,
                placeholder='Generated RQL query...',
                readonly=True
            ).classes('flex-grow').props('outlined')
            
            # Execute button
            ui.button(
                'Execute Query',
                icon='play_arrow',
                on_click=self._execute_query
            ).props('color=primary')
    
    def _add_filter(self, schema: List[Dict[str, Any]]):
        """Add a new filter."""
        self.filters.append({
            'column': schema[0]['name'] if schema else '',
            'operator': 'eq',
            'value': ''
        })
        ui.notify('Filter added - please refresh to see changes', type='info')
    
    def _remove_filter(self, index: int):
        """Remove a filter."""
        if 0 <= index < len(self.filters):
            self.filters.pop(index)
            ui.notify('Filter removed - please refresh to see changes', type='info')
    
    def _update_filter(self, index: int, field: str, value: str):
        """Update a filter field."""
        if 0 <= index < len(self.filters):
            self.filters[index][field] = value
    
    def _build_rql_query(self) -> str:
        """Build RQL query string from current settings."""
        query_parts = []
        
        # Add filters
        for filter_config in self.filters:
            if filter_config.get('column') and filter_config.get('value'):
                column = filter_config['column']
                operator = filter_config['operator']
                value = filter_config['value']
                
                if operator == 'in':
                    # Handle IN operator specially
                    values = [v.strip() for v in value.split(',')]
                    query_parts.append(f"{operator}({column},({','.join(values)}))")
                else:
                    query_parts.append(f"{operator}({column},{value})")
        
        # Add sorting
        if self.sort_column:
            direction = '+' if self.sort_direction == 'asc' else '-'
            query_parts.append(f"sort({direction}{self.sort_column})")
        
        # Add column selection
        if self.selected_columns:
            columns_str = ','.join(self.selected_columns)
            query_parts.append(f"select({columns_str})")
        
        # Add limit
        if self.limit_value and self.limit_value != 100:
            query_parts.append(f"limit({self.limit_value})")
        
        return '&'.join(query_parts)
    
    def _execute_query(self):
        """Execute the built query and show results."""
        rql_query = self._build_rql_query()
        
        try:
            # Execute query via API client
            result = self.api_client.get_table_data(
                self.table_name,
                rql_query=rql_query,
                limit=self.limit_value
            )
            
            # Display results in a simple table
            self._display_results(result)
            
        except Exception as e:
            ui.notify(f"Query error: {e}", type='negative')
    
    def _display_results(self, result: Dict[str, Any]):
        """Display query results in a simple table."""
        columns = result.get("columns", [])
        rows = result.get("data", [])
        total_count = result.get("total_count", 0)
        
        # Clear any existing results
        if hasattr(self, 'results_container'):
            self.results_container.clear()
        else:
            self.results_container = ui.column().classes('w-full mt-4')
        
        with self.results_container:
            ui.separator()
            ui.label(f'Results ({total_count} total)').classes('text-h6')
            
            if not rows:
                ui.label('No results found').classes('text-grey-6')
                return
            
            # Simple table for results
            table_columns = [
                {"name": col, "label": col, "field": col, "sortable": True}
                for col in columns
            ]
            
            ui.table(
                columns=table_columns,
                rows=rows,
                pagination={'rowsPerPage': min(25, len(rows))}
            ).classes('w-full')
