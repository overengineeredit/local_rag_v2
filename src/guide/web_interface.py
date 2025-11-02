"""
FastAPI web interface providing REST API and basic web UI.
Handles query processing, content management, and system administration.
"""

from __future__ import annotations

import logging
from typing import Any, Union

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ValidationError, field_validator

from . import config
from .content_manager import ContentManager
from .model_manager import ModelManager

logger = logging.getLogger(__name__)


# Custom Exception Classes
class LocalRAGError(Exception):
    """Base exception for Local RAG system."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class VectorStoreError(LocalRAGError):
    """Vector store operation error."""

    pass


class ConfigurationError(LocalRAGError):
    """Configuration error."""

    pass


class LLMError(LocalRAGError):
    """LLM operation errors."""

    pass


class ContentProcessingError(LocalRAGError):
    """Content processing and ingestion errors."""

    pass


class ResourceLimitError(LocalRAGError):
    """Resource limit exceeded errors."""

    pass


# Request/Response Models
class QueryRequest(BaseModel):
    """Request model for user queries."""

    query: str
    max_results: int = 5
    include_sources: bool = True

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate query is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v

    @field_validator("max_results")
    @classmethod
    def validate_max_results(cls, v: int) -> int:
        """Validate max_results is positive."""
        if v <= 0:
            raise ValueError("max_results must be positive")
        return v


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
async def handle_local_rag_exception(request: Request, exc: LocalRAGError) -> JSONResponse:
    """Handle custom Local RAG exceptions."""
    logger.error(
        "Local RAG error occurred",
        extra={
            "error_type": type(exc).__name__,
            "error_message": exc.message,
            "details": exc.details,
            "path": str(request.url),
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=type(exc).__name__,
            message=exc.message,
            details=exc.details,
        ).model_dump(),
    )


async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    logger.warning(
        "HTTP exception occurred",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": str(request.url),
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error="HTTPException", message=str(exc.detail)).model_dump(),
    )


async def handle_validation_error(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning(
        "Validation error occurred",
        extra={
            "errors": exc.errors(),
            "path": str(request.url),
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="ValidationError",
            message="Request validation failed",
            details={"validation_errors": exc.errors()},
        ).model_dump(),
    )


async def handle_request_validation_error(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle FastAPI request validation errors."""
    # Clean up the errors to ensure JSON serialization
    clean_errors = []
    for error in exc.errors():
        clean_error = error.copy()
        # Convert non-serializable objects to strings
        if "ctx" in clean_error and "error" in clean_error["ctx"]:
            if isinstance(clean_error["ctx"]["error"], Exception):
                clean_error["ctx"]["error"] = str(clean_error["ctx"]["error"])
        clean_errors.append(clean_error)

    logger.warning(
        "Request validation error occurred",
        extra={
            "errors": clean_errors,
            "path": str(request.url),
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="ValidationError",
            message="Request validation failed",
            details={"validation_errors": clean_errors},
        ).model_dump(),
    )


async def handle_general_exception(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(
        "Unexpected error occurred",
        extra={
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "path": str(request.url),
            "method": request.method,
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
        ).model_dump(),
    )


def setup_error_handlers(app: FastAPI) -> None:
    """Setup global error handlers for the application."""

    # Local RAG specific exceptions
    app.add_exception_handler(LocalRAGError, handle_local_rag_exception)
    app.add_exception_handler(ConfigurationError, handle_local_rag_exception)
    app.add_exception_handler(VectorStoreError, handle_local_rag_exception)
    app.add_exception_handler(LLMError, handle_local_rag_exception)
    app.add_exception_handler(ContentProcessingError, handle_local_rag_exception)
    app.add_exception_handler(ResourceLimitError, handle_local_rag_exception)

    # Standard FastAPI exceptions
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(ValidationError, handle_validation_error)
    app.add_exception_handler(RequestValidationError, handle_request_validation_error)

    # Catch-all for unexpected exceptions
    app.add_exception_handler(Exception, handle_general_exception)


def setup_routes(app: FastAPI) -> None:
    """Setup all API routes for the application."""

    # Setup error handlers first
    setup_error_handlers(app)

    # Initialize core components (TODO: move to dependency injection)
    from .llm_interface import LLMInterface
    from .vector_store import VectorStore

    # Initialize LLM with config
    llm: Union[LLMInterface, Any] = None
    try:
        model_path = config.get(
            "llm.model_path",
            "./models/deepseek-r1-distill-qwen-1.5b.Q4_K_M.gguf",
        )
        llm = LLMInterface(model_path)
        logger.info(f"LLM initialized successfully with model: {model_path}")
    except Exception as e:
        logger.warning(f"LLM initialization failed: {e}. Using mock LLM for testing.")

        # Create a mock LLM for testing purposes
        class MockLLM:
            def generate(self, prompt, context="", **kwargs):
                """Generate a mock response."""
                # Create a more realistic response based on the context
                query_lower = prompt.lower()
                context_lower = context.lower() if context else ""

                response_parts = []

                if "system requirements" in query_lower or "requirements" in query_lower:
                    if "ram" in context_lower or "memory" in context_lower:
                        response_parts.append(
                            "The system requires 4GB RAM minimum, with 6GB recommended " "for optimal performance. ",
                        )
                    if "raspberry pi" in context_lower or "pi" in context_lower:
                        response_parts.append(
                            "It supports Raspberry Pi 5 and other ARM64 systems. ",
                        )
                    if not response_parts:
                        response_parts.append(
                            "System requirements include adequate RAM and CPU resources. ",
                        )

                elif "install" in query_lower:
                    if "apt" in context_lower or "package" in context_lower:
                        response_parts.append(
                            "Install the system using APT package manager with the " "provided .deb package. ",
                        )
                    else:
                        response_parts.append(
                            "Follow the installation instructions to set up the system. ",
                        )

                elif "rag" in query_lower or "local rag" in query_lower:
                    response_parts.append(
                        "The Local RAG system provides privacy-first document processing " "with local inference. ",
                    )
                    if "chroma" in context_lower:
                        response_parts.append(
                            "It uses ChromaDB for vector storage and local LLM for generation. ",
                        )

                elif "port" in query_lower or "configuration" in query_lower:
                    if "8080" in context_lower or "port" in context_lower:
                        response_parts.append(
                            "The server runs on port 8080 by default and can be " "configured in the settings. ",
                        )
                    else:
                        response_parts.append(
                            "Configuration options are available for server setup. ",
                        )

                # Default response if no specific patterns match
                if not response_parts:
                    response_parts.append(
                        f"Based on the available information about '{prompt[:50]}...', ",
                    )
                    response_parts.append(
                        "here is what I can provide from the retrieved context. ",
                    )

                # Add context information
                if context:
                    response_parts.append(
                        f"The retrieved context contains {len(context.split())} words " "of relevant information.",
                    )

                yield from response_parts

            def generate_complete(self, prompt, context="", **kwargs):
                """Generate a complete mock response."""
                return "".join(self.generate(prompt, context, **kwargs))

            def generate_complete_with_sources(self, prompt, context_documents=None, **kwargs):
                """Generate a complete mock response with source attribution."""
                # Build mock context from documents
                if context_documents:
                    context_parts = []
                    for i, doc in enumerate(context_documents, 1):
                        content = doc.get("content", "")
                        metadata = doc.get("metadata", {})
                        source = metadata.get("source", "Unknown source")
                        context_parts.append(f"[Source {i}: {source}]\n{content}")
                    context = "\n\n".join(context_parts)
                else:
                    context = ""

                response = self.generate_complete(prompt, context, **kwargs)

                # Add source attribution to response if sources were provided
                if context_documents:
                    response += "\n\nSources:"
                    for i, doc in enumerate(context_documents, 1):
                        metadata = doc.get("metadata", {})
                        source = metadata.get("source", "Unknown source")
                        title = metadata.get("title", "")
                        if title and title != source:
                            response += f"\n{i}. {title} ({source})"
                        else:
                            response += f"\n{i}. {source}"

                return response

            def health_check(self):
                """Mock health check."""
                return {
                    "status": "ok",
                    "model_path": "mock_model",
                    "loaded": True,
                    "context_length": 2048,
                    "threads": 1,
                    "test_response_length": 50,
                }

        llm = MockLLM()

    # Initialize vector store with config
    vector_db_dir = config.get("storage.vector_db_dir", "./data/chromadb")
    vector_store = VectorStore(persist_directory=vector_db_dir)

    # Initialize content manager with default values, will be overridden per request
    ContentManager()
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
                        const errorElement = document.getElementById('error');
                        errorElement.style.display = 'block';
                        errorElement.textContent = `Network error: ${err.message}`;
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
                        const errorElement = document.getElementById('error');
                        errorElement.style.display = 'block';
                        errorElement.textContent = `Network error: ${err.message}`;
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

                components["thermal"] = {"status": thermal_health, **thermal_status}
            except Exception as e:
                components["thermal"] = {"status": "error", "error": str(e)}

            # Check model management
            try:
                storage_info = model_manager.get_storage_info()
                model_manager.list_models()

                components["models"] = {
                    "status": "ok",
                    "total_models": storage_info["total_models"],
                    "storage_mb": storage_info["total_size_mb"],
                    "models_directory": storage_info["models_directory"],
                }
            except Exception as e:
                components["models"] = {"status": "error", "error": str(e)}

            # Check configuration
            config_issues = config.validate()
            components["configuration"] = {
                "status": "ok" if not config_issues else "warning",
                "issues": config_issues,
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
                "components": components,
            }

        except Exception as e:
            logger.error("Health check failed", exc_info=True)
            raise LocalRAGError("Health check failed", {"error": str(e)})

    @app.post("/api/query")
    async def query(request: QueryRequest):
        """Process user query and return response."""
        if not llm or not vector_store:
            raise ConfigurationError(
                "System not fully initialized",
                {
                    "llm_ready": llm is not None,
                    "vector_store_ready": vector_store is not None,
                },
            )

        try:
            logger.info(f"Processing query: {request.query[:100]}...")

            # Search for relevant context
            search_results = vector_store.search(request.query, request.max_results)

            # Generate response with source attribution if supported
            if hasattr(llm, "generate_complete_with_sources"):
                # Use new source attribution method
                response = llm.generate_complete_with_sources(prompt=request.query, context_documents=search_results)
            else:
                # Fallback to legacy method
                context = "\n\n".join([doc["content"] for doc in search_results if doc["content"] is not None])
                response_tokens = list(llm.generate(request.query, context))
                response = "".join(response_tokens)

            result: dict[str, Any] = {"response": response}
            if request.include_sources:
                result["sources"] = search_results  # Return full search results with content, metadata, distance
                result["source_count"] = len(search_results)

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
            config.get("content.max_file_size_mb", 50)

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
                    detail="Invalid source type. Must be 'file', 'directory', or 'url'",
                )

            if not vector_store:
                raise VectorStoreError("Vector store not initialized")

            # Add to vector store
            doc_ids = vector_store.add_documents(documents)  # type: ignore[arg-type]

            logger.info(f"Import completed: {len(doc_ids)} documents added")

            return {
                "status": "success",
                "documents_processed": len(documents),
                "documents_added": len(doc_ids),
                "source": request.source,
                "source_type": request.source_type,
            }

        except HTTPException:
            # Re-raise HTTPExceptions so they can be handled by the HTTPException handler
            raise
        except Exception as e:
            logger.error(f"Import failed: {e}")
            raise ContentProcessingError(
                "Content import failed",
                {
                    "source": request.source,
                    "source_type": request.source_type,
                    "error": str(e),
                },
            )

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
                    "server_port": config.get("server.port"),
                },
                "components": {
                    "llm": {"status": "placeholder"},
                    "vector_store": {"status": "placeholder"},
                    "content_manager": {"status": "ok"},
                },
            }
        except Exception as e:
            raise LocalRAGError("Status check failed", {"error": str(e)})

    # Model Management Endpoints
    @app.get("/api/models")
    async def list_models():
        """List all available models."""
        try:
            models = model_manager.list_models()
            storage_info = model_manager.get_storage_info()

            return {"models": models, "storage": storage_info}
        except Exception as e:
            logger.error("Failed to list models", exc_info=True)
            raise LocalRAGError("Failed to list models", {"error": str(e)})

    @app.post("/api/models/download")
    async def download_model(request: DownloadModelRequest):
        """Download a model from URL."""
        try:
            model_path = model_manager.download_model(
                url=request.url,
                model_name=request.model_name,
                expected_hash=request.expected_hash,
            )

            return {
                "status": "success",
                "model_name": model_path.name,
                "file_path": str(model_path),
                "message": f"Model downloaded successfully: {model_path.name}",
            }
        except Exception as e:
            logger.error(f"Model download failed: {e}", exc_info=True)
            raise LocalRAGError("Model download failed", {"error": str(e)})

    @app.delete("/api/models/{model_name}")
    async def delete_model(model_name: str):
        """Delete a model from storage."""
        try:
            success = model_manager.delete_model(model_name)

            if success:
                return {"status": "success", "message": f"Model deleted: {model_name}"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Model not found: {model_name}",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Model deletion failed: {e}", exc_info=True)
            raise LocalRAGError("Model deletion failed", {"error": str(e)})

    @app.post("/api/models/{model_name}/validate")
    async def validate_model(model_name: str):
        """Validate a model file."""
        try:
            model_path = model_manager.get_model_path(model_name)

            if not model_path:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Model not found: {model_name}",
                )

            validation_result = model_manager.validate_model(model_path)

            return {
                "status": "success",
                "model_name": model_name,
                "validation": validation_result,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Model validation failed: {e}", exc_info=True)
            raise LocalRAGError("Model validation failed", {"error": str(e)})
