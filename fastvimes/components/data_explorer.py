"""Data explorer component for viewing and filtering table data."""

from typing import List, Dict, Any, Optional, Set
from nicegui import ui
import json

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
        self.selected_rows: Set[str] = set()  # Track selected rows for bulk operations
        self.edit_mode = False  # Track if we're in edit mode
        self.schema = None  # Cache schema
        self.data_result = None  # Cache current data
        
    def render(self):
        """Render the data explorer interface."""
        self._load_data()
        
        if not self.schema or not self.data_result:
            ui.label(f"Error loading data for {self.table_name}").classes('text-red-500')
            return
        
        with ui.card().classes('w-full'):
            # Header with title and action buttons
            self._render_header()
            
            # Filter controls
            self._render_filters()
            
            # Bulk operations toolbar
            self._render_bulk_operations()
            
            # Data table
            self._render_data_table()
            
            # Pagination controls
            self._render_pagination()
            
    def _load_data(self):
        """Load table schema and data."""
        try:
            if not self.schema:
                self.schema = self.api_client.get_table_schema(self.table_name)
            
            # Build RQL query from filters
            rql_query = self._build_rql_query()
            
            self.data_result = self.api_client.get_table_data(
                self.table_name,
                rql_query=rql_query,
                limit=self.page_size,
                offset=self.current_page * self.page_size
            )
        except Exception as e:
            ui.notify(f"Error loading data: {e}", type='negative')
            self.schema = None
            self.data_result = None
            
    def _render_header(self):
        """Render header with title and action buttons."""
        with ui.row().classes('w-full justify-between items-center mb-4'):
            ui.label(f'Data Explorer: {self.table_name}').classes('text-h6')
            
            with ui.row().classes('gap-2'):
                ui.button('Add Record', icon='add', on_click=self._add_record).props('dense')
                ui.button('Toggle Edit Mode', icon='edit', on_click=self._toggle_edit_mode).props('dense outline')
                ui.button('Refresh', icon='refresh', on_click=self._refresh_data).props('dense outline')
                ui.button('Export CSV', icon='download', on_click=self._export_csv).props('dense outline')
                
    def _render_filters(self):
        """Render filter controls for each column."""
        with ui.expansion('Filters', icon='filter_list'):
            with ui.row().classes('w-full'):
                for column in self.schema[:6]:  # Limit to first 6 columns for now
                    self._render_column_filter(column)
                    
            with ui.row().classes('w-full justify-end mt-2'):
                ui.button('Apply Filters', icon='filter_list', on_click=self._apply_filters).props('dense')
                ui.button('Clear Filters', icon='clear', on_click=self._clear_filters).props('dense outline')
                    
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
                
    def _render_bulk_operations(self):
        """Render bulk operations toolbar when rows are selected."""
        if not self.selected_rows:
            return
            
        with ui.row().classes('w-full p-2 bg-blue-50 rounded mb-2'):
            ui.label(f'{len(self.selected_rows)} rows selected').classes('text-sm')
            with ui.row().classes('gap-2 ml-auto'):
                ui.button('Edit Selected', icon='edit', on_click=self._bulk_edit).props('dense')
                ui.button('Delete Selected', icon='delete', on_click=self._bulk_delete).props('dense color=negative')
                ui.button('Clear Selection', icon='clear', on_click=self._clear_selection).props('dense outline')
                
    def _render_data_table(self):
        """Render the data table with inline editing capabilities."""
        columns = self.data_result["columns"]
        rows = self.data_result["data"]
        
        if not rows:
            ui.label('No data found').classes('text-grey-6')
            return
            
        # Convert to format expected by ui.table
        table_columns = [
            {"name": col, "label": col, "field": col, "sortable": True}
            for col in columns
        ]
        
        # Add selection column if needed
        if self.edit_mode:
            table_columns.insert(0, {
                "name": "selected",
                "label": "",
                "field": "selected",
                "sortable": False,
                "align": "center"
            })
            
            # Add selection checkboxes to rows
            for row in rows:
                row_id = str(row.get('id', id(row)))
                row['selected'] = row_id in self.selected_rows
        
        with ui.row().classes('w-full items-center justify-between mb-2'):
            ui.label(f'Showing {len(rows)} of {self.data_result["total_count"]} records').classes('text-sm text-grey-6')
            mode_label = 'Edit Mode' if self.edit_mode else 'View Mode'
            ui.label(f'Mode: {mode_label}').classes('text-sm text-blue-600')
        
        self.data_table = ui.table(
            columns=table_columns,
            rows=rows,
            pagination={'rowsPerPage': self.page_size, 'page': self.current_page + 1}
        ).classes('w-full')
        
        # Add event handlers
        if self.edit_mode:
            self.data_table.on('update:selected', self._handle_row_selection)
        self.data_table.on('click', self._handle_cell_click)
        
    def _render_pagination(self):
        """Render pagination controls."""
        total_count = self.data_result["total_count"]
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
            
    def _build_rql_query(self) -> str:
        """Build RQL query from current filters."""
        if not self.filters:
            return ""
        
        conditions = []
        for column, value in self.filters.items():
            if value is None or value == "":
                continue
                
            if column.endswith('_min'):
                col_name = column[:-4]
                conditions.append(f"ge({col_name},{value})")
            elif column.endswith('_max'):
                col_name = column[:-4]
                conditions.append(f"le({col_name},{value})")
            else:
                # String contains filter
                conditions.append(f"contains({column},{value})")
        
        if conditions:
            return f"and({','.join(conditions)})"
        return ""
        
    def _update_filter(self, column: str, value: Any):
        """Update filter for a column."""
        if value:
            self.filters[column] = value
        else:
            self.filters.pop(column, None)
        
    def _apply_filters(self):
        """Apply current filters and refresh data."""
        self.current_page = 0  # Reset to first page
        self._refresh_data()
        
    def _clear_filters(self):
        """Clear all filters and refresh data."""
        self.filters.clear()
        self.current_page = 0
        self._refresh_data()
        
    def _previous_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_data()
            
    def _next_page(self):
        """Go to next page."""
        self.current_page += 1
        self._refresh_data()
        
    def _refresh_data(self):
        """Refresh the data table."""
        ui.notify('Refreshing data...', type='info')
        self._load_data()
        # Re-render the component
        self.render()
        
    def _toggle_edit_mode(self):
        """Toggle between view and edit mode."""
        self.edit_mode = not self.edit_mode
        self.selected_rows.clear()
        self._refresh_data()
        
    def _add_record(self):
        """Open dialog to add a new record."""
        with ui.dialog().props('max-width=500px') as dialog:
            with ui.card():
                ui.label('Add New Record').classes('text-h6 mb-4')
                
                form_data = {}
                inputs = {}
                
                # Create form fields based on schema
                for column in self.schema:
                    col_name = column['name']
                    col_type = column['type']
                    
                    # Skip auto-increment primary keys
                    if col_name.lower() == 'id' and 'auto' in col_type.lower():
                        continue
                        
                    with ui.row().classes('w-full'):
                        ui.label(f'{col_name}:').classes('w-24')
                        
                        if 'varchar' in col_type.lower() or 'text' in col_type.lower():
                            inputs[col_name] = ui.input().classes('flex-1')
                        elif 'int' in col_type.lower():
                            inputs[col_name] = ui.number().classes('flex-1')
                        elif 'bool' in col_type.lower():
                            inputs[col_name] = ui.checkbox().classes('flex-1')
                        else:
                            inputs[col_name] = ui.input().classes('flex-1')
                
                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('Cancel', on_click=dialog.close).props('outline')
                    ui.button('Save', on_click=lambda: self._save_new_record(dialog, inputs))
                    
        dialog.open()
        
    def _save_new_record(self, dialog, inputs):
        """Save new record to database."""
        try:
            # Collect form data
            data = {}
            for col_name, input_widget in inputs.items():
                value = input_widget.value
                if value is not None and value != "":
                    data[col_name] = value
            
            # Create record via API
            result = self.api_client.create_record(self.table_name, data)
            ui.notify(f'Record created successfully', type='positive')
            dialog.close()
            self._refresh_data()
            
        except Exception as e:
            ui.notify(f'Error creating record: {e}', type='negative')
            
    def _handle_row_selection(self, event):
        """Handle row selection for bulk operations."""
        # Update selected rows based on checkbox state
        for row in self.data_result["data"]:
            row_id = str(row.get('id', id(row)))
            if row.get('selected', False):
                self.selected_rows.add(row_id)
            else:
                self.selected_rows.discard(row_id)
                
    def _clear_selection(self):
        """Clear all selected rows."""
        self.selected_rows.clear()
        self._refresh_data()
        
    def _bulk_edit(self):
        """Open bulk edit dialog."""
        if not self.selected_rows:
            ui.notify('No rows selected', type='warning')
            return
            
        with ui.dialog().props('max-width=500px') as dialog:
            with ui.card():
                ui.label(f'Edit {len(self.selected_rows)} Records').classes('text-h6 mb-4')
                
                inputs = {}
                
                # Create form fields for editable columns
                for column in self.schema:
                    col_name = column['name']
                    col_type = column['type']
                    
                    # Skip primary keys
                    if col_name.lower() == 'id':
                        continue
                        
                    with ui.row().classes('w-full'):
                        ui.label(f'{col_name}:').classes('w-24')
                        
                        if 'varchar' in col_type.lower() or 'text' in col_type.lower():
                            inputs[col_name] = ui.input(placeholder='Leave empty to keep current value').classes('flex-1')
                        elif 'int' in col_type.lower():
                            inputs[col_name] = ui.number(placeholder='Leave empty to keep current value').classes('flex-1')
                        elif 'bool' in col_type.lower():
                            inputs[col_name] = ui.select(['true', 'false'], placeholder='Keep current value').classes('flex-1')
                        else:
                            inputs[col_name] = ui.input(placeholder='Leave empty to keep current value').classes('flex-1')
                
                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('Cancel', on_click=dialog.close).props('outline')
                    ui.button('Update', on_click=lambda: self._save_bulk_edit(dialog, inputs))
                    
        dialog.open()
        
    def _save_bulk_edit(self, dialog, inputs):
        """Save bulk edit changes."""
        try:
            # Collect form data
            data = {}
            for col_name, input_widget in inputs.items():
                value = input_widget.value
                if value is not None and value != "":
                    if col_name.endswith('_bool') and value in ['true', 'false']:
                        data[col_name] = value == 'true'
                    else:
                        data[col_name] = value
            
            if not data:
                ui.notify('No changes to save', type='warning')
                return
                
            # Update records via API
            for row_id in self.selected_rows:
                filters = {'id': row_id}
                result = self.api_client.update_records(self.table_name, data, filters)
                
            ui.notify(f'Updated {len(self.selected_rows)} records', type='positive')
            dialog.close()
            self.selected_rows.clear()
            self._refresh_data()
            
        except Exception as e:
            ui.notify(f'Error updating records: {e}', type='negative')
            
    def _bulk_delete(self):
        """Delete selected records."""
        if not self.selected_rows:
            ui.notify('No rows selected', type='warning')
            return
            
        with ui.dialog() as dialog:
            with ui.card():
                ui.label(f'Delete {len(self.selected_rows)} Records').classes('text-h6 mb-4')
                ui.label('Are you sure you want to delete the selected records? This action cannot be undone.').classes('text-body2 mb-4')
                
                with ui.row().classes('w-full justify-end'):
                    ui.button('Cancel', on_click=dialog.close).props('outline')
                    ui.button('Delete', on_click=lambda: self._confirm_bulk_delete(dialog)).props('color=negative')
                    
        dialog.open()
        
    def _confirm_bulk_delete(self, dialog):
        """Confirm and execute bulk delete."""
        try:
            # Delete records via API
            for row_id in self.selected_rows:
                filters = {'id': row_id}
                result = self.api_client.delete_records(self.table_name, filters)
                
            ui.notify(f'Deleted {len(self.selected_rows)} records', type='positive')
            dialog.close()
            self.selected_rows.clear()
            self._refresh_data()
            
        except Exception as e:
            ui.notify(f'Error deleting records: {e}', type='negative')
        
    def _export_csv(self):
        """Export data to CSV."""
        try:
            # Get data in CSV format
            rql_query = self._build_rql_query()
            csv_data = self.api_client.get_table_data(
                self.table_name,
                rql_query=rql_query,
                format='csv'
            )
            
            # Create download
            filename = f"{self.table_name}_export.csv"
            ui.download(csv_data, filename)
            ui.notify(f'Exported to {filename}', type='positive')
            
        except Exception as e:
            ui.notify(f'Error exporting CSV: {e}', type='negative')
        
    def _handle_cell_click(self, event):
        """Handle cell click for inline editing."""
        if not self.edit_mode:
            return
            
        # TODO: Implement inline cell editing
        # This would require more complex UI handling
        pass
