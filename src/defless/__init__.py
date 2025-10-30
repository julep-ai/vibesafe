"""
Defless - AI-powered code generation with verifiable specs.

Allows developers to write readable specs as Python code that AI fills in,
with hash-locked verification and test-driven iteration.
"""

from defless.core import DeflessHandled, defless
from defless.runtime import load_active

__version__ = "0.1.0"

__all__ = [
    "DeflessHandled",
    "defless",
    "load_active",
    "__version__",
]
