"""
Vector store interface using ChromaDB for document storage and retrieval.
Handles embeddings, similarity search, and metadata management.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Entity model for documents in the RAG system."""

    source: str  # File path, URL, or source identifier
    content: str  # Full document content
    metadata: dict[str, Any] = field(default_factory=dict)
    content_hash: str = field(init=False)  # Auto-calculated
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self):
        """Calculate content hash after initialization."""
        self.content_hash = self._calculate_hash(self.content)

    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content for deduplication."""
        normalized = content.strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Convert document to dictionary for storage."""
        return {
            "source": self.source,
            "content": self.content,
            "metadata": self.metadata,
            "content_hash": self.content_hash,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Document:
        """Create document from dictionary."""
        # Parse created_at if it's a string
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif created_at is None:
            created_at = datetime.now(UTC)

        return cls(
            source=data["source"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            created_at=created_at,
        )


@dataclass
class DocumentChunk:
    """Entity model for document chunks in the vector store."""

    chunk_id: str  # Unique identifier for the chunk
    document_source: str  # Source document identifier
    content: str  # Chunk content
    chunk_index: int  # Position within the document
    chunk_size: int  # Size of this chunk
    chunk_overlap: int  # Overlap with adjacent chunks
    metadata: dict[str, Any] = field(default_factory=dict)
    content_hash: str = field(init=False)  # Auto-calculated
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self):
        """Calculate content hash after initialization."""
        self.content_hash = self._calculate_hash(self.content)

    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content for deduplication."""
        normalized = content.strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Convert chunk to dictionary for storage."""
        return {
            "chunk_id": self.chunk_id,
            "document_source": self.document_source,
            "content": self.content,
            "chunk_index": self.chunk_index,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "metadata": self.metadata,
            "content_hash": self.content_hash,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentChunk:
        """Create chunk from dictionary."""
        # Parse created_at if it's a string
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif created_at is None:
            created_at = datetime.now(UTC)

        return cls(
            chunk_id=data["chunk_id"],
            document_source=data["document_source"],
            content=data["content"],
            chunk_index=data["chunk_index"],
            chunk_size=data["chunk_size"],
            chunk_overlap=data["chunk_overlap"],
            metadata=data.get("metadata", {}),
            created_at=created_at,
        )

    @classmethod
    def create_chunk_id(
        cls, document_source: str, chunk_index: int, content_hash: str
    ) -> str:
        """Create a unique chunk ID."""
        # Combine document source, chunk index, and first 8 chars of content hash
        source_hash = hashlib.sha256(document_source.encode()).hexdigest()[:8]
        return f"chunk_{source_hash}_{chunk_index:04d}_{content_hash[:8]}"


class VectorStore:
    """ChromaDB-based vector store for document embeddings."""

    def __init__(self, persist_directory: str, collection_name: str = "documents"):
        """Initialize ChromaDB vector store.

        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the ChromaDB collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize ChromaDB client and collection."""
        logger.info(f"Initializing ChromaDB at {self.persist_directory}")

        # Ensure persist directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        try:
            # Configure ChromaDB with SQLite backend for embedded operation
            settings = Settings(
                persist_directory=self.persist_directory,
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True,
            )

            # Initialize persistent client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory, settings=settings
            )

            # Get or create collection with default embedding function
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},  # Use cosine similarity
            )

            logger.info(
                f"ChromaDB initialized successfully: collection '{self.collection_name}'"
            )

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise RuntimeError(f"ChromaDB initialization failed: {e}") from e

    def add_documents(self, documents: list[Document | dict[str, Any]]) -> list[str]:
        """Add documents to the vector store.

        Args:
            documents: List of Document objects or dictionaries with 'content', 'metadata'

        Returns:
            List of document chunk IDs that were added
        """
        if not self.collection:
            raise RuntimeError("ChromaDB not initialized")

        chunk_ids = []
        contents = []
        metadatas = []
        ids = []

        for doc in documents:
            # Handle both Document objects and dictionaries
            if isinstance(doc, Document):
                document = doc
            else:
                # Convert dictionary to Document object
                document = Document(
                    source=doc.get("source", "unknown"),
                    content=doc["content"],
                    metadata=doc.get("metadata", {}),
                )

            # Check for duplicates at document level
            if self._is_document_duplicate(document.content_hash):
                logger.info(f"Duplicate document detected: {document.content_hash[:8]}")
                continue

            # Chunk the document
            chunks = self._chunk_document(document)

            # Prepare chunks for batch insert
            for chunk in chunks:
                # Check for duplicate chunks
                if self._is_chunk_duplicate(chunk.content_hash):
                    logger.info(f"Duplicate chunk detected: {chunk.content_hash[:8]}")
                    continue

                chunk_ids.append(chunk.chunk_id)
                contents.append(chunk.content)

                # Combine document and chunk metadata
                combined_metadata = {
                    **document.metadata,
                    **chunk.metadata,
                    "document_source": chunk.document_source,
                    "chunk_index": chunk.chunk_index,
                    "chunk_size": chunk.chunk_size,
                    "chunk_overlap": chunk.chunk_overlap,
                    "document_hash": document.content_hash,
                    "chunk_hash": chunk.content_hash,
                    "created_at": chunk.created_at.isoformat(),
                }
                metadatas.append(combined_metadata)
                ids.append(chunk.chunk_id)

        # Batch add to ChromaDB
        if contents:
            try:
                self.collection.add(documents=contents, metadatas=metadatas, ids=ids)
                logger.info(f"Added {len(contents)} document chunks to ChromaDB")
            except Exception as e:
                logger.error(f"Failed to add documents to ChromaDB: {e}")
                raise RuntimeError(f"Document addition failed: {e}") from e

        return chunk_ids

    def search(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Search for similar documents.

        Args:
            query: Query text
            n_results: Number of results to return

        Returns:
            List of matching documents with metadata
        """
        if not self.collection:
            raise RuntimeError("ChromaDB not initialized")

        logger.info(f"Searching for: {query}")

        try:
            # Perform similarity search
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )

            # Format results
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append(
                        {
                            "content": doc,
                            "metadata": (
                                results["metadatas"][0][i]
                                if results["metadatas"]
                                else {}
                            ),
                            "distance": (
                                results["distances"][0][i]
                                if results["distances"]
                                else 0.0
                            ),
                        },
                    )

            logger.info(f"Found {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise RuntimeError(f"Search operation failed: {e}") from e

    def delete_documents(
        self, source: str | None = None, doc_ids: list[str] | None = None
    ) -> int:
        """Delete documents by source or IDs.

        Args:
            source: Source path to delete all documents from
            doc_ids: Specific document IDs to delete

        Returns:
            Number of documents deleted
        """
        if not self.collection:
            raise RuntimeError("ChromaDB not initialized")

        logger.info(f"Deleting documents: source={source}, ids={doc_ids}")

        try:
            deleted_count = 0

            if doc_ids:
                # Delete specific document IDs
                self.collection.delete(ids=doc_ids)
                deleted_count = len(doc_ids)

            elif source:
                # Find and delete all documents from source
                results = self.collection.get(
                    where={"source": source}, include=["metadatas"]
                )
                if results["ids"]:
                    self.collection.delete(ids=results["ids"])
                    deleted_count = len(results["ids"])

            logger.info(f"Deleted {deleted_count} documents")
            return deleted_count

        except Exception as e:
            logger.error(f"Deletion failed: {e}")
            raise RuntimeError(f"Document deletion failed: {e}") from e

    def clear_all_documents(self) -> int:
        """Clear all documents from the vector store.

        Returns:
            Number of documents deleted
        """
        if not self.collection:
            raise RuntimeError("ChromaDB not initialized")

        logger.info("Clearing all documents from vector store")

        try:
            # Get all document IDs
            results = self.collection.get(include=["metadatas"])
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                deleted_count = len(results["ids"])
                logger.info(f"Cleared {deleted_count} documents from vector store")
                return deleted_count
            else:
                logger.info("No documents to clear")
                return 0

        except Exception as e:
            logger.error(f"Clear all failed: {e}")
            raise RuntimeError(f"Clear all documents failed: {e}") from e

    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content for deduplication."""
        normalized = content.strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _is_duplicate(self, content_hash: str) -> bool:
        """Check if content hash already exists (legacy method)."""
        return self._is_chunk_duplicate(content_hash)

    def _is_document_duplicate(self, content_hash: str) -> bool:
        """Check if document hash already exists."""
        if not self.collection:
            return False

        try:
            results = self.collection.get(
                where={"document_hash": content_hash}, limit=1
            )
            return len(results["ids"]) > 0
        except Exception as e:
            logger.warning(f"Document duplicate check failed: {e}")
            return False

    def _is_chunk_duplicate(self, content_hash: str) -> bool:
        """Check if chunk hash already exists."""
        if not self.collection:
            return False

        try:
            results = self.collection.get(where={"chunk_hash": content_hash}, limit=1)
            return len(results["ids"]) > 0
        except Exception as e:
            logger.warning(f"Chunk duplicate check failed: {e}")
            return False

    def _chunk_document(self, document: Document) -> list[DocumentChunk]:
        """Split document into chunks for vector storage."""
        from . import config

        # Get chunking configuration
        chunk_size = config.get("content.chunk_size", 1000)
        chunk_overlap = config.get("content.chunk_overlap", 200)

        content = document.content
        chunks = []

        # Simple text chunking - split by characters with overlap
        start = 0
        chunk_index = 0

        while start < len(content):
            # Calculate end position
            end = min(start + chunk_size, len(content))

            # Try to break at word boundaries
            if end < len(content):
                # Look for space within last 50 characters
                last_space = content.rfind(" ", max(start, end - 50), end)
                if last_space > start:
                    end = last_space

            # Extract chunk content
            chunk_content = content[start:end].strip()

            if chunk_content:  # Only create non-empty chunks
                # Create chunk ID
                chunk_hash = hashlib.sha256(chunk_content.encode()).hexdigest()
                chunk_id = DocumentChunk.create_chunk_id(
                    document.source, chunk_index, chunk_hash
                )

                # Create chunk object
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    document_source=document.source,
                    content=chunk_content,
                    chunk_index=chunk_index,
                    chunk_size=len(chunk_content),
                    chunk_overlap=chunk_overlap if chunk_index > 0 else 0,
                    metadata={
                        "document_created_at": document.created_at.isoformat(),
                        "source_type": document.metadata.get("source_type", "unknown"),
                    },
                )

                chunks.append(chunk)
                chunk_index += 1

            # Move start position with overlap
            if end >= len(content):
                break

            start = max(start + 1, end - chunk_overlap)

        logger.info(f"Split document into {len(chunks)} chunks")
        return chunks

    def health_check(self) -> dict:
        """Check vector store health."""
        try:
            if not self.client or not self.collection:
                return {
                    "status": "error",
                    "persist_directory": self.persist_directory,
                    "collection_name": self.collection_name,
                    "connected": False,
                    "error": "Client or collection not initialized",
                }

            # Test basic operations
            count = self.collection.count()

            return {
                "status": "ok",
                "persist_directory": self.persist_directory,
                "collection_name": self.collection_name,
                "connected": True,
                "document_count": count,
                "backend": "SQLite (embedded)",
            }

        except Exception as e:
            return {
                "status": "error",
                "persist_directory": self.persist_directory,
                "collection_name": self.collection_name,
                "connected": False,
                "error": str(e),
            }
