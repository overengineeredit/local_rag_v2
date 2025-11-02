# Problem Statement

## Overview

This project implements a local Retrieval-Augmented Generation (RAG) system designed for privacy, learning, and offline operation. Inspired by the approach in ["A Local RAG on a RasPi"](https://overengineeredit.medium.com/a-local-rag-on-a-raspi-439496796324), this system runs entirely on local hardware without requiring internet connectivity for inference.

## Motivation

- **Privacy**: All data processing and inference happens locally
- **Education**: Learn RAG architecture, vector databases, and LLM deployment
- **Portability**: Run on resource-constrained devices like Raspberry Pi 5
- **Simplicity**: Easy installation and maintenance via standard Linux packaging

## Technical Requirements

- The system must be easy to deploy and maintain on a Raspberry Pi 5 (ARM64) and AMD64 Linux systems
- All dependencies (LLM, vector DB, web UI) should be installed via a single `.deb` package
- No Docker or external LLM server is required; all components run as a single systemd-managed Python service
- Local inference only; no internet dependency for generation
- Streaming tokens to UI for immediate responsiveness
- Battery-friendly: low idle draw, predictable thermal envelope
- Resilience: survive ungraceful power loss without corrupting state

## Core Components

- **LLM Engine**: llama-cpp-python for local inference with GGUF models
- **Vector Database**: ChromaDB (using embedded SQLite) for document storage and retrieval
- **Web Interface**: FastAPI backend with simple web UI
- **Content Ingestion**: Support for text files, HTML, and URLs
- **Package Management**: APT-based installation with systemd service integration

## RAG Workflow

1. **Document Ingestion**: Process text/HTML/URLs into chunks
2. **Embedding Generation**: Create vector embeddings for semantic search
3. **Vector Storage**: Store embeddings and metadata in ChromaDB
4. **Query Processing**: Accept user prompts via web interface
5. **Retrieval**: Find relevant document chunks using similarity search
6. **Generation**: Use retrieved context with LLM to generate responses
7. **Response Streaming**: Stream generated tokens back to user interface

## Hardware Stack

- **Primary Target**: Raspberry Pi 5 (4 ARM cores, 4-8GB RAM)
- **Secondary Target**: AMD64 Linux systems
- **Storage**: MicroSD or SSD for document storage and models
- **Network**: Local web interface, no external dependencies

## Software Stack

- **Runtime**: Python 3.11+ with systemd service management
- **LLM**: llama-cpp-python with small models (1-8B parameters)
- **Vector DB**: ChromaDB with SQLite backend
- **Web Framework**: FastAPI for REST API and web interface
- **Distribution**: Debian packages for ARM64 and AMD64

## Expected Challenges

- **Resource Constraints**: Limited RAM and CPU on Pi5 requiring careful optimization
- **Model Selection**: Finding the right balance between model capability and resource usage
- **Response Quality**: Ensuring good RAG performance with smaller models
- **Package Management**: Creating robust cross-architecture APT packages
- **Performance Expectations**: Reference implementation shows desktop 1-2 seconds, Pi/CM4 "a few minutes"

## Success Criteria

- Single-command installation on Pi5 and AMD64 systems
- Responsive web interface for document upload and querying
- Reliable document ingestion with deduplication
- Coherent responses to questions about ingested content
- System stability under resource constraints
- Easy content management and system monitoring
- Performance targets: Cold start 3-5 minutes, warm queries 1-3 minutes (Pi5)

## Extended Context (from "A Local RAG on a RasPi")

The project is inspired by the need for a **private, self-contained knowledge base** that can be queried using a local LLM. Key drivers include privacy, education, and technical curiosity about running RAG pipelines on hobbyist hardware.

## Lessons Learned

- Smaller LLMs may hallucinate; RAG helps by grounding answers in curated content
- Hardware constraints require careful model and DB selection
- Open-source tools make local RAG feasible but require tuning
- The technical landscape evolves rapidly; flexibility is important
