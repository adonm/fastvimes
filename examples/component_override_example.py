"""Example showing component override patterns in FastVimes."""

from pathlib import Path
from nicegui import ui
from fastvimes import FastVimes
from fastvimes.components import DataExplorer, FormGenerator, QueryBuilder, TableBrowser
from fastvimes.api_client import FastVimesAPIClient


class CustomDataExplorer(DataExplorer):
    """Custom data explorer with additional features."""
    
    def _render_header(self):
        """Custom header with additional buttons."""
        with ui.row().classes('w-full justify-between items-center mb-4'):
            ui.label(f'Custom Data Explorer: {self.table_name}').classes('text-h6 text-blue-600')
            
            with ui.row().classes('gap-2'):
                ui.button('Add Record', icon='add', on_click=self._add_record).props('dense')
                ui.button('Custom Action', icon='star', on_click=self._custom_action).props('dense color=purple')
                ui.button('Toggle Edit Mode', icon='edit', on_click=self._toggle_edit_mode).props('dense outline')
                ui.button('Refresh', icon='refresh', on_click=self._refresh_data).props('dense outline')
                ui.button('Export CSV', icon='download', on_click=self._export_csv).props('dense outline')
                
    def _custom_action(self):
        """Custom action example."""
        ui.notify('Custom action triggered!', type='info')


class CustomFormGenerator(FormGenerator):
    """Custom form generator with validation."""
    
    def render(self):
        """Render form with custom styling."""
        with ui.card().classes('w-full max-w-md mx-auto'):
            ui.label(f'Custom Form: {self.table_name}').classes('text-h6 text-green-600 mb-4')
            
            # Custom form styling
            ui.label('This is a custom form with enhanced styling!').classes('text-body2 text-gray-600 mb-4')
            
            # Call parent render method
            super().render()


class CustomQueryBuilder(QueryBuilder):
    """Custom query builder with presets."""
    
    def render(self):
        """Render query builder with preset queries."""
        with ui.card().classes('w-full'):
            ui.label(f'Custom Query Builder: {self.table_name}').classes('text-h6 text-purple-600 mb-4')
            
            # Add preset queries
            with ui.row().classes('mb-4'):
                ui.label('Quick Queries:').classes('text-sm font-bold')
                ui.button('Active Records', on_click=self._preset_active).props('dense outline')
                ui.button('Recent Records', on_click=self._preset_recent).props('dense outline')
                ui.button('Top 10', on_click=self._preset_top10).props('dense outline')
            
            # Call parent render method
            super().render()
            
    def _preset_active(self):
        """Load preset for active records."""
        self.filters = [{"column": "active", "operator": "eq", "value": "true"}]
        self._execute_query()
        
    def _preset_recent(self):
        """Load preset for recent records."""
        self.sort_column = "created_at"
        self.sort_direction = "desc"
        self.limit_value = 20
        self._execute_query()
        
    def _preset_top10(self):
        """Load preset for top 10 records."""
        self.limit_value = 10
        self._execute_query()


class CustomTableBrowser(TableBrowser):
    """Custom table browser with favorites."""
    
    def _render_table_list(self):
        """Render table list with favorites."""
        tables = self.api_client.list_tables()
        
        # Add favorites section
        with ui.expansion('⭐ Favorite Tables', icon='star').classes('mb-4'):
            favorite_tables = ['users', 'products', 'orders']  # Example favorites
            for table in tables:
                if table['name'] in favorite_tables:
                    self._render_table_item(table, is_favorite=True)
        
        # Regular tables
        with ui.expansion('📋 All Tables', icon='table_view', value=True):
            for table in tables:
                if table['name'] not in favorite_tables:
                    self._render_table_item(table, is_favorite=False)
                    
    def _render_table_item(self, table, is_favorite=False):
        """Render individual table item."""
        with ui.row().classes('w-full items-center justify-between p-2 hover:bg-gray-50 rounded'):
            with ui.row().classes('items-center gap-2'):
                icon = '⭐' if is_favorite else '📋'
                ui.label(f'{icon} {table["name"]}').classes('text-sm font-medium')
                ui.badge(table['type']).classes('text-xs')
                
            with ui.row().classes('gap-1'):
                ui.button(
                    icon='visibility',
                    on_click=lambda t=table['name']: ui.navigate.to(f'/table/{t}')
                ).props('dense flat size=sm')
                
                if is_favorite:
                    ui.button(
                        icon='star',
                        on_click=lambda: ui.notify('Remove from favorites', type='info')
                    ).props('dense flat size=sm color=yellow')


class CustomFastVimes(FastVimes):
    """Custom FastVimes with component overrides."""
    
    def table_component(self, table_name: str):
        """Override table component for specific tables."""
        if table_name == 'users':
            return CustomDataExplorer(self.api_client, table_name)
        elif table_name == 'products':
            # Different custom component for products
            return CustomDataExplorer(self.api_client, table_name)
        else:
            # Default component for other tables
            return super().table_component(table_name)
            
    def form_component(self, table_name: str):
        """Override form component for specific tables."""
        if table_name in ['users', 'products']:
            return CustomFormGenerator(self.api_client, table_name)
        else:
            return super().form_component(table_name)
            
    def query_component(self, table_name: str):
        """Override query component for specific tables."""
        if table_name == 'users':
            return CustomQueryBuilder(self.api_client, table_name)
        else:
            return super().query_component(table_name)
            
    def table_browser_component(self):
        """Override table browser component."""
        return CustomTableBrowser(self.api_client)


def main():
    """Run the custom FastVimes application."""
    app = CustomFastVimes()
    app.serve()


if __name__ == "__main__":
    main()
