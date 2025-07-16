"""FastVimes: Auto-Generated Datasette-Style Apps with NiceGUI + DuckLake

Generate Datasette-like exploratory interfaces automatically from DuckLake schemas
using NiceGUI's reactive components, with incremental override capabilities for
custom form/database applications.

Core Concept: `fastvimes serve` → instant reactive web app with sample data,
tables, forms, charts, and API. Point at DuckLake for production multi-user
capabilities. Incrementally override components for custom functionality.

Default Setup: Uses DuckLake in temporary directory with sample data, cleaned up
on exit. Production: point at persistent DuckLake with PostgreSQL/MySQL catalog
for multi-user access.
"""

from .app import FastVimes
from .config import FastVimesSettings

__version__ = "0.2.0"
__all__ = ["FastVimes", "FastVimesSettings"]
