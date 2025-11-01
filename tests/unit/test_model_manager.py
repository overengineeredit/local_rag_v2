"""
Unit tests for model management infrastructure.
Tests ModelManager class functionality and GGUF validation.
"""

import sys
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


def test_model_manager_import():
    """Test that ModelManager can be imported."""
    from guide.model_manager import ModelManager
    
    assert ModelManager is not None


def test_model_manager_initialization():
    """Test ModelManager initialization."""
    from guide.model_manager import ModelManager
    
    with patch('guide.config.get') as mock_config:
        mock_config.side_effect = lambda key, default: {
            "models.storage_path": "test_models",
            "models.download_timeout": 1800,
            "models.download_chunk_size": 4096,
            "models.download_max_retries": 2
        }.get(key, default)
        
        mm = ModelManager()
        
        assert mm.models_dir.name == "test_models"
        assert mm.download_timeout == 1800
        assert mm.chunk_size == 4096
        assert mm.max_retries == 2


def test_calculate_file_hash():
    """Test file hash calculation."""
    from guide.model_manager import ModelManager
    
    mm = ModelManager()
    
    # Create a temporary file with known content
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        # Calculate expected hash
        expected_hash = hashlib.sha256(b"test content").hexdigest()
        
        # Test hash calculation
        calculated_hash = mm._calculate_file_hash(temp_path)
        
        assert calculated_hash == expected_hash
    finally:
        temp_path.unlink()


def test_validate_gguf_header_success():
    """Test successful GGUF header validation."""
    from guide.model_manager import ModelManager
    
    mm = ModelManager()
    
    # Mock GGUF file content (magic + version + tensor_count + metadata_count)
    gguf_content = (
        b'GGUF' +  # Magic number
        b'\x02\x00\x00\x00' +  # Version 2 (little endian)
        b'\x10\x00\x00\x00\x00\x00\x00\x00' +  # Tensor count 16 (little endian 64-bit)
        b'\x05\x00\x00\x00\x00\x00\x00\x00'   # Metadata count 5 (little endian 64-bit)
    )
    
    with patch('builtins.open', mock_open(read_data=gguf_content)):
        result = mm._validate_gguf_header(Path("test.gguf"))
        
        assert result["valid"] == True
        assert result["version"] == 2
        assert result["tensor_count"] == 16
        assert result["metadata_count"] == 5


def test_validate_gguf_header_invalid_magic():
    """Test GGUF header validation with invalid magic number."""
    from guide.model_manager import ModelManager, ModelValidationError
    
    mm = ModelManager()
    
    # Mock invalid magic number
    invalid_content = b'INVALID_MAGIC'
    
    with patch('builtins.open', mock_open(read_data=invalid_content)):
        try:
            mm._validate_gguf_header(Path("test.gguf"))
            assert False, "Should have raised ModelValidationError"
        except ModelValidationError as e:
            assert "Invalid GGUF magic number" in str(e)


def test_validate_gguf_header_unsupported_version():
    """Test GGUF header validation with unsupported version."""
    from guide.model_manager import ModelManager, ModelValidationError
    
    mm = ModelManager()
    
    # Mock GGUF with version 1 (unsupported)
    gguf_content = (
        b'GGUF' +  # Magic number
        b'\x01\x00\x00\x00'  # Version 1 (unsupported)
    )
    
    with patch('builtins.open', mock_open(read_data=gguf_content)):
        try:
            mm._validate_gguf_header(Path("test.gguf"))
            assert False, "Should have raised ModelValidationError"
        except ModelValidationError as e:
            assert "Unsupported GGUF version" in str(e)


def test_validate_model_success():
    """Test successful model validation."""
    from guide.model_manager import ModelManager
    
    mm = ModelManager()
    
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test model content")
        temp_path = Path(f.name)
    
    try:
        with patch.object(mm, '_validate_gguf_header') as mock_gguf:
            mock_gguf.return_value = {
                "valid": True,
                "version": 2,
                "tensor_count": 10,
                "metadata_count": 5
            }
            
            result = mm.validate_model(temp_path)
            
            assert result["valid"] == True
            assert result["file_size"] > 0
            assert "sha256" in result
            assert "gguf_info" in result
    finally:
        temp_path.unlink()


def test_validate_model_nonexistent_file():
    """Test model validation with nonexistent file."""
    from guide.model_manager import ModelManager, ModelValidationError
    
    mm = ModelManager()
    
    try:
        mm.validate_model(Path("/nonexistent/file.gguf"))
        assert False, "Should have raised ModelValidationError"
    except ModelValidationError as e:
        assert "Model file not found" in str(e)


def test_validate_model_hash_mismatch():
    """Test model validation with hash mismatch."""
    from guide.model_manager import ModelManager, ModelValidationError
    
    mm = ModelManager()
    
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        temp_path = Path(f.name)
    
    try:
        with patch.object(mm, '_validate_gguf_header') as mock_gguf:
            mock_gguf.return_value = {"valid": True, "version": 2, "tensor_count": 1, "metadata_count": 1}
            
            try:
                mm.validate_model(temp_path, expected_hash="wrong_hash")
                assert False, "Should have raised ModelValidationError"
            except ModelValidationError as e:
                assert "Hash mismatch" in str(e)
    finally:
        temp_path.unlink()


@patch('requests.Session')
def test_download_model_success(mock_session):
    """Test successful model download."""
    from guide.model_manager import ModelManager
    
    mm = ModelManager()
    
    # Mock successful HTTP response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {'Content-Length': '1000'}
    mock_response.iter_content.return_value = [b'test', b'content']
    mock_response.__enter__ = Mock(return_value=mock_response)
    mock_response.__exit__ = Mock(return_value=None)
    
    mock_session.return_value.get.return_value = mock_response
    
    with patch.object(mm, 'validate_model') as mock_validate:
        mock_validate.return_value = {
            "valid": True,
            "file_size": 1000,
            "file_size_mb": 0.001,  # Add the missing field
            "sha256": "test_hash",
            "validated_at": 1234567890
        }
        
        with patch.object(mm, '_save_metadata'):
            with tempfile.TemporaryDirectory() as temp_dir:
                mm.models_dir = Path(temp_dir)
                
                result = mm.download_model("https://example.com/model.gguf")
                
                assert result.name == "model.gguf"
                assert result.exists()


def test_get_model_path_existing():
    """Test getting path for existing model."""
    from guide.model_manager import ModelManager
    
    mm = ModelManager()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        mm.models_dir = Path(temp_dir)
        model_file = mm.models_dir / "test_model.gguf"
        model_file.write_text("test")
        
        # Add to metadata
        mm.metadata["test_model.gguf"] = {
            "file_path": str(model_file)
        }
        
        result = mm.get_model_path("test_model.gguf")
        
        assert result == model_file


def test_get_model_path_nonexistent():
    """Test getting path for nonexistent model."""
    from guide.model_manager import ModelManager
    
    mm = ModelManager()
    
    result = mm.get_model_path("nonexistent_model.gguf")
    
    assert result is None


def test_list_models():
    """Test listing all models."""
    from guide.model_manager import ModelManager
    
    mm = ModelManager()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        mm.models_dir = Path(temp_dir)
        
        # Add test metadata
        mm.metadata = {
            "model1.gguf": {"file_path": str(mm.models_dir / "model1.gguf")},
            "model2.gguf": {"file_path": str(mm.models_dir / "model2.gguf")}
        }
        
        # Create actual files
        (mm.models_dir / "model1.gguf").write_text("test1")
        (mm.models_dir / "model2.gguf").write_text("test2")
        
        result = mm.list_models()
        
        assert len(result) == 2
        assert "model1.gguf" in result
        assert "model2.gguf" in result


def test_delete_model_success():
    """Test successful model deletion."""
    from guide.model_manager import ModelManager
    
    mm = ModelManager()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        mm.models_dir = Path(temp_dir)
        model_file = mm.models_dir / "test_model.gguf"
        model_file.write_text("test")
        
        mm.metadata["test_model.gguf"] = {
            "file_path": str(model_file)
        }
        
        with patch.object(mm, '_save_metadata'):
            result = mm.delete_model("test_model.gguf")
            
            assert result == True
            assert not model_file.exists()


def test_delete_model_not_found():
    """Test model deletion when model not found."""
    from guide.model_manager import ModelManager
    
    mm = ModelManager()
    
    result = mm.delete_model("nonexistent_model.gguf")
    
    assert result == False


def test_get_storage_info():
    """Test getting storage information."""
    from guide.model_manager import ModelManager
    
    mm = ModelManager()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        mm.models_dir = Path(temp_dir)
        
        # Create a test file to give some storage usage
        test_file = Path(temp_dir) / "test_model.gguf"
        test_file.write_bytes(b"x" * 1000)  # 1000 bytes
        
        info = mm.get_storage_info()
        
        assert "models_directory" in info
        assert "total_models" in info
        assert "total_size_bytes" in info
        assert "total_size_mb" in info
        assert "total_size_gb" in info
        assert info["total_models"] == 1
        assert info["total_size_bytes"] == 1000


def test_model_manager_metadata_loading_json_error():
    """Test metadata loading with JSON decode error."""
    from guide.model_manager import ModelManager
    
    mm = ModelManager()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        mm.models_dir = Path(temp_dir)
        mm.metadata_file = Path(temp_dir) / "metadata.json"
        
        # Create invalid JSON file
        mm.metadata_file.write_text("{ invalid json")
        
        metadata = mm._load_metadata()
        
        # Should return empty dict on JSON error
        assert metadata == {}


def test_model_manager_metadata_loading_os_error():
    """Test metadata loading with OS error."""
    from guide.model_manager import ModelManager
    
    mm = ModelManager()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        mm.models_dir = Path(temp_dir)
        mm.metadata_file = Path(temp_dir) / "metadata.json"
        
        # Create metadata file then make it unreadable
        mm.metadata_file.write_text('{"test": "data"}')
        mm.metadata_file.chmod(0o000)  # No permissions
        
        try:
            metadata = mm._load_metadata()
            
            # Should return empty dict on OS error
            assert metadata == {}
        finally:
            # Restore permissions for cleanup
            mm.metadata_file.chmod(0o644)


def test_model_manager_save_metadata_error():
    """Test metadata saving with OS error."""
    from guide.model_manager import ModelManager
    
    mm = ModelManager()
    mm.metadata = {"test": "data"}
    
    with tempfile.TemporaryDirectory() as temp_dir:
        mm.models_dir = Path(temp_dir)
        # Point to a non-writable location
        mm.metadata_file = Path("/non/existent/path/metadata.json")
        
        # Should not raise exception, just log error
        mm._save_metadata()


def test_model_manager_validate_model_invalid_magic():
    """Test model validation with invalid magic bytes."""
    from guide.model_manager import ModelManager, ModelValidationError
    
    mm = ModelManager()
    
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"invalid content")
        f.flush()
        
        try:
            with pytest.raises(ModelValidationError) as exc_info:
                mm.validate_model(Path(f.name))
            
            assert "Invalid GGUF magic number" in str(exc_info.value)
            
        finally:
            Path(f.name).unlink()


def test_model_manager_validate_model_read_error():
    """Test model validation with file read error."""
    from guide.model_manager import ModelManager, ModelValidationError
    
    mm = ModelManager()
    
    with pytest.raises(ModelValidationError) as exc_info:
        mm.validate_model(Path("/nonexistent/file.gguf"))
    
    assert "Model file not found" in str(exc_info.value)


def test_model_manager_download_progress_tracking():
    """Test download with progress tracking."""
    from guide.model_manager import ModelManager
    
    mm = ModelManager()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        mm.models_dir = Path(temp_dir)
        
        with patch.object(mm.session, 'get') as mock_get:
            # Mock the response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-length": "1000"}
            mock_response.iter_content.return_value = [b"x" * 100] * 10
            mock_response.raise_for_status.return_value = None
            
            mock_get.return_value.__enter__.return_value = mock_response
            mock_get.return_value.__exit__.return_value = None
            
            with patch.object(mm, 'validate_model') as mock_validate:
                mock_validate.return_value = {
                    "valid": True,
                    "file_size": 1000,
                    "file_size_mb": 0.001,
                    "sha256": "test_hash",
                    "validated_at": 1234567890
                }
                
                with patch.object(mm, '_save_metadata'):
                    result = mm.download_model("https://example.com/model.gguf")
                    
                    assert result.name == "model.gguf"
                    mock_get.assert_called_once()


def test_model_manager_calculate_file_hash():
    """Test file hash calculation."""
    from guide.model_manager import ModelManager
    
    mm = ModelManager()
    
    with tempfile.NamedTemporaryFile(delete=False) as f:
        test_content = b"test content for hashing"
        f.write(test_content)
        f.flush()
        
        try:
            file_path = Path(f.name)
            calculated_hash = mm._calculate_file_hash(file_path)
            
            # Verify against manually calculated hash
            expected_hash = hashlib.sha256(test_content).hexdigest()
            assert calculated_hash == expected_hash
            
        finally:
            Path(f.name).unlink()


def test_save_metadata_error_handling():
    """Test _save_metadata error handling."""
    from guide.model_manager import ModelManager
    
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('guide.config.get', return_value=temp_dir):
            mm = ModelManager()
            
            # Test with invalid path (read-only directory)
            with patch('builtins.open', side_effect=OSError("Permission denied")), \
                 patch.object(mm.logger, 'error') as mock_error:
                
                mm._save_metadata()
                
                # Should log error and continue gracefully
                mock_error.assert_called_once()
                assert "Failed to save model metadata" in mock_error.call_args[0][0]


def test_validate_gguf_header_struct_error():
    """Test _validate_gguf_header with struct.error."""
    from guide.model_manager import ModelManager, ModelValidationError
    import struct
    
    mm = ModelManager()
    
    with tempfile.NamedTemporaryFile(delete=False) as f:
        # Write invalid binary data that will cause struct.error
        f.write(b"GGUF\x00\x00\x00\x03invalid_data")
        f.flush()
        file_path = Path(f.name)
        
    try:
        with pytest.raises(ModelValidationError, match="Failed to read GGUF header"):
            mm._validate_gguf_header(file_path)
            
    finally:
        file_path.unlink()


def test_validate_model_empty_file():
    """Test validate_model with empty file."""
    from guide.model_manager import ModelManager, ModelValidationError
    
    mm = ModelManager()
    
    with tempfile.NamedTemporaryFile(delete=False) as f:
        # Create empty file
        file_path = Path(f.name)
        
    try:
        with pytest.raises(ModelValidationError, match="Model file is empty"):
            mm.validate_model(file_path)
            
    finally:
        file_path.unlink()


def test_download_model_progress_logging():
    """Test download progress logging functionality."""
    from guide.model_manager import ModelManager
    import time
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a proper config mock that returns different values for different keys
        def mock_config_get(key, default=None):
            config_values = {
                "models.storage_path": temp_dir,
                "models.download_timeout": 3600,  # 1 hour
                "models.download_chunk_size": 8192,  # 8KB chunks
                "models.download_max_retries": 3
            }
            return config_values.get(key, default)
        
        with patch('guide.config.get', side_effect=mock_config_get):
            mm = ModelManager()
            
            # Create mock response that properly supports context manager
            mock_response = Mock()
            mock_response.headers = {'content-length': '1000'}
            mock_response.iter_content.return_value = [b'x' * 100] * 10  # 10 chunks of 100 bytes each
            mock_response.raise_for_status.return_value = None
            
            # Create a context manager mock
            mock_context = Mock()
            mock_context.__enter__ = Mock(return_value=mock_response)
            mock_context.__exit__ = Mock(return_value=None)
            
            # Mock time.time to trigger progress logging (gap > 30 seconds)
            time_values = [0.0, 0.0, 31.0, 31.0] + [32.0] * 20  # Start, then after 31s gap, then normal
            
            with patch.object(mm.session, 'get', return_value=mock_context), \
                 patch('guide.model_manager.time.time', side_effect=time_values):
                
                with patch.object(mm.logger, 'info') as mock_info:
                    # Mock validation to pass with proper return structure
                    validation_return = {
                        'valid': True, 
                        'validated_at': 32,
                        'file_size_mb': 1.0,
                        'file_size': 1048576,
                        'sha256': 'mock_hash',
                        'gguf_info': {'version': 3, 'tensor_count': 100}
                    }
                    with patch.object(mm, 'validate_model', return_value=validation_return):
                        result = mm.download_model("http://example.com/model.bin", "test-model")
                    
                    # Should log progress due to time gap
                    download_calls = [call for call in mock_info.call_args_list 
                                    if "Downloaded:" in str(call) or "Download progress" in str(call)]
                    assert len(download_calls) > 0
def test_download_model_progress_logging_no_content_length():
    """Test download progress logging without content-length header."""
    from guide.model_manager import ModelManager
    import time
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a proper config mock that returns different values for different keys
        def mock_config_get(key, default=None):
            config_values = {
                "models.storage_path": temp_dir,
                "models.download_timeout": 3600,  # 1 hour
                "models.download_chunk_size": 8192,  # 8KB chunks
                "models.download_max_retries": 3
            }
            return config_values.get(key, default)
        
        with patch('guide.config.get', side_effect=mock_config_get):
            mm = ModelManager()
            
            # Create mock response without content-length
            mock_response = Mock()
            mock_response.headers = {}  # No content-length
            mock_response.iter_content.return_value = [b'x' * 100] * 10
            mock_response.raise_for_status.return_value = None
            
            # Create a context manager mock
            mock_context = Mock()
            mock_context.__enter__ = Mock(return_value=mock_response)
            mock_context.__exit__ = Mock(return_value=None)
            
            # Mock time.time to trigger progress logging (gap > 30 seconds)
            time_values = [0.0, 0.0, 31.0, 31.0] + [32.0] * 20
            
            with patch.object(mm.session, 'get', return_value=mock_context), \
                 patch('guide.model_manager.time.time', side_effect=time_values):
                
                with patch.object(mm.logger, 'info') as mock_info:
                    # Mock validation to pass with proper return structure
                    validation_return = {
                        'valid': True, 
                        'validated_at': 32,
                        'file_size_mb': 1.0,
                        'file_size': 1048576,
                        'sha256': 'mock_hash',
                        'gguf_info': {'version': 3, 'tensor_count': 100}
                    }
                    with patch.object(mm, 'validate_model', return_value=validation_return):
                        result = mm.download_model("http://example.com/model.bin", "test-model")
                    
                    # Should log downloaded size without percentage
                    download_calls = [call for call in mock_info.call_args_list 
                                    if "Downloaded:" in str(call)]
                    assert len(download_calls) > 0


def test_download_model_request_exception_cleanup():
    """Test download cleanup on requests.RequestException."""
    from guide.model_manager import ModelManager, ModelDownloadError
    import requests
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a proper config mock that returns different values for different keys
        def mock_config_get(key, default=None):
            config_values = {
                "models.storage_path": temp_dir,
                "models.download_timeout": 3600,  # 1 hour
                "models.download_chunk_size": 8192,  # 8KB chunks
                "models.download_max_retries": 3
            }
            return config_values.get(key, default)
        
        with patch('guide.config.get', side_effect=mock_config_get):
            mm = ModelManager()
            
            # Mock session.get to raise RequestException
            with patch.object(mm.session, 'get', side_effect=requests.RequestException("Network error")):
                
                with pytest.raises(ModelDownloadError, match="Download failed"):
                    mm.download_model("http://example.com/model.bin", "test-model")
                
                # Verify temp file was cleaned up (no temp files should exist)
                temp_files = list(Path(temp_dir).glob("*.tmp"))
                assert len(temp_files) == 0


def test_download_model_validation_exception_cleanup():
    """Test download cleanup on ModelValidationError."""
    from guide.model_manager import ModelManager, ModelValidationError
    import requests
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a proper config mock that returns different values for different keys
        def mock_config_get(key, default=None):
            config_values = {
                "models.storage_path": temp_dir,
                "models.download_timeout": 3600,  # 1 hour
                "models.download_chunk_size": 8192,  # 8KB chunks
                "models.download_max_retries": 3
            }
            return config_values.get(key, default)
        
        with patch('guide.config.get', side_effect=mock_config_get):
            mm = ModelManager()
            
            # Create mock response for successful download
            mock_response = Mock()
            mock_response.headers = {'content-length': '100'}
            mock_response.iter_content.return_value = [b'x' * 100]
            mock_response.raise_for_status.return_value = None
            
            # Create a context manager mock
            mock_context = Mock()
            mock_context.__enter__ = Mock(return_value=mock_response)
            mock_context.__exit__ = Mock(return_value=None)
            
            with patch.object(mm.session, 'get', return_value=mock_context):
                with patch.object(mm, 'validate_model', side_effect=ModelValidationError("Invalid model")):
                    
                    with pytest.raises(ModelValidationError):
                        mm.download_model("http://example.com/model.bin", "test-model")
                    
                    # Verify temp file was cleaned up
                    temp_files = list(Path(temp_dir).glob("*.tmp"))
                    assert len(temp_files) == 0


def test_download_model_unexpected_exception_cleanup():
    """Test download cleanup on unexpected exception."""
    from guide.model_manager import ModelManager, ModelDownloadError
    import requests
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a proper config mock that returns different values for different keys
        def mock_config_get(key, default=None):
            config_values = {
                "models.storage_path": temp_dir,
                "models.download_timeout": 3600,  # 1 hour
                "models.download_chunk_size": 8192,  # 8KB chunks
                "models.download_max_retries": 3
            }
            return config_values.get(key, default)
        
        with patch('guide.config.get', side_effect=mock_config_get):
            mm = ModelManager()
            
            # Create mock response for successful download
            mock_response = Mock()
            mock_response.headers = {'content-length': '100'}
            mock_response.iter_content.return_value = [b'x' * 100]
            mock_response.raise_for_status.return_value = None
            
            # Create a context manager mock
            mock_context = Mock()
            mock_context.__enter__ = Mock(return_value=mock_response)
            mock_context.__exit__ = Mock(return_value=None)
            
            with patch.object(mm.session, 'get', return_value=mock_context):
                with patch.object(mm, 'validate_model', side_effect=RuntimeError("Unexpected error")):
                    
                    with pytest.raises(ModelDownloadError, match="Unexpected error during download"):
                        mm.download_model("http://example.com/model.bin", "test-model")
                    
                    # Verify temp file was cleaned up
                    temp_files = list(Path(temp_dir).glob("*.tmp"))
                    assert len(temp_files) == 0


def test_model_manager_edge_case_coverage():
    """Test various edge cases for better coverage."""
    from guide.model_manager import ModelManager
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a proper config mock that returns different values for different keys
        def mock_config_get(key, default=None):
            config_values = {
                "models.storage_path": temp_dir,
                "models.download_timeout": 3600,  # 1 hour
                "models.download_chunk_size": 8192,  # 8KB chunks
                "models.download_max_retries": 3
            }
            return config_values.get(key, default)
        
        with patch('guide.config.get', side_effect=mock_config_get):
            mm = ModelManager()
            
            # Test get_model_path with non-existent model
            result = mm.get_model_path("nonexistent-model")
            assert result is None
            
            # Test delete_model with non-existent model  
            result = mm.delete_model("nonexistent-model")
            assert result is False