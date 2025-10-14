"""
Local RAG (Retrieval-Augmented Generation) System.

A CPU-first RAG system designed for privacy, learning, and offline operation.
Optimized for resource-constrained devices like Raspberry Pi 5.
"""

__version__ = "1.0.0"
__author__ = "Peenak Inamdar"
__description__ = "Local Retrieval-Augmented Generation system"

# Main components
from .main import create_app
from .llm_interface import LLMInterface
from .vector_store import VectorStore
from .content_manager import ContentManager
from .cli import LocalRAGCLI

__all__ = ["create_app", "LLMInterface", "VectorStore", "ContentManager", "LocalRAGCLI"]
