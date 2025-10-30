"""
AST parsing utilities to extract spec components.
"""

import ast
import contextlib
import doctest
import inspect
import linecache
import re
import textwrap
from collections.abc import Callable
from typing import Any


class SpecExtractor:
    """Extract spec components from a function."""

    def __init__(self, func: Callable[..., Any]):
        self.func = func
        raw_source = getattr(func, "__vibesafe_source__", None)
        if raw_source is None:
            raw_source = self._load_source(func)
            func.__vibesafe_source__ = raw_source

        # Dedent source to handle nested definitions or REPL stubs
        self.source = textwrap.dedent(raw_source)
        self.tree = ast.parse(self.source)
        self.module = inspect.getmodule(func)

    @staticmethod
    def _load_source(func: Callable[..., Any]) -> str:
        """Best-effort retrieval of function source code."""

        try:
            return inspect.getsource(func)
        except (OSError, TypeError):
            from_cache = SpecExtractor._source_from_linecache(func)
            if from_cache is not None:
                return from_cache
        return SpecExtractor._synthesized_source(func)

    @staticmethod
    def _source_from_linecache(func: Callable[..., Any]) -> str | None:
        """Attempt to reconstruct source using linecache for interactive sessions."""

        filename = inspect.getsourcefile(func) or func.__code__.co_filename
        if not filename:
            return None

        lines = linecache.getlines(filename)
        if not lines:
            return None

        lineno = func.__code__.co_firstlineno
        if lineno <= 0 or lineno > len(lines):
            return None

        block = inspect.getblock(lines[lineno - 1 :])
        if not block:
            return None

        return "".join(block)

    @staticmethod
    def _synthesized_source(func: Callable[..., Any]) -> str:
        """Fallback source stub when real source is unavailable."""

        signature = inspect.signature(func)
        prefix = "async def" if inspect.iscoroutinefunction(func) else "def"
        return f"{prefix} {func.__name__}{signature}:\n    ...\n"

    def extract_signature(self) -> str:
        """
        Extract function signature as a string.

        Returns:
            Signature string (e.g., "def foo(a: int, b: str) -> int")
        """
        sig = inspect.signature(self.func)
        name = self.func.__name__

        # Build parameter string
        params = []
        for param_name, param in sig.parameters.items():
            param_str = param_name
            if param.annotation != inspect.Parameter.empty:
                # Get annotation string
                anno = param.annotation
                if hasattr(anno, "__name__"):
                    param_str += f": {anno.__name__}"
                else:
                    param_str += f": {anno}"
            if param.default != inspect.Parameter.empty:
                param_str += f" = {param.default!r}"
            params.append(param_str)

        param_str = ", ".join(params)

        # Build return annotation
        return_anno = ""
        if sig.return_annotation != inspect.Signature.empty:
            ret = sig.return_annotation
            return_anno = f" -> {ret.__name__}" if hasattr(ret, "__name__") else f" -> {ret}"

        # Check if async
        prefix = "async def" if inspect.iscoroutinefunction(self.func) else "def"

        return f"{prefix} {name}({param_str}){return_anno}"

    def extract_docstring(self) -> str:
        """
        Extract docstring from function.

        Returns:
            Docstring or empty string if none
        """
        doc = inspect.getdoc(self.func)
        return doc or ""

    def extract_hypothesis_blocks(self) -> list[str]:
        """Extract fenced hypothesis blocks from the docstring."""

        doc = self.extract_docstring()
        if not doc:
            return []

        pattern = re.compile(r"```hypothesis\n(.*?)\n```", re.IGNORECASE | re.DOTALL)
        blocks = []
        for match in pattern.findall(doc):
            blocks.append(textwrap.dedent(match).strip())
        return blocks

    def extract_body_before_handled(self) -> str:
        """
        Extract function body code before VibesafeHandled() marker.

        Returns:
            Code string before yield/return VibesafeHandled()
        """
        source_lines = self.source.split("\n")

        # Find the function definition line
        func_def_line = 0
        for i, line in enumerate(source_lines):
            if "def " in line and self.func.__name__ in line:
                func_def_line = i
                break

        # Find body start (after docstring if present)
        body_start = func_def_line + 1

        # Skip docstring
        if self.func.__doc__:
            in_docstring = False
            for i in range(func_def_line + 1, len(source_lines)):
                line = source_lines[i].strip()
                if '"""' in line or "'''" in line:
                    if not in_docstring:
                        in_docstring = True
                        if line.count('"""') == 2 or line.count("'''") == 2:
                            # Single line docstring
                            body_start = i + 1
                            break
                    else:
                        body_start = i + 1
                        break

        # Extract body lines before VibesafeHandled
        body_lines = []
        sentinel_markers = {
            "pass",
            "...",
            "return ...",
            "return Ellipsis",
        }

        for i in range(body_start, len(source_lines)):
            line = source_lines[i]
            stripped = line.strip()
            if "VibesafeHandled" in stripped or stripped in sentinel_markers:
                break
            # Only include lines with actual content (strip empty/whitespace)
            if stripped:
                body_lines.append(line)

        # Join and dedent
        body_code = "\n".join(body_lines)
        with contextlib.suppress(Exception):
            body_code = inspect.cleandoc(body_code)

        return body_code

    def extract_doctests(self) -> list[doctest.Example]:
        """
        Extract doctest examples from docstring.

        Returns:
            List of doctest Example objects
        """
        docstring = self.extract_docstring()
        if not docstring:
            return []

        parser = doctest.DocTestParser()
        try:
            examples = parser.get_examples(docstring)
            return examples
        except Exception:
            return []

    def extract_dependencies(self) -> dict[str, str]:
        """
        Extract static dependencies (names referenced in spec body).

        Returns:
            Dictionary mapping name -> source code (if available)
        """
        body_code = self.extract_body_before_handled()
        if not body_code or self.module is None:
            return {}

        try:
            body_tree = ast.parse(textwrap.dedent(body_code))
        except SyntaxError:
            return {}

        names: set[str] = set()

        class _NameCollector(ast.NodeVisitor):
            def visit_Name(self, node: ast.Name) -> None:  # type: ignore[override]
                if isinstance(node.ctx, ast.Load):
                    names.add(node.id)
                self.generic_visit(node)

        _NameCollector().visit(body_tree)

        module_dict = getattr(self.module, "__dict__", {})
        dependencies: dict[str, str] = {}

        for name in sorted(names):
            if name == self.func.__name__:
                continue
            if name in module_dict:
                obj = module_dict[name]
                try:
                    source = inspect.getsource(obj)
                except (OSError, TypeError):
                    continue
                dependencies[name] = textwrap.dedent(source).strip()

        return dependencies

    def to_dict(self) -> dict[str, Any]:
        """
        Extract all spec components as a dictionary.

        Returns:
            Dictionary with signature, docstring, body, doctests, etc.
        """
        return {
            "signature": self.extract_signature(),
            "docstring": self.extract_docstring(),
            "body_before_handled": self.extract_body_before_handled(),
            "doctests": self.extract_doctests(),
            "hypothesis_blocks": self.extract_hypothesis_blocks(),
            "dependencies": self.extract_dependencies(),
            "source": self.source,
        }


def extract_spec(func: Callable[..., Any]) -> dict[str, Any]:
    """
    Convenience function to extract spec from a function.

    Args:
        func: Function to extract spec from

    Returns:
        Dictionary with spec components
    """
    extractor = SpecExtractor(func)
    return extractor.to_dict()
