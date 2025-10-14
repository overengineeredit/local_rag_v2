# Local RAG — Edge LLM (CPU-First)

This repository is a **Claude-friendly** code workspace scaffolded using a lightweight interpretation of **GitHub's SpecKit** approach:
- Work from an explicit, versioned **spec** (`/specs`).
- Keep **prompts** and **assumptions** visible (`/prompts`).
- Ship a minimal, testable **prototype** (`/src` + `/tests`).
- Automate formatting/tests with CI.

> Goal: a portable, offline RAG (Retrieval-Augmented Generation) system that runs local LLM inference via CPU-based llama-cpp-python. Cross-platform compatible (Pi5 ARM64, AMD64) with document ingestion and vector search capabilities.

## Quickstart

**Development Mode:**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start the web server
python -m guide.main

# In another terminal, use the CLI
python -m guide.cli status
python -m guide.cli import /path/to/documents
python -m guide.cli query "What is this about?"

# Or use the web interface at http://localhost:8080
```

**Production Deployment (future):**
```bash
# Install from .deb package
sudo apt install ./local-rag_1.0.0_arm64.deb

# Use production CLI commands
local-rag status
local-rag import /path/to/documents
local-rag query "What is this about?"

# Access web interface at http://localhost:8080
```

## Repo Layout

```
specs/     — Problem, requirements, design, milestones, risks (SpecKit-style docs)
prompts/   — System prompt(s) for Claude and task guides
src/guide/ — Python prototype: LLM interface, ChromaDB, FastAPI, web UI
tests/     — Minimal unit tests to keep interfaces honest
.github/   — CI workflow (lint + tests)
```

## What this **is**

A CPU-first RAG system with clean interfaces: document ingestion, vector storage (ChromaDB), local LLM inference (llama-cpp-python), and web-based query interface.

## What this **is not** (yet)

- A production-ready deployment (v1 prototype).
- Hardware-accelerated inference (NPU/GPU support planned for future versions).
- A full-featured document processing pipeline.

See the **Open Questions** in the spec and create issues/milestones from those checklists.
