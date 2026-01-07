"""Tests for config module."""

import json
import os
from pathlib import Path

import pytest

from topdf import config


@pytest.fixture
def temp_config_dir(tmp_path, monkeypatch):
    """Create temporary config directory and mock HOME."""
    config_dir = tmp_path / ".config" / "topdf"
    config_dir.mkdir(parents=True)

    # Mock the config module's paths
    monkeypatch.setattr(config, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", config_dir / "config.json")

    return config_dir


@pytest.fixture
def mock_env_key(monkeypatch):
    """Set mock environment variable."""
    monkeypatch.setenv("PERPLEXITY_API_KEY", "pplx-env-test-key")


class TestGetApiKey:
    """Tests for get_api_key function."""

    def test_returns_none_when_no_key(self, temp_config_dir, monkeypatch):
        """Should return None when no key is configured."""
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
        assert config.get_api_key() is None

    def test_returns_key_from_config(self, temp_config_dir):
        """Should return key from config file."""
        config_file = temp_config_dir / "config.json"
        config_file.write_text(json.dumps({"perplexity_api_key": "pplx-config-key"}))

        assert config.get_api_key() == "pplx-config-key"

    def test_returns_key_from_env(self, temp_config_dir, mock_env_key):
        """Should return key from environment variable."""
        assert config.get_api_key() == "pplx-env-test-key"

    def test_config_takes_precedence_over_env(self, temp_config_dir, mock_env_key):
        """Config file should take precedence over environment variable."""
        config_file = temp_config_dir / "config.json"
        config_file.write_text(json.dumps({"perplexity_api_key": "pplx-config-key"}))

        assert config.get_api_key() == "pplx-config-key"


class TestSaveApiKey:
    """Tests for save_api_key function."""

    def test_saves_key_to_config(self, temp_config_dir):
        """Should save key to config file."""
        config.save_api_key("pplx-new-key")

        config_file = temp_config_dir / "config.json"
        assert config_file.exists()

        data = json.loads(config_file.read_text())
        assert data["perplexity_api_key"] == "pplx-new-key"

    def test_creates_directory_if_missing(self, tmp_path, monkeypatch):
        """Should create config directory if it doesn't exist."""
        new_config_dir = tmp_path / "new_dir" / ".config" / "topdf"
        monkeypatch.setattr(config, "CONFIG_DIR", new_config_dir)
        monkeypatch.setattr(config, "CONFIG_FILE", new_config_dir / "config.json")

        config.save_api_key("pplx-test-key")

        assert new_config_dir.exists()
        assert (new_config_dir / "config.json").exists()

    def test_preserves_other_config_values(self, temp_config_dir):
        """Should preserve other values in config file."""
        config_file = temp_config_dir / "config.json"
        config_file.write_text(json.dumps({"other_key": "other_value"}))

        config.save_api_key("pplx-new-key")

        data = json.loads(config_file.read_text())
        assert data["perplexity_api_key"] == "pplx-new-key"
        assert data["other_key"] == "other_value"


class TestClearApiKey:
    """Tests for clear_api_key function."""

    def test_clears_key_from_config(self, temp_config_dir):
        """Should remove key from config file."""
        config_file = temp_config_dir / "config.json"
        config_file.write_text(json.dumps({"perplexity_api_key": "pplx-test-key"}))

        config.clear_api_key()

        # File should be deleted when empty
        assert not config_file.exists()

    def test_preserves_other_config_values(self, temp_config_dir):
        """Should preserve other values when clearing key."""
        config_file = temp_config_dir / "config.json"
        config_file.write_text(
            json.dumps({"perplexity_api_key": "pplx-test-key", "other_key": "other_value"})
        )

        config.clear_api_key()

        data = json.loads(config_file.read_text())
        assert "perplexity_api_key" not in data
        assert data["other_key"] == "other_value"

    def test_handles_missing_config(self, temp_config_dir):
        """Should handle case where config doesn't exist."""
        # Should not raise
        config.clear_api_key()


class TestHasApiKey:
    """Tests for has_api_key function."""

    def test_returns_true_when_key_exists(self, temp_config_dir):
        """Should return True when key is configured."""
        config_file = temp_config_dir / "config.json"
        config_file.write_text(json.dumps({"perplexity_api_key": "pplx-test-key"}))

        assert config.has_api_key() is True

    def test_returns_true_for_env_key(self, temp_config_dir, mock_env_key):
        """Should return True when key is in environment."""
        assert config.has_api_key() is True

    def test_returns_false_when_no_key(self, temp_config_dir, monkeypatch):
        """Should return False when no key is configured."""
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
        assert config.has_api_key() is False


class TestGetMaskedKey:
    """Tests for get_masked_key function."""

    def test_masks_long_key(self):
        """Should mask long keys properly."""
        key = "pplx-1234567890abcdefghijklmnop"
        masked = config.get_masked_key(key)

        assert masked.startswith("pplx-123")
        assert masked.endswith("mnop")
        assert "****" in masked

    def test_masks_short_key(self):
        """Should handle short keys."""
        key = "pplx-short"
        masked = config.get_masked_key(key)

        assert masked.startswith("pplx")
        assert "****" in masked

    def test_returns_none_for_no_key(self, temp_config_dir, monkeypatch):
        """Should return None when no key."""
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
        assert config.get_masked_key() is None

    def test_uses_current_key_when_none_provided(self, temp_config_dir):
        """Should use current configured key when none provided."""
        config_file = temp_config_dir / "config.json"
        config_file.write_text(json.dumps({"perplexity_api_key": "pplx-current-key-test"}))

        masked = config.get_masked_key()
        assert masked is not None
        assert "****" in masked


class TestGetKeySource:
    """Tests for get_key_source function."""

    def test_returns_config_when_from_file(self, temp_config_dir):
        """Should return 'config' when key is from file."""
        config_file = temp_config_dir / "config.json"
        config_file.write_text(json.dumps({"perplexity_api_key": "pplx-test-key"}))

        assert config.get_key_source() == "config"

    def test_returns_env_when_from_env(self, temp_config_dir, mock_env_key):
        """Should return 'env' when key is from environment."""
        assert config.get_key_source() == "env"

    def test_returns_none_when_no_key(self, temp_config_dir, monkeypatch):
        """Should return None when no key is configured."""
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
        assert config.get_key_source() is None
