"""
Local RAG (Retrieval-Augmented Generation) System.

A CPU-first RAG system designed for privacy, learning, and offline operation.
Optimized for resource-constrained devices like Raspberry Pi 5.
"""

__version__ = "1.0.0"
__author__ = "Peenak Inamdar"
__description__ = "Local Retrieval-Augmented Generation system"

# Main components
from .cli import LocalRAGCLI
from .content_manager import ContentManager
from .llm_interface import LLMInterface
from .main import create_app
from .vector_store import VectorStore

__all__ = ["create_app", "LLMInterface", "VectorStore", "ContentManager", "LocalRAGCLI"]
