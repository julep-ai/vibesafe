"""
Hash computation for specs and checkpoints.
"""

import hashlib
import inspect

from vibesafe import __version__


def compute_spec_hash(
    signature: str,
    docstring: str,
    body_before_handled: str,
    template_id: str,
    provider_model: str,
    dependency_digest: str = "",
) -> str:
    """
    Compute hash of a spec definition.

    H_spec = sha256(
        signature
        + normalized_docstring
        + body_before_VibesafeHandled
        + vibesafe_version
        + template_id
        + provider_model
        + dependency_digest
    )

    Args:
        signature: Function signature string
        docstring: Normalized docstring
        body_before_handled: Code before VibesafeHandled() marker
        template_id: Template identifier (e.g., "function.j2")
        provider_model: Provider model string (e.g., "gpt-4o-mini")
        dependency_digest: Hash of dependencies

    Returns:
        Hex digest of spec hash
    """
    components = [
        signature,
        normalize_docstring(docstring),
        body_before_handled.strip(),
        __version__,
        template_id,
        provider_model,
        dependency_digest,
    ]

    combined = "\n---\n".join(components)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def compute_checkpoint_hash(spec_hash: str, prompt_hash: str, generated_code: str) -> str:
    """
    Compute hash of a checkpoint.

    H_chk = sha256(H_spec + prompt_hash + generated_code)

    Args:
        spec_hash: Hash of the spec
        prompt_hash: Hash of the rendered prompt
        generated_code: Generated implementation code

    Returns:
        Hex digest of checkpoint hash
    """
    combined = f"{spec_hash}\n{prompt_hash}\n{generated_code}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def compute_prompt_hash(prompt: str) -> str:
    """
    Compute hash of a rendered prompt.

    Args:
        prompt: Rendered prompt string

    Returns:
        Hex digest of prompt hash
    """
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def compute_dependency_digest(dependencies: dict[str, str]) -> str:
    """
    Compute digest of function dependencies.

    Args:
        dependencies: Map of name -> source code

    Returns:
        Hex digest of combined dependencies
    """
    if not dependencies:
        return ""

    # Sort by name for consistency
    sorted_deps = sorted(dependencies.items())
    combined = "\n".join(f"{name}:\n{source}" for name, source in sorted_deps)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def normalize_docstring(docstring: str) -> str:
    """
    Normalize a docstring for consistent hashing.

    - Strips leading/trailing whitespace
    - Normalizes internal whitespace
    - Uses inspect.cleandoc for consistent formatting

    Args:
        docstring: Raw docstring

    Returns:
        Normalized docstring
    """
    if not docstring:
        return ""
    return inspect.cleandoc(docstring).strip()


def short_hash(full_hash: str, length: int = 8) -> str:
    """
    Get short version of hash for display.

    Args:
        full_hash: Full hash string
        length: Number of characters to include

    Returns:
        Shortened hash
    """
    return full_hash[:length]


def hash_code(code: str) -> str:
    """
    Compute hash of arbitrary code string.

    Args:
        code: Source code string

    Returns:
        Hex digest
    """
    return hashlib.sha256(code.encode("utf-8")).hexdigest()
