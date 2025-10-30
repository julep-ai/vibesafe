"""
Runtime loading and execution of generated implementations.
"""

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from vibesafe.config import get_config


class CheckpointNotFoundError(Exception):
    """Raised when no active checkpoint is found for a unit."""

    pass


class HashMismatchError(Exception):
    """Raised when checkpoint hash verification fails."""

    pass


def load_active(unit_id: str, verify_hash: bool = True) -> Callable[..., Any]:
    """
    Load active implementation for a unit.

    Args:
        unit_id: Unit identifier (e.g., "app.math.ops/sum_str")
        verify_hash: Whether to verify hash integrity

    Returns:
        Callable implementation

    Raises:
        CheckpointNotFoundError: If no active checkpoint found
        HashMismatchError: If hash verification fails
    """
    config = get_config()

    # Load index to get active spec hash
    index_path = config.resolve_path(config.paths.index)
    if not index_path.exists():
        raise CheckpointNotFoundError(f"No index found at {index_path}")

    with open(index_path, "rb") as f:
        index = tomllib.load(f)

    # Get active hash for this unit
    unit_index = index.get(unit_id)
    if not unit_index:
        raise CheckpointNotFoundError(f"No active checkpoint for unit: {unit_id}")

    active_hash = unit_index.get("active")
    if not active_hash:
        raise CheckpointNotFoundError(f"No active hash in index for unit: {unit_id}")

    # Get checkpoint directory
    checkpoints_base = config.resolve_path(config.paths.checkpoints)
    unit_path = unit_id.replace(".", "/")
    checkpoint_dir = checkpoints_base / unit_path / active_hash[:16]

    if not checkpoint_dir.exists():
        raise CheckpointNotFoundError(f"Checkpoint directory not found: {checkpoint_dir}")

    # Load implementation
    impl_path = checkpoint_dir / "impl.py"
    if not impl_path.exists():
        raise CheckpointNotFoundError(f"Implementation not found: {impl_path}")

    # Verify hash if requested
    if verify_hash and config.project.env == "prod":
        _verify_checkpoint_hash(checkpoint_dir, impl_path)

    # Load module
    spec = importlib.util.spec_from_file_location(
        f"vibesafe._generated.{unit_id.replace('/', '.')}", impl_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec from {impl_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Get function (last part of unit_id after /)
    func_name = unit_id.split("/")[-1]
    if not hasattr(module, func_name):
        raise AttributeError(f"Function {func_name} not found in generated module {impl_path}")

    return getattr(module, func_name)


def _verify_checkpoint_hash(checkpoint_dir: Path, impl_path: Path) -> None:
    """
    Verify checkpoint hash integrity.

    Args:
        checkpoint_dir: Path to checkpoint directory
        impl_path: Path to implementation file

    Raises:
        HashMismatchError: If hashes don't match
    """
    from vibesafe.hashing import compute_checkpoint_hash

    # Load metadata
    meta_path = checkpoint_dir / "meta.toml"
    with open(meta_path, "rb") as f:
        meta = tomllib.load(f)

    stored_chk_hash = meta["chk_sha"]
    spec_hash = meta["spec_sha"]
    prompt_hash = meta["prompt_sha"]

    # Read generated code
    generated_code = impl_path.read_text()

    # Recompute checkpoint hash
    computed_chk_hash = compute_checkpoint_hash(spec_hash, prompt_hash, generated_code)

    if computed_chk_hash != stored_chk_hash:
        raise HashMismatchError(
            f"Checkpoint hash mismatch! Expected {stored_chk_hash}, got {computed_chk_hash}"
        )


def build_shim(unit_id: str) -> str:
    """
    Build shim code that loads the active checkpoint.

    Args:
        unit_id: Unit identifier

    Returns:
        Shim code as string
    """
    func_name = unit_id.split("/")[-1]

    return f'''# AUTO-GENERATED SHIM BY VIBESAFE
# Unit: {unit_id}
# This file imports the active checkpoint implementation.

from vibesafe.runtime import load_active

{func_name} = load_active("{unit_id}")
'''


def write_shim(unit_id: str) -> Path:
    """
    Write shim file for a unit.

    Args:
        unit_id: Unit identifier (e.g., "app.math.ops/sum_str")

    Returns:
        Path to written shim file
    """
    config = get_config()

    # Parse unit_id to get module path
    # e.g., "app.math.ops/sum_str" -> app/math/ops.py
    module_path, _func_name = unit_id.rsplit("/", 1)
    module_file_path = module_path.replace(".", "/") + ".py"

    # Get __generated__ directory
    generated_base = config.resolve_path(config.paths.generated)
    shim_path = generated_base / module_file_path

    # Create parent directories
    shim_path.parent.mkdir(parents=True, exist_ok=True)

    # Build and write shim
    shim_code = build_shim(unit_id)
    shim_path.write_text(shim_code)

    return shim_path


def update_index(unit_id: str, active_hash: str) -> None:
    """
    Update index.toml with active checkpoint for a unit.

    Args:
        unit_id: Unit identifier
        active_hash: Hash of active checkpoint
    """

    config = get_config()
    index_path = config.resolve_path(config.paths.index)

    # Load existing index or create new one
    if index_path.exists():
        with open(index_path, "rb") as f:
            index = tomllib.load(f)
    else:
        index = {}

    # Update unit entry
    if unit_id not in index:
        index[unit_id] = {}

    index[unit_id]["active"] = active_hash

    # Write back
    index_path.parent.mkdir(parents=True, exist_ok=True)

    # Write TOML (manually since tomli doesn't have dump)
    with open(index_path, "w") as f:
        f.write("# Vibesafe checkpoint index\n")
        f.write("# Maps unit IDs to active checkpoint hashes\n\n")
        for uid, data in sorted(index.items()):
            f.write(f'["{uid}"]\n')
            for key, value in data.items():
                f.write(f'{key} = "{value}"\n')
            f.write("\n")
