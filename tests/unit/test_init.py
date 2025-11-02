"""Tests for guide.__init__ module (Config class and module initialization)."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml


class TestConfig:
    """Test Config class functionality."""

    def test_config_initialization_with_path(self):
        """Test Config initialization with explicit path."""
        from guide import Config

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "server": {"host": "localhost", "port": 9090},
                "storage": {"data_dir": "/custom/data"},
            }
            yaml.safe_dump(config_data, f)
            temp_path = f.name

        try:
            config = Config(temp_path)
            assert config.config_path == Path(temp_path)
            assert config.get("server.host") == "localhost"
            assert config.get("server.port") == 9090
        finally:
            os.unlink(temp_path)

    def test_config_initialization_without_path(self):
        """Test Config initialization using default search paths."""
        from guide import Config

        with (
            patch.object(Config, "_find_config_path") as mock_find,
            patch.object(Config, "_load_config") as mock_load,
        ):
            mock_find.return_value = Path("./local-rag.yaml")

            Config()

            mock_find.assert_called_once_with(None)
            mock_load.assert_called_once()

    def test_find_config_path_env_var(self):
        """Test config path discovery using environment variable."""
        from guide import Config

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test: value")
            temp_path = f.name

        try:
            with patch.dict(os.environ, {"LOCAL_RAG_CONFIG": temp_path}):
                config = Config()
                path = config._find_config_path(None)
                assert path == Path(temp_path)
        finally:
            os.unlink(temp_path)

    def test_find_config_path_with_existing_file(self):
        """Test config path discovery with existing file."""
        from guide import Config

        # Create a real temp file to test with
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test: config")
            temp_path = f.name

        try:
            config = Config.__new__(Config)
            path = config._find_config_path(temp_path)
            assert path == Path(temp_path)
        finally:
            os.unlink(temp_path)

    def test_find_config_path_default_fallback(self):
        """Test config path fallback to default when none found."""
        from guide import Config

        config = Config.__new__(Config)  # Create without calling __init__

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("pathlib.Path.exists", return_value=False),
        ):
            path = config._find_config_path(None)
            assert path == Path("./local-rag.yaml")

    def test_load_config_file_exists(self):
        """Test loading configuration from existing YAML file."""
        from guide import Config

        config_data = {
            "server": {"host": "testhost", "port": 8888},
            "custom_section": {"key": "value"},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(config_data, f)
            temp_path = f.name

        try:
            config = Config.__new__(Config)
            config.config_path = Path(temp_path)
            config._config_data = {}

            config._load_config()

            assert config._config_data["server"]["host"] == "testhost"
            assert config._config_data["server"]["port"] == 8888
        finally:
            os.unlink(temp_path)

    def test_load_config_file_not_exists(self):
        """Test loading configuration when file doesn't exist."""
        from guide import Config

        config = Config.__new__(Config)
        config.config_path = Path("/nonexistent/path.yaml")
        config._config_data = {}

        with patch.object(config, "_apply_defaults") as mock_apply:
            config._load_config()

            assert config._config_data == {}
            mock_apply.assert_called()

    def test_load_config_yaml_parse_error(self):
        """Test loading configuration with YAML parse error."""
        from guide import Config

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content:\n  - malformed")
            temp_path = f.name

        try:
            config = Config.__new__(Config)
            config.config_path = Path(temp_path)
            config._config_data = {}

            with patch.object(config, "_apply_defaults") as mock_apply:
                config._load_config()

                # Should fallback to empty config and apply defaults
                assert config._config_data == {}
                mock_apply.assert_called()
        finally:
            os.unlink(temp_path)

    def test_apply_defaults(self):
        """Test application of default configuration values."""
        from guide import Config

        config = Config.__new__(Config)
        config._config_data = {}

        config._apply_defaults()

        # Check that defaults are applied
        assert config._config_data["server"]["host"] == "127.0.0.1"
        assert config._config_data["server"]["port"] == 8080
        assert config._config_data["llm"]["temperature"] == 0.7
        assert "data_dir" in config._config_data["storage"]

    def test_get_simple_key(self):
        """Test getting configuration value with simple key."""
        from guide import Config

        config = Config.__new__(Config)
        config._config_data = {"test_key": "test_value"}

        assert config.get("test_key") == "test_value"
        assert config.get("nonexistent", "default") == "default"

    def test_get_nested_key(self):
        """Test getting configuration value with nested key."""
        from guide import Config

        config = Config.__new__(Config)
        config._config_data = {"server": {"host": "localhost", "port": 8080}}

        assert config.get("server.host") == "localhost"
        assert config.get("server.port") == 8080
        assert config.get("server.nonexistent", "default") == "default"

    def test_get_deep_nested_key(self):
        """Test getting configuration value with deeply nested key."""
        from guide import Config

        config = Config.__new__(Config)
        config._config_data = {"level1": {"level2": {"level3": "deep_value"}}}

        assert config.get("level1.level2.level3") == "deep_value"
        assert config.get("level1.level2.nonexistent", "default") == "default"

    def test_set_simple_key(self):
        """Test setting configuration value with simple key."""
        from guide import Config

        config = Config.__new__(Config)
        config._config_data = {}

        config.set("test_key", "test_value")
        assert config._config_data["test_key"] == "test_value"

    def test_set_nested_key(self):
        """Test setting configuration value with nested key."""
        from guide import Config

        config = Config.__new__(Config)
        config._config_data = {}

        config.set("server.host", "newhost")
        config.set("server.port", 9090)

        assert config._config_data["server"]["host"] == "newhost"
        assert config._config_data["server"]["port"] == 9090

    def test_set_deep_nested_key(self):
        """Test setting configuration value with deeply nested key."""
        from guide import Config

        config = Config.__new__(Config)
        config._config_data = {}

        config.set("level1.level2.level3", "deep_value")

        assert config._config_data["level1"]["level2"]["level3"] == "deep_value"

    def test_save_config(self):
        """Test saving configuration to YAML file."""
        from guide import Config

        config = Config.__new__(Config)
        config._config_data = {"server": {"host": "localhost", "port": 8080}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            config.save(temp_path)

            # Verify file was written correctly
            with open(temp_path) as f:
                saved_data = yaml.safe_load(f)

            assert saved_data["server"]["host"] == "localhost"
            assert saved_data["server"]["port"] == 8080
        finally:
            os.unlink(temp_path)

    def test_save_config_current_path(self):
        """Test saving configuration to current config path."""
        from guide import Config

        config = Config.__new__(Config)
        config._config_data = {"test": "value"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        config.config_path = Path(temp_path)

        try:
            config.save()

            # Verify file was written
            with open(temp_path) as f:
                saved_data = yaml.safe_load(f)

            assert saved_data["test"] == "value"
        finally:
            os.unlink(temp_path)

    def test_save_config_directory_creation(self):
        """Test saving configuration creates parent directories."""
        from guide import Config

        config = Config.__new__(Config)
        config._config_data = {"test": "value"}

        with tempfile.TemporaryDirectory() as temp_dir:
            save_path = Path(temp_dir) / "subdir" / "config.yaml"

            config.save(save_path)

            assert save_path.exists()
            assert save_path.parent.exists()

    def test_save_config_write_error(self):
        """Test saving configuration handles write errors."""
        from guide import Config

        config = Config.__new__(Config)
        config._config_data = {"test": "value"}

        # Try to save to invalid path (permission denied)
        invalid_path = "/root/cannot_write_here.yaml"

        with pytest.raises(PermissionError):
            config.save(invalid_path)

    def test_validate_config_success(self):
        """Test configuration validation with valid config."""
        from guide import Config

        config = Config.__new__(Config)
        config._config_data = {
            "storage": {"data_dir": tempfile.gettempdir() + "/data"},
            "llm": {"model_path": "/existing/model.gguf"},
            "server": {"port": 8080},
            "content": {"chunk_size": 1000},
        }

        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.side_effect = lambda: str(self).endswith("model.gguf")

            issues = config.validate()

            # Should have issues for missing data dir parent, but port and chunk_size are valid
            assert len(issues) >= 1  # At least the data dir parent issue

    def test_validate_config_invalid_port(self):
        """Test configuration validation with invalid port."""
        from guide import Config

        config = Config.__new__(Config)
        config._config_data = {
            "storage": {"data_dir": tempfile.gettempdir() + "/data"},
            "llm": {"model_path": "/nonexistent/model.gguf"},
            "server": {"port": 70000},  # Invalid port
            "content": {"chunk_size": 1000},
        }

        issues = config.validate()

        port_issue = next((issue for issue in issues if "port" in issue.lower()), None)
        assert port_issue is not None
        assert "70000" in port_issue

    def test_validate_config_invalid_chunk_size(self):
        """Test configuration validation with invalid chunk size."""
        from guide import Config

        config = Config.__new__(Config)
        config._config_data = {
            "storage": {"data_dir": tempfile.gettempdir() + "/data"},
            "llm": {"model_path": "/nonexistent/model.gguf"},
            "server": {"port": 8080},
            "content": {"chunk_size": 50000},  # Too large
        }

        issues = config.validate()

        chunk_issue = next((issue for issue in issues if "chunk" in issue.lower()), None)
        assert chunk_issue is not None
        assert "50000" in chunk_issue

    def test_data_property(self):
        """Test data property returns copy of configuration."""
        from guide import Config

        config = Config.__new__(Config)
        config._config_data = {"server": {"host": "localhost"}, "test": "value"}

        data_copy = config.data

        # Should be equal but not the same object
        assert data_copy == config._config_data
        assert data_copy is not config._config_data

        # Modifying top-level copy shouldn't affect original
        data_copy["new_key"] = "new_value"
        assert "new_key" not in config._config_data


class TestModuleInitialization:
    """Test module-level initialization and imports."""

    def test_module_constants(self):
        """Test module constants are defined."""
        assert hasattr(guide, "__version__")
        assert hasattr(guide, "__author__")
        assert hasattr(guide, "__description__")
        assert guide.__version__ == "1.0.0"

    def test_global_config_instance(self):
        """Test global config instance is created."""
        assert hasattr(guide, "config")
        assert isinstance(guide.config, guide.Config)

    def test_all_exports(self):
        """Test __all__ contains expected exports."""
        expected_exports = [
            "create_app",
            "LLMInterface",
            "VectorStore",
            "ContentManager",
            "LocalRAGCLI",
            "Config",
            "config",
        ]

        for export in expected_exports:
            assert export in guide.__all__
            assert hasattr(guide, export)

    def test_component_imports(self):
        """Test main components can be imported."""
        from guide import (
            Config,
            ContentManager,
            LLMInterface,
            LocalRAGCLI,
            VectorStore,
            config,
            create_app,
        )

        # Basic smoke test - make sure imports work
        assert callable(create_app)
        assert hasattr(LLMInterface, "__init__")
        assert hasattr(VectorStore, "__init__")
        assert hasattr(ContentManager, "__init__")
        assert hasattr(LocalRAGCLI, "__init__")
        assert hasattr(Config, "__init__")
        assert isinstance(config, Config)
