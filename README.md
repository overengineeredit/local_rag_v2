# Local RAG — Production-Ready Edge LLM System

This repository implements a **comprehensive, production-ready** local RAG system using **GitHub SpecKit** methodology:
- **Feature-driven development** with complete specifications (`/specs/001-local-rag-mvp/`)
- **4-milestone development strategy** with defined deliverables and success criteria
- **Dual hash strategy** for intelligent content management and change detection
- **Enterprise-grade architecture** with formal ADRs, risk assessment, and comprehensive testing
- **Cross-platform deployment** (Pi5 ARM64, AMD64) with professional APT packaging

> **Production Goal**: A complete, offline RAG (Retrieval-Augmented Generation) system that delivers enterprise-quality local LLM inference. Features comprehensive content management, thermal-aware operation, robust error handling, and professional deployment capabilities.

## ✨ Production Features

### Core Capabilities
- **🔒 Privacy-First**: 100% local processing, zero cloud dependencies
- **🧠 Smart Content Management**: Dual hash strategy with source-aware change detection
- **🔄 Efficient Updates**: Intelligent content refresh without re-downloading  
- **⚡ Performance Optimized**: Pi5 cold start 3-5min, warm queries 1-3min first token
- **📱 Cross-Platform**: ARM64 (Pi5) and AMD64 with identical functionality

### Enterprise Features
- **🌡️ Thermal Management**: CPU temperature monitoring with automatic throttling
- **🛡️ Resilience**: Power-loss recovery, database integrity checks, graceful degradation
- **📊 Production Monitoring**: Health checks, metrics, structured JSON logging
- **🔧 Professional Deployment**: APT packages, systemd service, configuration management
- **🧪 Comprehensive Testing**: Unit, integration, BDD tests with 85%+ coverage

### User Experience
- **🌐 Web Interface**: FastAPI backend with responsive UI (720p+ screens)
- **⚡ CLI Interface**: Rich terminal commands with progress reporting
- **📈 Real-time Feedback**: Streaming responses, import progress, health status
- **🎯 User-Focused**: Installation in <5 minutes, intuitive operation

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│             Production System               │
│                                             │
│  ┌─────────────────────────────────────────┐│
│  │         Python Application              ││
│  │                                         ││
│  │  ┌─────────────┐  ┌─────────────────┐   ││
│  │  │   FastAPI   │  │ llama-cpp-python│   ││
│  │  │ Web UI+API  │  │   LLM Engine    │   ││
│  │  └─────────────┘  └─────────────────┘   ││
│  │                                         ││
│  │  ┌─────────────────────────────────────┐││
│  │  │     ChromaDB (SQLite Backend)       │││
│  │  │   + Dual Hash Content Management    │││
│  │  └─────────────────────────────────────┘││
│  └─────────────────────────────────────────┘│
│                                             │
│  systemd + APT package management           │
└─────────────────────────────────────────────┘
```

## Quickstart

### Development Mode
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start the development server with full monitoring
python -m guide.main

# In another terminal, use the comprehensive CLI
python -m guide.cli status                  # System health and component status
python -m guide.cli import /path/to/docs    # Batch import with progress
python -m guide.cli import --url https://example.com/article.html
python -m guide.cli check-updates           # Intelligent update detection  
python -m guide.cli update --changed-only   # Selective content refresh
python -m guide.cli query "What is this about?"
python -m guide.cli backup /path/to/backup  # Data backup/restore

# Web interface with real-time features at http://localhost:8080
```

### Production Deployment
```bash
# Professional installation via APT package
sudo apt install ./local-rag_1.0.0_arm64.deb

# Production service management
sudo systemctl start local-rag
sudo systemctl enable local-rag

# Production CLI with full feature set
local-rag status                           # Health monitoring
local-rag import /path/to/documents        # Production content management
local-rag import --batch /path/to/folders  # Batch processing
local-rag check-updates                    # Automated update detection
local-rag update --resume                  # Resumable operations
local-rag download-model deepseek-r1       # Model management
local-rag backup --encrypt /secure/path    # Enterprise backup
```
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
