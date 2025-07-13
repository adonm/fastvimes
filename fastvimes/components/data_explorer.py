"""Data explorer component for viewing and filtering table data."""

from typing import List, Dict, Any, Optional
from nicegui import ui

from ..api_client import FastVimesAPIClient


class DataExplorer:
    """Component for exploring table data with filtering and pagination."""
    
    def __init__(self, api_client: FastVimesAPIClient, table_name: str):
        """Initialize data explorer for a specific table."""
        self.api_client = api_client
        self.table_name = table_name
        self.current_page = 0
        self.page_size = 25
        self.filters = {}
        
    def render(self):
        """Render the data explorer interface."""
        # Get table schema and data
        try:
            schema = self.api_client.get_table_schema(self.table_name)
            data_result = self.api_client.get_table_data(
                self.table_name,
                limit=self.page_size,
                offset=self.current_page * self.page_size
            )
        except Exception as e:
            ui.label(f"Error loading data: {e}").classes('text-red-500')
            return
        
        with ui.card().classes('w-full'):
            ui.label(f'Data Explorer: {self.table_name}').classes('text-h6')
            
            # Filter controls
            self._render_filters(schema)
            
            # Data table
            self._render_data_table(data_result)
            
            # Pagination controls
            self._render_pagination(data_result)
            
    def _render_filters(self, schema: List[Dict[str, Any]]):
        """Render filter controls for each column."""
        with ui.expansion('Filters', icon='filter_list'):
            with ui.row().classes('w-full'):
                for column in schema[:6]:  # Limit to first 6 columns for now
                    self._render_column_filter(column)
                    
    def _render_column_filter(self, column: Dict[str, Any]):
        """Render filter control for a single column."""
        column_name = column["name"]
        column_type = column["type"]
        
        with ui.column().classes('min-w-48'):
            ui.label(column_name).classes('text-sm font-bold')
            
            # Different filter widgets based on column type
            if 'varchar' in column_type.lower() or 'text' in column_type.lower():
                ui.input(
                    placeholder=f'Filter {column_name}...',
                    on_change=lambda value, col=column_name: self._update_filter(col, value)
                ).classes('w-full')
            elif 'int' in column_type.lower() or 'double' in column_type.lower():
                with ui.row():
                    ui.number(
                        placeholder='Min',
                        on_change=lambda value, col=column_name: self._update_filter(f'{col}_min', value)
                    ).classes('w-24')
                    ui.number(
                        placeholder='Max',
                        on_change=lambda value, col=column_name: self._update_filter(f'{col}_max', value)
                    ).classes('w-24')
            else:
                # Generic text filter for other types
                ui.input(
                    placeholder=f'Filter {column_name}...',
                    on_change=lambda value, col=column_name: self._update_filter(col, value)
                ).classes('w-full')
                
    def _render_data_table(self, data_result: Dict[str, Any]):
        """Render the data table."""
        columns = data_result["columns"]
        rows = data_result["data"]
        
        if not rows:
            ui.label('No data found').classes('text-grey-6')
            return
            
        # Convert to format expected by ui.table
        table_columns = [
            {"name": col, "label": col, "field": col, "sortable": True}
            for col in columns
        ]
        
        self.data_table = ui.table(
            columns=table_columns,
            rows=rows,
            pagination={'rowsPerPage': self.page_size, 'page': self.current_page + 1}
        ).classes('w-full')
        
    def _render_pagination(self, data_result: Dict[str, Any]):
        """Render pagination controls."""
        total_count = data_result["total_count"]
        total_pages = (total_count + self.page_size - 1) // self.page_size
        
        if total_pages <= 1:
            return
            
        with ui.row().classes('w-full justify-center'):
            # Previous button
            ui.button(
                'Previous',
                on_click=self._previous_page
            ).props('outline').set_enabled(self.current_page > 0)
            
            # Page info
            ui.label(f'Page {self.current_page + 1} of {total_pages}').classes('mx-4')
            
            # Next button
            ui.button(
                'Next',
                on_click=self._next_page
            ).props('outline').set_enabled(self.current_page < total_pages - 1)
            
    def _update_filter(self, column: str, value: Any):
        """Update filter for a column and refresh data."""
        if value:
            self.filters[column] = value
        else:
            self.filters.pop(column, None)
        # TODO: Refresh data table with new filters
        
    def _previous_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            # TODO: Refresh data table
            
    def _next_page(self):
        """Go to next page."""
        self.current_page += 1
        # TODO: Refresh data table
