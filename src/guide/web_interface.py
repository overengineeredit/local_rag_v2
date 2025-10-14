"""
FastAPI web interface providing REST API and basic web UI.
Handles query processing, content management, and system administration.
"""

from __future__ import annotations

import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .content_manager import ContentManager

logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    """Request model for user queries."""

    query: str
    max_results: int = 5


class ImportRequest(BaseModel):
    """Request model for content import."""

    source: str
    source_type: str = "file"  # file, directory, url


def setup_routes(app: FastAPI) -> None:
    """Setup all API routes for the application."""

    # Initialize core components (TODO: move to dependency injection)
    llm = None  # Will be initialized with actual config
    vector_store = None
    content_manager = ContentManager()

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
                button { padding: 10px 20px; background: #007cba; color: white; border: none; cursor: pointer; }
                .response { background: #f5f5f5; padding: 20px; margin: 20px 0; white-space: pre-wrap; }
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
                // Basic JavaScript for form handling (TODO: enhance)
                document.getElementById('queryForm').onsubmit = async (e) => {
                    e.preventDefault();
                    const query = document.getElementById('query').value;
                    const response = await fetch('/api/query', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({query})
                    });
                    const result = await response.text();
                    document.getElementById('response').style.display = 'block';
                    document.getElementById('response').textContent = result;
                };
            </script>
        </body>
        </html>
        """

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "ok",
            "service": "local-rag",
            "components": {
                "llm": llm.health_check() if llm else {"status": "not_initialized"},
                "vector_store": vector_store.health_check()
                if vector_store
                else {"status": "not_initialized"},
            },
        }

    @app.post("/api/query")
    async def query(request: QueryRequest):
        """Process user query and return response."""
        if not llm or not vector_store:
            raise HTTPException(status_code=503, detail="System not initialized")

        try:
            # Search for relevant context
            search_results = vector_store.search(request.query, request.max_results)
            context = "\n\n".join([doc["content"] for doc in search_results])

            # Generate response (placeholder - not streaming yet)
            response_tokens = list(llm.generate(request.query, context))
            response = "".join(response_tokens)

            return {"response": response, "sources": search_results}

        except Exception as e:
            logger.error(f"Query processing error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/import")
    async def import_content(request: ImportRequest):
        """Import content from various sources."""
        try:
            documents = []

            if request.source_type == "file":
                documents = content_manager.ingest_file(request.source)
            elif request.source_type == "directory":
                documents = content_manager.ingest_directory(request.source)
            elif request.source_type == "url":
                documents = content_manager.ingest_url(request.source)
            else:
                raise HTTPException(status_code=400, detail="Invalid source type")

            if not vector_store:
                raise HTTPException(status_code=503, detail="Vector store not initialized")

            # Add to vector store
            doc_ids = vector_store.add_documents(documents)

            return {
                "status": "success",
                "documents_processed": len(documents),
                "documents_added": len(doc_ids),
                "source": request.source,
            }

        except Exception as e:
            logger.error(f"Import error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/reset")
    async def reset_database():
        """Reset the vector database."""
        # TODO: Implement database reset
        return {"status": "success", "message": "Database reset (placeholder)"}

    @app.get("/api/status")
    async def system_status():
        """Get detailed system status."""
        return {
            "system": "local-rag",
            "version": "1.0.0",
            "components": {
                "llm": {"status": "placeholder"},
                "vector_store": {"status": "placeholder"},
                "content_manager": {"status": "ok"},
            },
        }
