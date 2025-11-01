"""
Model Management for Local RAG system.
Handles GGUF model downloading, validation, and storage management.
"""

from __future__ import annotations

import hashlib
import json
import logging
import struct
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import config


class ModelValidationError(Exception):
    """Exception raised when model validation fails."""

    pass


class ModelDownloadError(Exception):
    """Exception raised when model download fails."""

    pass


class ModelManager:
    """Manages GGUF model lifecycle: download, validation, storage."""

    def __init__(self):
        """Initialize model manager with configuration."""
        self.logger = logging.getLogger(f"{__name__}.ModelManager")

        # Get model storage configuration
        self.models_dir = Path(config.get("models.storage_path", "data/models"))
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Download configuration
        self.download_timeout = config.get("models.download_timeout", 3600)  # 1 hour
        self.chunk_size = config.get("models.download_chunk_size", 8192)  # 8KB chunks
        self.max_retries = config.get("models.download_max_retries", 3)

        # Model metadata cache
        self.metadata_file = self.models_dir / "models_metadata.json"
        self.metadata = self._load_metadata()

        # Setup HTTP session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504, 429],
            allowed_methods=["GET", "HEAD"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _load_metadata(self) -> dict[str, Any]:
        """Load model metadata from cache file.

        Returns:
            Dictionary of model metadata or empty dict if not found
        """
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                self.logger.warning(f"Failed to load model metadata: {e}")

        return {}

    def _save_metadata(self) -> None:
        """Save model metadata to cache file."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except OSError as e:
            self.logger.error(f"Failed to save model metadata: {e}")

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file.

        Args:
            file_path: Path to file to hash

        Returns:
            SHA256 hash as hex string
        """
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(self.chunk_size), b""):
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    def _validate_gguf_header(self, file_path: Path) -> dict[str, Any]:
        """Validate GGUF file format and extract metadata.

        Args:
            file_path: Path to GGUF file

        Returns:
            Dictionary with GGUF metadata

        Raises:
            ModelValidationError: If file is not valid GGUF format
        """
        try:
            with open(file_path, "rb") as f:
                # Read GGUF magic number (first 4 bytes)
                magic = f.read(4)

                if magic != b"GGUF":
                    raise ModelValidationError(f"Invalid GGUF magic number: {magic}")

                # Read version (4 bytes, little endian)
                version_bytes = f.read(4)
                version = struct.unpack("<I", version_bytes)[0]

                if version < 2:
                    raise ModelValidationError(f"Unsupported GGUF version: {version}")

                # Read tensor count (8 bytes, little endian)
                tensor_count_bytes = f.read(8)
                tensor_count = struct.unpack("<Q", tensor_count_bytes)[0]

                # Read metadata count (8 bytes, little endian)
                metadata_count_bytes = f.read(8)
                metadata_count = struct.unpack("<Q", metadata_count_bytes)[0]

                return {
                    "version": version,
                    "tensor_count": tensor_count,
                    "metadata_count": metadata_count,
                    "valid": True,
                }

        except (OSError, struct.error) as e:
            raise ModelValidationError(f"Failed to read GGUF header: {e}")

    def validate_model(self, file_path: Path, expected_hash: str | None = None) -> dict[str, Any]:
        """Validate a GGUF model file.

        Args:
            file_path: Path to model file
            expected_hash: Optional expected SHA256 hash

        Returns:
            Dictionary with validation results

        Raises:
            ModelValidationError: If validation fails
        """
        if not file_path.exists():
            raise ModelValidationError(f"Model file not found: {file_path}")

        # Check file size
        file_size = file_path.stat().st_size
        if file_size == 0:
            raise ModelValidationError("Model file is empty")

        # Validate GGUF format
        gguf_info = self._validate_gguf_header(file_path)

        # Calculate and verify hash if provided
        calculated_hash = self._calculate_file_hash(file_path)

        if expected_hash and calculated_hash != expected_hash.lower():
            raise ModelValidationError(
                f"Hash mismatch - expected: {expected_hash.lower()}, got: {calculated_hash}",
            )

        validation_result = {
            "valid": True,
            "file_size": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "sha256": calculated_hash,
            "gguf_info": gguf_info,
            "validated_at": time.time(),
        }

        self.logger.info(
            f"Model validation successful: {file_path.name}",
            extra={
                "file_size_mb": validation_result["file_size_mb"],
                "tensor_count": gguf_info["tensor_count"],
                "gguf_version": gguf_info["version"],
            },
        )

        return validation_result

    def download_model(
        self,
        url: str,
        model_name: str | None = None,
        expected_hash: str | None = None,
    ) -> Path:
        """Download a GGUF model from URL.

        Args:
            url: URL to download model from
            model_name: Optional custom model name (defaults to filename from URL)
            expected_hash: Optional expected SHA256 hash for validation

        Returns:
            Path to downloaded model file

        Raises:
            ModelDownloadError: If download fails
            ModelValidationError: If downloaded model validation fails
        """
        # Parse URL to get filename
        parsed_url = urlparse(url)
        if not model_name:
            model_name = Path(parsed_url.path).name

        if not model_name.endswith(".gguf"):
            model_name += ".gguf"

        model_path = self.models_dir / model_name
        temp_path = model_path.with_suffix(".tmp")

        self.logger.info(
            f"Starting model download: {url}",
            extra={"model_name": model_name, "destination": str(model_path)},
        )

        try:
            # Download with progress tracking
            with self.session.get(url, stream=True, timeout=self.download_timeout) as response:
                response.raise_for_status()

                # Get content length if available
                content_length = response.headers.get("Content-Length")
                total_size = int(content_length) if content_length else None

                downloaded_size = 0
                last_log_time = time.time()

                with open(temp_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:  # Filter out keep-alive chunks
                            f.write(chunk)
                            downloaded_size += len(chunk)

                            # Log progress every 30 seconds
                            current_time = time.time()
                            if current_time - last_log_time >= 30:
                                if total_size:
                                    progress = (downloaded_size / total_size) * 100
                                    self.logger.info(
                                        f"Download progress: {progress:.1f}%",
                                        extra={
                                            "downloaded_mb": round(
                                                downloaded_size / (1024 * 1024),
                                                2,
                                            ),
                                            "total_mb": round(total_size / (1024 * 1024), 2),
                                            "model_name": model_name,
                                        },
                                    )
                                else:
                                    self.logger.info(
                                        f"Downloaded: {downloaded_size / (1024 * 1024):.2f} MB",
                                        extra={"model_name": model_name},
                                    )
                                last_log_time = current_time

            # Validate downloaded model
            validation_result = self.validate_model(temp_path, expected_hash)

            # Move from temp to final location
            temp_path.rename(model_path)

            # Update metadata
            self.metadata[model_name] = {
                "url": url,
                "downloaded_at": time.time(),
                "file_path": str(model_path),
                **validation_result,
            }
            self._save_metadata()

            self.logger.info(
                f"Model download completed: {model_name}",
                extra={
                    "file_size_mb": validation_result["file_size_mb"],
                    "duration": time.time() - (validation_result["validated_at"] - 10),  # Approximate
                },
            )

            return model_path

        except requests.RequestException as e:
            # Clean up temp file on failure
            if temp_path.exists():
                temp_path.unlink()
            raise ModelDownloadError(f"Download failed: {e}")

        except ModelValidationError:
            # Clean up temp file on validation failure
            if temp_path.exists():
                temp_path.unlink()
            raise

        except Exception as e:
            # Clean up temp file on any other failure
            if temp_path.exists():
                temp_path.unlink()
            raise ModelDownloadError(f"Unexpected error during download: {e}")

    def get_model_path(self, model_name: str) -> Path | None:
        """Get path to a model by name.

        Args:
            model_name: Name of the model

        Returns:
            Path to model file or None if not found
        """
        if model_name in self.metadata:
            model_path = Path(self.metadata[model_name]["file_path"])
            if model_path.exists():
                return model_path
            else:
                # Remove stale metadata
                del self.metadata[model_name]
                self._save_metadata()

        # Check if file exists directly
        model_path = self.models_dir / model_name
        if model_path.exists():
            return model_path

        return None

    def list_models(self) -> dict[str, dict[str, Any]]:
        """List all available models with metadata.

        Returns:
            Dictionary mapping model names to their metadata
        """
        # Clean up stale entries
        stale_models = []
        for model_name, metadata in self.metadata.items():
            model_path = Path(metadata["file_path"])
            if not model_path.exists():
                stale_models.append(model_name)

        for model_name in stale_models:
            del self.metadata[model_name]

        if stale_models:
            self._save_metadata()

        return self.metadata.copy()

    def delete_model(self, model_name: str) -> bool:
        """Delete a model from storage.

        Args:
            model_name: Name of model to delete

        Returns:
            True if model was deleted, False if not found
        """
        model_path = self.get_model_path(model_name)

        if not model_path:
            return False

        try:
            model_path.unlink()

            # Remove from metadata
            if model_name in self.metadata:
                del self.metadata[model_name]
                self._save_metadata()

            self.logger.info(f"Model deleted: {model_name}")
            return True

        except OSError as e:
            self.logger.error(f"Failed to delete model {model_name}: {e}")
            return False

    def get_storage_info(self) -> dict[str, Any]:
        """Get information about model storage usage.

        Returns:
            Dictionary with storage statistics
        """
        total_size = 0
        model_count = 0

        for model_file in self.models_dir.glob("*.gguf"):
            if model_file.is_file():
                total_size += model_file.stat().st_size
                model_count += 1

        return {
            "models_directory": str(self.models_dir),
            "total_models": model_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2),
        }
