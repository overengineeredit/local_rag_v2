# Local RAG — Edge LLM (CPU-First)

This repository implements a **privacy-focused** local RAG system using **GitHub SpecKit** methodology:
- **Feature-driven development** with organized specs (`/specs/001-local-rag-mvp/`)
- **User story-based** task breakdown for independent delivery
- **Dual hash strategy** for intelligent content management and change detection
- **Cross-platform compatibility** (Pi5 ARM64, AMD64) with APT packaging

> **Goal**: A portable, offline RAG (Retrieval-Augmented Generation) system that runs local LLM inference via CPU-based llama-cpp-python. Features intelligent content management with source-aware change detection, cross-source deduplication, and efficient update mechanisms.

## ✨ Key Features

- **🔒 Privacy-First**: All processing happens locally, no cloud dependencies
- **🧠 Smart Content Management**: Dual hash strategy detects changes without re-downloading
- **🔄 Efficient Updates**: Only re-process content that has actually changed
- **📱 Cross-Platform**: ARM64 (Pi5) and AMD64 support via APT packages
- **🌐 Web Interface**: Clean FastAPI backend with intuitive web UI
- **⚡ CLI Interface**: Rich terminal commands for all operations
- **📊 Progress Tracking**: Real-time import progress and update status

## Quickstart

**Development Mode:**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start the web server
python -m guide.main

# In another terminal, use the enhanced CLI
python -m guide.cli status
python -m guide.cli import /path/to/documents
python -m guide.cli check-updates          # Check for content changes
python -m guide.cli update --changed-only  # Update only changed content
python -m guide.cli query "What is this about?"

# Or use the web interface at http://localhost:8080
```

**Production Deployment:**
```bash
# Install from .deb package (future release)
sudo apt install ./local-rag_1.0.0_arm64.deb

# Use production CLI with enhanced features
local-rag status
local-rag import /path/to/documents
local-rag import --url https://example.com/article.html
local-rag check-updates                    # Smart update detection
local-rag update --changed-only           # Efficient selective updates
local-rag list --show-updates             # View content status
local-rag query "What is this about?"

# Access web interface at http://localhost:8080
```

## Repository Layout

```text
specs/                 — SpecKit-compliant feature specifications
├── 001-local-rag-mvp/ — Current feature implementation
│   ├── spec.md        — User stories and requirements
│   ├── plan.md        — Technical implementation plan
│   ├── tasks.md       — Detailed task breakdown by user story
│   ├── data-model.md  — Entity definitions and relationships
│   ├── research.md    — Technology research and decisions
│   ├── quickstart.md  — Getting started guide
│   └── contracts/     — API specifications (OpenAPI)
└── [legacy docs]/     — Original fragmented specifications

.specify/              — SpecKit framework and templates
├── memory/constitution.md — Project principles and standards
├── scripts/           — Development workflow automation
└── templates/         — SpecKit templates for new features

src/guide/             — Python implementation
├── main.py           — FastAPI application entry point
├── llm_interface.py  — LLM integration (llama-cpp-python)
├── vector_store.py   — ChromaDB vector database management
├── content_manager.py — Dual hash content processing
├── web_interface.py  — FastAPI routes and web UI
└── cli.py           — Rich terminal interface

tests/                — Comprehensive test suite
├── unit/            — Unit tests for core modules
├── integration/     — API and workflow integration tests
└── acceptance/      — BDD tests for user scenarios

.github/              — CI/CD workflows and automation
prompts/              — AI assistant system prompts
```

## What this **is**

- 🎯 **Privacy-focused RAG system** with local-only inference and processing
- 🔄 **Intelligent content management** with dual hash strategy for change detection  
- 📈 **Efficient update workflows** that only re-process changed content
- 🌐 **Cross-source deduplication** maintaining separate source tracking
- 🖥️ **Cross-platform deployment** via APT packages (ARM64 + AMD64)
- 🎨 **Clean interfaces**: FastAPI backend, web UI, and rich CLI
- 📊 **Progress tracking** and status monitoring for all operations
- 🧪 **Comprehensive testing** with unit, integration, and BDD coverage

## What this **is not** (yet)

- ❌ Hardware-accelerated inference (NPU/GPU support planned for future versions)
- ❌ Multi-user authentication or enterprise features
- ❌ Real-time collaboration or cloud synchronization
- ❌ Advanced document parsing (PDFs, Office docs) - text/HTML/URLs only in v1
- ❌ Production-hardened security (single-user device assumption)

## Getting Started

1. **Quick Demo**: Follow the Development Mode quickstart above
2. **Full Documentation**: See `specs/001-local-rag-mvp/quickstart.md`
3. **API Reference**: Check `specs/001-local-rag-mvp/contracts/api.yaml`
4. **Implementation Tasks**: Review `specs/001-local-rag-mvp/tasks.md`

## Contributing

This project follows SpecKit methodology. See `.specify/memory/constitution.md` for development principles and quality standards.
