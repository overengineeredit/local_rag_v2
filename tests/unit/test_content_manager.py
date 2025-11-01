"""Tests for the ContentManager class."""

import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from guide.content_manager import ContentManager


class TestContentManager:
    """Test the ContentManager class."""

    def test_init_default_params(self):
        """Test ContentManager initialization with default parameters."""
        cm = ContentManager()
        assert cm.chunk_size == 512
        assert cm.chunk_overlap == 50

    def test_init_custom_params(self):
        """Test ContentManager initialization with custom parameters."""
        cm = ContentManager(chunk_size=1000, chunk_overlap=100)
        assert cm.chunk_size == 1000
        assert cm.chunk_overlap == 100

    def test_ingest_file_not_found(self):
        """Test ingest_file with non-existent file raises FileNotFoundError."""
        cm = ContentManager()

        with pytest.raises(FileNotFoundError) as exc_info:
            cm.ingest_file("/nonexistent/file.txt")

        assert "File not found: /nonexistent/file.txt" in str(exc_info.value)

    def test_ingest_file_success_text(self):
        """Test successful ingestion of a text file."""
        cm = ContentManager(chunk_size=5, chunk_overlap=2)  # Small chunks for testing

        content = "This is a test file with some content for chunking."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            f.flush()

            try:
                result = cm.ingest_file(f.name)

                assert len(result) > 0
                assert all("content" in doc for doc in result)
                assert all("metadata" in doc for doc in result)

                # Check metadata structure
                metadata = result[0]["metadata"]
                assert "source" in metadata
                assert "title" in metadata
                assert "timestamp" in metadata
                assert "content_hash" in metadata
                assert "chunk_index" in metadata
                assert "chunk_count" in metadata

                # Verify content hash
                expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
                assert metadata["content_hash"] == expected_hash

            finally:
                Path(f.name).unlink()

    def test_ingest_file_html(self):
        """Test ingesting an HTML file."""
        cm = ContentManager()

        html_content = "<html><head><title>Test Page</title></head><body>Some content</body></html>"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            f.flush()

            try:
                result = cm.ingest_file(f.name)

                assert len(result) > 0
                # Verify it uses HTML processing path
                assert (
                    result[0]["content"] == html_content
                )  # Currently just returns raw content

            finally:
                Path(f.name).unlink()

    def test_ingest_file_error_handling(self):
        """Test error handling during file ingestion."""
        cm = ContentManager()

        with patch("guide.content_manager.Path") as mock_path:
            mock_path_instance = mock_path.return_value
            mock_path_instance.exists.return_value = True
            mock_path_instance.read_text.side_effect = Exception("Read error")

            with pytest.raises(ValueError) as exc_info:
                cm.ingest_file("/some/file.txt")

            assert "Error processing /some/file.txt: Read error" in str(exc_info.value)

    def test_ingest_directory_not_directory(self):
        """Test ingesting a path that's not a directory."""
        cm = ContentManager()

        with pytest.raises(NotADirectoryError) as exc_info:
            cm.ingest_directory("/not/a/directory")

        assert "Not a directory: /not/a/directory" in str(exc_info.value)

    def test_ingest_directory_success(self):
        """Test successful directory ingestion."""
        cm = ContentManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            (temp_path / "file1.txt").write_text("Content of file 1")
            (temp_path / "file2.md").write_text("# File 2\nMarkdown content")
            (temp_path / "file3.html").write_text(
                "<html><body>HTML content</body></html>"
            )
            (temp_path / "ignored.pdf").write_text("Should be ignored")

            # Create subdirectory
            sub_dir = temp_path / "subdir"
            sub_dir.mkdir()
            (sub_dir / "file4.txt").write_text("Content in subdirectory")

            result = cm.ingest_directory(str(temp_path), recursive=True)

            # Should process .txt, .md, .html files but not .pdf
            assert len(result) == 4  # 4 files with content

            sources = [doc["metadata"]["source"] for doc in result]
            assert any("file1.txt" in source for source in sources)
            assert any("file2.md" in source for source in sources)
            assert any("file3.html" in source for source in sources)
            assert any("file4.txt" in source for source in sources)
            assert not any("ignored.pdf" in source for source in sources)

    def test_ingest_directory_non_recursive(self):
        """Test directory ingestion without recursion."""
        cm = ContentManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            (temp_path / "file1.txt").write_text("Content of file 1")

            # Create subdirectory with file
            sub_dir = temp_path / "subdir"
            sub_dir.mkdir()
            (sub_dir / "file2.txt").write_text("Content in subdirectory")

            result = cm.ingest_directory(str(temp_path), recursive=False)

            # Should only process top-level files
            assert len(result) == 1
            assert "file1.txt" in result[0]["metadata"]["source"]

    def test_ingest_url_placeholder(self):
        """Test URL ingestion (placeholder implementation)."""
        cm = ContentManager()

        url = "https://example.com/page"
        result = cm.ingest_url(url)

        assert len(result) > 0
        assert result[0]["metadata"]["source"] == url
        assert "URL Title" in result[0]["metadata"]["title"]
        assert "placeholder" in result[0]["content"]

    def test_read_file_text(self):
        """Test reading a text file."""
        cm = ContentManager()

        content = "Test file content"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            f.flush()

            try:
                path = Path(f.name)
                result = cm._read_file(path)

                assert result == content

            finally:
                Path(f.name).unlink()

    def test_read_file_html(self):
        """Test reading an HTML file."""
        cm = ContentManager()

        html_content = "<html><body>Test content</body></html>"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            f.flush()

            try:
                path = Path(f.name)
                result = cm._read_file(path)

                # Currently returns raw HTML content
                assert result == html_content

            finally:
                Path(f.name).unlink()

    def test_extract_html_text(self):
        """Test HTML text extraction (placeholder implementation)."""
        cm = ContentManager()

        html_content = (
            "<html><head><title>Test</title></head><body>Content</body></html>"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            f.flush()

            try:
                path = Path(f.name)
                result = cm._extract_html_text(path)

                # Currently just returns raw content
                assert result == html_content

            finally:
                Path(f.name).unlink()

    def test_extract_metadata_basic(self):
        """Test basic metadata extraction."""
        cm = ContentManager()

        content = "This is the title\nThis is the body content."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            f.flush()

            try:
                path = Path(f.name)
                metadata = cm._extract_metadata(path, content)

                assert metadata["source"] == str(path)
                assert metadata["title"] == "This is the title"
                assert "timestamp" in metadata
                assert "content_hash" in metadata

                # Verify hash
                expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
                assert metadata["content_hash"] == expected_hash

            finally:
                Path(f.name).unlink()

    def test_extract_metadata_markdown_title(self):
        """Test metadata extraction with markdown title."""
        cm = ContentManager()

        content = "# Markdown Title\nContent follows."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()

            try:
                path = Path(f.name)
                metadata = cm._extract_metadata(path, content)

                assert metadata["title"] == "Markdown Title"
                assert metadata["source"] == str(path)

            finally:
                Path(f.name).unlink()

    def test_extract_metadata_html_title(self):
        """Test metadata extraction with HTML title."""
        cm = ContentManager()

        content = "<title>HTML Title</title>\nContent follows."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(content)
            f.flush()

            try:
                path = Path(f.name)
                metadata = cm._extract_metadata(path, content)

                assert metadata["title"] == "HTML Title"
                assert metadata["source"] == str(path)

            finally:
                Path(f.name).unlink()

    def test_extract_metadata_empty_content(self):
        """Test metadata extraction with empty content."""
        cm = ContentManager()

        content = ""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            f.flush()

            try:
                path = Path(f.name)
                metadata = cm._extract_metadata(path, content)

                # Should fall back to filename stem
                assert metadata["title"] == path.stem
                assert metadata["source"] == str(path)

            finally:
                Path(f.name).unlink()

    def test_extract_metadata_whitespace_only(self):
        """Test metadata extraction with whitespace-only content."""
        cm = ContentManager()

        content = "   \n\n   "

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            f.flush()

            try:
                path = Path(f.name)
                metadata = cm._extract_metadata(path, content)

                # Should fall back to filename stem
                assert metadata["title"] == path.stem
                assert metadata["source"] == str(path)

            finally:
                Path(f.name).unlink()

    def test_chunk_content_small_content(self):
        """Test chunking content smaller than chunk size."""
        cm = ContentManager(chunk_size=10, chunk_overlap=2)

        content = "Small content"
        chunks = cm._chunk_content(content)

        assert len(chunks) == 1
        assert chunks[0] == content

    def test_chunk_content_large_content(self):
        """Test chunking large content."""
        cm = ContentManager(chunk_size=3, chunk_overlap=1)  # Small chunks for testing

        # Create content with 10 words
        words = ["word" + str(i) for i in range(10)]
        content = " ".join(words)

        chunks = cm._chunk_content(content)

        # Should create multiple chunks
        assert len(chunks) > 1

        # First chunk should have first 3 words
        assert chunks[0] == "word0 word1 word2"

        # Second chunk should start from word 2 (overlap of 1)
        assert chunks[1] == "word2 word3 word4"

    def test_chunk_content_exact_boundary(self):
        """Test chunking when content length exactly matches chunk size."""
        cm = ContentManager(chunk_size=3, chunk_overlap=1)

        content = "word1 word2 word3"  # Exactly 3 words
        chunks = cm._chunk_content(content)

        assert len(chunks) == 1
        assert chunks[0] == content

    def test_chunk_content_empty(self):
        """Test chunking empty content."""
        cm = ContentManager()

        content = ""
        chunks = cm._chunk_content(content)

        assert len(chunks) == 1
        assert chunks[0] == ""

    def test_chunk_content_whitespace_only(self):
        """Test chunking whitespace-only content."""
        cm = ContentManager()

        content = "   \n\t   "
        chunks = cm._chunk_content(content)

        # Split creates empty words, so this should return the original content
        assert len(chunks) == 1
        assert chunks[0] == content

    def test_chunk_content_overlap_larger_than_chunk(self):
        """Test chunking when overlap is larger than chunk size."""
        cm = ContentManager(chunk_size=2, chunk_overlap=5)  # Overlap > chunk_size

        words = ["word" + str(i) for i in range(10)]
        content = " ".join(words)

        chunks = cm._chunk_content(content)

        # Should still work, though overlap behavior may be unusual
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    @patch("guide.content_manager.logger")
    def test_logging_file_not_found(self, mock_logger):
        """Test logging when file is not found."""
        cm = ContentManager()

        with pytest.raises(FileNotFoundError):
            cm.ingest_file("/nonexistent/file.txt")

        mock_logger.error.assert_called_with("File not found: /nonexistent/file.txt")

    @patch("guide.content_manager.logger")
    def test_logging_file_processing_success(self, mock_logger):
        """Test logging when file processing succeeds."""
        cm = ContentManager()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            f.flush()

            try:
                cm.ingest_file(f.name)

                # Should log success
                path = Path(f.name)
                mock_logger.info.assert_called_with(f"Processed {path.name}: 1 chunks")

            finally:
                Path(f.name).unlink()

    @patch("guide.content_manager.logger")
    def test_logging_file_processing_error(self, mock_logger):
        """Test logging when file processing fails."""
        cm = ContentManager()

        with patch("guide.content_manager.Path") as mock_path:
            mock_path_instance = mock_path.return_value
            mock_path_instance.exists.return_value = True
            mock_path_instance.read_text.side_effect = Exception("Read error")

            with pytest.raises(ValueError):
                cm.ingest_file("/some/file.txt")

            mock_logger.error.assert_called_with(
                "Error processing /some/file.txt: Read error"
            )

    @patch("guide.content_manager.logger")
    def test_logging_directory_processing(self, mock_logger):
        """Test logging during directory processing."""
        cm = ContentManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "file1.txt").write_text("Content 1")

            cm.ingest_directory(str(temp_path))

            # Should log directory processing completion
            mock_logger.info.assert_called_with(
                f"Processed directory {temp_path.name}: 1 total documents",
            )

    @patch("guide.content_manager.logger")
    def test_logging_directory_not_found(self, mock_logger):
        """Test logging when directory is not found."""
        cm = ContentManager()

        with pytest.raises(NotADirectoryError):
            cm.ingest_directory("/not/a/directory")

        mock_logger.error.assert_called_with("Not a directory: /not/a/directory")

    @patch("guide.content_manager.logger")
    def test_logging_url_ingestion(self, mock_logger):
        """Test logging during URL ingestion."""
        cm = ContentManager()

        url = "https://example.com/page"
        cm.ingest_url(url)

        mock_logger.info.assert_called_with(f"Ingesting URL: {url}")
