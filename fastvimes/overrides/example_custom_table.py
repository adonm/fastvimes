"""Example custom table override.

To use: rename to custom_table.py and modify FastVimes app:

class MyApp(FastVimes):
    def override_table_page(self, table_name: str):
        if table_name == "users":
            return custom_user_table()
        return None  # Use default for other tables
"""

from nicegui import ui

def custom_user_table():
    """Custom user table with specialized features."""
    with ui.column().classes("w-full"):
        ui.label("Custom User Table").classes("text-xl font-bold")
        ui.label("This is a custom implementation for the users table")
        # Add your custom UI here
