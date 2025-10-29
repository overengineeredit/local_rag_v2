# Implementation Plan: Local RAG System

**Branch**: `001-local-rag-mvp` | **Date**: 2025-10-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-local-rag-mvp/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Primary requirement: Implement a local Retrieval-Augmented Generation (RAG) system that performs inference entirely on local hardware without internet dependency. Technical approach: Single Python application using llama-cpp-python for LLM inference, ChromaDB with SQLite for vector storage, FastAPI for web interface, and APT packaging for easy deployment on ARM64 (Pi5) and AMD64 systems.

## Technical Context

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, llama-cpp-python, ChromaDB, uvicorn, pydantic, rich (CLI)  
**Storage**: ChromaDB with SQLite backend for vector embeddings, filesystem for models and configuration  
**Testing**: pytest for unit tests, httpx for API testing, BDD testing for acceptance scenarios  
**Target Platform**: Linux (ARM64 for Raspberry Pi 5, AMD64 for desktop/server)
**Project Type**: Single Python application with embedded services  
**Performance Goals**: Pi5 cold start 3-5 minutes first token, warm queries 1-3 minutes first token, desktop sub-second to 30 seconds  
**Constraints**: <6GB RAM on Pi5, battery-friendly operation, offline-capable, survive power loss without corruption  
**Scale/Scope**: 100+ documents (2K-10K words each), single-user device, embedded service architecture

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**CRITICAL**: Constitution file contains only template placeholders. The following analysis is based on the template structure until actual project principles are defined:

- **[PRINCIPLE_1_NAME]**: NEEDS CONSTITUTION - Template placeholder, no actual principle defined
- **[PRINCIPLE_2_NAME]**: NEEDS CONSTITUTION - Template placeholder, no actual principle defined  
- **[PRINCIPLE_3_NAME]**: NEEDS CONSTITUTION - Template placeholder, no actual principle defined
- **[PRINCIPLE_4_NAME]**: NEEDS CONSTITUTION - Template placeholder, no actual principle defined
- **[PRINCIPLE_5_NAME]**: NEEDS CONSTITUTION - Template placeholder, no actual principle defined

**ACTION REQUIRED**: Update `.specify/memory/constitution.md` with actual project principles before proceeding with implementation.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Single Python application with embedded services
src/
├── guide/
│   ├── __init__.py
│   ├── main.py              # Application entry point and FastAPI app
│   ├── llm_interface.py     # llama-cpp-python integration
│   ├── vector_store.py      # ChromaDB management and operations
│   ├── content_manager.py   # Document ingestion and processing  
│   ├── web_interface.py     # FastAPI routes and web UI
│   └── cli.py              # Command-line interface

tests/
├── unit/                   # Unit tests for all modules
├── integration/            # API and CLI integration tests
└── acceptance/             # BDD acceptance tests

config/
├── local-rag.service       # systemd service configuration
└── config.yaml.example    # Example configuration file

packaging/
├── debian/                 # APT package build files
│   ├── control
│   ├── rules
│   ├── postinst
│   └── prerm
└── scripts/               # Package build and CI scripts
```

**Structure Decision**: Single project structure chosen because the system is designed as a monolithic Python application with embedded services (LLM, vector DB, web UI) running in a single process managed by systemd. This aligns with the requirement for easy deployment and resource efficiency on constrained hardware like Raspberry Pi 5.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
