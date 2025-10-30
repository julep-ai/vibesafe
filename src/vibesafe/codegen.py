"""
Code generation orchestration - prompt rendering and LLM calls.
"""

import platform
import sys
import textwrap
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from jinja2 import Environment, FileSystemLoader

from vibesafe import __version__
from vibesafe.ast_parser import extract_spec
from vibesafe.config import get_config
from vibesafe.exceptions import (
    VibesafeMissingDoctest,
    VibesafeProviderError,
    VibesafeValidationError,
)
from vibesafe.hashing import (
    compute_checkpoint_hash,
    compute_dependency_digest,
    compute_prompt_hash,
    compute_spec_hash,
    hash_code,
)
from vibesafe.providers import get_provider


class CodeGenerator:
    """Orchestrates code generation from spec to checkpoint."""

    def __init__(self, unit_id: str, unit_meta: dict[str, Any]):
        self.unit_id = unit_id
        self.unit_meta = unit_meta
        self.config = get_config()

        # Get provider config
        provider_name = unit_meta.get("provider") or "default"
        self.provider_config = self.config.get_provider(provider_name)
        self.provider = get_provider(provider_name)

        # Extract spec
        self.func = unit_meta["func"]
        self.spec = extract_spec(self.func)

    def generate(self, force: bool = False, allow_missing_doctest: bool = False) -> dict[str, Any]:
        """
        Generate implementation for this unit.

        Args:
            force: Force regeneration even if checkpoint exists

        Returns:
            Dictionary with checkpoint info (spec_hash, chk_hash, path, etc.)
        """
        if not self.spec["doctests"] and not allow_missing_doctest:
            raise VibesafeMissingDoctest(
                f"Spec {self.unit_id} does not declare any doctests; add at least one example."
            )

        # Compute spec hash
        spec_hash = self._compute_spec_hash()

        # Check if checkpoint already exists
        checkpoint_dir = self._get_checkpoint_dir(spec_hash)
        if checkpoint_dir.exists() and not force:
            # Load existing checkpoint
            return self._load_checkpoint_meta(checkpoint_dir)

        # Render prompt
        prompt = self._render_prompt()
        prompt_hash = compute_prompt_hash(prompt)

        # Call LLM
        generated_code = self._generate_code(prompt, spec_hash)
        self._validate_generated_code(generated_code)

        # Compute checkpoint hash
        chk_hash = compute_checkpoint_hash(spec_hash, prompt_hash, generated_code)

        # Save checkpoint
        checkpoint_info = self._save_checkpoint(spec_hash, chk_hash, prompt_hash, generated_code)

        return checkpoint_info

    def _compute_spec_hash(self) -> str:
        """Compute spec hash for this unit."""
        template_id = self.unit_meta.get("template", "function.j2")
        provider_model = self.provider_config.model
        dependency_digest = compute_dependency_digest(self.spec["dependencies"])
        provider_params = {
            "temperature": self.provider_config.temperature,
            "seed": self.provider_config.seed,
            "timeout": self.provider_config.timeout,
        }

        return compute_spec_hash(
            signature=self.spec["signature"],
            docstring=self.spec["docstring"],
            body_before_handled=self.spec["body_before_handled"],
            template_id=template_id,
            provider_model=provider_model,
            provider_params=provider_params,
            dependency_digest=dependency_digest,
        )

    def _render_prompt(self) -> str:
        """Render prompt from template."""
        template_path = self.unit_meta.get("template") or self.config.prompts.function
        if self.unit_meta.get("type") == "http":
            template_path = self.unit_meta.get("template") or self.config.prompts.http

        # Resolve template path
        template_file = Path(template_path)
        if not template_file.is_absolute():
            template_file = Path.cwd() / template_file

        if not template_file.exists():
            # Try relative to package
            pkg_dir = Path(__file__).parent.parent.parent
            template_file = pkg_dir / template_path

        if not template_file.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        # Load template
        template_dir = template_file.parent
        template_name = template_file.name

        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_name)

        # Render with context
        context = {
            "signature": self.spec["signature"],
            "docstring": self.spec["docstring"],
            "body_before_handled": self.spec["body_before_handled"],
            "doctests": self.spec["doctests"],
            "dependencies": self.spec["dependencies"],
            "unit_id": self.unit_id,
            "unit_meta": self.unit_meta,
            "vibesafe_version": __version__,
        }

        return template.render(**context)

    def _generate_code(self, prompt: str, spec_hash: str) -> str:
        """Call LLM to generate code."""
        seed = self.provider_config.seed
        try:
            generated = self.provider.complete(prompt=prompt, seed=seed, spec_hash=spec_hash)
        except Exception as exc:  # pragma: no cover - provider errors are environment-specific
            raise VibesafeProviderError(f"Provider request failed: {exc}") from exc
        return self._clean_generated_code(generated)

    def _clean_generated_code(self, code: str) -> str:
        """
        Clean generated code by removing markdown code blocks and extra whitespace.

        Args:
            code: Raw generated code that may contain markdown formatting

        Returns:
            Clean Python code
        """
        # Remove markdown code blocks if present
        lines = code.strip().split("\n")

        # Check if the code is wrapped in markdown code blocks
        if lines and lines[0].strip().startswith("```"):
            # Find the start and end of the code block
            start_idx = 1  # Skip the opening ```python or ```
            end_idx = len(lines)

            # Find the closing ```
            for i in range(len(lines) - 1, 0, -1):
                if lines[i].strip() == "```":
                    end_idx = i
                    break

            # Extract just the code between the markers
            code = "\n".join(lines[start_idx:end_idx])

        # Strip trailing whitespace from each line (for linting)
        lines = code.strip().split("\n")
        lines = [line.rstrip() for line in lines]
        return "\n".join(lines)

    def _validate_generated_code(self, code: str) -> None:
        """
        Perform basic validation on generated code.

        Ensures the implementation defines the expected function name.
        """
        func_name = self.func.__name__
        signature_token = f"def {func_name}"
        if signature_token not in code:
            raise VibesafeValidationError(
                f"Generated code for {self.unit_id} is missing definition '{signature_token}'."
            )

    def _get_checkpoint_dir(self, spec_hash: str) -> Path:
        """Get checkpoint directory for a spec hash."""
        checkpoints_base = self.config.resolve_path(self.config.paths.checkpoints)
        # Convert unit_id (app.math.ops/sum_str) to path
        unit_path = self.unit_id.replace(".", "/")
        return checkpoints_base / unit_path / spec_hash[:16]

    def _save_checkpoint(
        self, spec_hash: str, chk_hash: str, prompt_hash: str, generated_code: str
    ) -> dict[str, Any]:
        """Save checkpoint to disk."""
        checkpoint_dir = self._get_checkpoint_dir(spec_hash)
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Write implementation
        impl_path = checkpoint_dir / "impl.py"
        # Ensure code ends with a newline for linting
        code_with_newline = (
            generated_code if generated_code.endswith("\n") else generated_code + "\n"
        )
        impl_path.write_text(code_with_newline)

        # Write metadata
        created_at = datetime.now(UTC).isoformat()
        meta_path = checkpoint_dir / "meta.toml"
        template_id = self.unit_meta.get("template", "prompts/function.j2")
        dependency_digest = compute_dependency_digest(self.spec["dependencies"])
        signature_text = self.spec["signature"]
        docstring_text = self.spec["docstring"] or ""
        body_before = self.spec["body_before_handled"] or ""
        meta_content = textwrap.dedent(
            f"""\
            # Vibesafe checkpoint metadata
            created = "{created_at}"
            python = "{platform.python_version()}"
            env = "{self.config.project.env}"
            spec_sha = "{spec_hash}"
            chk_sha = "{chk_hash}"
            prompt_sha = "{prompt_hash}"
            vibesafe_version = "{__version__}"
            provider = "{self.provider_config.kind}:{self.provider_config.model}"
            template = "{template_id}"
            provider_temperature = {self.provider_config.temperature}
            provider_seed = {self.provider_config.seed}
            provider_timeout = {self.provider_config.timeout}

            [hash_inputs]
            signature_sha = "{hash_code(signature_text)}"
            docstring_sha = "{hash_code(docstring_text)}"
            body_sha = "{hash_code(body_before)}"
            dependency_digest = "{dependency_digest}"
            template_id = "{template_id}"
            provider_model = "{self.provider_config.model}"

            [signature]
            text = '''{signature_text}'''

            [docstring]
            text = '''{docstring_text}'''
            """
        )
        meta_path.write_text(meta_content)

        return {
            "spec_hash": spec_hash,
            "chk_hash": chk_hash,
            "prompt_hash": prompt_hash,
            "checkpoint_dir": checkpoint_dir,
            "impl_path": impl_path,
            "meta_path": meta_path,
            "created_at": created_at,
        }

    def _load_checkpoint_meta(self, checkpoint_dir: Path) -> dict[str, Any]:
        """Load metadata from existing checkpoint."""
        meta_path = checkpoint_dir / "meta.toml"
        with open(meta_path, "rb") as f:
            meta = tomllib.load(f)

        return {
            "spec_hash": meta["spec_sha"],
            "chk_hash": meta["chk_sha"],
            "prompt_hash": meta["prompt_sha"],
            "checkpoint_dir": checkpoint_dir,
            "impl_path": checkpoint_dir / "impl.py",
            "meta_path": meta_path,
        }


def generate_for_unit(
    unit_id: str, force: bool = False, allow_missing_doctest: bool = False
) -> dict[str, Any]:
    """
    Generate code for a specific unit.

    Args:
        unit_id: Unit identifier (e.g., "app.math.ops/sum_str")
        force: Force regeneration

    Returns:
        Checkpoint info dictionary
    """
    from vibesafe.core import vibesafe

    unit_meta = vibesafe.get_unit(unit_id)
    if not unit_meta:
        raise ValueError(f"Unit not found: {unit_id}")

    generator = CodeGenerator(unit_id, unit_meta)
    return generator.generate(force=force, allow_missing_doctest=allow_missing_doctest)
