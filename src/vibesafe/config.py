"""
Configuration loader for vibesafe.toml.
"""

import os
import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider."""

    kind: str = "openai-compatible"
    model: str = "gpt-5-mini"
    temperature: float = 0.0
    seed: int = 42
    base_url: str = "https://api.openai.com/v1"
    api_key_env: str = "OPENAI_API_KEY"
    timeout: int = 60


class PathsConfig(BaseModel):
    """Path configuration."""

    checkpoints: str = ".vibesafe/checkpoints"
    cache: str = ".vibesafe/cache"
    index: str = ".vibesafe/index.toml"
    generated: str = "__generated__"


class PromptsConfig(BaseModel):
    """Prompt template paths."""

    function: str = "prompts/function.j2"
    http: str = "prompts/http_endpoint.j2"
    cli: str = "prompts/cli_command.j2"


class ProjectConfig(BaseModel):
    """Project-level configuration."""

    python: str = ">=3.12"
    env: str = "dev"


class SandboxConfig(BaseModel):
    """Sandbox configuration for code execution."""

    enabled: bool = False
    timeout: int = 10
    memory_mb: int = 256


class VibesafeConfig(BaseModel):
    """Root configuration object."""

    project: ProjectConfig = Field(default_factory=ProjectConfig)
    provider: dict[str, ProviderConfig] = Field(
        default_factory=lambda: {"default": ProviderConfig()}
    )
    paths: PathsConfig = Field(default_factory=PathsConfig)
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)

    @classmethod
    def load(cls, config_path: Path | None = None) -> "VibesafeConfig":
        """
        Load configuration from vibesafe.toml.

        Args:
            config_path: Path to vibesafe.toml, or None to search upwards

        Returns:
            VibesafeConfig instance
        """
        if config_path is None:
            config_path = cls._find_config()

        if config_path is None or not config_path.exists():
            # Return default config
            config = cls()
            cls._apply_overrides(config, base_dir=Path.cwd())
            return config

        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        # Parse provider configs
        providers = {}
        if "provider" in data:
            for name, prov_data in data["provider"].items():
                providers[name] = ProviderConfig(**prov_data)

        config_dict: dict[str, Any] = {
            "project": ProjectConfig(**data.get("project", {})),
            "provider": providers or {"default": ProviderConfig()},
            "paths": PathsConfig(**data.get("paths", {})),
            "prompts": PromptsConfig(**data.get("prompts", {})),
            "sandbox": SandboxConfig(**data.get("sandbox", {})),
        }

        config = cls(**config_dict)
        cls._apply_overrides(config, base_dir=config_path.parent)
        return config

    @staticmethod
    def _find_config() -> Path | None:
        """
        Search for vibesafe.toml starting from current directory upwards.

        Returns:
            Path to vibesafe.toml or None if not found
        """
        current = Path.cwd()
        while True:
            config_path = current / "vibesafe.toml"
            if config_path.exists():
                return config_path

            # Stop at filesystem root
            parent = current.parent
            if parent == current:
                return None
            current = parent

    def get_provider(self, name: str = "default") -> ProviderConfig:
        """
        Get provider configuration by name.

        Args:
            name: Provider name, defaults to "default"

        Returns:
            ProviderConfig instance
        """
        return self.provider.get(name, self.provider["default"])

    def get_api_key(self, provider_name: str = "default") -> str:
        """
        Get API key for a provider from environment.

        Args:
            provider_name: Provider name

        Returns:
            API key string

        Raises:
            ValueError: If API key environment variable is not set
        """
        provider = self.get_provider(provider_name)
        api_key = os.getenv(provider.api_key_env)
        if not api_key:
            raise ValueError(f"API key not found in environment variable: {provider.api_key_env}")
        return api_key

    def resolve_path(self, path: str) -> Path:
        """
        Resolve a path relative to the config file location or CWD.

        Args:
            path: Path string (relative or absolute)

        Returns:
            Resolved absolute Path
        """
        p = Path(path)
        if p.is_absolute():
            return p
        return Path.cwd() / p

    @staticmethod
    def _apply_overrides(config: "VibesafeConfig", base_dir: Path) -> None:
        """
        Apply environment and local state overrides to the loaded config.
        Precedence: VIBESAFE_ENV > .vibesafe/mode > vibesafe.toml
        """
        env_override = os.getenv("VIBESAFE_ENV")
        if env_override:
            config.project.env = env_override
            return

        mode_file = base_dir / ".vibesafe" / "mode"
        if mode_file.exists():
            try:
                mode = mode_file.read_text().strip()
                if mode:
                    config.project.env = mode
            except OSError:
                pass


# Global config instance
_config: VibesafeConfig | None = None


def get_config(reload: bool = False) -> VibesafeConfig:
    """
    Get global configuration instance.

    Args:
        reload: Force reload from file

    Returns:
        VibesafeConfig instance
    """
    global _config
    if _config is None or reload:
        _config = VibesafeConfig.load()
    return _config


def resolve_template_id(
    unit_meta: dict[str, Any],
    config: VibesafeConfig | None = None,
    spec_type: str | None = None,
) -> str:
    """
    Determine the template identifier for a unit, respecting config defaults.

    Prefers an explicit template on the unit. Falls back to the configured
    function/http/cli template based on the unit's declared kind/type or
    inferred spec_type.
    """
    cfg = config or get_config()

    template = unit_meta.get("template")
    if template:
        return template

    unit_kind = unit_meta.get("kind") or unit_meta.get("type") or spec_type
    if unit_kind == "http":
        return cfg.prompts.http
    if unit_kind == "cli":
        return cfg.prompts.cli

    return cfg.prompts.function
