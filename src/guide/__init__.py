"""
Local RAG (Retrieval-Augmented Generation) System.

A CPU-first RAG system designed for privacy, learning, and offline operation.
Optimized for resource-constrained devices like Raspberry Pi 5.
"""

import logging
import os
from pathlib import Path
from typing import Any

import yaml

__version__ = "1.0.0"
__author__ = "Peenak Inamdar"
__description__ = "Local Retrieval-Augmented Generation system"

logger = logging.getLogger(__name__)


class Config:
    """Configuration management for Local RAG system."""

    def __init__(self, config_path: str | Path | None = None):
        """Initialize configuration.

        Args:
            config_path: Path to configuration file. If None, uses default locations.
        """
        self.config_path = self._find_config_path(config_path)
        self._config_data = {}
        self._load_config()

    def _find_config_path(self, config_path: str | Path | None) -> Path:
        """Find configuration file in default locations."""
        if config_path:
            return Path(config_path)

        # Search order: env var, current dir, user config, system config
        search_paths = [
            os.environ.get("LOCAL_RAG_CONFIG"),
            "./local-rag.yaml",
            "~/.config/local-rag/config.yaml",
            "/etc/local-rag/config.yaml",
        ]

        for path_str in search_paths:
            if not path_str:
                continue
            path = Path(path_str).expanduser()
            if path.exists():
                logger.info(f"Found config at: {path}")
                return path

        # Default to current directory if none found
        default_path = Path("./local-rag.yaml")
        logger.warning(f"No config found, using default: {default_path}")
        return default_path

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, encoding="utf-8") as f:
                    self._config_data = yaml.safe_load(f) or {}
                logger.info(f"Loaded config from {self.config_path}")
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                self._config_data = {}

            # Apply defaults
            self._apply_defaults()

        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            self._config_data = {}
            self._apply_defaults()

    def _apply_defaults(self) -> None:
        """Apply default configuration values."""
        defaults = {
            "server": {
                "host": "127.0.0.1",
                "port": 8080,
                "workers": 1,
                "reload": False,
            },
            "storage": {
                "data_dir": "./data",
                "models_dir": "./models",
                "vector_db_dir": "./data/chromadb",
            },
            "llm": {
                "model_path": "./models/llama-2-7b-chat.q4_0.gguf",
                "context_length": 2048,
                "temperature": 0.7,
                "max_tokens": 512,
                "n_threads": None,  # Auto-detect
            },
            "embedding": {"model": "all-MiniLM-L6-v2", "batch_size": 32},
            "content": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "max_file_size_mb": 50,
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": None,  # None means console only
            },
        }

        # Deep merge defaults with loaded config
        self._config_data = self._deep_merge(defaults, self._config_data)

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'server.port', 'llm.model_path')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config_data

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'server.port')
            value: Value to set
        """
        keys = key.split(".")
        config = self._config_data

        # Navigate to parent dict
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the value
        config[keys[-1]] = value

    def save(self, path: str | Path | None = None) -> None:
        """Save configuration to YAML file.

        Args:
            path: Path to save to. If None, uses current config_path.
        """
        save_path = Path(path) if path else self.config_path

        try:
            # Ensure directory exists
            save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(self._config_data, f, default_flow_style=False, indent=2)

            logger.info(f"Configuration saved to {save_path}")

        except Exception as e:
            logger.error(f"Failed to save config to {save_path}: {e}")
            raise

    def validate(self) -> list[str]:
        """Validate configuration and return list of issues.

        Returns:
            List of validation error messages
        """
        issues = []

        # Check required directories
        data_dir = Path(self.get("storage.data_dir"))
        if not data_dir.parent.exists():
            issues.append(f"Data directory parent does not exist: {data_dir.parent}")

        # Check model file exists
        model_path = Path(self.get("llm.model_path"))
        if not model_path.exists():
            issues.append(f"LLM model file not found: {model_path}")

        # Check port is valid
        port = self.get("server.port")
        if not isinstance(port, int) or port < 1 or port > 65535:
            issues.append(f"Invalid server port: {port}")

        # Check chunk size is reasonable
        chunk_size = self.get("content.chunk_size")
        if not isinstance(chunk_size, int) or chunk_size < 100 or chunk_size > 10000:
            issues.append(f"Invalid chunk size: {chunk_size}")

        return issues

    @property
    def data(self) -> dict:
        """Get the full configuration dictionary."""
        return self._config_data.copy()


# Global configuration instance
config = Config()

# Main components - imported after Config to avoid circular imports
from .cli import LocalRAGCLI  # noqa: E402
from .content_manager import ContentManager  # noqa: E402
from .llm_interface import LLMInterface  # noqa: E402
from .main import create_app  # noqa: E402
from .vector_store import VectorStore  # noqa: E402

__all__ = [
    "create_app",
    "LLMInterface",
    "VectorStore",
    "ContentManager",
    "LocalRAGCLI",
    "Config",
    "config",
]
