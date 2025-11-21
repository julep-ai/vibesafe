"""
Tests for vibesafe.runtime module.
"""

import sys

import pytest

if sys.version_info >= (3, 11):
    pass
else:
    pass

from vibesafe.exceptions import VibesafeCheckpointMissing, VibesafeHashMismatch
from vibesafe.runtime import load_checkpoint, update_index


class TestLoadCheckpoint:
    """Tests for load_checkpoint function."""

    def test_load_checkpoint_no_index_raises(self, test_config, temp_dir, monkeypatch):
        """Test loading without index raises error."""
        monkeypatch.chdir(temp_dir)
        from vibesafe import config as config_module

        config_module._config = test_config

        with pytest.raises(VibesafeCheckpointMissing, match="No index found"):
            load_checkpoint("test/unit")

    def test_load_checkpoint_no_unit_in_index_raises(self, test_config, temp_dir, monkeypatch):
        """Test loading unit not in index raises error."""
        index_path = temp_dir / ".vibesafe" / "index.toml"
        index_path.parent.mkdir(parents=True)
        index_path.write_text('["other/unit"]\nactive = "hash123"\n')

        monkeypatch.chdir(temp_dir)
        from vibesafe import config as config_module

        config_module._config = test_config

        with pytest.raises(VibesafeCheckpointMissing, match="No active checkpoint"):
            load_checkpoint("test/unit")

    def test_load_checkpoint_missing_checkpoint_dir_raises(self, test_config, temp_dir, monkeypatch):
        """Test loading with missing checkpoint directory raises error."""
        index_path = temp_dir / ".vibesafe" / "index.toml"
        index_path.parent.mkdir(parents=True)
        index_path.write_text('["test/unit"]\nactive = "abc123"\n')

        monkeypatch.chdir(temp_dir)
        from vibesafe import config as config_module

        config_module._config = test_config

        with pytest.raises(VibesafeCheckpointMissing, match="Checkpoint directory"):
            load_checkpoint("test/unit")

    def test_load_checkpoint_success(
        self, test_config, temp_dir, checkpoint_dir, sample_impl, sample_meta, monkeypatch
    ):
        """Test successfully loading active checkpoint."""
        # Set up index
        index_path = temp_dir / ".vibesafe" / "index.toml"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text('["test/func"]\nactive = "abc123"\n')

        # Move checkpoint to correct location
        dest_checkpoint = temp_dir / ".vibesafe" / "checkpoints" / "test" / "func" / "abc123"
        dest_checkpoint.parent.mkdir(parents=True, exist_ok=True)
        sample_impl.rename(dest_checkpoint / "impl.py")
        sample_meta.rename(dest_checkpoint / "meta.toml")

        monkeypatch.chdir(temp_dir)
        from vibesafe import config as config_module

        config_module._config = test_config

        func = load_checkpoint("test/func", verify_hash=False)
        result = func(2, 3)
        assert result == 5

    def test_load_checkpoint_spec_hash_mismatch(
        self, test_config, temp_dir, checkpoint_dir, sample_impl, sample_meta, monkeypatch
    ):
        """Providing an expected spec hash that differs should raise."""

        index_path = temp_dir / ".vibesafe" / "index.toml"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text('["test/func"]\nactive = "abc123"\n')

        dest_checkpoint = temp_dir / ".vibesafe" / "checkpoints" / "test" / "func" / "abc123"
        dest_checkpoint.parent.mkdir(parents=True, exist_ok=True)
        sample_impl.rename(dest_checkpoint / "impl.py")
        sample_meta.rename(dest_checkpoint / "meta.toml")

        monkeypatch.chdir(temp_dir)
        from vibesafe import config as config_module

        config_module._config = test_config

        with pytest.raises(VibesafeHashMismatch, match="Spec hash mismatch"):
            load_checkpoint("test/func", verify_hash=False, expected_spec_hash="different")

    def test_load_checkpoint_hash_mismatch(
        self, test_config, temp_dir, checkpoint_dir, sample_impl, sample_meta, monkeypatch
    ):
        """Hash mismatches in prod mode should raise VibesafeHashMismatch."""

        index_path = temp_dir / ".vibesafe" / "index.toml"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text('["test/func"]\nactive = "abc123"\n')

        dest_checkpoint = temp_dir / ".vibesafe" / "checkpoints" / "test" / "func" / "abc123"
        dest_checkpoint.parent.mkdir(parents=True, exist_ok=True)
        sample_impl.rename(dest_checkpoint / "impl.py")
        meta_path = dest_checkpoint / "meta.toml"
        sample_meta.rename(meta_path)

        # Corrupt checksum so verification fails
        meta_text = meta_path.read_text().replace('chk_sha = "def456ghi789"', 'chk_sha = "bogus"')
        meta_path.write_text(meta_text)

        monkeypatch.chdir(temp_dir)
        from vibesafe import config as config_module

        test_config.project.env = "prod"
        config_module._config = test_config

        with pytest.raises(VibesafeHashMismatch):
            load_checkpoint("test/func")


class TestUpdateIndex:
    """Tests for update_index function."""

    def test_update_index_creates_new(self, test_config, temp_dir, monkeypatch):
        """Test updating index creates new file if not exists."""
        monkeypatch.chdir(temp_dir)
        from vibesafe import config as config_module

        config_module._config = test_config

        update_index("test/unit", "abc123")

        index_path = temp_dir / ".vibesafe" / "index.toml"
        assert index_path.exists()

        content = index_path.read_text()
        assert "test/unit" in content
        assert "abc123" in content

    def test_update_index_updates_existing(self, test_config, temp_dir, monkeypatch):
        """Test updating existing index entry."""
        index_path = temp_dir / ".vibesafe" / "index.toml"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text('["test/unit"]\nactive = "old_hash"\n')

        monkeypatch.chdir(temp_dir)
        from vibesafe import config as config_module

        config_module._config = test_config

        update_index("test/unit", "new_hash")

        content = index_path.read_text()
        assert "new_hash" in content
        assert "old_hash" not in content

    def test_update_index_preserves_other_units(self, test_config, temp_dir, monkeypatch):
        """Test updating one unit preserves others."""
        index_path = temp_dir / ".vibesafe" / "index.toml"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        initial_content = """
["unit1/func"]
active = "hash1"

["unit2/func"]
active = "hash2"
"""
        index_path.write_text(initial_content)

        monkeypatch.chdir(temp_dir)
        from vibesafe import config as config_module

        config_module._config = test_config

        update_index("unit1/func", "new_hash1")

        content = index_path.read_text()
        assert "new_hash1" in content
        assert "unit2/func" in content
        assert "hash2" in content

    def test_update_index_records_created(self, test_config, temp_dir, monkeypatch):
        """Test that update_index persists created timestamp when provided."""
        monkeypatch.chdir(temp_dir)
        from vibesafe import config as config_module

        config_module._config = test_config

        created_at = "2025-10-30T12:00:00Z"
        update_index("unit/func", "hash123", created=created_at)

        index_path = temp_dir / ".vibesafe" / "index.toml"
        content = index_path.read_text()
        assert "unit/func" in content
        assert "hash123" in content
        assert f'created = "{created_at}"' in content
