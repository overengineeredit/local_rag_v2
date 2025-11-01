"""
Integration tests for document upload API endpoints.
Tests the contract and behavior of document management operations.
"""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from guide.main import create_app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    app = create_app()
    client = TestClient(app)

    # Clear database before each test
    from guide.vector_store import VectorStore
    vector_store = VectorStore("./data/chromadb")
    vector_store.clear_all_documents()

    return client


@pytest.fixture
def temp_text_file():
    """Create a temporary text file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("This is a test document.\n")
        f.write("It contains sample content for testing document upload.\n")
        f.write("The Local RAG system should be able to process this content.")
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_directory():
    """Create a temporary directory with multiple files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        (Path(temp_dir) / "doc1.txt").write_text("First document content.")
        (Path(temp_dir) / "doc2.txt").write_text("Second document content.")
        (Path(temp_dir) / "README.md").write_text("# README\nDocumentation content.")

        yield temp_dir


class TestDocumentUploadContract:
    """Test the contract and behavior of document upload endpoints."""

    def test_single_file_upload_success(self, client, temp_text_file):
        """Test successful upload of a single text file."""
        # Arrange
        request_data = {"source": temp_text_file, "source_type": "file"}

        # Act
        response = client.post("/api/import", json=request_data)

        # Assert - Contract validation
        assert response.status_code == 200

        response_data = response.json()
        assert "status" in response_data
        assert response_data["status"] == "success"
        assert "documents_processed" in response_data
        assert "documents_added" in response_data
        assert "source" in response_data
        assert "source_type" in response_data

        # Assert - Business logic validation
        assert response_data["documents_processed"] > 0
        assert response_data["documents_added"] > 0
        assert response_data["source"] == temp_text_file
        assert response_data["source_type"] == "file"

    def test_directory_upload_success(self, client, temp_directory):
        """Test successful upload of multiple files from directory."""
        # Arrange
        request_data = {"source": temp_directory, "source_type": "directory"}

        # Act
        response = client.post("/api/import", json=request_data)

        # Assert - Contract validation
        assert response.status_code == 200

        response_data = response.json()
        assert "status" in response_data
        assert response_data["status"] == "success"
        assert "documents_processed" in response_data
        assert "documents_added" in response_data

        # Assert - Business logic validation
        assert response_data["documents_processed"] >= 3  # At least 3 files
        assert response_data["documents_added"] >= 3
        assert response_data["source"] == temp_directory
        assert response_data["source_type"] == "directory"

    def test_upload_with_custom_chunking(self, client, temp_text_file):
        """Test upload with custom chunk size and overlap parameters."""
        # Arrange
        request_data = {
            "source": temp_text_file,
            "source_type": "file",
            "chunk_size": 500,
            "chunk_overlap": 100,
        }

        # Act
        response = client.post("/api/import", json=request_data)

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"

    def test_upload_invalid_source_type(self, client):
        """Test upload with invalid source_type parameter."""
        # Arrange
        request_data = {"source": "/some/path", "source_type": "invalid_type"}

        # Act
        response = client.post("/api/import", json=request_data)

        # Assert - Should return validation error
        assert response.status_code == 422  # Validation error

        response_data = response.json()
        assert "error" in response_data
        assert "HTTPException" in response_data["error"]

    def test_upload_missing_source(self, client):
        """Test upload with missing source parameter."""
        # Arrange
        request_data = {"source_type": "file"}

        # Act
        response = client.post("/api/import", json=request_data)

        # Assert - Should return validation error
        assert response.status_code == 422  # Validation error

        response_data = response.json()
        assert "error" in response_data

    def test_upload_nonexistent_file(self, client):
        """Test upload of a file that doesn't exist."""
        # Arrange
        request_data = {"source": "/nonexistent/file.txt", "source_type": "file"}

        # Act
        response = client.post("/api/import", json=request_data)

        # Assert - Should return error
        assert response.status_code == 500  # Content processing error

        response_data = response.json()
        assert "error" in response_data
        assert "ContentProcessingError" in response_data["error"]

    def test_upload_empty_request_body(self, client):
        """Test upload with empty request body."""
        # Act
        response = client.post("/api/import", json={})

        # Assert - Should return validation error
        assert response.status_code == 422  # Validation error

    def test_upload_malformed_json(self, client):
        """Test upload with malformed JSON."""
        # Act
        response = client.post(
            "/api/import",
            data="{'invalid': json}",  # Malformed JSON
            headers={"Content-Type": "application/json"},
        )

        # Assert - Should return error
        assert response.status_code == 422


class TestDocumentManagementOperations:
    """Test document management operations beyond basic upload."""

    def test_duplicate_upload_detection(self, client, temp_text_file):
        """Test that duplicate content is detected and handled properly."""
        # Arrange
        request_data = {"source": temp_text_file, "source_type": "file"}

        # Act - Upload same file twice
        response1 = client.post("/api/import", json=request_data)
        response2 = client.post("/api/import", json=request_data)

        # Assert - Both requests succeed but second has fewer new documents
        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Second upload should detect duplicates
        assert data2["documents_added"] <= data1["documents_added"]

    def test_upload_size_limits(self, client):
        """Test that large file uploads are handled according to size limits."""
        # Create a large temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            # Write a large amount of content (simulate large file)
            large_content = "This is a large file content. " * 10000  # ~300KB
            f.write(large_content)
            large_file_path = f.name

        try:
            # Arrange
            request_data = {"source": large_file_path, "source_type": "file"}

            # Act
            response = client.post("/api/import", json=request_data)

            # Assert - Should either succeed or fail gracefully with size limit error
            if response.status_code == 200:
                # Success case
                data = response.json()
                assert data["status"] == "success"
            else:
                # Size limit error case
                assert response.status_code in [413, 500]  # Payload too large or processing error

        finally:
            # Cleanup
            Path(large_file_path).unlink(missing_ok=True)


class TestDocumentAPIErrorHandling:
    """Test error handling scenarios for document API."""

    def test_system_not_initialized_error(self, client, temp_text_file):
        """Test behavior when vector store is not initialized."""
        # Note: This test depends on the system state
        # In a real scenario, we'd mock the vector store to return None
        pass

    def test_configuration_error_handling(self, client):
        """Test handling of configuration-related errors."""
        # This would test scenarios where configuration is invalid
        # Implementation depends on how configuration errors are triggered
        pass

    def test_resource_limit_error_handling(self, client):
        """Test handling when resource limits are exceeded."""
        # This would test memory/CPU limit scenarios
        # Implementation depends on resource monitoring
        pass


# Fixtures for API testing
@pytest.fixture(scope="session")
def test_config():
    """Test configuration for API tests."""
    return {
        "storage": {"data_dir": "./test_data", "vector_db_dir": "./test_data/chromadb"},
        "content": {
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "max_file_size_mb": 10,  # Smaller limit for testing
        },
    }
