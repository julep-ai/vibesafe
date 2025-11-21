"""
Runtime loading and execution of generated implementations.
"""

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from typing import ParamSpec, TypeVar, cast

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from vibesafe.config import get_config
from vibesafe.exceptions import (
    VibesafeCheckpointMissing,
    VibesafeHashMismatch,
)

P = ParamSpec("P")
R = TypeVar("R")


def load_checkpoint(
    unit_id: str,
    verify_hash: bool = True,
    *,
    expected_spec_hash: str | None = None,
) -> Callable[P, R]:
    """
    Load active implementation for a unit.

    Args:
        unit_id: Unit identifier (e.g., "app.math.ops/sum_str")
        verify_hash: Whether to verify hash integrity

    Returns:
        Callable implementation

    Raises:
        VibesafeCheckpointMissing: If no active checkpoint found
        VibesafeHashMismatch: If hash verification fails or spec hash mismatches
    """
    config = get_config()

    index_path = config.resolve_path(config.paths.index)
    checkpoints_base = config.resolve_path(config.paths.checkpoints)

    checkpoint_dir: Path | None = None
    active_hash: str | None = None

    if index_path.exists():
        with open(index_path, "rb") as f:
            index = tomllib.load(f)

        unit_index = index.get(unit_id)
        if unit_index:
            candidate_hash = unit_index.get("active")
            if candidate_hash:
                active_hash = candidate_hash
                unit_path = unit_id.replace(".", "/")
                checkpoint_dir = checkpoints_base / unit_path / candidate_hash[:16]

    allow_fallback = expected_spec_hash is None

    if (checkpoint_dir is None or active_hash is None) and allow_fallback:
        resolved = _resolve_checkpoint_from_disk(config, unit_id)
        if resolved is None:
            message = (
                f"No index found at {index_path}"
                if not index_path.exists()
                else f"No active checkpoint for unit: {unit_id}"
            )
            raise VibesafeCheckpointMissing(message)

        checkpoint_dir, resolved_hash = resolved
        active_hash = resolved_hash or checkpoint_dir.name

        if resolved_hash:
            try:  # Best-effort reconstruction of index
                from datetime import UTC, datetime

                update_index(unit_id, resolved_hash, created=datetime.now(UTC).isoformat())
            except Exception:
                pass

    if checkpoint_dir is None or active_hash is None:
        raise VibesafeCheckpointMissing(f"No active checkpoint for unit: {unit_id}")

    if expected_spec_hash and active_hash:
        mismatch = False
        if len(active_hash) < len(expected_spec_hash):
            mismatch = not expected_spec_hash.startswith(active_hash)
        else:
            mismatch = expected_spec_hash != active_hash

        if mismatch:
            raise VibesafeHashMismatch(
                f"Spec hash mismatch for {unit_id}: active checkpoint targets {active_hash[:10]} "
                f"but current spec hash is {expected_spec_hash[:10]}. "
                f"Run 'vibesafe compile --target {unit_id}' to regenerate."
            )

    if checkpoint_dir is None or not checkpoint_dir.exists():
        raise VibesafeCheckpointMissing(f"Checkpoint directory not found: {checkpoint_dir}")

    # Load implementation
    impl_path = checkpoint_dir / "impl.py"
    if not impl_path.exists():
        raise VibesafeCheckpointMissing(f"Implementation not found: {impl_path}")

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
    func_name = unit_id.split("/")[-1].split(".")[-1]
    if not hasattr(module, func_name):
        raise AttributeError(f"Function {func_name} not found in generated module {impl_path}")

    return cast(Callable[P, R], getattr(module, func_name))


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
        raise VibesafeHashMismatch(
            f"Checkpoint hash mismatch! Expected {stored_chk_hash}, got {computed_chk_hash}"
        )


def _resolve_checkpoint_from_disk(
    config,
    unit_id: str,
) -> tuple[Path, str | None] | None:
    """Best-effort resolution of a checkpoint when the index is missing."""

    checkpoints_base = config.resolve_path(config.paths.checkpoints)
    unit_dir = checkpoints_base / unit_id.replace(".", "/")
    if not unit_dir.exists():
        return None

    candidates = sorted(
        (path for path in unit_dir.iterdir() if path.is_dir()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not candidates:
        return None

    candidate = candidates[0]
    spec_hash = _read_spec_hash(candidate)
    return candidate, spec_hash


def _read_spec_hash(checkpoint_dir: Path) -> str | None:
    """Extract spec hash from a checkpoint directory if metadata is present."""

    meta_path = checkpoint_dir / "meta.toml"
    if not meta_path.exists():
        return None

    with open(meta_path, "rb") as f:
        meta = tomllib.load(f)

    spec_hash = meta.get("spec_sha")
    return spec_hash if isinstance(spec_hash, str) else None


def update_index(unit_id: str, active_hash: str, *, created: str | None = None) -> None:
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
    if created:
        index[unit_id]["created"] = created

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
