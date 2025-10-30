"""
Vibesafe - AI-powered code generation with verifiable specs.

Allows developers to write readable specs as Python code that AI fills in,
with hash-locked verification and test-driven iteration.
"""

from vibesafe.core import VibesafeHandled, vibesafe
from vibesafe.runtime import load_active

__version__ = "0.1.0"

__all__ = [
    "VibesafeHandled",
    "vibesafe",
    "load_active",
    "__version__",
]
