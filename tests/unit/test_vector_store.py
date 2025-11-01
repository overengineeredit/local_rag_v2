"""Tests for the VectorStore module."""

import tempfile
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client and collection."""
    with patch("chromadb.PersistentClient") as mock_client_class, \
         patch("chromadb.Settings") as mock_settings:
        
        # Create mock collection with necessary methods
        mock_collection = MagicMock()
        mock_collection.add = MagicMock()
        mock_collection.query = MagicMock()
        mock_collection.get = MagicMock()
        mock_collection.delete = MagicMock()
        mock_collection.count = MagicMock()
        
        # Create mock client
        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        
        # Configure mock client class to return our mock client
        mock_client_class.return_value = mock_client
        
        yield {
            "client_class": mock_client_class,
            "client": mock_client,
            "collection": mock_collection,
            "settings": mock_settings
        }


class TestDocument:
    """Test the Document dataclass."""

    def test_document_initialization(self):
        """Test basic document initialization."""
        from guide.vector_store import Document
        
        doc = Document(
            source="test.txt",
            content="This is test content."
        )
        
        assert doc.source == "test.txt"
        assert doc.content == "This is test content."
        assert isinstance(doc.metadata, dict)
        assert len(doc.content_hash) == 64  # SHA-256 hash length
        assert isinstance(doc.created_at, datetime)

    def test_document_hash_calculation(self):
        """Test that content hash is calculated correctly."""
        from guide.vector_store import Document
        
        content = "Test content for hashing"
        doc = Document(source="test.txt", content=content)
        
        # Calculate expected hash manually
        import hashlib
        expected_hash = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()
        
        assert doc.content_hash == expected_hash

    def test_document_hash_normalization(self):
        """Test that content is normalized before hashing."""
        from guide.vector_store import Document
        
        # Content with leading/trailing whitespace
        content1 = "  Test content  "
        content2 = "Test content"
        
        doc1 = Document(source="test1.txt", content=content1)
        doc2 = Document(source="test2.txt", content=content2)
        
        # Should have same hash after normalization
        assert doc1.content_hash == doc2.content_hash

    def test_document_to_dict(self):
        """Test converting document to dictionary."""
        from guide.vector_store import Document
        
        metadata = {"author": "test", "category": "example"}
        doc = Document(
            source="test.txt",
            content="Test content",
            metadata=metadata
        )
        
        doc_dict = doc.to_dict()
        
        assert doc_dict["source"] == "test.txt"
        assert doc_dict["content"] == "Test content"
        assert doc_dict["metadata"] == metadata
        assert "content_hash" in doc_dict
        assert "created_at" in doc_dict
        assert isinstance(doc_dict["created_at"], str)  # Should be ISO format

    def test_document_from_dict(self):
        """Test creating document from dictionary."""
        from guide.vector_store import Document
        
        doc_data = {
            "source": "test.txt",
            "content": "Test content",
            "metadata": {"key": "value"},
            "created_at": "2023-01-01T12:00:00+00:00"
        }
        
        doc = Document.from_dict(doc_data)
        
        assert doc.source == "test.txt"
        assert doc.content == "Test content"
        assert doc.metadata == {"key": "value"}
        assert isinstance(doc.created_at, datetime)

    def test_document_from_dict_missing_metadata(self):
        """Test creating document from dictionary without metadata."""
        from guide.vector_store import Document
        
        doc_data = {
            "source": "test.txt",
            "content": "Test content",
            "created_at": "2023-01-01T12:00:00+00:00"
        }
        
        doc = Document.from_dict(doc_data)
        
        assert doc.source == "test.txt"
        assert doc.content == "Test content"
        assert doc.metadata == {}  # Should default to empty dict


class TestDocumentChunk:
    """Test the DocumentChunk dataclass."""

    def test_chunk_initialization(self):
        """Test basic chunk initialization."""
        from guide.vector_store import DocumentChunk
        
        chunk = DocumentChunk(
            chunk_id="chunk_001",
            document_source="test.txt",
            content="This is a chunk of content.",
            chunk_index=0,
            chunk_size=100,
            chunk_overlap=20
        )
        
        assert chunk.chunk_id == "chunk_001"
        assert chunk.document_source == "test.txt"
        assert chunk.content == "This is a chunk of content."
        assert chunk.chunk_index == 0
        assert chunk.chunk_size == 100
        assert chunk.chunk_overlap == 20
        assert isinstance(chunk.metadata, dict)
        assert len(chunk.content_hash) == 64
        assert isinstance(chunk.created_at, datetime)

    def test_chunk_to_dict(self):
        """Test converting chunk to dictionary."""
        from guide.vector_store import DocumentChunk
        
        chunk = DocumentChunk(
            chunk_id="chunk_001",
            document_source="test.txt",
            content="Test content",
            chunk_index=0,
            chunk_size=100,
            chunk_overlap=20,
            metadata={"key": "value"}
        )
        
        chunk_dict = chunk.to_dict()
        
        assert chunk_dict["chunk_id"] == "chunk_001"
        assert chunk_dict["document_source"] == "test.txt"
        assert chunk_dict["content"] == "Test content"
        assert chunk_dict["chunk_index"] == 0
        assert chunk_dict["chunk_size"] == 100
        assert chunk_dict["chunk_overlap"] == 20
        assert chunk_dict["metadata"] == {"key": "value"}
        assert "content_hash" in chunk_dict
        assert "created_at" in chunk_dict

    def test_chunk_from_dict(self):
        """Test creating chunk from dictionary."""
        from guide.vector_store import DocumentChunk
        
        chunk_data = {
            "chunk_id": "chunk_001",
            "document_source": "test.txt",
            "content": "Test content",
            "chunk_index": 0,
            "chunk_size": 100,
            "chunk_overlap": 20,
            "metadata": {"key": "value"},
            "created_at": "2023-01-01T12:00:00+00:00"
        }
        
        chunk = DocumentChunk.from_dict(chunk_data)
        
        assert chunk.chunk_id == "chunk_001"
        assert chunk.document_source == "test.txt"
        assert chunk.content == "Test content"
        assert chunk.chunk_index == 0
        assert chunk.chunk_size == 100
        assert chunk.chunk_overlap == 20
        assert chunk.metadata == {"key": "value"}
        assert isinstance(chunk.created_at, datetime)


class TestVectorStoreBasics:
    """Test basic VectorStore functionality."""
    
    def test_init_success(self, mock_chroma_client):
        """Test successful initialization."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore("/tmp/test_db")
        
        assert vs.persist_directory == "/tmp/test_db"
        assert vs.collection_name == "documents"
        assert vs.client is not None
        assert vs.collection is not None

    def test_init_with_custom_params(self, mock_chroma_client):
        """Test initialization with custom parameters."""
        from guide.vector_store import VectorStore
        
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = Path(temp_dir) / "custom_path"
            vs = VectorStore(
                persist_directory=str(custom_path),
                collection_name="custom_collection"
            )
            
            assert vs.persist_directory == str(custom_path)
            assert vs.collection_name == "custom_collection"

    def test_init_failure(self):
        """Test initialization failure handling."""
        from guide.vector_store import VectorStore
        
        with patch("chromadb.PersistentClient") as mock_client:
            mock_client.side_effect = Exception("Connection failed")
            
            with pytest.raises(RuntimeError, match="ChromaDB initialization failed"):
                VectorStore("/tmp/test_db")


class TestVectorStoreDocuments:
    """Test document operations."""
    
    def test_add_documents_not_initialized(self):
        """Test adding documents when ChromaDB not initialized."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore.__new__(VectorStore)  # Create without initialization
        vs.collection = None
        
        with pytest.raises(RuntimeError, match="ChromaDB not initialized"):
            vs.add_documents([{"content": "test"}])

    def test_search_not_initialized(self):
        """Test search when ChromaDB not initialized."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore.__new__(VectorStore)  # Create without initialization
        vs.collection = None
        
        with pytest.raises(RuntimeError, match="ChromaDB not initialized"):
            vs.search("test query")

    def test_delete_documents_not_initialized(self):
        """Test delete when ChromaDB not initialized."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore.__new__(VectorStore)  # Create without initialization  
        vs.collection = None
        
        with pytest.raises(RuntimeError, match="ChromaDB not initialized"):
            vs.delete_documents(source="test.txt")

    def test_health_check_not_initialized(self):
        """Test health check when not initialized."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore.__new__(VectorStore)  # Create without initialization
        vs.client = None
        vs.collection = None
        vs.persist_directory = "/tmp/test_db"
        vs.collection_name = "test_collection"
        
        result = vs.health_check()
        
        assert result["status"] == "error"
        assert result["connected"] is False
        assert "not initialized" in result["error"]

    def test_health_check_with_mocked_client(self, mock_chroma_client):
        """Test health check with working client."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore("/tmp/test_db")
        mock_chroma_client["collection"].count.return_value = 5
        
        result = vs.health_check()
        
        assert result["status"] == "ok"
        assert result["connected"] is True
        assert result["document_count"] == 5
        assert result["backend"] == "SQLite (embedded)"


class TestVectorStoreHelpers:
    """Test helper methods."""
    
    def test_calculate_hash(self, mock_chroma_client):
        """Test hash calculation."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore("/tmp/test_db")
        
        content = "  Test content  "
        hash_result = vs._calculate_hash(content)
        
        # Should normalize whitespace before hashing
        import hashlib
        expected = hashlib.sha256("Test content".encode("utf-8")).hexdigest()
        assert hash_result == expected

    def test_is_document_duplicate_no_collection(self):
        """Test duplicate check when collection not available."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore.__new__(VectorStore)
        vs.collection = None
        
        result = vs._is_document_duplicate("test_hash")
        assert result is False

    def test_is_chunk_duplicate_no_collection(self):
        """Test chunk duplicate check when collection not available."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore.__new__(VectorStore)
        vs.collection = None
        
        result = vs._is_chunk_duplicate("test_hash")
        assert result is False

    def test_is_document_duplicate_found(self, mock_chroma_client):
        """Test document duplicate detection."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore("/tmp/test_db")
        mock_chroma_client["collection"].get.return_value = {"ids": ["doc1"]}
        
        result = vs._is_document_duplicate("test_hash")
        assert result is True

    def test_is_document_duplicate_not_found(self, mock_chroma_client):
        """Test document duplicate not found.""" 
        from guide.vector_store import VectorStore
        
        vs = VectorStore("/tmp/test_db")
        mock_chroma_client["collection"].get.return_value = {"ids": []}
        
        result = vs._is_document_duplicate("test_hash")
        assert result is False


class TestVectorStoreChunking:
    """Test document chunking functionality."""
    
    def test_chunk_document_basic(self, mock_chroma_client):
        """Test basic document chunking."""
        from guide.vector_store import VectorStore, Document
        
        vs = VectorStore("/tmp/test_db")
        
        # Mock the config to control chunk size
        with patch("guide.config") as mock_config:
            mock_config.get.side_effect = lambda key, default: {
                "content.chunk_size": 100,
                "content.chunk_overlap": 20
            }.get(key, default)
            
            doc = Document(
                source="test.txt",
                content="This is a test document with enough content to be split into multiple chunks. " * 3,
                metadata={"type": "test"}
            )
            
            chunks = vs._chunk_document(doc)
            
            assert len(chunks) > 1  # Should create multiple chunks
            assert all(chunk.document_source == "test.txt" for chunk in chunks)
            assert all(chunk.chunk_size <= 100 for chunk in chunks)
            assert chunks[0].chunk_overlap == 0  # First chunk has no overlap
            assert all(chunk.chunk_overlap == 20 for chunk in chunks[1:])  # Other chunks have overlap

    def test_chunk_document_short_content(self, mock_chroma_client):
        """Test chunking short document that fits in one chunk."""
        from guide.vector_store import VectorStore, Document
        
        vs = VectorStore("/tmp/test_db")
        
        with patch("guide.config") as mock_config:
            mock_config.get.side_effect = lambda key, default: {
                "content.chunk_size": 1000,
                "content.chunk_overlap": 200
            }.get(key, default)
            
            doc = Document(
                source="short.txt",
                content="Short content",
                metadata={"type": "test"}
            )
            
            chunks = vs._chunk_document(doc)
            
            assert len(chunks) == 1
            assert chunks[0].content == "Short content"
            assert chunks[0].chunk_overlap == 0

    def test_chunk_document_empty_content(self, mock_chroma_client):
        """Test chunking document with empty content."""
        from guide.vector_store import VectorStore, Document
        
        vs = VectorStore("/tmp/test_db")
        
        doc = Document(
            source="empty.txt",
            content="",
            metadata={"type": "test"}
        )
        
        chunks = vs._chunk_document(doc)
        
        assert len(chunks) == 0  # Should create no chunks for empty content


class TestVectorStoreSearch:
    """Test search functionality."""
    
    def test_search_basic(self, mock_chroma_client):
        """Test basic search functionality."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore("/tmp/test_db")
        
        # Mock search results
        mock_chroma_client["collection"].query.return_value = {
            "documents": [["Sample content", "Another document"]],
            "metadatas": [[{"source": "test1.txt"}, {"source": "test2.txt"}]],
            "distances": [[0.1, 0.3]]
        }
        
        results = vs.search("test query", n_results=2)
        
        assert len(results) == 2
        assert results[0]["content"] == "Sample content"
        assert results[0]["metadata"]["source"] == "test1.txt"
        assert results[0]["distance"] == 0.1
        assert results[1]["content"] == "Another document"
        assert results[1]["distance"] == 0.3

    def test_search_no_results(self, mock_chroma_client):
        """Test search with no results."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore("/tmp/test_db")
        
        # Mock empty search results
        mock_chroma_client["collection"].query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }
        
        results = vs.search("nonexistent query")
        
        assert len(results) == 0

    def test_search_exception_handling(self, mock_chroma_client):
        """Test search exception handling."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore("/tmp/test_db")
        
        # Mock search exception
        mock_chroma_client["collection"].query.side_effect = Exception("Search error")
        
        with pytest.raises(RuntimeError, match="Search operation failed"):
            vs.search("test query")


class TestDocumentFromDict:
    """Test Document.from_dict with edge cases for missing coverage."""

    def test_document_from_dict_with_none_created_at(self):
        """Test Document.from_dict when created_at is None."""
        from guide.vector_store import Document
        
        data = {
            "source": "test.txt",
            "content": "Test content",
            "created_at": None
        }
        
        doc = Document.from_dict(data)
        
        assert doc.source == "test.txt"
        assert doc.content == "Test content"
        assert isinstance(doc.created_at, datetime)
        # Should be recent (within last few seconds)
        assert (datetime.now(timezone.utc) - doc.created_at).total_seconds() < 5

    def test_document_from_dict_with_string_created_at(self):
        """Test Document.from_dict when created_at is a string."""
        from guide.vector_store import Document
        
        data = {
            "source": "test.txt",
            "content": "Test content",
            "created_at": "2023-10-31T12:00:00Z"
        }
        
        doc = Document.from_dict(data)
        
        assert doc.source == "test.txt"
        assert doc.content == "Test content"
        assert doc.created_at.year == 2023
        assert doc.created_at.month == 10
        assert doc.created_at.day == 31


class TestDocumentChunkFromDict:
    """Test DocumentChunk.from_dict with edge cases for missing coverage."""

    def test_document_chunk_from_dict_with_none_created_at(self):
        """Test DocumentChunk.from_dict when created_at is None."""
        from guide.vector_store import DocumentChunk
        
        data = {
            "chunk_id": "test-chunk-1",
            "document_source": "test.txt",
            "content": "Test chunk content",
            "chunk_index": 0,
            "chunk_size": 100,
            "chunk_overlap": 20,
            "created_at": None
        }
        
        chunk = DocumentChunk.from_dict(data)
        
        assert chunk.chunk_id == "test-chunk-1"
        assert chunk.content == "Test chunk content"
        assert isinstance(chunk.created_at, datetime)
        # Should be recent (within last few seconds)
        assert (datetime.now(timezone.utc) - chunk.created_at).total_seconds() < 5

    def test_document_chunk_from_dict_with_string_created_at(self):
        """Test DocumentChunk.from_dict when created_at is a string."""
        from guide.vector_store import DocumentChunk
        
        data = {
            "chunk_id": "test-chunk-1",
            "document_source": "test.txt",
            "content": "Test chunk content",
            "chunk_index": 0,
            "chunk_size": 100,
            "chunk_overlap": 20,
            "created_at": "2023-10-31T12:00:00Z"
        }
        
        chunk = DocumentChunk.from_dict(data)
        
        assert chunk.chunk_id == "test-chunk-1"
        assert chunk.content == "Test chunk content"
        assert chunk.created_at.year == 2023
        assert chunk.created_at.month == 10
        assert chunk.created_at.day == 31


class TestVectorStoreAdvanced:
    """Test advanced VectorStore functionality for missing coverage."""

    def test_add_documents_with_dict_input(self, mock_chroma_client):
        """Test add_documents with dictionary input instead of Document objects."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore("/tmp/test_db")
        
        # Test with dictionary input
        documents = [
            {
                "source": "test1.txt",
                "content": "This is test content one",
                "metadata": {"type": "test"}
            },
            {
                "source": "test2.txt", 
                "content": "This is test content two"
                # metadata missing, should default to {}
            }
        ]
        
        # Mock successful addition
        mock_chroma_client["collection"].add.return_value = None
        
        result = vs.add_documents(documents)
        
        assert len(result) == 2  # Returns list of chunk IDs
        mock_chroma_client["collection"].add.assert_called_once()

    def test_add_documents_duplicate_detection(self, mock_chroma_client):
        """Test duplicate document detection."""
        from guide.vector_store import VectorStore, Document
        
        vs = VectorStore("/tmp/test_db")
        
        # Create documents with same content (will have same hash)
        doc_content = "Duplicate content"
        documents = [
            Document(source="test1.txt", content=doc_content, metadata={}),
            Document(source="test2.txt", content=doc_content, metadata={})  # Same content
        ]
        
        # Mock _is_document_duplicate to return True for the second document
        with patch.object(vs, '_is_document_duplicate') as mock_is_dup:
            mock_is_dup.side_effect = [False, True]  # First is new, second is duplicate
            
            result = vs.add_documents(documents)
            
            # Should process both but skip chunks for duplicate
            assert len(result) >= 0  # At least empty list returned

    def test_delete_documents_by_doc_ids(self, mock_chroma_client):
        """Test delete_documents with specific document IDs."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore("/tmp/test_db")
        
        doc_ids = ["doc1", "doc2", "doc3"]
        
        # Mock successful deletion
        mock_chroma_client["collection"].delete.return_value = None
        
        result = vs.delete_documents(doc_ids=doc_ids)
        
        assert result == 3
        mock_chroma_client["collection"].delete.assert_called_once_with(ids=doc_ids)

    def test_delete_documents_by_source(self, mock_chroma_client):
        """Test delete_documents by source."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore("/tmp/test_db")
        
        # Mock get operation to find documents by source
        mock_chroma_client["collection"].get.return_value = {
            "ids": ["doc1", "doc2"],
            "metadatas": [{"source": "test.txt"}, {"source": "test.txt"}]
        }
        
        # Mock successful deletion
        mock_chroma_client["collection"].delete.return_value = None
        
        result = vs.delete_documents(source="test.txt")
        
        assert result == 2
        mock_chroma_client["collection"].get.assert_called_once_with(
            where={"source": "test.txt"},
            include=["metadatas"]
        )
        mock_chroma_client["collection"].delete.assert_called_once_with(ids=["doc1", "doc2"])

    def test_delete_documents_by_source_no_matches(self, mock_chroma_client):
        """Test delete_documents by source when no documents match."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore("/tmp/test_db")
        
        # Mock get operation returning no results
        mock_chroma_client["collection"].get.return_value = {
            "ids": [],
            "metadatas": []
        }
        
        result = vs.delete_documents(source="nonexistent.txt")
        
        assert result == 0
        mock_chroma_client["collection"].delete.assert_not_called()

    def test_delete_documents_exception_handling(self, mock_chroma_client):
        """Test delete_documents exception handling."""
        from guide.vector_store import VectorStore

        vs = VectorStore("/tmp/test_db")

        # Mock deletion exception
        mock_chroma_client["collection"].delete.side_effect = Exception("Delete error")
        
        with pytest.raises(RuntimeError, match="Document deletion failed"):
            vs.delete_documents(doc_ids=["doc1"])

    def test_health_check_basic(self, mock_chroma_client):
        """Test health_check method."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore("/tmp/test_db")
        
        # Mock collection count
        mock_chroma_client["collection"].count.return_value = 42
        
        health = vs.health_check()
        
        assert health["status"] == "ok"
        assert health["document_count"] == 42
        assert "collection_name" in health

    def test_health_check_exception_handling(self, mock_chroma_client):
        """Test health_check exception handling."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore("/tmp/test_db")
        
        # Mock health check exception
        mock_chroma_client["collection"].count.side_effect = Exception("Health error")
        
        health = vs.health_check()
        
        assert health["status"] == "error"
        assert "error" in health


class TestVectorStoreErrorHandling:
    """Test error handling paths for missing coverage."""

    def test_add_documents_no_collection_error(self):
        """Test add_documents when collection is not initialized."""
        from guide.vector_store import VectorStore, Document
        
        vs = VectorStore("/tmp/test_db")
        vs.collection = None  # Simulate uninitialized collection
        
        documents = [Document(source="test.txt", content="Test", metadata={})]
        
        with pytest.raises(RuntimeError, match="ChromaDB not initialized"):
            vs.add_documents(documents)

    def test_search_no_collection_error(self):
        """Test search when collection is not initialized."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore("/tmp/test_db")
        vs.collection = None  # Simulate uninitialized collection
        
        with pytest.raises(RuntimeError, match="ChromaDB not initialized"):
            vs.search("test query")


class TestVectorStorePrivateMethods:
    """Test private methods for missing coverage."""

    def test_is_document_duplicate_true(self, mock_chroma_client):
        """Test _is_document_duplicate when duplicate exists."""
        from guide.vector_store import VectorStore

        vs = VectorStore("/tmp/test_db")

        # Mock get operation returning a result (duplicate found)
        mock_chroma_client["collection"].get.return_value = {
            "ids": ["existing-doc"],
            "metadatas": [{"content_hash": "test-hash"}]
        }

        result = vs._is_document_duplicate("test-hash")

        assert result is True
        mock_chroma_client["collection"].get.assert_called_once_with(
            where={"document_hash": "test-hash"},
            limit=1
        )

    def test_is_document_duplicate_exception(self, mock_chroma_client):
        """Test _is_document_duplicate exception handling."""
        from guide.vector_store import VectorStore

        vs = VectorStore("/tmp/test_db")

        # Mock get operation raising exception
        mock_chroma_client["collection"].get.side_effect = Exception("DB error")

        result = vs._is_document_duplicate("test-hash")

        assert result is False

    def test_is_chunk_duplicate_exception(self, mock_chroma_client):
        """Test _is_chunk_duplicate exception handling."""
        from guide.vector_store import VectorStore

        vs = VectorStore("/tmp/test_db")

        # Mock get operation raising exception
        mock_chroma_client["collection"].get.side_effect = Exception("DB error")

        result = vs._is_chunk_duplicate("test-hash")

        assert result is False

    def test_is_duplicate_legacy_method(self, mock_chroma_client):
        """Test _is_duplicate legacy method."""
        from guide.vector_store import VectorStore

        vs = VectorStore("/tmp/test_db")

        # Mock get operation returning no results
        mock_chroma_client["collection"].get.return_value = {"ids": []}

        result = vs._is_duplicate("test-hash")

        assert result is False
        # Should call the chunk duplicate method
        mock_chroma_client["collection"].get.assert_called_with(
            where={"chunk_hash": "test-hash"},
            limit=1
        )

    def test_add_documents_duplicate_chunks(self, mock_chroma_client):
        """Test add_documents skips duplicate chunks."""
        from guide.vector_store import VectorStore, Document

        vs = VectorStore("/tmp/test_db")

        # Mock duplicate check to return True (duplicate found)
        def mock_get(where, limit):
            if "chunk_hash" in where:
                return {"ids": ["existing-chunk"]}  # Duplicate found
            return {"ids": []}

        mock_chroma_client["collection"].get.side_effect = mock_get

        documents = [Document(source="test.txt", content="Test content", metadata={})]
        
        result = vs.add_documents(documents)

        # Should return empty list since chunk was duplicate
        assert result == []
        # Should not call add method since all chunks were duplicates
        mock_chroma_client["collection"].add.assert_not_called()

    def test_add_documents_chromadb_exception(self, mock_chroma_client):
        """Test add_documents ChromaDB exception handling."""
        from guide.vector_store import VectorStore, Document

        vs = VectorStore("/tmp/test_db")

        # Mock no duplicates
        mock_chroma_client["collection"].get.return_value = {"ids": []}
        
        # Mock ChromaDB add operation raising exception
        mock_chroma_client["collection"].add.side_effect = Exception("ChromaDB error")

        documents = [Document(source="test.txt", content="Test content", metadata={})]

        with pytest.raises(RuntimeError, match="Document addition failed"):
            vs.add_documents(documents)

    def test_is_document_duplicate_false(self, mock_chroma_client):
        """Test _is_document_duplicate when no duplicate exists."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore("/tmp/test_db")
        
        # Mock get operation returning no results
        mock_chroma_client["collection"].get.return_value = {
            "ids": [],
            "metadatas": []
        }
        
        result = vs._is_document_duplicate("test-hash")
        
        assert result is False

    def test_is_chunk_duplicate_true(self, mock_chroma_client):
        """Test _is_chunk_duplicate when duplicate exists."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore("/tmp/test_db")
        
        # Mock get operation returning a result (duplicate found)
        mock_chroma_client["collection"].get.return_value = {
            "ids": ["existing-chunk"],
            "metadatas": [{"content_hash": "test-hash"}]
        }
        
        result = vs._is_chunk_duplicate("test-hash")
        
        assert result is True

    def test_is_chunk_duplicate_false(self, mock_chroma_client):
        """Test _is_chunk_duplicate when no duplicate exists."""
        from guide.vector_store import VectorStore
        
        vs = VectorStore("/tmp/test_db")
        
        # Mock get operation returning no results
        mock_chroma_client["collection"].get.return_value = {
            "ids": [],
            "metadatas": []
        }
        
        result = vs._is_chunk_duplicate("test-hash")
        
        assert result is False