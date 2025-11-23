"""
Shared pytest fixtures for vibesafe tests.
"""

import importlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

import vibesafe.core as vibesafe_core
from vibesafe import VibeCoded, vibesafe
from vibesafe.config import VibesafeConfig, get_config

# Tell pytest not to collect test_checkpoint and test_unit from vibesafe.testing
collect_ignore_glob = []


def pytest_collection_modifyitems(items):
    """Filter out test_checkpoint and test_unit functions from vibesafe.testing module."""
    filtered_items = []
    for item in items:
        # Skip if it's from src/vibesafe/testing.py
        if "src/vibesafe/testing.py" in str(item.fspath):
            continue
        filtered_items.append(item)
    items[:] = filtered_items


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def config_file(temp_dir: Path) -> Path:
    """Create a test configuration file."""
    config_content = """
[project]
python = ">=3.12"
env = "dev"

[provider.default]
kind = "openai-compatible"
model = "gpt-4o-mini"
seed = 42
service_tier = "auto"
base_url = "https://api.openai.com/v1"
api_key_env = "TEST_API_KEY"
timeout = 60

[paths]
checkpoints = ".vibesafe/checkpoints"
cache = ".vibesafe/cache"
index = ".vibesafe/index.toml"
generated = "__generated__"

[prompts]
function = "vibesafe/templates/function.j2"
http = "vibesafe/templates/http_endpoint.j2"
cli = "vibesafe/templates/cli_command.j2"

[sandbox]
enabled = false
timeout = 10
memory_mb = 256
"""
    config_path = temp_dir / "vibesafe.toml"
    config_path.write_text(config_content)
    return config_path


@pytest.fixture
def test_config(config_file: Path, monkeypatch: pytest.MonkeyPatch) -> VibesafeConfig:
    """Load test configuration."""
    monkeypatch.chdir(config_file.parent)
    monkeypatch.setenv("TEST_API_KEY", "test-key-12345")
    return VibesafeConfig.load(config_file)


@pytest.fixture
def sample_function() -> Callable[..., Any]:
    """Sample function for testing."""

    @vibesafe
    def add_numbers(a: int, b: int) -> int:
        """
        Add two numbers.

        >>> add_numbers(2, 3)
        5
        >>> add_numbers(10, 20)
        30
        """
        raise VibeCoded()

    return add_numbers


@pytest.fixture
def sample_async_function() -> Callable[..., Any]:
    """Sample async function for testing."""

    @vibesafe(kind="http")
    async def test_endpoint(x: int) -> dict[str, int]:
        """
        Test endpoint.

        >>> import anyio
        >>> anyio.run(test_endpoint, 5)
        {'result': 5}
        """
        return VibeCoded()

    return test_endpoint


@pytest.fixture
def mock_llm_response(mocker: Any) -> Any:
    """Mock LLM provider response."""

    def add_numbers(a: int, b: int) -> int:
        """
        Add two numbers.

        >>> add_numbers(2, 3)
        5
        >>> add_numbers(10, 20)
        30
        """
        return a + b

    # Mock the OpenAI client
    mock_client = mocker.MagicMock()
    mock_response = mocker.MagicMock()
    mock_response.choices = [mocker.MagicMock()]
    mock_response.choices[0].message.content = """
def add_numbers(a: int, b: int) -> int:
    \"\"\"
    Add two numbers.

    >>> add_numbers(2, 3)
    5
    >>> add_numbers(10, 20)
    30
    \"\"\"
    return a + b
"""
    mock_client.chat.completions.create.return_value = mock_response

    return mock_client


@pytest.fixture
def checkpoint_dir(temp_dir: Path) -> Path:
    """Create a checkpoint directory structure."""
    checkpoint = temp_dir / ".vibesafe" / "checkpoints" / "test" / "func" / "abc123"
    checkpoint.mkdir(parents=True, exist_ok=True)
    return checkpoint


@pytest.fixture
def sample_impl(checkpoint_dir: Path) -> Path:
    """Create a sample implementation file."""
    impl_code = """
def func(a: int, b: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    return a + b
"""
    impl_path = checkpoint_dir / "impl.py"
    impl_path.write_text(impl_code)
    return impl_path


@pytest.fixture
def sample_meta(checkpoint_dir: Path) -> Path:
    """Create sample metadata file."""
    meta_content = """
spec_sha = "abc123def456"
chk_sha = "def456ghi789"
prompt_sha = "ghi789jkl012"
vibesafe_version = "0.2.1"
provider = "openai-compatible:gpt-4o-mini"
template = "function.j2"

[signature]
text = '''def add_numbers(a: int, b: int) -> int'''

[docstring]
text = '''Add two numbers.'''
"""
    meta_path = checkpoint_dir / "meta.toml"
    meta_path.write_text(meta_content)
    return meta_path


@pytest.fixture
def clear_vibesafe_registry():
    """Clear vibesafe registry between tests."""
    # Ensure default example modules are registered once so the baseline registry matches docs
    if not getattr(clear_vibesafe_registry, "_seeded", False):
        try:
            for module in ("examples.math.ops", "examples.api.routes"):
                importlib.import_module(module)
        except ImportError:
            pass  # Examples might not be in path during tests
        clear_vibesafe_registry._seeded = True

    # Store original registry
    original = vibesafe_core._registry.copy()
    vibesafe_core._registry.clear()

    # Remove index file so tests start without active checkpoints
    config = get_config(reload=True)
    index_path = config.resolve_path(config.paths.index)
    if index_path.exists():
        index_path.unlink()

    yield

    # Restore original registry
    vibesafe_core._registry.clear()
    vibesafe_core._registry.update(original)


@pytest.fixture(autouse=True)
def reset_config():
    """Reset global config between tests."""
    from vibesafe import config

    config._config = None
    yield
    config._config = None
