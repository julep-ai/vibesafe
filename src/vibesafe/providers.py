"""
LLM provider interface and implementations.
"""

import hashlib
import json
from pathlib import Path
from typing import Protocol

from openai import OpenAI

from vibesafe.config import ProviderConfig, get_config


class Provider(Protocol):
    """Protocol for LLM providers."""

    def complete(self, *, prompt: str, seed: int, **kwargs: str | int | float) -> str:
        """
        Generate completion from prompt.

        Args:
            prompt: Input prompt
            seed: Random seed for deterministic generation
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text
        """
        ...


class OpenAICompatibleProvider:
    """OpenAI-compatible API provider."""

    def __init__(self, config: ProviderConfig, api_key: str):
        self.config = config
        self.client = OpenAI(
            api_key=api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )

    def complete(self, *, prompt: str, seed: int, **kwargs: str | int | float) -> str:
        """
        Generate completion using OpenAI-compatible API.

        Args:
            prompt: Input prompt
            seed: Random seed
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        params: dict[str, str | int | float | list[dict[str, str]] | None] = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "seed": seed,
            **kwargs,  # type: ignore[arg-type]
        }
        if self.config.reasoning_effort:
            params["reasoning_effort"] = self.config.reasoning_effort

        response = self.client.chat.completions.create(**params)

        content = response.choices[0].message.content
        return content or ""


class CachedProvider:
    """Wrapper that caches provider responses."""

    def __init__(self, provider: Provider, cache_dir: Path):
        self.provider = provider
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _compute_cache_key(
        self, prompt: str, seed: int, kwargs: dict[str, str | int | float]
    ) -> str:
        """Compute cache key from inputs."""
        spec_hash = kwargs.pop("spec_hash", None)
        if spec_hash:
            key_data = f"{spec_hash}\n{seed}\n{json.dumps(kwargs, sort_keys=True)}"
        else:
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
            key_data = f"{prompt_hash}\n{seed}\n{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]

    def complete(self, *, prompt: str, seed: int, **kwargs: str | int | float) -> str:
        """
        Generate completion with caching.

        Args:
            prompt: Input prompt
            seed: Random seed
            **kwargs: Additional parameters

        Returns:
            Generated text (from cache if available)
        """
        kwargs_copy = dict(kwargs)
        cache_key = self._compute_cache_key(prompt, seed, kwargs_copy)
        cache_file = self.cache_dir / f"{cache_key}.json"

        # Check cache
        if cache_file.exists():
            with open(cache_file) as f:
                data = json.load(f)
                return data["completion"]

        # Generate (use kwargs_copy which has spec_hash removed)
        completion = self.provider.complete(prompt=prompt, seed=seed, **kwargs_copy)

        # Save to cache
        with open(cache_file, "w") as f:
            json.dump(
                {
                    "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()[:8],
                    "spec_hash": kwargs.get("spec_hash"),
                    "seed": seed,
                    "completion": completion,
                },
                f,
                indent=2,
            )

        return completion


def get_provider(provider_name: str = "default", use_cache: bool = True) -> Provider:
    """
    Get a provider instance.

    Args:
        provider_name: Name of provider in config
        use_cache: Whether to wrap in cache

    Returns:
        Provider instance
    """
    config = get_config()
    provider_config = config.get_provider(provider_name)
    api_key = config.get_api_key(provider_name)

    # Create base provider
    provider: Provider
    if provider_config.kind == "openai-compatible":
        provider = OpenAICompatibleProvider(provider_config, api_key)
    else:
        raise ValueError(f"Unknown provider kind: {provider_config.kind}")

    # Wrap in cache if requested
    if use_cache:
        cache_dir = config.resolve_path(config.paths.cache)
        provider = CachedProvider(provider, cache_dir)

    return provider
