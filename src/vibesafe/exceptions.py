"""
Exception types used across the vibesafe runtime.
"""


class VibesafeError(Exception):
    """Base exception for vibesafe errors."""


class VibesafeMissingDoctest(VibesafeError):
    """Raised when a spec lacks required doctest examples."""


class VibesafeTypeError(VibesafeError):
    """Raised when a spec is missing or has invalid type annotations."""


class VibesafeHashMismatch(VibesafeError):
    """Raised when checkpoint hash verification fails."""


class VibesafeCheckpointMissing(VibesafeError):
    """Raised when no active checkpoint can be found for a unit."""


class VibesafeProviderError(VibesafeError):
    """Raised when an upstream provider call fails."""


class VibesafeValidationError(VibesafeError):
    """Raised when generated code fails validation checks."""


# Backwards compatibility aliases (pre-SPEC naming)
CheckpointNotFoundError = VibesafeCheckpointMissing
HashMismatchError = VibesafeHashMismatch
