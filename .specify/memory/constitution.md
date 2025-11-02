<!--
Version: 1.0.0 → 1.0.0 (INITIAL)
Changes: First constitution based on existing CONSTITUTION.md and project analysis
Added: Privacy-First, Resource Efficiency, Local-Only Operation, Single Process Architecture, Testing Excellence principles
Templates: ✅ Plan template aligned ✅ Spec template aligned ✅ Tasks template aligned
-->

# Local RAG System Constitution

## Core Principles

### I. Privacy-First Architecture

All data processing and inference MUST happen locally without external dependencies. The system MUST NOT transmit user content, queries, or generated responses to external services. Internet connectivity is permitted only for initial model downloads and software updates.

**Rationale**: Privacy is non-negotiable for knowledge management systems containing sensitive information.

### II. Resource Efficiency

The system MUST operate within Pi5 constraints (<6GB RAM, ARM64 CPU) while maintaining functionality. All components MUST be optimized for memory usage and thermal management. Resource monitoring and configurable limits are mandatory.

**Rationale**: Edge deployment on constrained hardware requires careful resource management.

### III. Local-Only Operation

The system MUST function completely offline after initial setup. All LLM inference, vector operations, and content processing MUST work without internet connectivity. Recovery from power loss MUST NOT require external resources.

**Rationale**: Ensures system reliability in isolated or network-constrained environments.

### IV. Single Process Architecture

All components (FastAPI, llama-cpp-python, ChromaDB) MUST run within a single Python process managed by systemd. No external services or containers are permitted. Inter-process communication overhead MUST be avoided.

**Rationale**: Simplifies deployment, reduces resource overhead, and improves reliability on edge devices.

### V. Testing Excellence

Test-driven development is mandatory: tests MUST be written before implementation, achieve >85% coverage, and include unit, integration, and BDD acceptance tests. All critical paths MUST have comprehensive error handling tests.

**Rationale**: High reliability requirements demand rigorous testing practices.

## Deployment Standards

The system MUST use Debian (.deb) packages for distribution across ARM64 (Pi5) and AMD64 architectures. Installation MUST complete in under 5 minutes on clean systems. Systemd integration is mandatory for service lifecycle management. Configuration MUST be centralized in `/etc/local-rag/config.yaml`.

## Performance Requirements

The system MUST achieve Pi5 cold start within 3-5 minutes for first token, warm queries within 1-3 minutes for first token. The system MUST handle 100+ documents (2K-10K words each) without performance degradation. Real-time streaming responses are mandatory for user interface responsiveness.

## Governance

This constitution supersedes all conflicting practices. All code changes MUST verify compliance with these principles. Complexity additions MUST be explicitly justified against simplicity requirements. Amendments require technical impact assessment and alignment with existing specifications.

**Version**: 1.0.0 | **Ratified**: 2025-10-30 | **Last Amended**: 2025-10-30
