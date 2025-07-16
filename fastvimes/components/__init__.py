"""Backward compatibility for old component imports."""

import warnings
from nicegui import ui

# Deprecation warning
warnings.warn(
    "Importing from fastvimes.components is deprecated. Use NiceGUI built-ins (ui.aggrid, ui.tree, etc.) directly.",
    DeprecationWarning,
    stacklevel=2
)

# Minimal backward compatibility components
class AGGridDataExplorer:
    def __init__(self, db_service, table_name):
        self.db_service = db_service
        self.table_name = table_name
        
class TreeSchemaExplorer:
    def __init__(self, db_service, on_table_select=None):
        self.db_service = db_service
        self.on_table_select = on_table_select
        
class FormGenerator:
    def __init__(self, db_service, table_name):
        self.db_service = db_service
        self.table_name = table_name
        
class QueryBuilder:
    def __init__(self, db_service, table_name):
        self.db_service = db_service
        self.table_name = table_name

__all__ = [
    "AGGridDataExplorer",
    "FormGenerator", 
    "QueryBuilder",
    "TreeSchemaExplorer",
]
