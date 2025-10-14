"""
Main application entry point for Local RAG system.
Initializes FastAPI app, configures routes, and starts the web server.
"""
from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from .web_interface import setup_routes


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Local RAG",
        description="Local Retrieval-Augmented Generation system",
        version="1.0.0"
    )
    
    # Setup API routes
    setup_routes(app)
    
    return app


def main() -> None:
    """Main entry point for the application."""
    app = create_app()
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8080,
        log_level="info"
    )


if __name__ == "__main__":
    main()