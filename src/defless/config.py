"""
Configuration loader for defless.toml.
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
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    seed: int = 42
    base_url: str = "https://api.openai.com/v1"
    api_key_env: str = "OPENAI_API_KEY"
    timeout: int = 60


class PathsConfig(BaseModel):
    """Path configuration."""

    checkpoints: str = ".defless/checkpoints"
    cache: str = ".defless/cache"
    index: str = ".defless/index.toml"
    generated: str = "__generated__"


class PromptsConfig(BaseModel):
    """Prompt template paths."""

    function: str = "prompts/function.j2"
    http: str = "prompts/http_endpoint.j2"


class ProjectConfig(BaseModel):
    """Project-level configuration."""

    python: str = ">=3.12"
    env: str = "dev"


class SandboxConfig(BaseModel):
    """Sandbox configuration for code execution."""

    enabled: bool = False
    timeout: int = 10
    memory_mb: int = 256


class DeflessConfig(BaseModel):
    """Root configuration object."""

    project: ProjectConfig = Field(default_factory=ProjectConfig)
    provider: dict[str, ProviderConfig] = Field(
        default_factory=lambda: {"default": ProviderConfig()}
    )
    paths: PathsConfig = Field(default_factory=PathsConfig)
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)

    @classmethod
    def load(cls, config_path: Path | None = None) -> "DeflessConfig":
        """
        Load configuration from defless.toml.

        Args:
            config_path: Path to defless.toml, or None to search upwards

        Returns:
            DeflessConfig instance
        """
        if config_path is None:
            config_path = cls._find_config()

        if config_path is None or not config_path.exists():
            # Return default config
            return cls()

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

        return cls(**config_dict)

    @staticmethod
    def _find_config() -> Path | None:
        """
        Search for defless.toml starting from current directory upwards.

        Returns:
            Path to defless.toml or None if not found
        """
        current = Path.cwd()
        while True:
            config_path = current / "defless.toml"
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


# Global config instance
_config: DeflessConfig | None = None


def get_config(reload: bool = False) -> DeflessConfig:
    """
    Get global configuration instance.

    Args:
        reload: Force reload from file

    Returns:
        DeflessConfig instance
    """
    global _config
    if _config is None or reload:
        _config = DeflessConfig.load()
    return _config
