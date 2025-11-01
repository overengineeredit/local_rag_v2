"""
FastAPI web interface providing REST API and basic web UI.
Handles query processing, content management, and system administration.
"""

from __future__ import annotations

import logging
import traceback
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ValidationError

from . import config
from .content_manager import ContentManager
from .model_manager import ModelManager

logger = logging.getLogger(__name__)


# Custom Exception Classes
class LocalRAGException(Exception):
    """Base exception for Local RAG system."""
    
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(LocalRAGException):
    """Configuration-related errors."""
    pass


class VectorStoreError(LocalRAGException):
    """Vector store operation errors."""
    pass


class LLMError(LocalRAGException):
    """LLM operation errors."""
    pass


class ContentProcessingError(LocalRAGException):
    """Content processing and ingestion errors."""
    pass


class ResourceLimitError(LocalRAGException):
    """Resource limit exceeded errors."""
    pass


# Request/Response Models
class QueryRequest(BaseModel):
    """Request model for user queries."""

    query: str
    max_results: int = 5
    include_sources: bool = True


class ImportRequest(BaseModel):
    """Request model for content import."""

    source: str
    source_type: str = "file"  # file, directory, url
    chunk_size: int | None = None
    chunk_overlap: int | None = None


class DownloadModelRequest(BaseModel):
    """Request model for model downloads."""
    
    model_config = {"protected_namespaces": ()}
    
    url: str
    model_name: str | None = None
    expected_hash: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None


# Error Handler Functions
async def handle_local_rag_exception(request: Request, exc: LocalRAGException) -> JSONResponse:
    """Handle custom Local RAG exceptions."""
    logger.error(
        "Local RAG error occurred",
        extra={
            "error_type": type(exc).__name__,
            "error_message": exc.message,
            "details": exc.details,
            "path": str(request.url),
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=type(exc).__name__,
            message=exc.message,
            details=exc.details
        ).dict()
    )


async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    logger.warning(
        "HTTP exception occurred",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": str(request.url),
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTPException",
            message=str(exc.detail)
        ).dict()
    )


async def handle_validation_error(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning(
        "Validation error occurred",
        extra={
            "errors": exc.errors(),
            "path": str(request.url),
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="ValidationError",
            message="Request validation failed",
            details={"validation_errors": exc.errors()}
        ).dict()
    )


async def handle_general_exception(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(
        "Unexpected error occurred",
        extra={
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "path": str(request.url),
            "method": request.method
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred"
        ).dict()
    )


def setup_error_handlers(app: FastAPI) -> None:
    """Setup global error handlers for the application."""
    
    # Local RAG specific exceptions
    app.add_exception_handler(LocalRAGException, handle_local_rag_exception)
    app.add_exception_handler(ConfigurationError, handle_local_rag_exception)
    app.add_exception_handler(VectorStoreError, handle_local_rag_exception)
    app.add_exception_handler(LLMError, handle_local_rag_exception)
    app.add_exception_handler(ContentProcessingError, handle_local_rag_exception)
    app.add_exception_handler(ResourceLimitError, handle_local_rag_exception)
    
    # Standard FastAPI exceptions
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(ValidationError, handle_validation_error)
    
    # Catch-all for unexpected exceptions
    app.add_exception_handler(Exception, handle_general_exception)


def setup_routes(app: FastAPI) -> None:
    """Setup all API routes for the application."""
    
    # Setup error handlers first
    setup_error_handlers(app)

    # Initialize core components (TODO: move to dependency injection)
    llm = None  # Will be initialized with actual config
    vector_store = None
    # Initialize content manager with default values, will be overridden per request
    content_manager = ContentManager()
    model_manager = ModelManager()

    @app.get("/", response_class=HTMLResponse)
    async def index():
        """Serve the main web interface."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Local RAG</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                input, textarea { width: 100%; padding: 10px; margin: 10px 0; }
                button {
                    padding: 10px 20px; background: #007cba; color: white;
                    border: none; cursor: pointer;
                }
                .response {
                    background: #f5f5f5; padding: 20px; margin: 20px 0;
                    white-space: pre-wrap;
                }
                .error {
                    background: #ffe6e6; border: 1px solid #ff9999; padding: 15px;
                    margin: 10px 0; border-radius: 4px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Local RAG System</h1>
                <form id="queryForm">
                    <textarea id="query" placeholder="Enter your question..." rows="3"></textarea>
                    <button type="submit">Ask Question</button>
                </form>
                <div id="response" class="response" style="display: none;"></div>
                <div id="error" class="error" style="display: none;"></div>

                <h2>Content Management</h2>
                <form id="importForm">
                    <input type="text" id="source" placeholder="File path, directory, or URL">
                    <select id="sourceType">
                        <option value="file">File</option>
                        <option value="directory">Directory</option>
                        <option value="url">URL</option>
                    </select>
                    <button type="submit">Import Content</button>
                </form>
            </div>

            <script>
                // Enhanced JavaScript with error handling
                async function handleResponse(response) {
                    const responseDiv = document.getElementById('response');
                    const errorDiv = document.getElementById('error');
                    
                    if (response.ok) {
                        const result = await response.json();
                        responseDiv.style.display = 'block';
                        errorDiv.style.display = 'none';
                        responseDiv.textContent = JSON.stringify(result, null, 2);
                    } else {
                        const error = await response.json();
                        errorDiv.style.display = 'block';
                        responseDiv.style.display = 'none';
                        errorDiv.textContent = `Error: ${error.message || 'Unknown error'}`;
                    }
                }
                
                document.getElementById('queryForm').onsubmit = async (e) => {
                    e.preventDefault();
                    const query = document.getElementById('query').value;
                    try {
                        const response = await fetch('/api/query', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({query})
                        });
                        await handleResponse(response);
                    } catch (err) {
                        document.getElementById('error').style.display = 'block';
                        document.getElementById('error').textContent = `Network error: ${err.message}`;
                    }
                };
                
                document.getElementById('importForm').onsubmit = async (e) => {
                    e.preventDefault();
                    const source = document.getElementById('source').value;
                    const sourceType = document.getElementById('sourceType').value;
                    try {
                        const response = await fetch('/api/import', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({source, source_type: sourceType})
                        });
                        await handleResponse(response);
                    } catch (err) {
                        document.getElementById('error').style.display = 'block';
                        document.getElementById('error').textContent = `Network error: ${err.message}`;
                    }
                };
            </script>
        </body>
        </html>
        """

    @app.get("/health")
    async def health_check():
        """Health check endpoint with comprehensive component status."""
        try:
            components = {}
            
            # Check LLM status
            if llm:
                try:
                    components["llm"] = llm.health_check()
                except Exception as e:
                    components["llm"] = {"status": "error", "error": str(e)}
            else:
                components["llm"] = {"status": "not_initialized"}
            
            # Check vector store status
            if vector_store:
                try:
                    components["vector_store"] = vector_store.health_check()
                except Exception as e:
                    components["vector_store"] = {"status": "error", "error": str(e)}
            else:
                components["vector_store"] = {"status": "not_initialized"}
            
            # Check content manager
            components["content_manager"] = {"status": "ok"}
            
            # Check thermal monitoring
            try:
                from .main import thermal_monitor
                thermal_status = thermal_monitor.get_thermal_status()
                
                # Determine thermal status level
                if thermal_status["is_halted"]:
                    thermal_health = "error"
                elif thermal_status["is_throttled"]:
                    thermal_health = "warning"
                elif not thermal_status["thermal_zone_available"]:
                    thermal_health = "warning"
                else:
                    thermal_health = "ok"
                
                components["thermal"] = {
                    "status": thermal_health,
                    **thermal_status
                }
            except Exception as e:
                components["thermal"] = {"status": "error", "error": str(e)}
            
            # Check model management
            try:
                storage_info = model_manager.get_storage_info()
                models = model_manager.list_models()
                
                components["models"] = {
                    "status": "ok",
                    "total_models": storage_info["total_models"],
                    "storage_mb": storage_info["total_size_mb"],
                    "models_directory": storage_info["models_directory"]
                }
            except Exception as e:
                components["models"] = {"status": "error", "error": str(e)}
            
            # Check configuration
            config_issues = config.validate()
            components["configuration"] = {
                "status": "ok" if not config_issues else "warning",
                "issues": config_issues
            }
            
            # Overall status
            overall_status = "healthy"
            for component in components.values():
                if component.get("status") == "error":
                    overall_status = "unhealthy"
                    break
                elif component.get("status") in ["warning", "not_initialized"]:
                    overall_status = "degraded"
                    
            return {
                "status": overall_status,
                "service": "local-rag",
                "version": "1.0.0",
                "components": components
            }
            
        except Exception as e:
            logger.error("Health check failed", exc_info=True)
            raise LocalRAGException("Health check failed", {"error": str(e)})

    @app.post("/api/query")
    async def query(request: QueryRequest):
        """Process user query and return response."""
        if not llm or not vector_store:
            raise ConfigurationError("System not fully initialized", {
                "llm_ready": llm is not None,
                "vector_store_ready": vector_store is not None
            })

        try:
            logger.info(f"Processing query: {request.query[:100]}...")
            
            # Search for relevant context
            search_results = vector_store.search(request.query, request.max_results)
            context = "\n\n".join([doc["content"] for doc in search_results])

            # Generate response (placeholder - not streaming yet)
            response_tokens = list(llm.generate(request.query, context))
            response = "".join(response_tokens)

            result = {"response": response}
            if request.include_sources:
                result["sources"] = search_results

            logger.info("Query processed successfully")
            return result

        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            raise LLMError("Query processing failed", {"query": request.query, "error": str(e)})

    @app.post("/api/import")
    async def import_content(request: ImportRequest):
        """Import content from various sources."""
        try:
            logger.info(f"Importing content from {request.source_type}: {request.source}")
            
            # Check resource limits
            max_file_size = config.get("content.max_file_size_mb", 50)
            
            # Create content manager with custom chunk parameters if provided
            chunk_size = request.chunk_size or config.get("content.chunk_size", 1000)
            chunk_overlap = request.chunk_overlap or config.get("content.chunk_overlap", 200)
            
            cm = ContentManager(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            
            documents = []
            if request.source_type == "file":
                documents = cm.ingest_file(request.source)
            elif request.source_type == "directory":
                documents = cm.ingest_directory(request.source)
            elif request.source_type == "url":
                documents = cm.ingest_url(request.source)
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid source type. Must be 'file', 'directory', or 'url'"
                )
            
            if not vector_store:
                raise VectorStoreError("Vector store not initialized")
            
            # Add to vector store
            doc_ids = vector_store.add_documents(documents)
            
            logger.info(f"Import completed: {len(doc_ids)} documents added")
            
            return {
                "status": "success",
                "documents_processed": len(documents),
                "documents_added": len(doc_ids),
                "source": request.source,
                "source_type": request.source_type
            }

        except Exception as e:
            logger.error(f"Import failed: {e}")
            raise ContentProcessingError("Content import failed", {
                "source": request.source,
                "source_type": request.source_type,
                "error": str(e)
            })

    @app.post("/api/reset")
    async def reset_database():
        """Reset the vector database."""
        try:
            logger.warning("Database reset requested")
            # TODO: Implement database reset
            return {"status": "success", "message": "Database reset (placeholder)"}
        except Exception as e:
            raise VectorStoreError("Database reset failed", {"error": str(e)})

    @app.get("/api/status")
    async def system_status():
        """Get detailed system status."""
        try:
            return {
                "system": "local-rag",
                "version": "1.0.0",
                "config": {
                    "data_dir": config.get("storage.data_dir"),
                    "models_dir": config.get("storage.models_dir"),
                    "server_host": config.get("server.host"),
                    "server_port": config.get("server.port")
                },
                "components": {
                    "llm": {"status": "placeholder"},
                    "vector_store": {"status": "placeholder"},
                    "content_manager": {"status": "ok"},
                },
            }
        except Exception as e:
            raise LocalRAGException("Status check failed", {"error": str(e)})

    # Model Management Endpoints
    @app.get("/api/models")
    async def list_models():
        """List all available models."""
        try:
            models = model_manager.list_models()
            storage_info = model_manager.get_storage_info()
            
            return {
                "models": models,
                "storage": storage_info
            }
        except Exception as e:
            logger.error("Failed to list models", exc_info=True)
            raise LocalRAGException("Failed to list models", {"error": str(e)})

    @app.post("/api/models/download")
    async def download_model(request: DownloadModelRequest):
        """Download a model from URL."""
        try:
            model_path = model_manager.download_model(
                url=request.url,
                model_name=request.model_name,
                expected_hash=request.expected_hash
            )
            
            return {
                "status": "success",
                "model_name": model_path.name,
                "file_path": str(model_path),
                "message": f"Model downloaded successfully: {model_path.name}"
            }
        except Exception as e:
            logger.error(f"Model download failed: {e}", exc_info=True)
            raise LocalRAGException("Model download failed", {"error": str(e)})

    @app.delete("/api/models/{model_name}")
    async def delete_model(model_name: str):
        """Delete a model from storage."""
        try:
            success = model_manager.delete_model(model_name)
            
            if success:
                return {
                    "status": "success",
                    "message": f"Model deleted: {model_name}"
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Model not found: {model_name}"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Model deletion failed: {e}", exc_info=True)
            raise LocalRAGException("Model deletion failed", {"error": str(e)})

    @app.post("/api/models/{model_name}/validate")
    async def validate_model(model_name: str):
        """Validate a model file."""
        try:
            model_path = model_manager.get_model_path(model_name)
            
            if not model_path:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Model not found: {model_name}"
                )
            
            validation_result = model_manager.validate_model(model_path)
            
            return {
                "status": "success",
                "model_name": model_name,
                "validation": validation_result
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Model validation failed: {e}", exc_info=True)
            raise LocalRAGException("Model validation failed", {"error": str(e)})
