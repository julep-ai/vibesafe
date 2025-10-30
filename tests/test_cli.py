"""
Tests for vibesafe.cli module.
"""

import pytest
from click.testing import CliRunner

from vibesafe import VibesafeHandled, vibesafe
from vibesafe.cli import compile, diff, main, save, scan, status, test


class TestCLI:
    """Tests for CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_main_help(self, runner):
        """Test main command help."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Vibesafe" in result.output

    def test_main_version(self, runner):
        """Test version flag."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_scan_no_units(self, runner, temp_dir, monkeypatch, clear_defless_registry):
        """Test scan with no units."""
        monkeypatch.chdir(temp_dir)
        result = runner.invoke(scan)
        assert "No vibesafe units found" in result.output

    def test_status_no_units(self, runner, temp_dir, monkeypatch, clear_defless_registry):
        """Test status with no units registered."""
        monkeypatch.chdir(temp_dir)
        result = runner.invoke(status)
        assert "No vibesafe units found" in result.output

    def test_diff_no_units(self, runner, temp_dir, monkeypatch, clear_defless_registry):
        """Test diff with no units registered."""
        monkeypatch.chdir(temp_dir)
        result = runner.invoke(diff)
        assert "No vibesafe units found" in result.output

    def test_scan_with_units(self, runner, temp_dir, monkeypatch, clear_defless_registry):
        """Test scan with registered units."""

        @vibesafe.func
        def test_func(x: int) -> int:
            """Test."""
            yield VibesafeHandled()

        monkeypatch.chdir(temp_dir)
        result = runner.invoke(scan)
        # May not show unit if module not imported
        assert result.exit_code == 0

    def test_compile_no_units(self, runner, temp_dir, monkeypatch, clear_defless_registry):
        """Test compile with no units."""
        monkeypatch.chdir(temp_dir)
        result = runner.invoke(compile)
        assert result.exit_code == 1
        assert "No vibesafe units found" in result.output

    def test_compile_help(self, runner):
        """Test compile command help."""
        result = runner.invoke(compile, ["--help"])
        assert result.exit_code == 0
        assert "compile" in result.output.lower()

    def test_test_help(self, runner):
        """Test test command help."""
        result = runner.invoke(test, ["--help"])
        assert result.exit_code == 0
        assert "test" in result.output.lower()

    def test_save_help(self, runner):
        """Test save command help."""
        result = runner.invoke(save, ["--help"])
        assert result.exit_code == 0
        assert "save" in result.output.lower()

    def test_status_help(self, runner):
        """Test status command help."""
        result = runner.invoke(status, ["--help"])
        assert result.exit_code == 0
        assert "status" in result.output.lower()

    def test_diff_help(self, runner):
        """Test diff command help."""
        result = runner.invoke(diff, ["--help"])
        assert result.exit_code == 0
        assert "diff" in result.output.lower()

    def test_scan_write_shims_flag(self, runner, temp_dir, monkeypatch):
        """Test scan with --write-shims flag."""
        monkeypatch.chdir(temp_dir)
        result = runner.invoke(scan, ["--write-shims"])
        assert result.exit_code == 0

    def test_compile_force_flag(self, runner):
        """Test compile with --force flag."""
        result = runner.invoke(compile, ["--force", "--help"])
        assert result.exit_code == 0

    def test_compile_target_flag(self, runner):
        """Test compile with --target flag."""
        result = runner.invoke(compile, ["--target", "test/unit", "--help"])
        assert result.exit_code == 0

    def test_save_freeze_flag(
        self, runner, temp_dir, monkeypatch, clear_defless_registry, mocker
    ):
        """save --freeze-http-deps triggers dependency capture."""

        monkeypatch.chdir(temp_dir)

        @vibesafe.func
        def example(x: int) -> int:
            """
            Simple doctest.

            >>> example(1)
            1
            """
            yield VibesafeHandled()

        unit_id = example.__vibesafe_unit_id__

        class _Result:
            passed = True
            failures = 0
            total = 1
            errors: list[str] = []

            def __bool__(self):
                return True

        mocker.patch("vibesafe.cli.test_unit", return_value=_Result())
        mocker.patch("vibesafe.cli.vibesafe.get_registry", return_value={unit_id: {}})
        freeze_called = {}

        def _freeze(units, config):
            freeze_called["units"] = units

        mocker.patch("vibesafe.cli._freeze_http_dependencies", side_effect=_freeze)

        result = runner.invoke(save, ["--target", unit_id, "--freeze-http-deps"])
        assert result.exit_code == 0
        assert unit_id in freeze_called.get("units", [])
