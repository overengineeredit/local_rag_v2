"""
Content management for document ingestion, processing, and chunking.
Handles text files, HTML, URLs with deduplication and metadata extraction.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ContentManager:
    """Manages content ingestion and processing for the RAG system."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """Initialize content manager.

        Args:
            chunk_size: Size of text chunks for vectorization
            chunk_overlap: Overlap between consecutive chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def ingest_file(self, file_path: str) -> list[dict[str, Any]]:
        """Ingest a single file and return processed documents.

        Args:
            file_path: Path to file to ingest

        Returns:
            List of document chunks with metadata

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If file processing fails
        """
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            content = self._read_file(path)
            metadata = self._extract_metadata(path, content)
            chunks = self._chunk_content(content)

            documents = []
            for i, chunk in enumerate(chunks):
                doc = {
                    "content": chunk,
                    "metadata": {
                        **metadata,
                        "chunk_index": i,
                        "chunk_count": len(chunks),
                    },
                }
                documents.append(doc)

            logger.info(f"Processed {path.name}: {len(chunks)} chunks")
            return documents

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            raise ValueError(f"Error processing {file_path}: {e}") from e

    def ingest_directory(self, directory_path: str, recursive: bool = True) -> list[dict[str, Any]]:
        """Ingest all supported files from a directory.

        Args:
            directory_path: Path to directory
            recursive: Whether to process subdirectories

        Returns:
            List of all processed documents

        Raises:
            NotADirectoryError: If the path is not a directory
            ValueError: If directory processing fails
        """
        path = Path(directory_path)
        all_documents = []

        if not path.is_dir():
            logger.error(f"Not a directory: {directory_path}")
            raise NotADirectoryError(f"Not a directory: {directory_path}")

        pattern = "**/*" if recursive else "*"
        supported_extensions = {".txt", ".md", ".html", ".htm"}

        for file_path in path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                documents = self.ingest_file(str(file_path))
                all_documents.extend(documents)

        logger.info(f"Processed directory {path.name}: {len(all_documents)} total documents")
        return all_documents

    def ingest_url(self, url: str) -> list[dict[str, Any]]:
        """Ingest content from a URL.

        Args:
            url: URL to fetch and process

        Returns:
            List of document chunks
        """
        # TODO: Implement URL fetching and processing
        logger.info(f"Ingesting URL: {url}")

        # Placeholder implementation
        content = f"Content from {url} (placeholder)"
        metadata = {
            "source": url,
            "title": "URL Title",
            "timestamp": datetime.now().isoformat(),
            "content_hash": hashlib.sha256(content.encode()).hexdigest(),
        }

        chunks = self._chunk_content(content)
        documents = []
        for i, chunk in enumerate(chunks):
            doc = {
                "content": chunk,
                "metadata": {**metadata, "chunk_index": i, "chunk_count": len(chunks)},
            }
            documents.append(doc)

        return documents

    def _read_file(self, path: Path) -> str:
        """Read file content based on extension."""
        if path.suffix.lower() in {".html", ".htm"}:
            return self._extract_html_text(path)
        else:
            return path.read_text(encoding="utf-8", errors="ignore")

    def _extract_html_text(self, path: Path) -> str:
        """Extract text content from HTML file."""
        # TODO: Implement proper HTML parsing
        content = path.read_text(encoding="utf-8", errors="ignore")
        # Placeholder: just return raw content for now
        return content

    def _extract_metadata(self, path: Path, content: str) -> dict[str, Any]:
        """Extract metadata from file and content."""
        # Extract title (first line or filename)
        lines = content.strip().split("\n")
        title = lines[0].strip() if lines else path.stem

        # Remove common markdown/html prefixes
        title = title.lstrip("#").strip()
        if title.startswith("<title>") and title.endswith("</title>"):
            title = title[7:-8]

        return {
            "source": str(path),
            "title": title or path.stem,
            "timestamp": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        }

    def _chunk_content(self, content: str) -> list[str]:
        """Split content into overlapping chunks."""
        # Simple word-based chunking
        words = content.split()
        chunks = []

        start = 0
        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk = " ".join(words[start:end])
            chunks.append(chunk)

            if end >= len(words):
                break

            # Ensure we always move forward, even with large overlap
            next_start = end - self.chunk_overlap
            start = max(next_start, start + 1)  # Always advance at least 1 position

        return chunks if chunks else [content]
