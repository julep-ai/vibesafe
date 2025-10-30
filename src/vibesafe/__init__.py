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
from vibesafe.fastapi import mount
from vibesafe.runtime import load_active

__version__ = "0.1.0"

func = vibesafe.func
http = vibesafe.http

__all__ = [
    "vibesafe",
    "func",
    "http",
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
    "mount",
    "__version__",
]
