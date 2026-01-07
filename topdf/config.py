"""
API Key Configuration for topdf
===============================
Manages Perplexity API key storage and retrieval.

Key lookup order:
1. Config file (~/.config/topdf/config.json)
2. Environment variable (PERPLEXITY_API_KEY)

The config file takes precedence over environment variables.
"""

import json
import os
from pathlib import Path
from typing import Optional

# Config file location
CONFIG_DIR = Path.home() / ".config" / "topdf"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Environment variable name
ENV_VAR_NAME = "PERPLEXITY_API_KEY"


def get_api_key() -> Optional[str]:
    """Get Perplexity API key from config file or environment.

    Lookup order:
    1. Config file (~/.config/topdf/config.json)
    2. Environment variable (PERPLEXITY_API_KEY)

    Returns:
        API key string if found, None otherwise.
    """
    # Try config file first
    key = _load_key_from_config()
    if key:
        return key

    # Fall back to environment variable
    return os.environ.get(ENV_VAR_NAME)


def save_api_key(key: str) -> None:
    """Save Perplexity API key to config file.

    Creates the config directory if it doesn't exist.

    Args:
        key: The API key to save.
    """
    # Ensure config directory exists
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing config or create new
    config = _load_config()
    config["perplexity_api_key"] = key

    # Write config file
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def clear_api_key() -> None:
    """Remove saved API key from config file."""
    if not CONFIG_FILE.exists():
        return

    config = _load_config()
    if "perplexity_api_key" in config:
        del config["perplexity_api_key"]

        # Write updated config or delete if empty
        if config:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)
        else:
            CONFIG_FILE.unlink()


def has_api_key() -> bool:
    """Check if an API key is configured.

    Returns:
        True if key exists in config or environment, False otherwise.
    """
    return get_api_key() is not None


def get_masked_key(key: Optional[str] = None) -> Optional[str]:
    """Get masked version of API key for display.

    Args:
        key: Key to mask. If None, gets current configured key.

    Returns:
        Masked key like "pplx-****...****" or None if no key.
    """
    if key is None:
        key = get_api_key()

    if not key:
        return None

    if len(key) <= 12:
        return key[:4] + "****"

    return f"{key[:8]}****...****{key[-4:]}"


def get_key_source() -> Optional[str]:
    """Get the source of the current API key.

    Returns:
        "config" if from config file, "env" if from environment, None if not set.
    """
    if _load_key_from_config():
        return "config"
    if os.environ.get(ENV_VAR_NAME):
        return "env"
    return None


def _load_config() -> dict:
    """Load config file contents.

    Returns:
        Config dict, empty if file doesn't exist.
    """
    if not CONFIG_FILE.exists():
        return {}

    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _load_key_from_config() -> Optional[str]:
    """Load API key from config file.

    Returns:
        API key if found in config, None otherwise.
    """
    config = _load_config()
    return config.get("perplexity_api_key")
