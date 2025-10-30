"""
Vibesafe - AI-powered code generation with verifiable specs.

Allows developers to write readable specs as Python code that AI fills in,
with hash-locked verification and test-driven iteration.
"""

from vibesafe.core import VibeHandled, VibesafeHandled, vibesafe
from vibesafe.exceptions import (
    VibesafeCheckpointMissing,
    VibesafeError,
    VibesafeHashMismatch,
    VibesafeMissingDoctest,
    VibesafeProviderError,
    VibesafeTypeError,
    VibesafeValidationError,
)
from vibesafe.runtime import load_active

__version__ = "0.1.0"

__all__ = [
    "vibesafe",
    "VibesafeHandled",
    "VibeHandled",
    "VibesafeError",
    "VibesafeMissingDoctest",
    "VibesafeTypeError",
    "VibesafeHashMismatch",
    "VibesafeCheckpointMissing",
    "VibesafeProviderError",
    "VibesafeValidationError",
    "load_active",
    "__version__",
]
