"""FastVimes: Lightweight composition of FastAPI and Ibis for data tools."""

from .app import FastVimes
from .config import FastVimesSettings, TableConfig

__version__ = "0.1.0"

__all__ = [
    "FastVimes",
    "FastVimesSettings",
    "TableConfig",
    "__version__",
]
