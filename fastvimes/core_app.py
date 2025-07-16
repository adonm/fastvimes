"""Backward compatibility shim for old core_app.py imports."""

import warnings
from .app import FastVimes as _FastVimes

# Deprecation warning
warnings.warn(
    "Importing from fastvimes.core_app is deprecated. Use 'from fastvimes import FastVimes' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Backward compatibility
FastVimes = _FastVimes
