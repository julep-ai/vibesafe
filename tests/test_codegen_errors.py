"""Tests for error handling paths in vibesafe.codegen."""

import pytest

from vibesafe import VibeCoded, get_unit, vibesafe
from vibesafe.codegen import CodeGenerator
from vibesafe.exceptions import (
    VibesafeMissingDoctest,
    VibesafeProviderError,
    VibesafeValidationError,
)


@pytest.mark.usefixtures("clear_defless_registry")
class TestCodegenErrors:
    """Ensure CodeGenerator raises SPEC-aligned exceptions."""

    def test_missing_doctest_error(self, test_config, temp_dir, monkeypatch, mocker):
        """Generating a unit without doctests should raise VibesafeMissingDoctest."""
        self._prepare_config(monkeypatch, test_config, temp_dir)

        @vibesafe
        def no_doctest(x: int) -> int:
            """Docstring without doctest examples."""
            raise VibeCoded()

        unit_id = no_doctest.__vibesafe_unit_id__
        unit_meta = get_unit(unit_id)

        mocker.patch("vibesafe.codegen.get_provider")

        generator = CodeGenerator(unit_id, unit_meta)

        with pytest.raises(VibesafeMissingDoctest):
            generator.generate()

    def test_provider_error_wrapped(self, test_config, temp_dir, monkeypatch, mocker):
        """Provider failures are wrapped in VibesafeProviderError."""
        self._prepare_config(monkeypatch, test_config, temp_dir)

        @vibesafe
        def has_doctest(x: int) -> int:
            """
            Simple function.

            >>> has_doctest(1)
            1
            """
            raise VibeCoded()

        unit_id = has_doctest.__vibesafe_unit_id__
        unit_meta = get_unit(unit_id)

        mock_provider = mocker.MagicMock()
        mock_provider.complete.side_effect = RuntimeError("boom")
        mocker.patch("vibesafe.codegen.get_provider", return_value=mock_provider)

        generator = CodeGenerator(unit_id, unit_meta)

        with pytest.raises(VibesafeProviderError):
            generator.generate(force=True)

    def test_validation_error_on_missing_function(self, test_config, temp_dir, monkeypatch, mocker):
        """Generated code that omits the expected function triggers VibesafeValidationError."""
        self._prepare_config(monkeypatch, test_config, temp_dir)

        @vibesafe
        def spec_with_doctest(x: int) -> int:
            """
            Spec with doctest.

            >>> spec_with_doctest(2)
            2
            """
            raise VibeCoded()

        unit_id = spec_with_doctest.__vibesafe_unit_id__
        unit_meta = get_unit(unit_id)

        mock_provider = mocker.MagicMock()
        mock_provider.complete.return_value = "# generated with no function"
        mocker.patch("vibesafe.codegen.get_provider", return_value=mock_provider)

        generator = CodeGenerator(unit_id, unit_meta)

        with pytest.raises(VibesafeValidationError):
            generator.generate(force=True)

    @staticmethod
    def _prepare_config(monkeypatch, test_config, temp_dir):
        monkeypatch.chdir(temp_dir)
        from vibesafe import config as config_module

        config_module._config = test_config
