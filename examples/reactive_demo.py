#!/usr/bin/env python3
"""Demo showing the difference between old manual refresh and new reactive patterns."""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from nicegui import ui
from fastvimes.database_service import DatabaseService
from fastvimes.components.data_explorer import DataExplorer  # Old pattern
from fastvimes.components.reactive_data_explorer import ReactiveDataExplorer  # New pattern
from fastvimes.components.schema_tree import SchemaTree  # Old pattern
from fastvimes.components.reactive_schema_tree import ReactiveSchemaTree  # New pattern


def create_demo_database():
    """Create a demo database for testing."""
    import tempfile
    import os
    
    # Create temporary database
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_file.close()
    
    db_service = DatabaseService(temp_file.name)
    
    # Create sample table
    db_service.connection.execute("""
        CREATE TABLE demo_users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(50),
            email VARCHAR(100),
            age INTEGER,
            active BOOLEAN DEFAULT true
        )
    """)
    
    # Insert sample data
    sample_data = [
        (1, "Alice Johnson", "alice@example.com", 28, True),
        (2, "Bob Smith", "bob@example.com", 35, True),
        (3, "Charlie Brown", "charlie@example.com", 42, False),
        (4, "Diana Prince", "diana@example.com", 31, True),
        (5, "Eve Adams", "eve@example.com", 26, True),
    ]
    
    db_service.connection.executemany(
        "INSERT INTO demo_users (id, name, email, age, active) VALUES (?, ?, ?, ?, ?)",
        sample_data
    )
    
    return db_service, temp_file.name


@ui.page("/")
def main_page():
    """Main demo page comparing old vs new patterns."""
    ui.label("Reactive Patterns Demo").classes("text-h4 font-bold mb-6")
    
    # Create demo database
    db_service, db_path = create_demo_database()
    
    with ui.tabs() as tabs:
        old_tab = ui.tab("Old Patterns (Manual Refresh)", icon="refresh")
        new_tab = ui.tab("New Patterns (Reactive)", icon="auto_awesome")
        comparison_tab = ui.tab("Comparison", icon="compare")
    
    with ui.tab_panels(tabs, value=old_tab):
        # Old patterns demo
        with ui.tab_panel(old_tab):
            ui.label("Old Manual Refresh Patterns").classes("text-h5 mb-4")
            
            with ui.row().classes("w-full gap-4"):
                # Old schema tree
                with ui.card().classes("w-1/3"):
                    ui.label("Schema Tree (Manual DOM)").classes("text-h6 mb-2")
                    ui.markdown("""
                    **Issues:**
                    - Manual `node.props("selected")` calls
                    - Manual refresh with `self.refresh()`
                    - No automatic UI updates
                    """).classes("text-sm mb-4")
                    
                    old_schema_tree = SchemaTree(db_service)
                    old_schema_tree.render()
                
                # Old data explorer
                with ui.card().classes("w-2/3"):
                    ui.label("Data Explorer (Manual Refresh)").classes("text-h6 mb-2")
                    ui.markdown("""
                    **Issues:**
                    - `@ui.refreshable` decorator
                    - Manual `self._refresh_data()` calls
                    - Global app_state instead of component state
                    - Full component rebuilds
                    """).classes("text-sm mb-4")
                    
                    old_data_explorer = DataExplorer(db_service, "demo_users")
                    old_data_explorer.render()
        
        # New patterns demo
        with ui.tab_panel(new_tab):
            ui.label("New Reactive Patterns").classes("text-h5 mb-4")
            
            with ui.row().classes("w-full gap-4"):
                # New reactive schema tree
                with ui.card().classes("w-1/3"):
                    ui.label("Reactive Schema Tree").classes("text-h6 mb-2")
                    ui.markdown("""
                    **Improvements:**
                    - `ui.state()` for reactive selection
                    - `bind_props_from()` for automatic updates
                    - No manual DOM manipulation
                    - Automatic UI synchronization
                    """).classes("text-sm mb-4")
                    
                    reactive_schema_tree = ReactiveSchemaTree(db_service)
                    reactive_schema_tree.render()
                
                # New reactive data explorer
                with ui.card().classes("w-2/3"):
                    ui.label("Reactive Data Explorer").classes("text-h6 mb-2")
                    ui.markdown("""
                    **Improvements:**
                    - `ui.state()` for all reactive data
                    - `bind_text_from()`, `bind_visibility_from()` 
                    - Automatic UI updates on state changes
                    - Targeted updates, no full rebuilds
                    """).classes("text-sm mb-4")
                    
                    reactive_data_explorer = ReactiveDataExplorer(db_service, "demo_users")
                    reactive_data_explorer.render()
        
        # Comparison tab
        with ui.tab_panel(comparison_tab):
            ui.label("Pattern Comparison").classes("text-h5 mb-4")
            
            with ui.row().classes("w-full gap-4"):
                # Old patterns
                with ui.card().classes("w-1/2"):
                    ui.label("❌ Old Anti-Patterns").classes("text-h6 mb-4 text-red-600")
                    
                    ui.markdown("""
                    ### Manual Refresh Pattern
                    ```python
                    @ui.refreshable
                    def _render_content(self):
                        self._load_data()  # Manual loading
                        # ... render UI
                    
                    def _refresh_data(self):
                        self.refresh()  # Full rebuild
                    ```
                    
                    ### Manual DOM Manipulation
                    ```python
                    node.props("selected", True)   # Manual
                    node.props("selected", False)  # Manual
                    ```
                    
                    ### Global State
                    ```python
                    update_app_state(
                        current_table=table_name,
                        explorer_page=0
                    )
                    ```
                    
                    **Problems:**
                    - Performance issues (full rebuilds)
                    - Manual synchronization
                    - Error-prone state management
                    - Not following NiceGUI best practices
                    """).classes("text-sm")
                
                # New patterns
                with ui.card().classes("w-1/2"):
                    ui.label("✅ New Reactive Patterns").classes("text-h6 mb-4 text-green-600")
                    
                    ui.markdown("""
                    ### Reactive State Pattern
                    ```python
                    def __init__(self):
                        self.table_data = ui.state([])
                        self.current_page = ui.state(0)
                        self.loading = ui.state(False)
                    
                    def _render_content(self):
                        # Automatic updates when state changes
                        ui.table().bind_rows_from(self.table_data)
                    ```
                    
                    ### Reactive Data Binding
                    ```python
                    ui.label().bind_text_from(
                        self.total_count,
                        backward=lambda x: f"{x} records"
                    )
                    
                    ui.button().bind_enabled_from(
                        self.current_page,
                        backward=lambda x: x > 0
                    )
                    ```
                    
                    ### Component State
                    ```python
                    self.selected_table = ui.state(None)
                    self.filters = ui.state({})
                    ```
                    
                    **Benefits:**
                    - Automatic UI updates
                    - Better performance (targeted updates)
                    - Follows NiceGUI best practices
                    - Cleaner, more maintainable code
                    """).classes("text-sm")
    
    # Cleanup on page close
    ui.on_disconnect(lambda: cleanup_database(db_path))


def cleanup_database(db_path: str):
    """Clean up temporary database file."""
    import os
    try:
        os.unlink(db_path)
    except Exception:
        pass


if __name__ == "__main__":
    ui.run(title="Reactive Patterns Demo", port=8002)
