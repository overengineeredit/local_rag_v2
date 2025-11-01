"""Tests for the Main module."""

import json
import logging
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from collections import deque
import threading
import time

import pytest

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestThermalMonitor:
    """Test the ThermalMonitor class."""

    def test_thermal_monitor_initialization(self):
        """Test thermal monitor initialization."""
        from guide.main import ThermalMonitor
        
        with patch.object(ThermalMonitor, '_discover_thermal_zones'):
            monitor = ThermalMonitor(check_interval=10.0, temp_samples=5)
            
            assert monitor.check_interval == 10.0
            assert monitor.temp_samples == 5
            assert monitor.temperature_history.maxlen == 5
            assert monitor.is_monitoring is False
            assert monitor.monitor_thread is None
            assert monitor.alert_threshold == 75.0
            assert monitor.halt_threshold == 85.0
            assert monitor.resume_threshold == 70.0
            assert monitor.is_throttled is False
            assert monitor.is_halted is False

    def test_discover_thermal_zones_no_sys(self):
        """Test thermal zone discovery when /sys/class/thermal doesn't exist."""
        from guide.main import ThermalMonitor
        
        with patch("pathlib.Path.exists", return_value=False):
            monitor = ThermalMonitor()
            
            assert monitor.thermal_zone_path is None

    def test_discover_thermal_zones_no_zones(self):
        """Test thermal zone discovery when no zones found."""
        from guide.main import ThermalMonitor
        
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.glob", return_value=[]):
            monitor = ThermalMonitor()
            
            assert monitor.thermal_zone_path is None

    def test_discover_thermal_zones_zone0_exists(self):
        """Test thermal zone discovery when thermal_zone0 exists."""
        from guide.main import ThermalMonitor
        
        # Mock the Path operations more specifically
        with patch("guide.main.Path") as mock_path_class:
            mock_thermal_base = MagicMock()
            mock_thermal_base.exists.return_value = True
            mock_thermal_base.glob.return_value = [MagicMock()]  # Some zones exist
            
            mock_zone0_temp = MagicMock()
            mock_zone0_temp.exists.return_value = True
            
            # Setup the path construction chain
            mock_thermal_base.__truediv__.return_value.__truediv__.return_value = mock_zone0_temp
            mock_path_class.return_value = mock_thermal_base
            
            monitor = ThermalMonitor()
            
            assert monitor.thermal_zone_path == mock_zone0_temp

    def test_discover_thermal_zones_fallback(self):
        """Test thermal zone discovery fallback to highest numbered zone."""
        from guide.main import ThermalMonitor
        
        # Create mock zones with proper parent structure
        mock_zone1 = MagicMock()
        mock_zone1.parent.name = "thermal_zone1"
        mock_zone2 = MagicMock()
        mock_zone2.parent.name = "thermal_zone2"
        mock_zones = [mock_zone1, mock_zone2]
        
        with patch("guide.main.Path") as mock_path_class:
            mock_thermal_base = MagicMock()
            mock_thermal_base.exists.return_value = True
            mock_thermal_base.glob.return_value = mock_zones
            
            # Mock zone0 not existing
            mock_zone0_temp = MagicMock()
            mock_zone0_temp.exists.return_value = False
            mock_thermal_base.__truediv__.return_value.__truediv__.return_value = mock_zone0_temp
            
            mock_path_class.return_value = mock_thermal_base
            
            monitor = ThermalMonitor()
            
            # Should select thermal_zone2 (highest number)
            assert monitor.thermal_zone_path == mock_zone2

    def test_read_temperature_success(self):
        """Test successful temperature reading."""
        from guide.main import ThermalMonitor
        
        mock_path = MagicMock()
        
        with patch.object(ThermalMonitor, '_discover_thermal_zones'), \
             patch("builtins.open", mock_open(read_data="45678\n")):
            monitor = ThermalMonitor()
            monitor.thermal_zone_path = mock_path
            
            temp = monitor._read_temperature()
            
            assert temp == 45.678  # 45678 millidegrees / 1000

    def test_read_temperature_no_path(self):
        """Test temperature reading when no thermal zone path."""
        from guide.main import ThermalMonitor
        
        with patch.object(ThermalMonitor, '_discover_thermal_zones'):
            monitor = ThermalMonitor()
            monitor.thermal_zone_path = None
            
            temp = monitor._read_temperature()
            
            assert temp is None

    def test_read_temperature_file_error(self):
        """Test temperature reading when file read fails."""
        from guide.main import ThermalMonitor
        
        mock_path = MagicMock()
        
        with patch.object(ThermalMonitor, '_discover_thermal_zones'), \
             patch("builtins.open", side_effect=OSError("File not found")):
            monitor = ThermalMonitor()
            monitor.thermal_zone_path = mock_path
            
            temp = monitor._read_temperature()
            
            assert temp is None

    def test_get_current_temperature(self):
        """Test getting current temperature."""
        from guide.main import ThermalMonitor
        
        with patch.object(ThermalMonitor, '_discover_thermal_zones'), \
             patch.object(ThermalMonitor, '_read_temperature', return_value=42.5):
            monitor = ThermalMonitor()
            
            temp = monitor.get_current_temperature()
            
            assert temp == 42.5

    def test_get_average_temperature_no_data(self):
        """Test getting average temperature with no data."""
        from guide.main import ThermalMonitor
        
        with patch.object(ThermalMonitor, '_discover_thermal_zones'):
            monitor = ThermalMonitor()
            
            avg = monitor.get_average_temperature()
            
            assert avg is None

    def test_get_average_temperature_with_data(self):
        """Test getting average temperature with data."""
        from guide.main import ThermalMonitor
        
        with patch.object(ThermalMonitor, '_discover_thermal_zones'):
            monitor = ThermalMonitor()
            monitor.temperature_history.extend([40.0, 42.0, 44.0])
            
            avg = monitor.get_average_temperature()
            
            assert avg == 42.0  # (40 + 42 + 44) / 3

    def test_start_monitoring_no_thermal_zone(self):
        """Test starting monitoring without thermal zone."""
        from guide.main import ThermalMonitor
        
        with patch.object(ThermalMonitor, '_discover_thermal_zones'):
            monitor = ThermalMonitor()
            monitor.thermal_zone_path = None
            
            monitor.start_monitoring()
            
            assert monitor.is_monitoring is False
            assert monitor.monitor_thread is None

    def test_start_monitoring_already_monitoring(self):
        """Test starting monitoring when already monitoring."""
        from guide.main import ThermalMonitor
        
        with patch.object(ThermalMonitor, '_discover_thermal_zones'):
            monitor = ThermalMonitor()
            monitor.is_monitoring = True
            monitor.thermal_zone_path = MagicMock()
            
            monitor.start_monitoring()
            
            # Should not create new thread
            assert monitor.monitor_thread is None

    def test_stop_monitoring(self):
        """Test stopping monitoring."""
        from guide.main import ThermalMonitor
        
        with patch.object(ThermalMonitor, '_discover_thermal_zones'):
            monitor = ThermalMonitor()
            mock_thread = MagicMock()
            monitor.monitor_thread = mock_thread
            monitor.is_monitoring = True
            
            monitor.stop_monitoring()
            
            assert monitor.is_monitoring is False
            mock_thread.join.assert_called_once_with(timeout=5.0)

    def test_check_thermal_thresholds_halt(self):
        """Test thermal threshold checking - halt condition."""
        from guide.main import ThermalMonitor
        
        with patch.object(ThermalMonitor, '_discover_thermal_zones'):
            monitor = ThermalMonitor()
            
            # Test halt threshold
            monitor._check_thermal_thresholds(90.0)  # Above halt threshold (85°C)
            
            assert monitor.is_halted is True
            assert monitor.is_throttled is True

    def test_check_thermal_thresholds_throttle(self):
        """Test thermal threshold checking - throttle condition."""
        from guide.main import ThermalMonitor
        
        with patch.object(ThermalMonitor, '_discover_thermal_zones'):
            monitor = ThermalMonitor()
            
            # Test throttle threshold
            monitor._check_thermal_thresholds(80.0)  # Above alert threshold (75°C)
            
            assert monitor.is_halted is False
            assert monitor.is_throttled is True

    def test_check_thermal_thresholds_resume_from_halt(self):
        """Test thermal threshold checking - resume from halt."""
        from guide.main import ThermalMonitor
        
        with patch.object(ThermalMonitor, '_discover_thermal_zones'):
            monitor = ThermalMonitor()
            monitor.is_halted = True
            monitor.is_throttled = True
            
            # Test resume threshold
            monitor._check_thermal_thresholds(65.0)  # Below resume threshold (70°C)
            
            assert monitor.is_halted is False
            assert monitor.is_throttled is False

    def test_check_thermal_thresholds_resume_from_throttle(self):
        """Test thermal threshold checking - resume from throttle."""
        from guide.main import ThermalMonitor
        
        with patch.object(ThermalMonitor, '_discover_thermal_zones'):
            monitor = ThermalMonitor()
            monitor.is_throttled = True
            
            # Test resume threshold
            monitor._check_thermal_thresholds(68.0)  # Below resume threshold (70°C)
            
            assert monitor.is_halted is False
            assert monitor.is_throttled is False

    def test_get_thermal_status(self):
        """Test getting thermal status."""
        from guide.main import ThermalMonitor
        
        with patch.object(ThermalMonitor, '_discover_thermal_zones'), \
             patch.object(ThermalMonitor, 'get_current_temperature', return_value=45.0), \
             patch.object(ThermalMonitor, 'get_average_temperature', return_value=43.5):
            monitor = ThermalMonitor()
            monitor.is_monitoring = True
            monitor.thermal_zone_path = MagicMock()
            monitor.is_throttled = True
            
            status = monitor.get_thermal_status()
            
            assert status["monitoring_active"] is True
            assert status["thermal_zone_available"] is True
            assert status["current_temperature_celsius"] == 45.0
            assert status["average_temperature_celsius"] == 43.5
            assert status["is_throttled"] is True
            assert status["is_halted"] is False
            assert status["thresholds"]["alert"] == 75.0
            assert status["thresholds"]["halt"] == 85.0
            assert status["thresholds"]["resume"] == 70.0


class TestJSONFormatter:
    """Test the JSONFormatter class."""

    def test_json_formatter_basic(self):
        """Test basic JSON formatting."""
        from guide.main import JSONFormatter
        
        formatter = JSONFormatter()
        
        # Create a mock log record
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=123,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_function"
        )
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test.logger"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "file"
        assert log_data["function"] == "test_function"
        assert log_data["line"] == 123

    def test_json_formatter_with_exception(self):
        """Test JSON formatting with exception info."""
        from guide.main import JSONFormatter
        
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="/path/to/file.py",
            lineno=123,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["level"] == "ERROR"
        assert log_data["message"] == "Error occurred"
        assert "exception" in log_data
        assert "ValueError: Test exception" in log_data["exception"]

    def test_json_formatter_with_extra_fields(self):
        """Test JSON formatting with extra fields."""
        from guide.main import JSONFormatter
        
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=123,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Add extra fields
        record.thermal_event = "throttle"
        record.temperature = 78.5
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["thermal_event"] == "throttle"
        assert log_data["temperature"] == 78.5


class TestLoggingSetup:
    """Test logging setup functionality."""

    def test_setup_logging_basic(self):
        """Test basic logging setup."""
        from guide.main import setup_logging
        
        # Clear existing handlers first
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        with patch("guide.main.config") as mock_config:
            mock_config.get.side_effect = lambda key, default=None: {
                "logging.level": "DEBUG",
                "logging.format": None,  # Use default format, not "standard"
                "logging.file": None
            }.get(key, default)
            
            setup_logging()
            
            # Check root logger configuration
            assert root_logger.level == logging.DEBUG
            assert len(root_logger.handlers) >= 1  # At least console handler

    def test_setup_logging_with_json_format(self):
        """Test logging setup with JSON format."""
        from guide.main import setup_logging, JSONFormatter
        
        with patch("guide.main.config") as mock_config:
            mock_config.get.side_effect = lambda key, default=None: {
                "logging.level": "INFO",
                "logging.format": "json",
                "logging.file": None
            }.get(key, default)
            
            setup_logging()
            
            # Check that console handler uses JSON formatter
            root_logger = logging.getLogger()
            console_handler = root_logger.handlers[0]
            assert isinstance(console_handler.formatter, JSONFormatter)

    def test_setup_logging_with_file_handler(self):
        """Test logging setup with file handler."""
        from guide.main import setup_logging
        
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            
            with patch("guide.main.config") as mock_config:
                mock_config.get.side_effect = lambda key, default=None: {
                    "logging.level": "INFO",
                    "logging.format": None,  # Use default format
                    "logging.file": str(log_file)
                }.get(key, default)
                
                setup_logging()
                
                # Check that file handler was added
                root_logger = logging.getLogger()
                assert len(root_logger.handlers) >= 2  # Console + file handler


class TestCreateApp:
    """Test FastAPI app creation."""

    def test_create_app_success(self):
        """Test successful app creation."""
        from guide.main import create_app
        
        with patch("guide.main.setup_logging"), \
             patch("guide.main.config") as mock_config, \
             patch("guide.main.setup_routes") as mock_setup_routes, \
             patch("guide.main.thermal_monitor") as mock_thermal_monitor:
            
            mock_config.validate.return_value = []
            mock_thermal_monitor.thermal_zone_path = MagicMock()
            
            app = create_app()
            
            assert app.title == "Local RAG"
            assert app.description == "Local Retrieval-Augmented Generation system"
            assert app.version == "1.0.0"
            assert app.docs_url == "/docs"
            assert app.redoc_url == "/redoc"
            
            mock_setup_routes.assert_called_once_with(app)
            mock_thermal_monitor.start_monitoring.assert_called_once()

    def test_create_app_with_config_issues(self):
        """Test app creation with configuration issues."""
        from guide.main import create_app
        
        with patch("guide.main.setup_logging"), \
             patch("guide.main.config") as mock_config, \
             patch("guide.main.setup_routes"), \
             patch("guide.main.thermal_monitor") as mock_thermal_monitor:
            
            mock_config.validate.return_value = ["Missing required field", "Invalid value"]
            mock_thermal_monitor.thermal_zone_path = None
            
            app = create_app()
            
            # Should still create app despite config issues
            assert app.title == "Local RAG"

    def test_create_app_no_thermal_monitoring(self):
        """Test app creation without thermal monitoring."""
        from guide.main import create_app
        
        with patch("guide.main.setup_logging"), \
             patch("guide.main.config") as mock_config, \
             patch("guide.main.setup_routes"), \
             patch("guide.main.thermal_monitor") as mock_thermal_monitor:
            
            mock_config.validate.return_value = []
            mock_thermal_monitor.thermal_zone_path = None
            
            app = create_app()
            
            assert app.title == "Local RAG"
            mock_thermal_monitor.start_monitoring.assert_called_once()


class TestMain:
    """Test main function."""

    def test_main_success(self):
        """Test successful main execution."""
        from guide.main import main
        
        with patch("guide.main.create_app") as mock_create_app, \
             patch("guide.main.config") as mock_config, \
             patch("uvicorn.run") as mock_uvicorn_run:
            
            mock_create_app.return_value = MagicMock()
            mock_config.get.side_effect = lambda key, default=None: {
                "server.host": "0.0.0.0",
                "server.port": 8080,
                "server.workers": 1,
                "server.reload": False
            }.get(key, default)
            
            main()
            
            mock_create_app.assert_called_once()
            # Check the actual call arguments
            call_args = mock_uvicorn_run.call_args
            assert call_args[1]["factory"] is True
            assert call_args[1]["port"] == 8080
            assert call_args[1]["workers"] == 1
            assert call_args[1]["reload"] is False

    def test_main_exception(self):
        """Test main function with exception."""
        from guide.main import main
        
        with patch("guide.main.create_app", side_effect=Exception("App creation failed")), \
             patch("logging.basicConfig") as mock_basic_config, \
             patch("sys.exit") as mock_exit:
            
            main()
            
            mock_basic_config.assert_called_once_with(level=logging.ERROR)
            mock_exit.assert_called_once_with(1)