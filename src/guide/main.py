"""
Main application entry point for Local RAG system.
Initializes FastAPI app, configures routes, and starts the web server.
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import sys
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI

from . import config
from .web_interface import setup_routes


class ThermalMonitor:
    """Thermal monitoring system for Pi5 and other systems."""

    def __init__(self, check_interval: float = 30.0, temp_samples: int = 3):
        """Initialize thermal monitor.

        Args:
            check_interval: Seconds between temperature checks
            temp_samples: Number of samples for rolling average
        """
        self.check_interval = check_interval
        self.temp_samples = temp_samples
        self.temperature_history = deque(maxlen=temp_samples)
        self.thermal_zone_path = None
        self.is_monitoring = False
        self.monitor_thread = None
        self.logger = logging.getLogger(f"{__name__}.ThermalMonitor")

        # Temperature thresholds (Celsius)
        self.alert_threshold = 75.0
        self.halt_threshold = 85.0
        self.resume_threshold = 70.0

        # State management
        self.is_throttled = False
        self.is_halted = False

        self._discover_thermal_zones()

    def _discover_thermal_zones(self) -> None:
        """Discover available thermal zones and select primary."""
        thermal_base = Path("/sys/class/thermal")

        if not thermal_base.exists():
            self.logger.warning("Thermal monitoring not available - /sys/class/thermal not found")
            return

        # Look for thermal zones
        zones = list(thermal_base.glob("thermal_zone*/temp"))

        if not zones:
            self.logger.warning("No thermal zones found")
            return

        # Prefer thermal_zone0, fallback to highest numbered zone
        zone0 = thermal_base / "thermal_zone0" / "temp"

        if zone0.exists():
            self.thermal_zone_path = zone0
            self.logger.info("Using thermal_zone0 for temperature monitoring")
        else:
            # Use highest numbered zone as fallback
            zone_numbers = []
            for zone in zones:
                try:
                    zone_num = int(zone.parent.name.replace("thermal_zone", ""))
                    zone_numbers.append((zone_num, zone))
                except ValueError:
                    continue

            if zone_numbers:
                zone_numbers.sort(reverse=True)  # Highest first
                self.thermal_zone_path = zone_numbers[0][1]
                zone_name = zone_numbers[0][1].parent.name
                self.logger.info(f"Using {zone_name} for temperature monitoring (fallback)")

    def _read_temperature(self) -> float | None:
        """Read temperature from thermal zone.

        Returns:
            Temperature in Celsius or None if read fails
        """
        if not self.thermal_zone_path:
            return None

        try:
            with open(self.thermal_zone_path) as f:
                # Temperature is in millidegrees Celsius
                temp_millidegrees = int(f.read().strip())
                temp_celsius = temp_millidegrees / 1000.0
                return temp_celsius
        except (OSError, ValueError) as e:
            self.logger.warning(f"Failed to read temperature: {e}")
            return None

    def get_current_temperature(self) -> float | None:
        """Get current temperature reading.

        Returns:
            Current temperature in Celsius or None if unavailable
        """
        return self._read_temperature()

    def get_average_temperature(self) -> float | None:
        """Get rolling average temperature.

        Returns:
            Average temperature over recent samples or None if insufficient data
        """
        if len(self.temperature_history) == 0:
            return None

        return sum(self.temperature_history) / len(self.temperature_history)

    def start_monitoring(self) -> None:
        """Start thermal monitoring in background thread."""
        if self.is_monitoring or not self.thermal_zone_path:
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info(f"Thermal monitoring started (interval: {self.check_interval}s)")

    def stop_monitoring(self) -> None:
        """Stop thermal monitoring."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        self.logger.info("Thermal monitoring stopped")

    def _monitor_loop(self) -> None:
        """Main monitoring loop running in background thread."""
        failure_count = 0
        max_failures = 3

        while self.is_monitoring:
            try:
                temp = self._read_temperature()

                if temp is not None:
                    self.temperature_history.append(temp)
                    failure_count = 0  # Reset failure count on success

                    # Calculate rolling average
                    avg_temp = self.get_average_temperature()

                    if avg_temp is not None:
                        self._check_thermal_thresholds(avg_temp)

                        # Log temperature info (less frequent to avoid spam)
                        if len(self.temperature_history) % 10 == 0:  # Every 10 readings
                            self.logger.debug(f"Temperature: {temp:.1f}°C (avg: {avg_temp:.1f}°C)")

                else:
                    failure_count += 1
                    if failure_count >= max_failures:
                        # Increase polling interval on repeated failures
                        adjusted_interval = self.check_interval * 2
                        self.logger.warning(
                            f"Temperature read failures, increasing interval to " f"{adjusted_interval}s",
                        )
                        time.sleep(adjusted_interval)
                        continue

                time.sleep(self.check_interval)

            except Exception as e:
                self.logger.error(f"Thermal monitoring error: {e}")
                time.sleep(self.check_interval)

    def _check_thermal_thresholds(self, avg_temp: float) -> None:
        """Check temperature against thresholds and take action.

        Args:
            avg_temp: Average temperature in Celsius
        """
        if avg_temp >= self.halt_threshold and not self.is_halted:
            self.is_halted = True
            self.is_throttled = True
            self.logger.critical(
                f"THERMAL HALT: {avg_temp:.1f}°C >= {self.halt_threshold}°C",
                extra={
                    "thermal_event": "halt",
                    "temperature": avg_temp,
                    "threshold": self.halt_threshold,
                },
            )
            # Note: Actual processing halt would be implemented in LLM interface

        elif avg_temp >= self.alert_threshold and not self.is_throttled:
            self.is_throttled = True
            self.logger.warning(
                f"THERMAL THROTTLE: {avg_temp:.1f}°C >= {self.alert_threshold}°C",
                extra={
                    "thermal_event": "throttle",
                    "temperature": avg_temp,
                    "threshold": self.alert_threshold,
                },
            )
            # Note: Actual throttling would be implemented in LLM interface

        elif avg_temp <= self.resume_threshold and (self.is_throttled or self.is_halted):
            was_halted = self.is_halted
            self.is_halted = False
            self.is_throttled = False

            event_type = "resume_from_halt" if was_halted else "resume_from_throttle"
            self.logger.info(
                f"THERMAL RESUME: {avg_temp:.1f}°C <= {self.resume_threshold}°C",
                extra={
                    "thermal_event": event_type,
                    "temperature": avg_temp,
                    "threshold": self.resume_threshold,
                },
            )

    def get_thermal_status(self) -> dict[str, Any]:
        """Get current thermal status for health checks.

        Returns:
            Dictionary with thermal status information
        """
        current_temp = self.get_current_temperature()
        avg_temp = self.get_average_temperature()

        return {
            "monitoring_active": self.is_monitoring,
            "thermal_zone_available": self.thermal_zone_path is not None,
            "current_temperature_celsius": current_temp,
            "average_temperature_celsius": avg_temp,
            "is_throttled": self.is_throttled,
            "is_halted": self.is_halted,
            "thresholds": {
                "alert": self.alert_threshold,
                "halt": self.halt_threshold,
                "resume": self.resume_threshold,
            },
        }


# Global thermal monitor instance
thermal_monitor = ThermalMonitor()


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
            }:
                log_data[key] = value

        return json.dumps(log_data, default=str, ensure_ascii=False)


def setup_logging() -> None:
    """Setup structured logging with JSON formatting and rotation."""

    # Get logging configuration
    log_level = config.get("logging.level", "INFO")
    log_format = config.get("logging.format")
    log_file = config.get("logging.file")

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler with either JSON or standard formatting
    console_handler = logging.StreamHandler(sys.stdout)

    if log_format == "json":
        console_formatter = JSONFormatter()
    else:
        console_formatter = logging.Formatter(
            log_format or "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation if configured
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Use rotating file handler (10MB max, 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )

        # Always use JSON format for file logs
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("chromadb").setLevel(logging.WARNING)  # ChromaDB can be verbose

    # Log startup information
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "level": log_level,
            "format": "json" if log_format == "json" else "standard",
            "file_enabled": log_file is not None,
            "file_path": log_file,
        },
    )


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Creating FastAPI application")

    # Validate configuration
    config_issues = config.validate()
    if config_issues:
        logger.warning("Configuration validation issues found", extra={"issues": config_issues})

    app = FastAPI(
        title="Local RAG",
        description="Local Retrieval-Augmented Generation system",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Setup API routes
    setup_routes(app)

    # Start thermal monitoring
    thermal_monitor.start_monitoring()
    if thermal_monitor.thermal_zone_path:
        logger.info(
            "Thermal monitoring enabled",
            extra={
                "thermal_zone": str(thermal_monitor.thermal_zone_path),
                "check_interval": thermal_monitor.check_interval,
                "alert_threshold": thermal_monitor.alert_threshold,
                "halt_threshold": thermal_monitor.halt_threshold,
            },
        )
    else:
        logger.warning("Thermal monitoring not available - no thermal zones found")

    logger.info("FastAPI application created successfully")
    return app


def main() -> None:
    """Main entry point for the application."""
    try:
        create_app()

        # Get server configuration
        host = config.get("server.host", "127.0.0.1")
        port = config.get("server.port", 8080)
        workers = config.get("server.workers", 1)
        reload = config.get("server.reload", False)

        logger = logging.getLogger(__name__)
        logger.info(
            "Starting Local RAG server",
            extra={"host": host, "port": port, "workers": workers, "reload": reload},
        )

        # Start server
        uvicorn.run(
            "guide.main:create_app",
            factory=True,
            host=host,
            port=port,
            workers=workers,
            reload=reload,
            log_level="info",
            access_log=True,
        )

    except Exception:
        # Ensure we have basic logging even if setup fails
        logging.basicConfig(level=logging.ERROR)
        logger = logging.getLogger(__name__)
        logger.error("Failed to start Local RAG server", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
