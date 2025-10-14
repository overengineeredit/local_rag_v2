"""
Basic unit tests for Local RAG system components.
Tests import functionality and basic class instantiation.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def test_cli_import():
    """Test that CLI module can be imported and LocalRAGCLI class exists."""
    from guide.cli import LocalRAGCLI, DEFAULT_BASE_URL
    assert LocalRAGCLI is not None
    assert DEFAULT_BASE_URL == "http://localhost:8080"


def test_cli_initialization():
    """Test LocalRAGCLI can be instantiated."""
    from guide.cli import LocalRAGCLI
    
    with patch('httpx.Client'):
        cli = LocalRAGCLI()
        assert cli.base_url == "http://localhost:8080"
        
        # Test with custom URL
        custom_cli = LocalRAGCLI("http://localhost:9000")
        assert custom_cli.base_url == "http://localhost:9000"


def test_web_interface_import():
    """Test that web interface module can be imported."""
    from guide.web_interface import QueryRequest, ImportRequest, setup_routes
    assert QueryRequest is not None
    assert ImportRequest is not None
    assert setup_routes is not None


def test_query_request_model():
    """Test QueryRequest Pydantic model."""
    from guide.web_interface import QueryRequest
    
    # Test with required field only
    request = QueryRequest(query="test query")
    assert request.query == "test query"
    assert request.max_results == 5  # default value
    
    # Test with all fields
    request2 = QueryRequest(query="another query", max_results=10)
    assert request2.query == "another query"
    assert request2.max_results == 10


def test_import_request_model():
    """Test ImportRequest Pydantic model."""
    from guide.web_interface import ImportRequest
    
    # Test with required field only
    request = ImportRequest(source="/path/to/file")
    assert request.source == "/path/to/file"
    assert request.source_type == "file"  # default value
    
    # Test with all fields
    request2 = ImportRequest(source="/path/to/dir", source_type="directory")
    assert request2.source == "/path/to/dir"
    assert request2.source_type == "directory"


def test_content_manager_import():
    """Test that content manager module can be imported."""
    from guide.content_manager import ContentManager
    assert ContentManager is not None


def test_llm_interface_import():
    """Test that LLM interface module can be imported."""
    from guide.llm_interface import LLMInterface
    assert LLMInterface is not None


def test_vector_store_import():
    """Test that vector store module can be imported."""
    from guide.vector_store import VectorStore
    assert VectorStore is not None


def test_main_module_import():
    """Test that main module can be imported."""
    import guide.main
    assert guide.main is not None