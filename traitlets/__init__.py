"""Minimal `traitlets` package stub for packaging-time only.
Provides submodule `traitlets` so imports like `traitlets.traitlets` succeed.
Install the real `traitlets` package for runtime functionality.
"""
from .traitlets import *

__all__ = ['HasTraits', 'observe']
