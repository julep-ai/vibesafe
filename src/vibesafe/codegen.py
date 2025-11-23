"""
Code generation orchestration - prompt rendering and LLM calls.
"""

import ast
import inspect
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
from vibesafe.config import get_config, resolve_template_id
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

    def generate(
        self,
        force: bool = False,
        allow_missing_doctest: bool = False,
        feedback: str | None = None,
        previous_response_id: str | None = None,
        previous_reasoning_details: dict | None = None,
        debug: bool = False,
    ) -> dict[str, Any]:
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

        # Render prompt base
        base_prompt = self._render_prompt()
        last_prompt: str | None = None

        # Retry loop for validation errors (e.g. SyntaxError)
        max_retries = 3
        current_feedback = feedback

        for attempt in range(max_retries + 1):
            # Construct prompt with feedback
            prompt = base_prompt
            if current_feedback:
                prompt = (
                    f"{base_prompt}\n\n---\nPrevious attempt failed with:\n{current_feedback}\n"
                    "Please fix the issues above and output only the corrected implementation."
                )

            last_prompt = prompt
            prompt_hash = compute_prompt_hash(prompt)

            try:
                # Call LLM
                generated_code = self._generate_code(
                    prompt,
                    spec_hash,
                    previous_response_id=previous_response_id,
                    previous_reasoning_details=previous_reasoning_details,
                )
                self._validate_generated_code(generated_code)

                # Compute checkpoint hash
                chk_hash = compute_checkpoint_hash(spec_hash, prompt_hash, generated_code)

                # Save checkpoint
                checkpoint_info = self._save_checkpoint(
                    spec_hash, chk_hash, prompt_hash, generated_code
                )

                # Attach provider metadata so callers can chain reasoning-aware retries
                checkpoint_info["response_id"] = getattr(
                    self.provider, "last_metadata", {}
                ).response_id
                checkpoint_info["reasoning_details"] = getattr(
                    getattr(self.provider, "last_metadata", None), "reasoning_details", None
                )

                if debug:
                    checkpoint_info["debug_prompt"] = last_prompt
                    checkpoint_info["debug_output"] = generated_code

                return checkpoint_info

            except VibesafeValidationError as exc:
                if attempt < max_retries:
                    # Prepare feedback for next attempt
                    current_feedback = f"Generated code was invalid: {exc}"

                    # Update context for chaining if available
                    if hasattr(self.provider, "last_metadata"):
                        previous_response_id = getattr(
                            self.provider.last_metadata, "response_id", previous_response_id
                        )
                        previous_reasoning_details = getattr(
                            self.provider.last_metadata,
                            "reasoning_details",
                            previous_reasoning_details,
                        )
                    continue
                raise exc

        # This point should never be reached because successful generation returns
        # and failures either retry or raise. Keep an explicit guard for type-checkers
        # and clearer runtime diagnostics.
        raise VibesafeValidationError(
            f"Failed to generate code for {self.unit_id} after {max_retries + 1} attempts."
        )

    def _compute_spec_hash(self) -> str:
        """Compute spec hash for this unit."""
        template_id = resolve_template_id(
            self.unit_meta,
            self.config,
            spec_type=self.spec.get("type"),
        )
        provider_model = self.provider_config.model
        dependency_digest = compute_dependency_digest(self.spec["dependencies"])
        provider_params: dict[str, str | int | float] = {
            "seed": self.provider_config.seed,
            "timeout": self.provider_config.timeout,
        }
        if self.provider_config.reasoning_effort:
            provider_params["reasoning_effort"] = self.provider_config.reasoning_effort

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
        template_path = resolve_template_id(
            self.unit_meta,
            self.config,
            spec_type=self.spec.get("type"),
        )

        # Resolve template path
        template_file = Path(template_path)
        if not template_file.is_absolute():
            template_file = Path.cwd() / template_file

        if not template_file.exists():
            # TODO(prototype): switch to importlib.resources for packaged templates to avoid path drift.
            # Try relative to package
            # vibesafe/codegen.py -> vibesafe/ -> src/ -> root
            # We want to look inside the package, so we need to find where 'vibesafe' package is installed
            # If template_path is 'vibesafe/templates/function.j2', we should look for it relative to site-packages or src

            # Try finding it relative to this file's parent (vibesafe package root)
            # If template_path starts with 'vibesafe/', strip it to avoid duplication if we are already in vibesafe dir

            current_file_dir = Path(__file__).parent

            # Case 1: template_path is like "vibesafe/templates/function.j2"
            # and we are in ".../site-packages/vibesafe"
            # We want ".../site-packages/vibesafe/templates/function.j2"

            if template_path.startswith("vibesafe/"):
                rel_path = template_path.replace("vibesafe/", "", 1)
                candidate = current_file_dir / rel_path
                if candidate.exists():
                    template_file = candidate

            if not template_file.exists():
                # Fallback: allow configured top-level prompts/ paths to resolve to packaged templates
                candidate = current_file_dir / "templates" / Path(template_path).name
                if candidate.exists():
                    template_file = candidate

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
            "spec_type": self.spec.get("type"),
            "module_name": self.unit_meta.get("module", ""),
            "file_path": inspect.getfile(self.func),
        }

        return template.render(**context)

    def _generate_code(
        self,
        prompt: str,
        spec_hash: str,
        *,
        previous_response_id: str | None = None,
        previous_reasoning_details: dict | None = None,
    ) -> str:
        """Call LLM to generate code."""
        seed = self.provider_config.seed
        try:
            generated = self.provider.complete(
                prompt=prompt,
                seed=seed,
                spec_hash=spec_hash,
                previous_response_id=previous_response_id,
                reasoning_details=previous_reasoning_details,
            )
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
        lines = code.strip().split("\n")

        # Find start of code block
        start_idx = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("```"):
                start_idx = i
                break

        # If code block found
        if start_idx != -1:
            # Find end of code block
            end_idx = -1
            for i in range(len(lines) - 1, start_idx, -1):
                if lines[i].strip().startswith("```"):
                    end_idx = i
                    break

            if end_idx != -1:
                # Extract code between markers
                # start_idx + 1 to skip the opening ```
                code = "\n".join(lines[start_idx + 1 : end_idx])
            else:
                # Unclosed block? Take everything after start
                code = "\n".join(lines[start_idx + 1 :])

        # Strip trailing whitespace from each line (for linting)
        lines = code.strip().split("\n")
        lines = [line.rstrip() for line in lines]
        return "\n".join(lines)

    def _validate_generated_code(self, code: str) -> None:
        """
        Perform basic validation on generated code.

        Ensures the implementation defines the expected function name,
        matches async/sync, and preserves the parameter signature shape.
        """
        func_name = self.func.__name__

        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            raise VibesafeValidationError(
                f"Generated code for {self.unit_id} is not valid Python: {exc}"
            ) from exc

        fn_node = None
        is_async_impl = False
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                fn_node = node
                break
            if isinstance(node, ast.AsyncFunctionDef) and node.name == func_name:
                fn_node = node
                is_async_impl = True
                break

        if fn_node is None:
            raise VibesafeValidationError(
                f"Generated code for {self.unit_id} is missing definition '{func_name}'."
            )

        expected_async = inspect.iscoroutinefunction(self.func)
        if expected_async != is_async_impl:
            mode = "async" if expected_async else "sync"
            raise VibesafeValidationError(
                f"Generated implementation for {self.unit_id} must be {mode} to match the spec."
            )

        expected_sig = inspect.signature(self.func)
        generated_sig = self._signature_from_ast(fn_node)

        if generated_sig != self._signature_to_shape(expected_sig):
            raise VibesafeValidationError(
                f"Generated signature for {self.unit_id} does not match spec. "
                f"expected={self._signature_to_shape(expected_sig)}, got={generated_sig}"
            )

    # ----------------- Signature utilities -----------------
    def _signature_from_ast(
        self, fn_node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> list[tuple[str, str]]:
        """Return a lightweight shape of the function signature."""
        args = fn_node.args
        shape: list[tuple[str, str]] = []

        for arg in args.posonlyargs:
            shape.append((arg.arg, "posonly"))
        for arg in args.args:
            shape.append((arg.arg, "poskw"))
        if args.vararg:
            shape.append((args.vararg.arg, "vararg"))
        for arg in args.kwonlyargs:
            shape.append((arg.arg, "kwonly"))
        if args.kwarg:
            shape.append((args.kwarg.arg, "varkw"))
        return shape

    def _signature_to_shape(self, sig: inspect.Signature) -> list[tuple[str, str]]:
        """Convert an inspect.Signature to the same lightweight shape."""
        mapping = {
            inspect.Parameter.POSITIONAL_ONLY: "posonly",
            inspect.Parameter.POSITIONAL_OR_KEYWORD: "poskw",
            inspect.Parameter.VAR_POSITIONAL: "vararg",
            inspect.Parameter.KEYWORD_ONLY: "kwonly",
            inspect.Parameter.VAR_KEYWORD: "varkw",
        }
        shape: list[tuple[str, str]] = []
        for param in sig.parameters.values():
            shape.append((param.name, mapping[param.kind]))
        return shape

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
        template_id = resolve_template_id(
            self.unit_meta,
            self.config,
            spec_type=self.spec.get("type"),
        )
        dependency_digest = compute_dependency_digest(self.spec["dependencies"])
        signature_text = self.spec["signature"]
        docstring_text = self.spec["docstring"] or ""
        body_before = self.spec["body_before_handled"] or ""
        reasoning_line = ""
        if self.provider_config.reasoning_effort:
            reasoning_line = (
                f'reasoning_effort = "{self.provider_config.reasoning_effort}"\n            '
            )

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
            {reasoning_line}provider_seed = {self.provider_config.seed}
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
    unit_id: str,
    force: bool = False,
    allow_missing_doctest: bool = False,
    feedback: str | None = None,
    previous_response_id: str | None = None,
    previous_reasoning_details: dict | None = None,
    debug: bool = False,
) -> dict[str, Any]:
    """
    Generate code for a specific unit.

    Args:
        unit_id: Unit identifier (e.g., "app.math.ops/sum_str")
        force: Force regeneration

    Returns:
        Checkpoint info dictionary
    """
    from vibesafe.core import get_unit

    unit_meta = get_unit(unit_id)
    if not unit_meta:
        raise ValueError(f"Unit not found: {unit_id}")

    generator = CodeGenerator(unit_id, unit_meta)
    return generator.generate(
        force=force,
        allow_missing_doctest=allow_missing_doctest,
        feedback=feedback,
        previous_response_id=previous_response_id,
        previous_reasoning_details=previous_reasoning_details,
        debug=debug,
    )
