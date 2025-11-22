"""
Tests for vibesafe.cli module.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from vibesafe import VibeCoded, __version__, get_unit, vibesafe
from vibesafe.cli import (
    check,
    compile,
    diff,
    install_claude_plugin,
    main,
    mode,
    repl,
    save,
    scan,
    status,
    test,
)


class TestCLI:
    """Tests for CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture(autouse=True)
    def mock_console(self, monkeypatch):
        """Patch the global console object with a MagicMock."""
        mock = MagicMock()
        monkeypatch.setattr("vibesafe.cli.console", mock)
        return mock

    def assert_console_output(self, mock_console, text):
        """Assert that the text was printed to the console."""
        output = "\n".join(
            str(call.args[0]) if call.args else "" for call in mock_console.print.call_args_list
        )
        assert text in output

    def test_main_help(self, runner):
        """Test main command help."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Vibesafe" in result.output

    def test_main_version(self, runner):
        """Test version flag."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_scan_no_units(
        self, runner, temp_dir, monkeypatch, clear_vibesafe_registry, mock_console
    ):
        """Test scan with no units."""
        monkeypatch.chdir(temp_dir)
        result = runner.invoke(scan)
        self.assert_console_output(mock_console, "No vibesafe units found")

    def test_status_no_units(
        self, runner, temp_dir, monkeypatch, clear_vibesafe_registry, mock_console
    ):
        """Test status with no units registered."""
        monkeypatch.chdir(temp_dir)
        result = runner.invoke(status)
        self.assert_console_output(mock_console, "No vibesafe units found")

    def test_diff_no_units(
        self, runner, temp_dir, monkeypatch, clear_vibesafe_registry, mock_console
    ):
        """Test diff with no units registered."""
        monkeypatch.chdir(temp_dir)
        result = runner.invoke(diff)
        self.assert_console_output(mock_console, "No vibesafe units found")

    def test_scan_with_units(
        self, runner, temp_dir, monkeypatch, clear_vibesafe_registry, mock_console
    ):
        """Test scan with registered units."""

        @vibesafe
        def test_func(x: int) -> int:
            """Test."""
            raise VibeCoded()

        monkeypatch.chdir(temp_dir)
        result = runner.invoke(scan)

        if result.exit_code != 0:
            with open("/home/diwank/github.com/julep-ai/vibesafe/debug_cli.txt", "w") as f:
                f.write(f"Output: {result.output}\n")
                f.write(f"Exception: {result.exception}\n")
                import traceback

                traceback.print_tb(result.exc_info[2], file=f)

        assert result.exit_code == 0

    def test_compile_no_units(
        self, runner, temp_dir, monkeypatch, clear_vibesafe_registry, mock_console
    ):
        """Test compile with no units."""
        monkeypatch.chdir(temp_dir)
        result = runner.invoke(compile)
        assert result.exit_code == 1
        self.assert_console_output(mock_console, "No vibesafe units found")

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

    def test_check_help(self, runner):
        """Test check command help."""
        result = runner.invoke(check, ["--help"])
        assert result.exit_code == 0
        assert "lint" in result.output.lower()

    def test_check_runs(
        self,
        runner,
        monkeypatch,
        clear_vibesafe_registry,
        mock_console,
    ):
        """Check command succeeds when helpers succeed."""

        monkeypatch.setattr("vibesafe.cli._import_project_modules", lambda: None)
        monkeypatch.setattr("vibesafe.cli._run_command", lambda cmd: True)
        monkeypatch.setattr("vibesafe.cli.run_all_tests", lambda: {})
        monkeypatch.setattr("vibesafe.cli._detect_drift", lambda: (0, False))

        result = runner.invoke(check)
        assert result.exit_code == 0
        self.assert_console_output(mock_console, "Check complete")

    def test_check_filters_missing_lint_dirs(
        self,
        runner,
        temp_dir,
        monkeypatch,
        clear_vibesafe_registry,
        mock_console,
    ):
        """Check command only lints directories that exist."""

        monkeypatch.chdir(temp_dir)
        (temp_dir / "src").mkdir()

        commands: list[list[str]] = []

        monkeypatch.setattr("vibesafe.cli._import_project_modules", lambda: None)
        monkeypatch.setattr("vibesafe.cli.run_all_tests", lambda: {})
        monkeypatch.setattr("vibesafe.cli._detect_drift", lambda: (0, False))

        def _record_command(cmd: list[str]) -> bool:
            commands.append(cmd)
            return True

        monkeypatch.setattr("vibesafe.cli._run_command", _record_command)

        result = runner.invoke(check)

        assert result.exit_code == 0
        assert commands == [["ruff", "check", "src"]]
        self.assert_console_output(mock_console, "No mypy target found")
        self.assert_console_output(mock_console, "Check complete")

    def test_check_skips_lint_when_no_targets(
        self,
        runner,
        temp_dir,
        monkeypatch,
        clear_vibesafe_registry,
        mock_console,
    ):
        """Check command skips linting when no directories exist."""

        monkeypatch.chdir(temp_dir)

        commands: list[list[str]] = []

        monkeypatch.setattr("vibesafe.cli._import_project_modules", lambda: None)
        monkeypatch.setattr("vibesafe.cli.run_all_tests", lambda: {})
        monkeypatch.setattr("vibesafe.cli._detect_drift", lambda: (0, False))

        def _record_command(cmd: list[str]) -> bool:
            commands.append(cmd)
            return True

        monkeypatch.setattr("vibesafe.cli._run_command", _record_command)

        result = runner.invoke(check)

        assert result.exit_code == 0
        assert commands == []
        self.assert_console_output(mock_console, "No lint targets found")
        self.assert_console_output(mock_console, "No mypy target found")
        self.assert_console_output(mock_console, "Check complete")

    def test_repl_help(self, runner):
        """Test repl command help."""
        result = runner.invoke(repl, ["--help"])
        assert result.exit_code == 0
        assert "Interactive" in result.output

    def test_repl_requires_target(
        self, runner, temp_dir, monkeypatch, clear_vibesafe_registry, mock_console
    ):
        """REPL without --target should exit with guidance."""
        monkeypatch.chdir(temp_dir)
        monkeypatch.setattr("vibesafe.cli._import_project_modules", lambda: None)
        monkeypatch.setattr("vibesafe.cli.get_registry", lambda: {"demo/unit": {}})
        result = runner.invoke(repl)
        assert result.exit_code == 1
        self.assert_console_output(mock_console, "Specify --target")

    def test_repl_unknown_unit(
        self, runner, temp_dir, monkeypatch, clear_vibesafe_registry, mock_console
    ):
        """Unknown unit should be rejected."""
        monkeypatch.chdir(temp_dir)
        monkeypatch.setattr("vibesafe.cli._import_project_modules", lambda: None)
        monkeypatch.setattr(
            "vibesafe.cli.get_registry",
            lambda: {"demo/unit": {}},
        )
        result = runner.invoke(repl, ["--target", "missing/unit"])
        assert result.exit_code == 1
        self.assert_console_output(mock_console, "Unknown unit")

    def test_repl_quit_immediately(
        self,
        runner,
        temp_dir,
        monkeypatch,
        clear_vibesafe_registry,
        mock_console,
    ):
        """REPL processes summary then exits on 'q'."""

        monkeypatch.chdir(temp_dir)
        monkeypatch.setattr("vibesafe.cli._import_project_modules", lambda: None)

        @vibesafe
        def demo_spec(x: int) -> int:
            """Demo.

            >>> demo_spec(1)
            2
            """

            raise VibeCoded()

        unit_id = demo_spec.__vibesafe_unit_id__
        unit_meta = get_unit(unit_id)

        monkeypatch.setattr(
            "vibesafe.cli.get_registry",
            lambda: {unit_id: unit_meta},
        )
        monkeypatch.setattr("vibesafe.cli.get_unit", lambda _: unit_meta)

        result = runner.invoke(repl, ["--target", unit_id], input="q\n")

        if result.exit_code != 0:
            with open("/home/diwank/github.com/julep-ai/vibesafe/debug_cli.txt", "w") as f:
                f.write(f"Output: {result.output}\n")
                f.write(f"Exception: {result.exception}\n")
                import traceback

                traceback.print_tb(result.exc_info[2], file=f)

        assert result.exit_code == 0
        self.assert_console_output(mock_console, "Bye!")

    def test_compile_force_flag(self, runner):
        """Test compile with --force flag."""
        result = runner.invoke(compile, ["--force", "--help"])
        assert result.exit_code == 0

    def test_compile_target_flag(self, runner):
        """Test compile with --target flag."""
        result = runner.invoke(compile, ["--target", "test/unit", "--help"])
        assert result.exit_code == 0

    def test_save_freeze_flag(
        self, runner, temp_dir, monkeypatch, clear_vibesafe_registry, mocker, mock_console
    ):
        """save --freeze-http-deps triggers dependency capture."""

        monkeypatch.chdir(temp_dir)

        @vibesafe
        def example(x: int) -> int:
            """
            Simple doctest.

            >>> example(1)
            1
            """
            raise VibeCoded()

        unit_id = example.__vibesafe_unit_id__

        class _Result:
            passed = True
            failures = 0
            total = 1
            errors: list[str] = []

            def __bool__(self):
                return True

        mocker.patch("vibesafe.cli.test_unit", return_value=_Result())
        mocker.patch("vibesafe.cli.get_registry", return_value={unit_id: {}})
        freeze_called = {}

        def _freeze(units, config):
            freeze_called["units"] = units

        mocker.patch("vibesafe.cli._freeze_http_dependencies", side_effect=_freeze)

        result = runner.invoke(save, ["--target", unit_id, "--freeze-http-deps"])
        assert result.exit_code == 0
        assert unit_id in freeze_called.get("units", [])
        self.assert_console_output(mock_console, "Tests passed")

    def test_mode_set_persists(self, runner, temp_dir, monkeypatch, mock_console):
        """mode --value writes .vibesafe/mode."""
        monkeypatch.chdir(temp_dir)
        result = runner.invoke(mode, ["--value", "prod"])
        assert result.exit_code == 0
        mode_file = Path(temp_dir) / ".vibesafe" / "mode"
        assert mode_file.read_text() == "prod"
        self.assert_console_output(mock_console, "Persisted mode set to 'prod'")

    def test_mode_show_reads_persisted(self, runner, temp_dir, monkeypatch, mock_console):
        """mode (no args) reports effective mode from persisted file."""
        monkeypatch.chdir(temp_dir)
        mode_file = Path(temp_dir) / ".vibesafe" / "mode"
        mode_file.parent.mkdir(parents=True, exist_ok=True)
        mode_file.write_text("dev")

        result = runner.invoke(mode)
        assert result.exit_code == 0
        self.assert_console_output(mock_console, "Effective mode: dev")

    def test_install_claude_plugin_runs_commands(
        self, runner, monkeypatch, mock_console, temp_dir
    ):
        """install-claude-plugin should invoke claude CLI commands."""

        calls = []

        def fake_which(prog: str):
            if prog == "claude":
                return "/usr/bin/claude"
            return None

        def fake_run(cmd, check):
            calls.append(cmd)
            return 0

        monkeypatch.setattr("vibesafe.cli.shutil.which", fake_which)
        monkeypatch.setattr("vibesafe.cli.subprocess.run", fake_run)

        result = runner.invoke(install_claude_plugin)
        assert result.exit_code == 0
        assert len(calls) == 2
        assert "/plugin marketplace add julep-ai/vibesafe" in " ".join(calls[0])
        assert "/plugin install vibesafe@Vibesafe" in " ".join(calls[1])
