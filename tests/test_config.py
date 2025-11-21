"""
Tests for vibesafe.config module.
"""

from pathlib import Path

import pytest

from vibesafe.config import (
    PathsConfig,
    ProjectConfig,
    PromptsConfig,
    ProviderConfig,
    SandboxConfig,
    VibesafeConfig,
    get_config,
)


class TestProviderConfig:
    """Tests for ProviderConfig."""

    def test_default_values(self):
        """Test provider config with default values."""
        config = ProviderConfig()
        assert config.kind == "openai-compatible"
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.0
        assert config.seed == 42
        assert config.timeout == 60

    def test_custom_values(self):
        """Test provider config with custom values."""
        config = ProviderConfig(
            kind="custom",
            model="gpt-4",
            temperature=0.5,
            seed=100,
            timeout=120,
        )
        assert config.kind == "custom"
        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.seed == 100
        assert config.timeout == 120


class TestPathsConfig:
    """Tests for PathsConfig."""

    def test_default_paths(self):
        """Test default path configuration."""
        config = PathsConfig()
        assert config.checkpoints == ".vibesafe/checkpoints"
        assert config.cache == ".vibesafe/cache"
        assert config.index == ".vibesafe/index.toml"
        assert config.generated == "__generated__"

    def test_custom_paths(self):
        """Test custom path configuration."""
        config = PathsConfig(
            checkpoints="custom/checkpoints",
            cache="custom/cache",
            index="custom/index.toml",
            generated="custom/generated",
        )
        assert config.checkpoints == "custom/checkpoints"
        assert config.cache == "custom/cache"


class TestPromptsConfig:
    """Tests for PromptsConfig."""

    def test_default_prompts(self):
        """Test default prompt paths."""
        config = PromptsConfig()
        assert config.function == "prompts/function.j2"
        assert config.http == "prompts/http_endpoint.j2"
        assert config.cli == "prompts/cli_command.j2"


class TestProjectConfig:
    """Tests for ProjectConfig."""

    def test_default_project(self):
        """Test default project configuration."""
        config = ProjectConfig()
        assert config.python == ">=3.12"
        assert config.env == "dev"

    def test_prod_env(self):
        """Test production environment."""
        config = ProjectConfig(env="prod")
        assert config.env == "prod"


class TestSandboxConfig:
    """Tests for SandboxConfig."""

    def test_default_sandbox(self):
        """Test default sandbox configuration."""
        config = SandboxConfig()
        assert config.enabled is False
        assert config.timeout == 10
        assert config.memory_mb == 256

    def test_enabled_sandbox(self):
        """Test enabled sandbox."""
        config = SandboxConfig(enabled=True, timeout=30, memory_mb=512)
        assert config.enabled is True
        assert config.timeout == 30
        assert config.memory_mb == 512


class TestVibesafeConfig:
    """Tests for VibesafeConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = VibesafeConfig()
        assert config.project.env == "dev"
        assert "default" in config.provider
        assert config.paths.checkpoints == ".vibesafe/checkpoints"

    def test_load_from_file(self, config_file: Path):
        """Test loading configuration from file."""
        config = VibesafeConfig.load(config_file)
        assert config.project.python == ">=3.12"
        assert config.provider["default"].model == "gpt-4o-mini"
        assert config.paths.checkpoints == ".vibesafe/checkpoints"

    def test_load_nonexistent_file_returns_default(self, temp_dir: Path):
        """Test loading nonexistent file returns default config."""
        nonexistent = temp_dir / "nonexistent.toml"
        config = VibesafeConfig.load(nonexistent)
        assert config.project.env == "dev"

    def test_get_provider_default(self, test_config: VibesafeConfig):
        """Test getting default provider."""
        provider = test_config.get_provider()
        assert provider.model == "gpt-4o-mini"
        assert provider.kind == "openai-compatible"

    def test_get_provider_by_name(self, test_config: VibesafeConfig):
        """Test getting provider by name falls back to default."""
        provider = test_config.get_provider("nonexistent")
        assert provider.model == "gpt-4o-mini"

    def test_get_api_key(self, test_config: VibesafeConfig, monkeypatch: pytest.MonkeyPatch):
        """Test getting API key from environment."""
        monkeypatch.setenv("TEST_API_KEY", "test-key-123")
        api_key = test_config.get_api_key()
        assert api_key == "test-key-123"

    def test_get_api_key_missing_raises(
        self, test_config: VibesafeConfig, monkeypatch: pytest.MonkeyPatch
    ):
        """Test missing API key raises ValueError."""
        monkeypatch.delenv("TEST_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key not found"):
            test_config.get_api_key()

    def test_resolve_path_absolute(self, test_config: VibesafeConfig):
        """Test resolving absolute path."""
        abs_path = Path("/absolute/path")
        resolved = test_config.resolve_path(str(abs_path))
        assert resolved == abs_path

    def test_resolve_path_relative(self, test_config: VibesafeConfig):
        """Test resolving relative path."""
        rel_path = "relative/path"
        resolved = test_config.resolve_path(rel_path)
        assert resolved.is_absolute()
        assert str(resolved).endswith(rel_path)

    def test_find_config_current_dir(self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch):
        """Test finding config in current directory."""
        config_path = temp_dir / "vibesafe.toml"
        config_path.write_text("[project]\npython = '>=3.12'\n")
        monkeypatch.chdir(temp_dir)

        found = VibesafeConfig._find_config()
        assert found == config_path

    def test_find_config_parent_dir(self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch):
        """Test finding config in parent directory."""
        config_path = temp_dir / "vibesafe.toml"
        config_path.write_text("[project]\npython = '>=3.12'\n")

        subdir = temp_dir / "subdir"
        subdir.mkdir()
        monkeypatch.chdir(subdir)

        found = VibesafeConfig._find_config()
        assert found == config_path

    def test_find_config_not_found(self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch):
        """Test find_config returns None when not found."""
        monkeypatch.chdir(temp_dir)
        found = VibesafeConfig._find_config()
        assert found is None

    def test_load_with_multiple_providers(self, temp_dir: Path):
        """Test loading config with multiple providers."""
        config_content = """
[project]
python = ">=3.12"

[provider.default]
kind = "openai-compatible"
model = "gpt-4o-mini"
api_key_env = "OPENAI_API_KEY"

[provider.anthropic]
kind = "anthropic"
model = "claude-3-sonnet"
api_key_env = "ANTHROPIC_API_KEY"
"""
        config_path = temp_dir / "vibesafe.toml"
        config_path.write_text(config_content)

        config = VibesafeConfig.load(config_path)
        assert "default" in config.provider
        assert "anthropic" in config.provider
        assert config.provider["anthropic"].model == "claude-3-sonnet"


class TestGetConfig:
    """Tests for get_config function."""

    def test_get_config_singleton(self, config_file: Path, monkeypatch: pytest.MonkeyPatch):
        """Test that get_config returns same instance."""
        monkeypatch.chdir(config_file.parent)

        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_get_config_reload(self, config_file: Path, monkeypatch: pytest.MonkeyPatch):
        """Test that reload=True forces reload."""
        monkeypatch.chdir(config_file.parent)

        config1 = get_config()
        config2 = get_config(reload=True)
        assert config1 is not config2

    def test_get_config_creates_default_if_missing(
        self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Test get_config creates default if no file found."""
        monkeypatch.chdir(temp_dir)
        config = get_config(reload=True)
        assert config.project.env == "dev"
