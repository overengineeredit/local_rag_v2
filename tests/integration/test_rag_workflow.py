"""
Integration tests for complete RAG workflow.
Tests end-to-end functionality from document upload to query processing.
"""

import tempfile
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from guide.main import create_app


@pytest.fixture
def client():
    """Create test client for FastAPI app with clean database."""
    app = create_app()
    client = TestClient(app)

    # Clear any existing data from the vector store
    try:
        from guide.main import config
        from guide.vector_store import VectorStore

        vector_db_dir = config.get("storage.vector_db_dir", "./data/chromadb")
        vector_store = VectorStore(persist_directory=vector_db_dir)
        vector_store.clear_all_documents()
    except Exception:
        # If clearing fails, it's likely the first test run or empty database
        pass

    return client


@pytest.fixture
def test_documents():
    """Create temporary test documents with known content."""
    documents = {}

    # Create technical documentation
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(
            """
        Local RAG System Documentation

        Overview:
        The Local RAG (Retrieval-Augmented Generation) system is designed for
        privacy-first document processing and question answering. It operates
        entirely on local hardware without requiring internet connectivity.

        Key Features:
        - ChromaDB vector database for document storage and retrieval
        - llama-cpp-python for local LLM inference
        - FastAPI web interface for user interaction
        - Automatic document chunking and embedding generation
        - Real-time query processing with context retrieval

        Architecture:
        The system uses a single-process architecture optimized for resource-
        constrained devices like Raspberry Pi 5. All components run in the same
        Python process to minimize memory overhead and complexity.
        """
        )
        documents["technical_doc"] = f.name

    # Create FAQ document
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(
            """
        # Frequently Asked Questions

        ## Installation and Setup

        **Q: How do I install the Local RAG system?**
        A: The system can be installed via APT package on Debian-based systems
        or by running the Python package directly from source.

        **Q: What are the system requirements?**
        A: Minimum 4GB RAM, preferably 6GB. Compatible with ARM64 and AMD64
        architectures. Optimized for Raspberry Pi 5.

        ## Usage and Features

        **Q: How do I upload documents?**
        A: Use the web interface at localhost:8080 or the REST API endpoint
        /api/import with file paths or directories.

        **Q: What file formats are supported?**
        A: Currently supports text files (.txt), Markdown (.md), and PDF files.
        The system automatically extracts and chunks content.

        **Q: How accurate are the responses?**
        A: Response quality depends on the relevance of uploaded documents and
        the sophistication of queries. The system retrieves the most relevant
        context before generating responses.
        """
        )
        documents["faq_doc"] = f.name

    # Create configuration guide
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(
            """
        Configuration Guide

        The Local RAG system uses YAML configuration files for customization.

        Default Configuration Locations:
        1. Environment variable: LOCAL_RAG_CONFIG
        2. Current directory: ./local-rag.yaml
        3. User config: ~/.config/local-rag/config.yaml
        4. System config: /etc/local-rag/config.yaml

        Key Configuration Sections:

        Server Settings:
        - host: 127.0.0.1 (bind address)
        - port: 8080 (web interface port)
        - workers: 1 (process workers)

        Storage Settings:
        - data_dir: ./data (document storage)
        - models_dir: ./models (LLM models)
        - vector_db_dir: ./data/chromadb (vector database)

        LLM Settings:
        - model_path: path to GGUF model file
        - context_length: 2048 (token context window)
        - temperature: 0.7 (response creativity)
        - max_tokens: 512 (response length limit)

        Content Processing:
        - chunk_size: 1000 (document chunk size)
        - chunk_overlap: 200 (overlap between chunks)
        - max_file_size_mb: 50 (file size limit)
        """
        )
        documents["config_doc"] = f.name

    yield documents

    # Cleanup
    for path in documents.values():
        Path(path).unlink(missing_ok=True)


class TestCompleteRAGWorkflow:
    """Test complete end-to-end RAG workflow scenarios."""

    def test_full_document_to_query_workflow(self, client, test_documents):
        """Test complete workflow: upload documents -> query -> receive response."""

        # Phase 1: Upload documents
        uploaded_docs = []
        for doc_name, doc_path in test_documents.items():
            upload_request = {"source": doc_path, "source_type": "file"}

            response = client.post("/api/import", json=upload_request)
            assert response.status_code == 200, f"Failed to upload {doc_name}"

            response_data = response.json()
            assert response_data["status"] == "success"
            assert response_data["documents_added"] > 0
            uploaded_docs.append(doc_name)

        # Verify all documents were uploaded
        assert len(uploaded_docs) == 3

        # Phase 2: Test various query scenarios
        test_queries = [
            {
                "query": "What is the Local RAG system?",
                "expected_topics": ["RAG", "privacy", "local"],
                "description": "Basic system overview query",
            },
            {
                "query": "How do I install the system?",
                "expected_topics": ["install", "APT", "package"],
                "description": "Installation instructions query",
            },
            {
                "query": "What are the system requirements?",
                "expected_topics": ["RAM", "4GB", "6GB", "Raspberry Pi"],
                "description": "Hardware requirements query",
            },
            {
                "query": "How do I configure the server port?",
                "expected_topics": ["port", "8080", "server", "configuration"],
                "description": "Configuration query",
            },
        ]

        # Phase 3: Execute queries and validate responses
        for test_query in test_queries:
            query_request = {
                "query": test_query["query"],
                "max_results": 5,
                "include_sources": True,
            }

            response = client.post("/api/query", json=query_request)
            assert response.status_code == 200, f"Query failed: {test_query['description']}"

            response_data = response.json()
            assert "response" in response_data
            assert "sources" in response_data

            # Validate response quality
            response_text = response_data["response"].lower()
            assert len(response_text) > 20, "Response too short"

            # Check that response is relevant (basic keyword checking)
            # Note: In real tests, this would be more sophisticated
            relevant_keywords = sum(1 for topic in test_query["expected_topics"] if topic.lower() in response_text)
            assert relevant_keywords > 0, f"Response not relevant to query: {test_query['query']}"

            # Validate sources
            sources = response_data["sources"]
            assert len(sources) > 0, "No sources returned"

            for source in sources:
                assert "content" in source
                assert "metadata" in source
                assert "distance" in source
                assert isinstance(source["distance"], int | float)

    def test_incremental_document_addition(self, client, test_documents):
        """Test adding documents incrementally and querying after each addition."""

        # Start with empty system, add documents one by one
        doc_items = list(test_documents.items())

        for i, (doc_name, doc_path) in enumerate(doc_items, 1):
            # Upload current document
            upload_request = {"source": doc_path, "source_type": "file"}

            response = client.post("/api/import", json=upload_request)
            assert response.status_code == 200

            # Query the system after each upload
            query_request = {
                "query": "Tell me about the Local RAG system",
                "max_results": 10,
                "include_sources": True,
            }

            response = client.post("/api/query", json=query_request)
            assert response.status_code == 200

            response_data = response.json()
            sources = response_data["sources"]

            # Should have sources from uploaded documents
            assert len(sources) > 0
            # Number of available sources should generally increase
            # (though duplicates might be filtered)

    def test_workflow_with_directory_upload(self, client, test_documents):
        """Test workflow using directory upload instead of individual files."""

        # Create temporary directory with test documents
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy test documents to directory
            for i, (doc_name, doc_path) in enumerate(test_documents.items()):
                content = Path(doc_path).read_text()
                (Path(temp_dir) / f"{doc_name}_{i}.txt").write_text(content)

            # Upload entire directory
            upload_request = {"source": temp_dir, "source_type": "directory"}

            response = client.post("/api/import", json=upload_request)
            assert response.status_code == 200

            response_data = response.json()
            assert response_data["status"] == "success"
            assert response_data["documents_processed"] >= 3

            # Test query after directory upload
            query_request = {
                "query": "What file formats are supported?",
                "include_sources": True,
            }

            response = client.post("/api/query", json=query_request)
            assert response.status_code == 200

            response_data = response.json()
            assert "response" in response_data
            assert len(response_data["sources"]) > 0

    def test_workflow_performance_characteristics(self, client, test_documents):
        """Test performance characteristics of the complete workflow."""

        # Upload documents and measure time
        start_time = time.time()

        for doc_path in test_documents.values():
            upload_request = {"source": doc_path, "source_type": "file"}

            response = client.post("/api/import", json=upload_request)
            assert response.status_code == 200

        upload_time = time.time() - start_time

        # Upload should complete within reasonable time
        assert upload_time < 60.0, "Document upload took too long"

        # Query performance test
        query_times = []
        test_queries = [
            "What is the Local RAG system?",
            "How do I install it?",
            "What are the configuration options?",
            "Tell me about system requirements",
        ]

        for query in test_queries:
            start_time = time.time()

            query_request = {"query": query, "max_results": 5}

            response = client.post("/api/query", json=query_request)
            assert response.status_code == 200

            query_time = time.time() - start_time
            query_times.append(query_time)

        # Query performance validation
        avg_query_time = sum(query_times) / len(query_times)
        max_query_time = max(query_times)

        assert avg_query_time < 10.0, "Average query time too slow"
        assert max_query_time < 20.0, "Maximum query time too slow"


class TestWorkflowErrorRecovery:
    """Test error recovery and resilience in workflows."""

    def test_workflow_with_mixed_valid_invalid_documents(self, client, test_documents):
        """Test workflow with mix of valid and invalid document uploads."""

        # Upload valid documents
        valid_uploads = 0
        for doc_path in list(test_documents.values())[:2]:  # First 2 documents
            upload_request = {"source": doc_path, "source_type": "file"}

            response = client.post("/api/import", json=upload_request)
            if response.status_code == 200:
                valid_uploads += 1

        # Try to upload invalid document
        invalid_upload_request = {
            "source": "/nonexistent/file.txt",
            "source_type": "file",
        }

        response = client.post("/api/import", json=invalid_upload_request)
        assert response.status_code == 500  # Should fail

        # System should still work with valid documents
        query_request = {"query": "What is the Local RAG system?", "max_results": 5}

        response = client.post("/api/query", json=query_request)
        assert response.status_code == 200

        response_data = response.json()
        assert "response" in response_data
        assert len(response_data["response"]) > 0

    def test_workflow_system_state_consistency(self, client, test_documents):
        """Test that system maintains consistent state throughout workflow."""

        # Upload documents
        for doc_path in test_documents.values():
            upload_request = {"source": doc_path, "source_type": "file"}

            response = client.post("/api/import", json=upload_request)
            assert response.status_code == 200

        # Check system status
        response = client.get("/api/status")
        assert response.status_code == 200

        status_data = response.json()
        assert "system" in status_data
        assert "components" in status_data

        # Check health
        response = client.get("/health")
        assert response.status_code == 200

        health_data = response.json()
        assert "status" in health_data
        # Status should be healthy or at least degraded (not unhealthy)
        assert health_data["status"] in ["healthy", "degraded"]


class TestWorkflowEdgeCases:
    """Test edge cases and boundary conditions in workflows."""

    def test_workflow_with_duplicate_uploads(self, client, test_documents):
        """Test workflow behavior with duplicate document uploads."""

        # Upload same document multiple times
        doc_path = list(test_documents.values())[0]
        upload_request = {"source": doc_path, "source_type": "file"}

        responses = []
        for i in range(3):  # Upload 3 times
            response = client.post("/api/import", json=upload_request)
            assert response.status_code == 200
            responses.append(response.json())

        # First upload should add documents
        assert responses[0]["documents_added"] > 0

        # Subsequent uploads should detect duplicates
        # (Implementation detail: might still add or might skip)

        # Query should work normally regardless
        query_request = {"query": "What is this document about?", "max_results": 5}

        response = client.post("/api/query", json=query_request)
        assert response.status_code == 200

    def test_workflow_with_empty_documents(self, client):
        """Test workflow with empty or minimal content documents."""

        # Create minimal content document
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("A")  # Single character
            minimal_doc = f.name

        try:
            upload_request = {"source": minimal_doc, "source_type": "file"}

            response = client.post("/api/import", json=upload_request)
            # Should either succeed or fail gracefully
            assert response.status_code in [200, 400, 422]

            # If successful, query should still work
            if response.status_code == 200:
                query_request = {"query": "What is in the document?", "max_results": 5}

                response = client.post("/api/query", json=query_request)
                assert response.status_code == 200

        finally:
            Path(minimal_doc).unlink(missing_ok=True)


# Workflow test utilities
@pytest.fixture
def workflow_performance_thresholds():
    """Performance thresholds for workflow testing."""
    return {
        "max_upload_time_per_doc": 30.0,  # seconds
        "max_query_time": 15.0,  # seconds
        "max_total_workflow_time": 120.0,  # seconds
    }
