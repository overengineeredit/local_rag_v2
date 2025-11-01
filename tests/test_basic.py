"""
Basic unit tests for Local RAG system components.
Tests import functionality and basic class instantiation.
"""

import sys
from pathlib import Path
from unittest.mock import patch

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def test_cli_import():
    """Test that CLI module can be imported and LocalRAGCLI class exists."""
    from guide.cli import DEFAULT_BASE_URL, LocalRAGCLI

    assert LocalRAGCLI is not None
    assert DEFAULT_BASE_URL == "http://localhost:8080"


def test_cli_initialization():
    """Test LocalRAGCLI can be instantiated."""
    from guide.cli import LocalRAGCLI

    with patch("httpx.Client"):
        cli = LocalRAGCLI()
        assert cli.base_url == "http://localhost:8080"

        # Test with custom URL
        custom_cli = LocalRAGCLI("http://localhost:9000")
        assert custom_cli.base_url == "http://localhost:9000"


def test_web_interface_import():
    """Test that web interface module can be imported."""
    from guide.web_interface import DownloadModelRequest, ImportRequest, QueryRequest, setup_routes

    assert QueryRequest is not None
    assert ImportRequest is not None
    assert DownloadModelRequest is not None
    assert setup_routes is not None


def test_query_request_model():
    """Test QueryRequest Pydantic model."""
    from guide.web_interface import QueryRequest

    # Test with required field only
    request = QueryRequest(query="test query")
    assert request.query == "test query"
    assert request.max_results == 5  # default value
    assert request.include_sources is True  # default value

    # Test with all fields
    request2 = QueryRequest(query="another query", max_results=10, include_sources=False)
    assert request2.query == "another query"
    assert request2.max_results == 10
    assert request2.include_sources is False


def test_import_request_model():
    """Test ImportRequest Pydantic model."""
    from guide.web_interface import ImportRequest

    # Test with required field only
    request = ImportRequest(source="/path/to/file")
    assert request.source == "/path/to/file"
    assert request.source_type == "file"  # default value

    # Test with all fields
    request2 = ImportRequest(
        source="/path/to/dir", source_type="directory", chunk_size=500, chunk_overlap=100,
    )
    assert request2.source == "/path/to/dir"
    assert request2.source_type == "directory"
    assert request2.chunk_size == 500
    assert request2.chunk_overlap == 100


def test_download_model_request_model():
    """Test DownloadModelRequest Pydantic model."""
    from guide.web_interface import DownloadModelRequest

    # Test with required field only
    request = DownloadModelRequest(url="https://example.com/model.gguf")
    assert request.url == "https://example.com/model.gguf"
    assert request.model_name is None
    assert request.expected_hash is None

    # Test with all fields
    request2 = DownloadModelRequest(
        url="https://example.com/model.gguf", model_name="test-model.gguf", expected_hash="abc123",
    )
    assert request2.url == "https://example.com/model.gguf"
    assert request2.model_name == "test-model.gguf"
    assert request2.expected_hash == "abc123"


def test_content_manager_import():
    """Test that content manager module can be imported."""
    from guide.content_manager import ContentManager

    assert ContentManager is not None


def test_content_manager_initialization():
    """Test ContentManager can be instantiated with default and custom parameters."""
    from guide.content_manager import ContentManager

    # Test default initialization
    cm1 = ContentManager()
    assert cm1.chunk_size == 512  # default
    assert cm1.chunk_overlap == 50  # default

    # Test custom initialization
    cm2 = ContentManager(chunk_size=1000, chunk_overlap=200)
    assert cm2.chunk_size == 1000
    assert cm2.chunk_overlap == 200


def test_llm_interface_import():
    """Test that LLM interface module can be imported."""
    from guide.llm_interface import LLMInterface

    assert LLMInterface is not None


def test_vector_store_import():
    """Test that vector store module can be imported."""
    from guide.vector_store import VectorStore

    assert VectorStore is not None


def test_model_manager_import():
    """Test that model manager module can be imported."""
    from guide.model_manager import ModelManager

    assert ModelManager is not None


def test_model_manager_initialization():
    """Test ModelManager can be instantiated."""
    from guide.model_manager import ModelManager

    mm = ModelManager()
    assert mm.models_dir.name == "models"
    assert mm.chunk_size == 8192  # default


def test_thermal_monitor_import():
    """Test that thermal monitor can be imported from main module."""
    from guide.main import ThermalMonitor, thermal_monitor

    assert ThermalMonitor is not None
    assert thermal_monitor is not None
    assert hasattr(thermal_monitor, "get_thermal_status")


def test_main_module_import():
    """Test that main module can be imported."""
    import guide.main

    assert guide.main is not None
    assert hasattr(guide.main, "create_app")
    assert hasattr(guide.main, "setup_logging")


def test_config_module_import():
    """Test that config module can be imported."""
    from guide import config

    assert config is not None
    assert hasattr(config, "get")
    assert hasattr(config, "validate")


def test_main_create_app():
    """Test that FastAPI app can be created without errors."""
    from guide.main import create_app

    app = create_app()
    assert app is not None
    assert hasattr(app, "routes")
    # Should have at least some routes defined
    assert len(app.routes) > 0
