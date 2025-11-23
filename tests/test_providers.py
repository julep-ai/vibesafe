"""
Tests for vibesafe.providers module.
"""

import json
from pathlib import Path

import pytest

from vibesafe.config import ProviderConfig
from vibesafe.providers import CachedProvider, OpenAICompatibleProvider, get_provider


class TestOpenAICompatibleProvider:
    """Tests for OpenAICompatibleProvider."""

    def test_initialization(self):
        """Test provider initialization."""
        config = ProviderConfig(
            kind="openai-compatible",
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
        )
        provider = OpenAICompatibleProvider(config, "test-key")
        assert provider.config.model == "gpt-4o-mini"

    def test_complete_with_mock(self, mocker):
        """Test completion with mocked OpenAI client."""
        config = ProviderConfig()

        # Mock Responses client
        mock_client = mocker.MagicMock()
        mock_response = mocker.MagicMock()
        mock_response.output_text = "Generated code"
        mock_response.id = "resp_123"
        mock_client.responses.create.return_value = mock_response

        provider = OpenAICompatibleProvider(config, "test-key")
        provider.client = mock_client

        result = provider.complete(prompt="Test prompt", seed=42)
        assert result == "Generated code"
        mock_client.responses.create.assert_called_once()

    def test_complete_calls_with_correct_params(self, mocker):
        """Test that complete calls API with correct parameters (Responses path)."""
        config = ProviderConfig(model="gpt-4", seed=100)

        mock_client = mocker.MagicMock()
        mock_response = mocker.MagicMock()
        mock_response.output_text = "result"
        mock_client.responses.create.return_value = mock_response

        provider = OpenAICompatibleProvider(config, "test-key")
        provider.client = mock_client

        provider.complete(prompt="Test", seed=42)

        call_args = mock_client.responses.create.call_args
        assert call_args[1]["model"] == "gpt-4"
        assert call_args[1]["input"] == [{"role": "user", "content": "Test"}]

    def test_complete_has_no_temperature_param(self, mocker):
        """Provider should omit temperature entirely (Responses path)."""
        config = ProviderConfig(model="gpt-4", seed=100)

        mock_client = mocker.MagicMock()
        mock_response = mocker.MagicMock()
        mock_response.output_text = "result"
        mock_client.responses.create.return_value = mock_response

        provider = OpenAICompatibleProvider(config, "test-key")
        provider.client = mock_client

        provider.complete(prompt="Test", seed=9)

        call_args = mock_client.responses.create.call_args
        assert "temperature" not in call_args[1]

    def test_openrouter_path_uses_extra_body(self, mocker):
        """OpenRouter base_url should send extra_body reasoning block."""

        config = ProviderConfig(
            base_url="https://openrouter.ai/api/v1",
            reasoning_effort="medium",
        )

        mock_client = mocker.MagicMock()
        mock_resp = mocker.MagicMock()
        mock_choice = mocker.MagicMock()
        mock_choice.message.content = "ok"
        mock_choice.message.reasoning_details = {"foo": "bar"}
        mock_resp.choices = [mock_choice]
        mock_resp.id = "or_123"
        mock_client.chat.completions.create.return_value = mock_resp

        provider = OpenAICompatibleProvider(config, "test-key")
        provider.client = mock_client

        provider.complete(prompt="Hi", seed=1)

        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]["extra_body"] == {"reasoning": {"enabled": True, "effort": "medium"}}
        assert provider.last_metadata.response_id == "or_123"
        assert provider.last_metadata.reasoning_details == {"foo": "bar"}


class TestCachedProvider:
    """Tests for CachedProvider."""

    def test_initialization(self, temp_dir: Path, mocker):
        """Test cached provider initialization."""
        base_provider = mocker.MagicMock()
        cached = CachedProvider(base_provider, temp_dir)
        assert cached.cache_dir == temp_dir
        assert cached.cache_dir.exists()

    def test_cache_miss_calls_provider(self, temp_dir: Path, mocker):
        """Test that cache miss calls underlying provider."""
        base_provider = mocker.MagicMock()
        base_provider.complete.return_value = "Generated result"

        cached = CachedProvider(base_provider, temp_dir)
        result = cached.complete(prompt="Test prompt", seed=42, spec_hash="hash1")

        assert result == "Generated result"
        base_provider.complete.assert_called_once()

    def test_cache_hit_skips_provider(self, temp_dir: Path, mocker):
        """Test that cache hit doesn't call provider."""
        base_provider = mocker.MagicMock()
        base_provider.complete.return_value = "First result"

        cached = CachedProvider(base_provider, temp_dir)

        # First call - cache miss
        result1 = cached.complete(prompt="Test", seed=42, spec_hash="hash1")
        assert result1 == "First result"
        assert base_provider.complete.call_count == 1

        # Second call - cache hit
        base_provider.complete.return_value = "Different result"
        result2 = cached.complete(prompt="Test", seed=42, spec_hash="hash1")
        assert result2 == "First result"  # Should be cached
        assert base_provider.complete.call_count == 1  # No new calls

    def test_prompt_change_busts_cache_even_with_same_spec_hash(self, temp_dir: Path, mocker):
        """Feedback retries change prompt hash so provider is called again."""

        base_provider = mocker.MagicMock()
        base_provider.complete.side_effect = ["Attempt 1", "Attempt 2"]

        cached = CachedProvider(base_provider, temp_dir)

        first = cached.complete(prompt="Prompt 1", seed=42, spec_hash="spec123")
        second = cached.complete(prompt="Prompt 2", seed=42, spec_hash="spec123")

        assert first == "Attempt 1"
        assert second == "Attempt 2"
        assert base_provider.complete.call_count == 2

    def test_different_spec_hashes_different_cache(self, temp_dir: Path, mocker):
        """Different spec hashes should create distinct cache entries."""
        base_provider = mocker.MagicMock()
        base_provider.complete.side_effect = ["Spec A", "Spec B"]

        cached = CachedProvider(base_provider, temp_dir)

        result1 = cached.complete(prompt="Prompt", seed=42, spec_hash="specA")
        result2 = cached.complete(prompt="Prompt", seed=42, spec_hash="specB")

        assert result1 == "Spec A"
        assert result2 == "Spec B"
        assert base_provider.complete.call_count == 2

    def test_cache_file_format(self, temp_dir: Path, mocker):
        """Test cache file contains correct data."""
        base_provider = mocker.MagicMock()
        base_provider.complete.return_value = "Cached result"

        cached = CachedProvider(base_provider, temp_dir)
        cached.complete(prompt="Test", seed=42, spec_hash="hash-file")

        # Find cache file
        cache_files = list(temp_dir.glob("*.json"))
        assert len(cache_files) == 1

        # Check contents
        with open(cache_files[0]) as f:
            data = json.load(f)
            assert "completion" in data
            assert data["completion"] == "Cached result"
            assert data["seed"] == 42
            assert data["spec_hash"] == "hash-file"


class TestGetProvider:
    """Tests for get_provider function."""

    @pytest.mark.unit
    def test_get_provider_default(self, test_config, monkeypatch):
        """Test getting default provider."""
        monkeypatch.setenv("TEST_API_KEY", "test-key")

        # Mock the config to return our test config
        from vibesafe import config as config_module

        config_module._config = test_config

        provider = get_provider("default", use_cache=False)
        assert isinstance(provider, OpenAICompatibleProvider)

    @pytest.mark.unit
    def test_get_provider_with_cache(self, test_config, temp_dir, monkeypatch):
        """Test getting provider with cache."""
        monkeypatch.setenv("TEST_API_KEY", "test-key")

        from vibesafe import config as config_module

        config_module._config = test_config

        provider = get_provider("default", use_cache=True)
        assert isinstance(provider, CachedProvider)

    @pytest.mark.unit
    def test_get_provider_unknown_kind_raises(self, temp_dir, monkeypatch):
        """Test that unknown provider kind raises error."""
        from vibesafe.config import ProviderConfig, VibesafeConfig

        config = VibesafeConfig()
        config.provider["bad"] = ProviderConfig(kind="unknown-provider")

        from vibesafe import config as config_module

        config_module._config = config

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        with pytest.raises(ValueError, match="Unknown provider kind"):
            get_provider("bad", use_cache=False)
