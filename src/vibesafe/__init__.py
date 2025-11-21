"""
Vibesafe - AI-powered code generation with verifiable specs.

Allows developers to write readable specs as Python code that AI fills in,
with hash-locked verification and test-driven iteration.
"""

from vibesafe.core import (
    VibeHandled,
    VibesafeHandled,
    get_registry,
    get_unit,
    vibesafe,
)
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
from vibesafe.runtime import load_checkpoint

__version__ = "0.1.0"

# Backwards compatibility aliases (deprecated)
func = vibesafe
http = vibesafe
load_active = load_checkpoint

__all__ = [
    "vibesafe",
    "get_registry",
    "get_unit",
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
    "load_checkpoint",
    "load_active",
    "mount",
    "__version__",
]
