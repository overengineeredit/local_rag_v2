"""
Main application entry point for Local RAG system.
Initializes FastAPI app, configures routes, and starts the web server.
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI

from . import config
from .web_interface import setup_routes


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
            if key not in {"name", "msg", "args", "levelname", "levelno", "pathname", 
                          "filename", "module", "lineno", "funcName", "created", 
                          "msecs", "relativeCreated", "thread", "threadName", 
                          "processName", "process", "getMessage", "exc_info", 
                          "exc_text", "stack_info"}:
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
            log_format or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
            encoding='utf-8'
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
    logger.info("Logging configured", extra={
        "level": log_level,
        "format": "json" if log_format == "json" else "standard",
        "file_enabled": log_file is not None,
        "file_path": log_file
    })


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Creating FastAPI application")
    
    # Validate configuration
    config_issues = config.validate()
    if config_issues:
        logger.warning("Configuration validation issues found", extra={
            "issues": config_issues
        })
    
    app = FastAPI(
        title="Local RAG",
        description="Local Retrieval-Augmented Generation system",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Setup API routes
    setup_routes(app)
    
    logger.info("FastAPI application created successfully")
    return app


def main() -> None:
    """Main entry point for the application."""
    try:
        app = create_app()
        
        # Get server configuration
        host = config.get("server.host", "127.0.0.1")
        port = config.get("server.port", 8080)
        workers = config.get("server.workers", 1)
        reload = config.get("server.reload", False)
        
        logger = logging.getLogger(__name__)
        logger.info("Starting Local RAG server", extra={
            "host": host,
            "port": port,
            "workers": workers,
            "reload": reload
        })
        
        # Start server
        uvicorn.run(
            "guide.main:create_app",
            factory=True,
            host=host,
            port=port,
            workers=workers,
            reload=reload,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        # Ensure we have basic logging even if setup fails
        logging.basicConfig(level=logging.ERROR)
        logger = logging.getLogger(__name__)
        logger.error("Failed to start Local RAG server", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
