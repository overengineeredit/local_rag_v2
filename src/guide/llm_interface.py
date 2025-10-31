"""
LLM interface using llama-cpp-python for local inference.
Handles model loading, configuration, and token streaming.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Query:
    """Entity model for user queries in the RAG system."""
    
    query_id: str  # Unique identifier for the query
    text: str  # Query text
    user_id: str | None = None  # Optional user identifier
    max_results: int = 5  # Maximum number of context results to retrieve
    include_sources: bool = True  # Whether to include sources in response
    temperature: float | None = None  # Override default temperature
    max_tokens: int | None = None  # Override default max tokens
    context_documents: list[dict[str, Any]] = field(default_factory=list)  # Retrieved context
    response: str = ""  # Generated response
    metadata: dict[str, Any] = field(default_factory=dict)  # Additional metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: datetime | None = None  # When processing completed
    processing_time: float | None = None  # Processing time in seconds
    
    def to_dict(self) -> dict[str, Any]:
        """Convert query to dictionary for storage/logging."""
        return {
            "query_id": self.query_id,
            "text": self.text,
            "user_id": self.user_id,
            "max_results": self.max_results,
            "include_sources": self.include_sources,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "context_documents": self.context_documents,
            "response": self.response,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "processing_time": self.processing_time
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Query":
        """Create query from dictionary."""
        # Parse datetime fields
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        elif created_at is None:
            created_at = datetime.now(timezone.utc)
            
        processed_at = data.get("processed_at")
        if isinstance(processed_at, str):
            processed_at = datetime.fromisoformat(processed_at.replace('Z', '+00:00'))
            
        return cls(
            query_id=data["query_id"],
            text=data["text"],
            user_id=data.get("user_id"),
            max_results=data.get("max_results", 5),
            include_sources=data.get("include_sources", True),
            temperature=data.get("temperature"),
            max_tokens=data.get("max_tokens"),
            context_documents=data.get("context_documents", []),
            response=data.get("response", ""),
            metadata=data.get("metadata", {}),
            created_at=created_at,
            processed_at=processed_at,
            processing_time=data.get("processing_time")
        )
    
    def mark_processed(self, response: str, processing_time: float) -> None:
        """Mark query as processed with response and timing."""
        self.response = response
        self.processed_at = datetime.now(timezone.utc)
        self.processing_time = processing_time
    
    def add_context_document(self, content: str, metadata: dict[str, Any], distance: float) -> None:
        """Add a context document to the query."""
        self.context_documents.append({
            "content": content,
            "metadata": metadata,
            "distance": distance,
            "added_at": datetime.now(timezone.utc).isoformat()
        })
    
    def get_context_text(self) -> str:
        """Get combined context text from all retrieved documents."""
        return "\n\n".join([doc["content"] for doc in self.context_documents])
    
    @classmethod
    def create_query_id(cls, text: str, user_id: str | None = None) -> str:
        """Create a unique query ID."""
        import hashlib
        import uuid
        
        # Use timestamp and text hash for uniqueness
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:8]
        unique_suffix = str(uuid.uuid4())[:8]
        
        return f"query_{timestamp}_{text_hash}_{unique_suffix}"


class LLMInterface:
    """Interface for local LLM inference using llama-cpp-python."""

    def __init__(self, model_path: str, **kwargs):
        """Initialize the LLM interface.

        Args:
            model_path: Path to GGUF model file
            **kwargs: Additional llama-cpp-python parameters
        """
        self.model_path = model_path
        self.model = None
        self.default_params = {
            "n_ctx": kwargs.get("n_ctx", 2048),  # Context length
            "n_threads": kwargs.get("n_threads"),  # CPU threads (auto-detect if None)
            "n_gpu_layers": kwargs.get("n_gpu_layers", 0),  # GPU layers
            "verbose": kwargs.get("verbose", False),
            "seed": kwargs.get("seed", -1)  # Random seed
        }
        self._load_model(**kwargs)

    def _load_model(self, **kwargs) -> None:
        """Load the GGUF model using llama-cpp-python."""
        try:
            logger.info(f"Loading model from {self.model_path}")
            
            # Import llama-cpp-python
            from llama_cpp import Llama
            
            # Merge default params with provided kwargs
            model_params = {**self.default_params, **kwargs}
            
            # Auto-detect CPU threads if not specified
            if model_params["n_threads"] is None:
                import os
                model_params["n_threads"] = os.cpu_count()
                logger.info(f"Auto-detected {model_params['n_threads']} CPU threads")
            
            # Load the model
            self.model = Llama(
                model_path=self.model_path,
                **model_params
            )
            
            logger.info("Model loaded successfully")
            
        except ImportError:
            logger.error("llama-cpp-python not installed. Run: pip install llama-cpp-python")
            raise RuntimeError("llama-cpp-python dependency missing")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model loading failed: {e}") from e

    def generate(self, prompt: str, context: str = "", **kwargs) -> Iterator[str]:
        """Generate response tokens from prompt and context.

        Args:
            prompt: User query
            context: Retrieved context from vector database
            **kwargs: Override generation parameters (temperature, max_tokens, etc.)

        Yields:
            Generated tokens
        """
        if not self.model:
            raise RuntimeError("Model not loaded")
            
        try:
            # Build the full prompt
            full_prompt = self._build_prompt(prompt, context)
            
            # Get generation parameters from config and kwargs
            from . import config
            generation_params = {
                "max_tokens": kwargs.get("max_tokens") or config.get("llm.max_tokens", 512),
                "temperature": kwargs.get("temperature") or config.get("llm.temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
                "top_k": kwargs.get("top_k", 40),
                "repeat_penalty": kwargs.get("repeat_penalty", 1.1),
                "stream": True  # Always stream
            }
            
            logger.info(f"Generating response with params: {generation_params}")
            
            # Generate tokens
            response_stream = self.model(
                full_prompt,
                **generation_params
            )
            
            # Yield tokens from the stream
            for token_data in response_stream:
                if isinstance(token_data, dict) and "choices" in token_data:
                    choice = token_data["choices"][0]
                    if "text" in choice:
                        yield choice["text"]
                    elif "delta" in choice and "content" in choice["delta"]:
                        yield choice["delta"]["content"]
                else:
                    # Handle different response formats
                    yield str(token_data)
                    
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise RuntimeError(f"Text generation failed: {e}") from e

    def generate_complete(self, prompt: str, context: str = "", **kwargs) -> str:
        """Generate complete response (non-streaming).

        Args:
            prompt: User query
            context: Retrieved context from vector database
            **kwargs: Override generation parameters

        Returns:
            Complete generated response
        """
        try:
            tokens = list(self.generate(prompt, context, **kwargs))
            return "".join(tokens)
        except Exception as e:
            logger.error(f"Complete generation failed: {e}")
            raise

    def process_query(self, query: Query) -> Query:
        """Process a Query object and update it with response.

        Args:
            query: Query object to process

        Returns:
            Updated query object with response
        """
        import time
        
        start_time = time.time()
        
        try:
            # Get context text from query
            context = query.get_context_text()
            
            # Generate response
            response = self.generate_complete(
                prompt=query.text,
                context=context,
                temperature=query.temperature,
                max_tokens=query.max_tokens
            )
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update query with response
            query.mark_processed(response, processing_time)
            
            logger.info(f"Query processed in {processing_time:.2f}s")
            return query
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_response = f"Error generating response: {str(e)}"
            query.mark_processed(error_response, processing_time)
            logger.error(f"Query processing failed after {processing_time:.2f}s: {e}")
            raise

    def _build_prompt(self, query: str, context: str) -> str:
        """Build the final prompt with context and query."""
        if not context.strip():
            # No context available
            return f"""You are a helpful AI assistant. Please answer the following question to the best of your ability.

Question: {query}

Answer:"""
        
        # With context
        return f"""You are a helpful AI assistant. Use the following context to answer the question. If the context doesn't contain relevant information, say so clearly.

Context:
{context}

Question: {query}

Answer:"""

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for given text.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        if self.model and hasattr(self.model, "tokenize"):
            try:
                tokens = self.model.tokenize(text.encode("utf-8"))
                return len(tokens)
            except Exception:
                pass
        
        # Fallback estimation: roughly 4 characters per token
        return len(text) // 4

    def validate_context_length(self, prompt: str, context: str, max_context_ratio: float = 0.7) -> tuple[str, bool]:
        """Validate and truncate context to fit within model limits.
        
        Args:
            prompt: User query
            context: Retrieved context
            max_context_ratio: Maximum ratio of context tokens to total context window
            
        Returns:
            Tuple of (adjusted_context, was_truncated)
        """
        from . import config
        
        max_context_length = config.get("llm.context_length", 2048)
        
        # Build prompt to estimate total tokens
        full_prompt = self._build_prompt(prompt, context)
        total_tokens = self.estimate_tokens(full_prompt)
        
        if total_tokens <= max_context_length:
            return context, False
        
        # Calculate available tokens for context
        prompt_template_tokens = self.estimate_tokens(self._build_prompt(prompt, ""))
        available_context_tokens = int((max_context_length - prompt_template_tokens) * max_context_ratio)
        
        if available_context_tokens <= 0:
            logger.warning("Query too long, context will be empty")
            return "", True
        
        # Truncate context to fit
        target_chars = available_context_tokens * 4  # Rough estimation
        if len(context) > target_chars:
            truncated_context = context[:target_chars].rsplit('.', 1)[0] + "..."
            logger.warning(f"Context truncated from {len(context)} to {len(truncated_context)} characters")
            return truncated_context, True
        
        return context, False

    def health_check(self) -> dict:
        """Check if the LLM is healthy and responsive."""
        try:
            if not self.model:
                return {
                    "status": "error",
                    "model_path": self.model_path,
                    "loaded": False,
                    "error": "Model not loaded"
                }
            
            # Test basic functionality
            test_response = self.generate_complete("Test", max_tokens=5)
            
            return {
                "status": "ok",
                "model_path": self.model_path,
                "loaded": True,
                "context_length": self.default_params["n_ctx"],
                "threads": self.default_params["n_threads"],
                "test_response_length": len(test_response)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "model_path": self.model_path,
                "loaded": self.model is not None,
                "error": str(e)
            }
