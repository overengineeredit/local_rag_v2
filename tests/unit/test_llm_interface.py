"""Tests for the LLMInterface module."""

import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestQuery:
    """Test the Query dataclass."""

    def test_query_initialization(self):
        """Test basic query initialization."""
        from guide.llm_interface import Query

        query = Query(query_id="test_001", text="What is the capital of France?", user_id="user123")

        assert query.query_id == "test_001"
        assert query.text == "What is the capital of France?"
        assert query.user_id == "user123"
        assert query.max_results == 5  # default
        assert query.include_sources is True  # default
        assert query.temperature is None  # default
        assert query.max_tokens is None  # default
        assert query.context_documents == []  # default
        assert query.response == ""  # default
        assert isinstance(query.metadata, dict)
        assert isinstance(query.created_at, datetime)
        assert query.processed_at is None
        assert query.processing_time is None

    def test_query_to_dict(self):
        """Test converting query to dictionary."""
        from guide.llm_interface import Query

        query = Query(
            query_id="test_001",
            text="Test query",
            user_id="user123",
            max_results=10,
            temperature=0.8,
            max_tokens=100,
        )

        query_dict = query.to_dict()

        assert query_dict["query_id"] == "test_001"
        assert query_dict["text"] == "Test query"
        assert query_dict["user_id"] == "user123"
        assert query_dict["max_results"] == 10
        assert query_dict["temperature"] == 0.8
        assert query_dict["max_tokens"] == 100
        assert query_dict["response"] == ""
        assert isinstance(query_dict["created_at"], str)
        assert query_dict["processed_at"] is None
        assert query_dict["processing_time"] is None

    def test_query_from_dict(self):
        """Test creating query from dictionary."""
        from guide.llm_interface import Query

        query_data = {
            "query_id": "test_001",
            "text": "Test query",
            "user_id": "user123",
            "max_results": 10,
            "include_sources": False,
            "temperature": 0.8,
            "max_tokens": 100,
            "context_documents": [{"content": "test"}],
            "response": "Test response",
            "metadata": {"key": "value"},
            "created_at": "2023-01-01T12:00:00+00:00",
            "processed_at": "2023-01-01T12:01:00+00:00",
            "processing_time": 5.5,
        }

        query = Query.from_dict(query_data)

        assert query.query_id == "test_001"
        assert query.text == "Test query"
        assert query.user_id == "user123"
        assert query.max_results == 10
        assert query.include_sources is False
        assert query.temperature == 0.8
        assert query.max_tokens == 100
        assert query.context_documents == [{"content": "test"}]
        assert query.response == "Test response"
        assert query.metadata == {"key": "value"}
        assert isinstance(query.created_at, datetime)
        assert isinstance(query.processed_at, datetime)
        assert query.processing_time == 5.5

    def test_query_mark_processed(self):
        """Test marking query as processed."""
        from guide.llm_interface import Query

        query = Query(query_id="test_001", text="Test query")

        # Initially not processed
        assert query.response == ""
        assert query.processed_at is None
        assert query.processing_time is None

        # Mark as processed
        query.mark_processed("Test response", 2.5)

        assert query.response == "Test response"
        assert isinstance(query.processed_at, datetime)
        assert query.processing_time == 2.5

    def test_query_add_context_document(self):
        """Test adding context documents."""
        from guide.llm_interface import Query

        query = Query(query_id="test_001", text="Test query")

        # Initially no context
        assert len(query.context_documents) == 0

        # Add context document
        query.add_context_document(
            content="Test content", metadata={"source": "test.txt"}, distance=0.1,
        )

        assert len(query.context_documents) == 1
        doc = query.context_documents[0]
        assert doc["content"] == "Test content"
        assert doc["metadata"]["source"] == "test.txt"
        assert doc["distance"] == 0.1
        assert "added_at" in doc

    def test_query_get_context_text(self):
        """Test getting combined context text."""
        from guide.llm_interface import Query

        query = Query(query_id="test_001", text="Test query")

        # No context initially
        assert query.get_context_text() == ""

        # Add multiple context documents
        query.add_context_document("First document", {}, 0.1)
        query.add_context_document("Second document", {}, 0.2)

        context = query.get_context_text()
        assert context == "First document\n\nSecond document"

    def test_query_create_query_id(self):
        """Test creating unique query IDs."""
        from guide.llm_interface import Query

        query_id1 = Query.create_query_id("Test query", "user123")
        query_id2 = Query.create_query_id("Test query", "user123")

        # Should be unique even with same inputs
        assert query_id1 != query_id2
        assert query_id1.startswith("query_")
        assert query_id2.startswith("query_")


@pytest.fixture
def mock_llama():
    """Mock the Llama class from llama-cpp-python."""
    with patch("llama_cpp.Llama") as mock_llama_class:
        mock_model = MagicMock()
        mock_model.tokenize.return_value = [1, 2, 3, 4, 5]  # Mock tokenization
        mock_llama_class.return_value = mock_model
        yield {"class": mock_llama_class, "instance": mock_model}


class TestLLMInterface:
    """Test the LLMInterface class."""

    def test_init_success(self, mock_llama):
        """Test successful initialization."""
        from guide.llm_interface import LLMInterface

        llm = LLMInterface("/path/to/model.gguf")

        assert llm.model_path == "/path/to/model.gguf"
        assert llm.model is not None
        assert llm.default_params["n_ctx"] == 2048
        assert llm.default_params["n_gpu_layers"] == 0
        assert llm.default_params["verbose"] is False
        assert llm.default_params["seed"] == -1

    def test_init_with_custom_params(self, mock_llama):
        """Test initialization with custom parameters."""
        from guide.llm_interface import LLMInterface

        llm = LLMInterface("/path/to/model.gguf", n_ctx=4096, n_gpu_layers=10, temperature=0.5)

        assert llm.default_params["n_ctx"] == 4096
        assert llm.default_params["n_gpu_layers"] == 10
        # temperature is not in default_params, it's passed to model

    def test_init_missing_dependency(self):
        """Test initialization when llama-cpp-python is missing."""
        from guide.llm_interface import LLMInterface

        with patch("llama_cpp.Llama", side_effect=ImportError("No module named 'llama_cpp'")):
            with pytest.raises(RuntimeError, match="llama-cpp-python dependency missing"):
                LLMInterface("/path/to/model.gguf")

    def test_init_model_loading_failure(self):
        """Test initialization when model loading fails."""
        from guide.llm_interface import LLMInterface

        with patch("llama_cpp.Llama", side_effect=Exception("Model file not found")):
            with pytest.raises(RuntimeError, match="Model loading failed"):
                LLMInterface("/path/to/model.gguf")

    def test_auto_detect_threads(self, mock_llama):
        """Test auto-detection of CPU threads."""
        from guide.llm_interface import LLMInterface

        with patch("os.cpu_count", return_value=8):
            LLMInterface("/path/to/model.gguf", n_threads=None)

            # Should auto-detect threads
            mock_llama["class"].assert_called_once()
            call_kwargs = mock_llama["class"].call_args[1]
            assert call_kwargs["n_threads"] == 8


class TestLLMGeneration:
    """Test text generation functionality."""

    def test_generate_not_loaded(self):
        """Test generate when model not loaded."""
        from guide.llm_interface import LLMInterface

        llm = LLMInterface.__new__(LLMInterface)  # Create without initialization
        llm.model = None

        with pytest.raises(RuntimeError, match="Model not loaded"):
            list(llm.generate("Test prompt"))

    def test_generate_with_context(self, mock_llama):
        """Test generate with context."""
        from guide.llm_interface import LLMInterface

        llm = LLMInterface("/path/to/model.gguf")

        # Mock generation response
        mock_response = [
            {"choices": [{"text": "Hello"}]},
            {"choices": [{"text": " world"}]},
            {"choices": [{"text": "!"}]},
        ]
        # Mock the model call to return the response
        mock_llama["instance"].return_value = iter(mock_response)

        # Mock config
        with patch("guide.config") as mock_config:
            mock_config.get.side_effect = lambda key, default: {
                "llm.max_tokens": 512,
                "llm.temperature": 0.7,
            }.get(key, default)

            tokens = list(llm.generate("Test prompt", "Test context"))

            assert tokens == ["Hello", " world", "!"]

    def test_generate_delta_format(self, mock_llama):
        """Test generate with delta response format."""
        from guide.llm_interface import LLMInterface

        llm = LLMInterface("/path/to/model.gguf")

        # Mock generation response with delta format
        mock_response = [
            {"choices": [{"delta": {"content": "Hello"}}]},
            {"choices": [{"delta": {"content": " world"}}]},
        ]
        mock_llama["instance"].return_value = iter(mock_response)

        with patch("guide.config") as mock_config:
            mock_config.get.side_effect = lambda key, default: {
                "llm.max_tokens": 512,
                "llm.temperature": 0.7,
            }.get(key, default)

            tokens = list(llm.generate("Test prompt"))

            assert tokens == ["Hello", " world"]

    def test_generate_complete(self, mock_llama):
        """Test complete generation (non-streaming)."""
        from guide.llm_interface import LLMInterface

        llm = LLMInterface("/path/to/model.gguf")

        # Mock the generate method to return tokens
        with patch.object(llm, "generate", return_value=["Hello", " world", "!"]):
            response = llm.generate_complete("Test prompt", "Test context")

            assert response == "Hello world!"

    def test_generate_exception_handling(self, mock_llama):
        """Test generation exception handling."""
        from guide.llm_interface import LLMInterface

        llm = LLMInterface("/path/to/model.gguf")

        # Mock generation exception
        mock_llama["instance"].side_effect = Exception("Generation error")

        with patch("guide.config") as mock_config:
            mock_config.get.side_effect = lambda key, default: default

            with pytest.raises(RuntimeError, match="Text generation failed"):
                list(llm.generate("Test prompt"))


class TestLLMUtilities:
    """Test utility methods."""

    def test_build_prompt_with_context(self, mock_llama):
        """Test building prompt with context."""
        from guide.llm_interface import LLMInterface

        llm = LLMInterface("/path/to/model.gguf")

        prompt = llm._build_prompt("Test query", "Test context")

        assert "Test query" in prompt
        assert "Test context" in prompt
        assert "Context:" in prompt
        assert "Question:" in prompt
        assert "Answer:" in prompt

    def test_build_prompt_no_context(self, mock_llama):
        """Test building prompt without context."""
        from guide.llm_interface import LLMInterface

        llm = LLMInterface("/path/to/model.gguf")

        prompt = llm._build_prompt("Test query", "")

        assert "Test query" in prompt
        assert "Context:" not in prompt
        assert "Question:" in prompt
        assert "Answer:" in prompt

    def test_estimate_tokens_with_model(self, mock_llama):
        """Test token estimation with loaded model."""
        from guide.llm_interface import LLMInterface

        llm = LLMInterface("/path/to/model.gguf")

        # Mock tokenize method
        mock_llama["instance"].tokenize.return_value = [1, 2, 3, 4, 5]

        token_count = llm.estimate_tokens("Test text")

        assert token_count == 5

    def test_estimate_tokens_fallback(self, mock_llama):
        """Test token estimation fallback when tokenize fails."""
        from guide.llm_interface import LLMInterface

        llm = LLMInterface("/path/to/model.gguf")

        # Mock tokenize to raise exception
        mock_llama["instance"].tokenize.side_effect = Exception("Tokenize error")

        token_count = llm.estimate_tokens("Test text with 20 chars")

        # Should fallback to character count / 4
        assert token_count == 5  # 20 chars / 4

    def test_estimate_tokens_no_model(self):
        """Test token estimation without model."""
        from guide.llm_interface import LLMInterface

        llm = LLMInterface.__new__(LLMInterface)
        llm.model = None

        token_count = llm.estimate_tokens("Test text with 20 chars")

        # Should use fallback estimation
        assert token_count == 5  # 20 chars / 4

    def test_validate_context_length_fits(self, mock_llama):
        """Test context validation when content fits."""
        from guide.llm_interface import LLMInterface

        llm = LLMInterface("/path/to/model.gguf")

        with (
            patch("guide.config") as mock_config,
            patch.object(llm, "estimate_tokens", return_value=100),
        ):
            mock_config.get.return_value = 2048

            result_context, was_truncated = llm.validate_context_length(
                "Short query", "Short context",
            )

            assert result_context == "Short context"
            assert was_truncated is False

    def test_validate_context_length_truncated(self, mock_llama):
        """Test context validation with truncation."""
        from guide.llm_interface import LLMInterface

        llm = LLMInterface("/path/to/model.gguf")

        with (
            patch("guide.config") as mock_config,
            patch.object(llm, "estimate_tokens") as mock_estimate,
        ):
            mock_config.get.return_value = 100  # Small context length

            # Mock estimate_tokens to return high values for full prompt
            def estimate_side_effect(text):
                if "Long context" in text:
                    return 200  # Too large
                return 50  # Template size

            mock_estimate.side_effect = estimate_side_effect

            long_context = "Long context that should be truncated. " * 100
            result_context, was_truncated = llm.validate_context_length("Query", long_context)

            assert len(result_context) < len(long_context)
            assert was_truncated is True

    def test_health_check_success(self, mock_llama):
        """Test successful health check."""
        from guide.llm_interface import LLMInterface

        llm = LLMInterface("/path/to/model.gguf")

        with patch.object(llm, "generate_complete", return_value="Test response"):
            result = llm.health_check()

            assert result["status"] == "ok"
            assert result["loaded"] is True
            assert result["model_path"] == "/path/to/model.gguf"
            assert "context_length" in result
            assert "test_response_length" in result

    def test_health_check_no_model(self):
        """Test health check with no model loaded."""
        from guide.llm_interface import LLMInterface

        llm = LLMInterface.__new__(LLMInterface)
        llm.model = None
        llm.model_path = "/path/to/model.gguf"

        result = llm.health_check()

        assert result["status"] == "error"
        assert result["loaded"] is False
        assert "Model not loaded" in result["error"]

    def test_health_check_exception(self, mock_llama):
        """Test health check with exception."""
        from guide.llm_interface import LLMInterface

        llm = LLMInterface("/path/to/model.gguf")

        with patch.object(llm, "generate_complete", side_effect=Exception("Health check error")):
            result = llm.health_check()

            assert result["status"] == "error"
            assert "Health check error" in result["error"]


class TestQueryFromDictEdgeCases:
    """Test edge cases for Query.from_dict missing coverage."""

    def test_query_from_dict_none_created_at(self):
        """Test Query.from_dict when created_at is None."""
        from guide.llm_interface import Query

        data = {
            "query_id": "test-123",
            "text": "Test query",
            "created_at": None,  # This should trigger lines 60-61
        }

        query = Query.from_dict(data)

        assert query.query_id == "test-123"
        assert query.text == "Test query"
        assert isinstance(query.created_at, datetime)
        # Should be recent (within last few seconds)
        assert (datetime.now(UTC) - query.created_at).total_seconds() < 5


class TestLLMInterfaceGenerationErrorHandling:
    """Test error handling in generation methods for missing coverage."""

    def test_generate_exception_handling(self):
        """Test generate method exception handling (line 216)."""
        from guide.llm_interface import LLMInterface

        # Mock model loading to avoid file system dependencies
        with patch.object(LLMInterface, "_load_model"):
            llm = LLMInterface("/path/to/model.gguf")

            # Mock the model to raise an exception during generation
            llm.model = Mock()
            llm.model.side_effect = Exception("Model generation error")

            with pytest.raises(RuntimeError, match="Text generation failed"):
                list(llm.generate("test prompt"))

    def test_generate_complete_exception_handling(self):
        """Test generate_complete exception handling (lines 236-238)."""
        from guide.llm_interface import LLMInterface

        # Mock model loading to avoid file system dependencies
        with patch.object(LLMInterface, "_load_model"):
            llm = LLMInterface("/path/to/model.gguf")

            # Mock generate to raise an exception
            with patch.object(llm, "generate", side_effect=Exception("Generation error")):
                with pytest.raises(Exception, match="Generation error"):
                    llm.generate_complete("test prompt")


class TestLLMInterfaceQueryProcessing:
    """Test core RAG query processing functionality for missing coverage."""

    def test_process_query_success(self):
        """Test successful query processing (lines 249-279)."""
        from guide.llm_interface import LLMInterface, Query

        # Mock model loading to avoid file system dependencies
        with patch.object(LLMInterface, "_load_model"):
            llm = LLMInterface("/path/to/model.gguf")

            # Create a test query
            query = Query(
                query_id="test-query", text="What is AI?", temperature=0.7, max_tokens=100,
            )

            # Mock the generation method
            with patch.object(
                llm, "generate_complete", return_value="AI is artificial intelligence.",
            ) as mock_generate:
                result = llm.process_query(query)

                # Verify the query was processed
                assert result.response == "AI is artificial intelligence."
                assert result.processed_at is not None
                assert result.processing_time is not None
                assert result.processing_time > 0

                # Verify generate_complete was called with correct parameters
                mock_generate.assert_called_once_with(
                    prompt="What is AI?",
                    context="",  # Empty context since no context_documents
                    temperature=0.7,
                    max_tokens=100,
                )

    def test_process_query_with_context(self):
        """Test query processing with context documents."""
        from guide.llm_interface import LLMInterface, Query

        # Mock model loading to avoid file system dependencies
        with patch.object(LLMInterface, "_load_model"):
            llm = LLMInterface("/path/to/model.gguf")

            # Create a query with context documents
            query = Query(
                query_id="test-query",
                text="What is machine learning?",
                context_documents=[
                    {
                        "content": "Machine learning is a subset of AI.",
                        "metadata": {},
                        "distance": 0.1,
                    },
                    {
                        "content": "It uses algorithms to learn patterns.",
                        "metadata": {},
                        "distance": 0.2,
                    },
                ],
            )

            with patch.object(
                llm, "generate_complete", return_value="ML is about learning from data.",
            ) as mock_generate:
                llm.process_query(query)

                # Verify context was included in the call
                call_args = mock_generate.call_args
                assert "Machine learning is a subset of AI." in call_args.kwargs["context"]
                assert "It uses algorithms to learn patterns." in call_args.kwargs["context"]

    def test_process_query_exception_handling(self):
        """Test query processing exception handling."""
        from guide.llm_interface import LLMInterface, Query

        # Mock model loading to avoid file system dependencies
        with patch.object(LLMInterface, "_load_model"):
            llm = LLMInterface("/path/to/model.gguf")

            query = Query(query_id="test-query", text="Test query")

            # Mock generate_complete to raise an exception
            with patch.object(llm, "generate_complete", side_effect=Exception("Generation failed")):
                with pytest.raises(Exception, match="Generation failed"):
                    llm.process_query(query)

                # Verify query was marked as processed with error
                assert "Error generating response" in query.response
                assert query.processing_time is not None
                assert query.processing_time > 0


class TestLLMInterfaceContextTruncation:
    """Test context truncation functionality for missing coverage."""

    def test_validate_context_length_warning_empty_context(self):
        """Test context validation when query is too long (line 347-348)."""
        from guide.llm_interface import LLMInterface

        # Mock model loading to avoid file system dependencies
        with patch.object(LLMInterface, "_load_model"):
            llm = LLMInterface("/path/to/model.gguf")

            # Create a very long query that exceeds context window
            very_long_query = "This is a test query. " * 1000  # Very long query
            short_context = "Some context."

            with patch("guide.config.get", return_value=100):  # Small context window
                with patch.object(
                    llm, "estimate_tokens", side_effect=lambda text: len(text.split()),
                ):
                    result_context, was_truncated = llm.validate_context_length(
                        very_long_query, short_context,
                    )

                    # Should return empty context and warning when query too long
                    assert result_context == ""
                    assert was_truncated is True

    def test_validate_context_length_truncation(self):
        """Test context truncation when context is too long (line 357)."""
        from guide.llm_interface import LLMInterface

        # Mock model loading to avoid file system dependencies
        with patch.object(LLMInterface, "_load_model"):
            llm = LLMInterface("/path/to/model.gguf")

            short_query = "Short query?"
            very_long_context = "This is context. " * 1000  # Very long context

            with patch("guide.config.get", return_value=500):  # Small context window
                with patch.object(
                    llm, "estimate_tokens", side_effect=lambda text: len(text.split()),
                ):
                    result_context, was_truncated = llm.validate_context_length(
                        short_query, very_long_context,
                    )

                    # Context should be truncated
                    assert len(result_context) < len(very_long_context)
                    assert was_truncated is True
                    assert result_context.endswith("...")

    def test_validate_context_length_no_truncation_needed(self):
        """Test context validation when no truncation needed."""
        from guide.llm_interface import LLMInterface

        # Mock model loading to avoid file system dependencies
        with patch.object(LLMInterface, "_load_model"):
            llm = LLMInterface("/path/to/model.gguf")

            short_query = "Short query?"
            short_context = "Short context."

            with patch("guide.config.get", return_value=2048):  # Large context window
                with patch.object(
                    llm, "estimate_tokens", side_effect=lambda text: len(text.split()),
                ):
                    result_context, was_truncated = llm.validate_context_length(
                        short_query, short_context,
                    )

                    # No truncation should occur
                    assert result_context == short_context
                    assert was_truncated is False
