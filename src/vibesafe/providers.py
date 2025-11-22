"""
LLM provider interface and implementations.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from openai import OpenAI

from vibesafe.config import ProviderConfig, get_config


class Provider(Protocol):
    """Protocol for LLM providers."""

    def complete(self, *, prompt: str, seed: int, **kwargs: object) -> str:
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


@dataclass
class CompletionMetadata:
    """Metadata captured from a provider response."""

    response_id: str | None = None
    reasoning_details: dict | None = None


class OpenAICompatibleProvider:
    """OpenAI-compatible API provider."""

    def __init__(self, config: ProviderConfig, api_key: str):
        self.config = config
        self.client = OpenAI(
            api_key=api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )
        self.last_metadata = CompletionMetadata()

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
        # Remove fields used only for caching and handoff
        previous_response_id = kwargs.pop("previous_response_id", None)
        reasoning_details = kwargs.pop("reasoning_details", None)
        kwargs.pop("spec_hash", None)

        is_openrouter = "openrouter.ai" in self.config.base_url

        if is_openrouter:
            messages: list[dict[str, object]] = [{"role": "user", "content": prompt}]
            if reasoning_details:
                messages.append(
                    {
                        "role": "assistant",
                        "content": "",
                        "reasoning_details": reasoning_details,
                    }
                )

            extra_body = {"reasoning": {"enabled": True}}
            effort = self.config.reasoning_effort or kwargs.pop("reasoning_effort", None)
            if effort:
                extra_body["reasoning"]["effort"] = effort

            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                seed=seed,
                extra_body=extra_body,
                **kwargs,  # type: ignore[arg-type]
            )

            content = response.choices[0].message.content or ""
            self.last_metadata = CompletionMetadata(
                response_id=getattr(response, "id", None),
                reasoning_details=getattr(response.choices[0].message, "reasoning_details", None),
            )
            return content

        # OpenAI Responses API path (preserves reasoning between attempts)
        reasoning = None
        effort = self.config.reasoning_effort or kwargs.pop("reasoning_effort", None)
        if effort:
            reasoning = {"effort": effort}

        response = self.client.responses.create(
            model=self.config.model,
            input=[{"role": "user", "content": prompt}],
            reasoning=reasoning,
            previous_response_id=previous_response_id,
            **kwargs,  # type: ignore[arg-type]
        )

        # Responses API exposes output_text convenience
        content = getattr(response, "output_text", None)
        if content is None:
            try:
                content = "".join(
                    part.get("text", {}).get("value", "") for part in response.output[0].content
                )
            except Exception:
                content = ""

        self.last_metadata = CompletionMetadata(response_id=getattr(response, "id", None))
        return content or ""


class CachedProvider:
    """Wrapper that caches provider responses."""

    def __init__(self, provider: Provider, cache_dir: Path):
        self.provider: Provider = provider
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.last_metadata = CompletionMetadata()

    def _compute_cache_key(
        self, prompt: str, seed: int, kwargs: dict[str, str | int | float]
    ) -> str:
        """Compute cache key from inputs.

        The prompt hash is always included so retries with feedback (changed
        prompt text) don't reuse a stale completion. The spec hash still
        participates to keep cache entries scoped to a spec version.
        """

        spec_hash = kwargs.pop("spec_hash", None)
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()

        key_parts = []
        if spec_hash:
            key_parts.append(spec_hash)

        key_parts.extend([prompt_hash, str(seed), json.dumps(kwargs, sort_keys=True)])

        return hashlib.sha256("\n".join(key_parts).encode()).hexdigest()[:16]

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
                self.last_metadata = CompletionMetadata(
                    response_id=data.get("response_id"),
                    reasoning_details=data.get("reasoning_details"),
                )
                return data["completion"]

        # Generate (use kwargs_copy which has spec_hash removed)
        completion = self.provider.complete(prompt=prompt, seed=seed, **kwargs_copy)

        # Capture metadata if underlying provider set it
        provider_meta = getattr(self.provider, "last_metadata", CompletionMetadata())
        if not isinstance(provider_meta, CompletionMetadata):
            provider_meta = CompletionMetadata()
        self.last_metadata = provider_meta

        # Save to cache
        def _json_safe(value: object) -> object:
            try:
                json.dumps(value)
                return value
            except TypeError:
                return None

        with open(cache_file, "w") as f:
            json.dump(
                {
                    "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()[:8],
                    "spec_hash": kwargs.get("spec_hash"),
                    "seed": seed,
                    "completion": completion,
                    "response_id": provider_meta.response_id,
                    "reasoning_details": _json_safe(provider_meta.reasoning_details),
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
