"""
Unit tests for thermal monitoring infrastructure.
Tests ThermalMonitor class functionality and behavior.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


def test_thermal_monitor_import():
    """Test that ThermalMonitor can be imported."""
    from guide.main import ThermalMonitor

    assert ThermalMonitor is not None


def test_thermal_monitor_initialization():
    """Test ThermalMonitor initialization with default and custom parameters."""
    from guide.main import ThermalMonitor

    # Test default initialization
    tm1 = ThermalMonitor()
    assert tm1.check_interval == 30.0
    assert tm1.temp_samples == 3
    assert tm1.alert_threshold == 75.0
    assert tm1.halt_threshold == 85.0
    assert tm1.resume_threshold == 70.0

    # Test custom initialization
    tm2 = ThermalMonitor(check_interval=60.0, temp_samples=5)
    assert tm2.check_interval == 60.0
    assert tm2.temp_samples == 5


@patch("guide.main.Path")
def test_thermal_zone_discovery_success(mock_path_class):
    """Test successful thermal zone discovery."""
    from unittest.mock import MagicMock

    from guide.main import ThermalMonitor

    # Create mock objects for thermal zone discovery
    mock_zone0 = MagicMock()
    mock_zone0.exists.return_value = True
    mock_zone0.parent.name = "thermal_zone0"

    # Create thermal_base mock that supports glob and path operations
    mock_thermal_base = MagicMock()
    mock_thermal_base.glob.return_value = [mock_zone0]
    mock_thermal_base.exists.return_value = True

    # Create intermediate path mock for chaining
    mock_thermal_zone_dir = MagicMock()
    mock_thermal_zone_dir.__truediv__.return_value = mock_zone0

    # Configure thermal_base to support / operator
    mock_thermal_base.__truediv__.return_value = mock_thermal_zone_dir

    # Configure the Path class mock to return thermal_base for the thermal path
    mock_path_class.return_value = mock_thermal_base

    tm = ThermalMonitor()

    assert tm.thermal_zone_path == mock_zone0


@patch("pathlib.Path.exists")
def test_thermal_zone_discovery_failure(mock_exists):
    """Test thermal zone discovery when no zones available."""
    from guide.main import ThermalMonitor

    # Mock no thermal zones available
    mock_exists.return_value = False

    tm = ThermalMonitor()

    assert tm.thermal_zone_path is None


def test_read_temperature_success():
    """Test successful temperature reading."""
    from guide.main import ThermalMonitor

    tm = ThermalMonitor()

    # Mock thermal zone path and file content
    with patch("builtins.open", mock_open(read_data="45123\n")):
        with patch.object(
            tm, "thermal_zone_path", Path("/sys/class/thermal/thermal_zone0/temp")
        ):
            temp = tm._read_temperature()

            assert temp == 45.123  # 45123 millidegrees = 45.123 degrees


def test_read_temperature_failure():
    """Test temperature reading failure."""
    from guide.main import ThermalMonitor

    tm = ThermalMonitor()

    # Mock thermal zone path but no file
    with patch.object(tm, "thermal_zone_path", None):
        temp = tm._read_temperature()
        assert temp is None


def test_get_current_temperature():
    """Test getting current temperature."""
    from guide.main import ThermalMonitor

    tm = ThermalMonitor()

    with patch.object(tm, "_read_temperature", return_value=50.5):
        temp = tm.get_current_temperature()
        assert temp == 50.5


def test_get_average_temperature():
    """Test getting rolling average temperature."""
    from guide.main import ThermalMonitor

    tm = ThermalMonitor()

    # Test with no temperature history
    avg = tm.get_average_temperature()
    assert avg is None

    # Add temperature readings
    tm.temperature_history.extend([50.0, 52.0, 48.0])
    avg = tm.get_average_temperature()
    assert avg == 50.0  # (50 + 52 + 48) / 3


def test_thermal_threshold_checking():
    """Test thermal threshold detection and state changes."""
    from guide.main import ThermalMonitor

    tm = ThermalMonitor()

    # Test normal temperature
    tm._check_thermal_thresholds(65.0)
    assert not tm.is_throttled
    assert not tm.is_halted

    # Test alert threshold
    tm._check_thermal_thresholds(76.0)
    assert tm.is_throttled
    assert not tm.is_halted

    # Test halt threshold
    tm._check_thermal_thresholds(86.0)
    assert tm.is_throttled
    assert tm.is_halted

    # Test resume threshold
    tm._check_thermal_thresholds(68.0)
    assert not tm.is_throttled
    assert not tm.is_halted


def test_thermal_status():
    """Test getting thermal status information."""
    from guide.main import ThermalMonitor

    tm = ThermalMonitor()
    tm.temperature_history.extend([50.0, 52.0, 48.0])

    with patch.object(tm, "_read_temperature", return_value=51.0):
        with patch.object(
            tm, "thermal_zone_path", Path("/sys/class/thermal/thermal_zone0/temp")
        ):
            with patch.object(tm, "is_monitoring", True):
                status = tm.get_thermal_status()

                assert status["monitoring_active"] is True
                assert status["thermal_zone_available"] is True
                assert status["current_temperature_celsius"] == 51.0
                assert status["average_temperature_celsius"] == 50.0
                assert "thresholds" in status
                assert status["thresholds"]["alert"] == 75.0


@patch("threading.Thread")
def test_start_monitoring(mock_thread):
    """Test starting thermal monitoring."""
    from guide.main import ThermalMonitor

    tm = ThermalMonitor()

    with patch.object(
        tm, "thermal_zone_path", Path("/sys/class/thermal/thermal_zone0/temp")
    ):
        tm.start_monitoring()

        assert tm.is_monitoring is True
        mock_thread.assert_called_once()


def test_stop_monitoring():
    """Test stopping thermal monitoring."""
    from guide.main import ThermalMonitor

    tm = ThermalMonitor()
    tm.is_monitoring = True

    with patch.object(tm, "monitor_thread", Mock()):
        tm.stop_monitoring()

        assert tm.is_monitoring is False


def test_global_thermal_monitor():
    """Test that global thermal monitor instance exists."""
    from guide.main import thermal_monitor

    assert thermal_monitor is not None
    assert hasattr(thermal_monitor, "get_thermal_status")
    assert hasattr(thermal_monitor, "start_monitoring")
    assert hasattr(thermal_monitor, "stop_monitoring")
