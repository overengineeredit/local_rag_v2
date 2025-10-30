# Implementation Plan: Local RAG System

**Branch**: `001-local-rag-mvp` | **Date**: 2025-10-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-local-rag-mvp/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Primary requirement: Implement a local Retrieval-Augmented Generation (RAG) system that performs inference entirely on local hardware without internet dependency. Technical approach: Single Python application using llama-cpp-python for LLM inference, ChromaDB with SQLite for vector storage, FastAPI for web interface, and Debian package (.deb) deployment for easy installation on ARM64 (Pi5) and AMD64 systems via APT package manager.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, llama-cpp-python, ChromaDB, uvicorn, pydantic, rich (CLI)  
**Storage**: ChromaDB with SQLite backend for vector embeddings, filesystem for models and configuration  
**Testing**: pytest for unit tests, httpx for API testing, BDD testing for acceptance scenarios  
**Target Platform**: Debian-based Linux distributions (Ubuntu 22.04 LTS, Debian 12, Raspberry Pi OS) on ARM64 (Pi5) and AMD64 architectures
**Project Type**: Single Python application with embedded services  
**Performance Goals**: Pi5 cold start 3-5 minutes first token, warm queries 1-3 minutes first token, desktop sub-second to 30 seconds  
**Constraints**: <6GB RAM on Pi5, battery-friendly operation, offline-capable, survive power loss without corruption  
**Scale/Scope**: 100+ documents (2K-10K words each), single-user device, embedded service architecture

### Architecture Overview

The system consists of a single Python process managed by systemd, containing all necessary components:

```txt
┌─────────────────────────────────────────────┐
│                 Pi5/AMD64 Host              │
│                                             │
│  ┌─────────────────────────────────────────┐│
│  │         Python Application              ││
│  │                                         ││
│  │  ┌─────────────┐  ┌─────────────────┐   ││
│  │  │   FastAPI   │  │ llama-cpp-python│   ││
│  │  │  Web UI     │  │   LLM Engine    │   ││
│  │  │   + API     │  │                 │   ││
│  │  └─────────────┘  └─────────────────┘   ││
│  │                                         ││
│  │  ┌─────────────────────────────────────┐││
│  │  │            ChromaDB                 │|│
│  │  │        (SQLite Backend)             │|│
│  │  └─────────────────────────────────────┘││
│  └─────────────────────────────────────────┘│
│                                             │
│  systemd manages the service lifecycle      │
└─────────────────────────────────────────────┘
```

### Module Responsibilities

#### Core Application Modules

**`main.py` - Application Entry Point**

- FastAPI app initialization and configuration loading
- Health check endpoints (`/health`) and system status reporting
- Configuration validation and environment setup
- Service lifecycle management and graceful shutdown
- Error handling and logging configuration

**`llm_interface.py` - LLM Integration Layer**

- llama-cpp-python integration and model loading
- GGUF model management and validation
- Token streaming and response generation with interruption support
- Inference parameter management (temperature, top-p, context size)
- Error handling, retry logic, and thermal monitoring
- Memory management and model lifecycle

**`vector_store.py` - Vector Database Operations**

- ChromaDB initialization and connection management
- Document embedding generation and storage with dual-hash system
- Similarity search and retrieval operations
- Metadata management (title, source_uri, source_hash, content_hash, timestamps)
- Collection management and database integrity checks
- Backup and restore functionality

**`content_manager.py` - Content Processing Pipeline**

- Document ingestion from files, URLs, and HTML sources
- Content preprocessing, normalization, and chunking (512 tokens, 50 overlap)
- Dual-hash calculation: source_hash (URI + metadata + content), content_hash (content only)
- Import/update/delete operations with progress tracking
- Deduplication logic and import summary reporting
- Resumable import operations and batch processing

**`web_interface.py` - Web UI and API Layer**

- FastAPI route definitions for web UI and API endpoints
- User query handling and streaming response management
- Administrative endpoints (health, reset, content management)
- Request validation and error handling
- Static file serving and template rendering
- CORS and security header management

**`cli.py` - Command Line Interface**

- API client for communicating with FastAPI backend
- User-friendly command structure for system operations
- Health checks, content management, and system reset commands
- Configuration validation and environment checking
- Progress reporting and interactive feedback
- Error reporting with actionable guidance

### Configuration Management

#### Environment Variables

- `CONFIG_PATH`: Configuration file path (default: `/etc/local-rag/config.yaml`)
- `DATA_DIR`: Data directory path (default: `/var/lib/local-rag`)
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `LLM_MODEL_PATH`: Path to GGUF model file
- `MAX_RAM_MB`: Maximum RAM usage in MB (default: 6144 for Pi5)
- `API_HOST`: FastAPI bind address (default: `127.0.0.1`)
- `API_PORT`: FastAPI port (default: `8080`)

#### Configuration File Structure

```yaml
llm:
  model_path: "/var/lib/local-rag/models/deepseek-r1-distill-qwen-1.5b.Q4_K_M.gguf"
  context_size: 2048
  threads: 4
  max_tokens: 512
  temperature: 0.7
  top_p: 0.9

vector_db:
  persist_directory: "/var/lib/local-rag/chromadb"
  collection_name: "documents"
  chunk_size: 512
  chunk_overlap: 50

api:
  host: "127.0.0.1"
  port: 8080
  cors_origins: ["http://localhost:8080"]

logging:
  level: "INFO"
  file: "/var/log/local-rag/app.log"
  max_size: "10MB"
  backup_count: 5
  format: "json"

resources:
  max_ram_mb: 6144
  max_disk_gb: 32
  thermal_limit_celsius: 80
```

### Data Flow Architecture

#### Content Ingestion Workflow

1. **Input Processing**: Accept files/URLs via CLI or API
2. **Content Extraction**: Extract text from various formats (txt, md, html)
3. **Normalization**: Clean whitespace, normalize encoding (UTF-8)
4. **Metadata Generation**: Extract title, calculate dual hashes, timestamp
5. **Chunking**: Split content into 512-token chunks with 50-token overlap
6. **Embedding**: Generate vectors using ChromaDB DefaultEmbeddingFunction
7. **Storage**: Store chunks and metadata in ChromaDB with integrity checks
8. **Reporting**: Generate import summary with success/failure counts

#### Query Processing Workflow

1. **Query Reception**: Receive user query via web interface
2. **Query Embedding**: Generate embedding for similarity search
3. **Retrieval**: Perform ChromaDB similarity search with ranking
4. **Context Assembly**: Combine relevant chunks with source attribution
5. **LLM Processing**: Send context + query to llama-cpp-python
6. **Response Streaming**: Stream tokens to user interface in real-time
7. **Completion**: Finalize response with metadata and source citations

### Error Handling Strategy

#### LLM Error Handling

- Retry failed inference up to 3 times with exponential backoff
- Log detailed error information for debugging
- Return user-friendly error messages
- Graceful degradation if model unavailable
- Thermal throttling with user notification

#### Vector Database Error Handling

- Validate ChromaDB connection on startup
- Handle corruption with graceful fallback and repair
- Provide clear error messages for storage issues
- Automatic backup before risky operations
- Rollback capability for failed transactions

#### Content Import Error Handling

- Continue processing other files if one fails
- Log failed imports with specific error details and file paths
- Provide resumable import capability with checkpointing
- Report comprehensive import summary with counts
- Validate content before processing

### Security and Access Control

#### Input Validation

- Sanitize all user inputs and file paths
- Validate file types and sizes before processing
- URL validation and domain filtering options
- SQL injection prevention for metadata queries
- XSS protection for web interface

#### Network Security

- Bind to localhost by default for single-user security
- Configurable CORS origins for web interface
- No external network access required after setup
- Optional authentication hooks for future enhancement
- Rate limiting for API endpoints

### Risk Assessment and Mitigation

#### High Priority Risks

##### Resource Exhaustion on Pi5

- **Risk**: Limited RAM/CPU on Pi5 could cause system instability or poor performance
- **Impact**: High - System unusable or unreliable
- **Mitigation**:
  - Implement configurable resource limits via environment variables
  - Add memory monitoring with graceful degradation
  - Use streaming responses to minimize memory peaks
  - Choose optimized model sizes (1-3B parameters max)
  - Implement resource usage logging and alerts

##### Model Performance and Quality

- **Risk**: Small LLMs may provide poor response quality or hallucinate frequently
- **Impact**: High - Poor user experience, unreliable answers
- **Mitigation**:
  - Use retrieval-augmented generation to ground responses
  - Implement prompt engineering to reduce hallucination
  - Choose well-reviewed models (DeepSeek R1, Llama variants)
  - Add response quality logging for continuous improvement
  - Provide clear disclaimers about limitations

##### Thermal Management

- **Risk**: Continuous LLM inference could cause thermal throttling on Pi5
- **Impact**: Medium - Reduced performance, potential hardware damage
- **Mitigation**:
  - Monitor CPU temperature via system APIs
  - Implement thermal throttling in application layer
  - Use efficient inference parameters (lower thread count if needed)
  - Recommend proper cooling solutions in documentation
  - Add temperature monitoring to health checks

##### Data Integrity and Corruption

- **Risk**: Power loss or system crashes could corrupt ChromaDB or model files
- **Impact**: High - Data loss, system unusable
- **Mitigation**:
  - Use ChromaDB's built-in durability features
  - Implement atomic operations for critical data updates
  - Add database integrity checks on startup
  - Provide backup/restore functionality via CLI
  - Use journaling filesystem recommendations

##### Cross-Architecture Compatibility

- **Risk**: APT packages or dependencies may not work consistently across ARM64/AMD64
- **Impact**: Medium - Deployment failures, user frustration
- **Mitigation**:
  - Build and test packages on both architectures
  - Use CI/CD with multi-arch build environments
  - Pin dependency versions for consistency
  - Provide architecture-specific documentation
  - Test on real hardware, not just emulation

#### Medium Priority Risks

##### Package Installation Complexity

- **Risk**: APT package dependencies or systemd integration may fail
- **Impact**: Medium - Installation difficulties, user support burden
- **Mitigation**:
  - Thoroughly test installation on clean systems
  - Provide comprehensive pre-installation checks
  - Include detailed troubleshooting documentation
  - Use standard Debian packaging practices
  - Implement rollback capability for failed installs

##### Content Import Failures

- **Risk**: Large imports may fail mid-process, leaving inconsistent state
- **Impact**: Medium - Data loss, user frustration
- **Mitigation**:
  - Implement resumable import operations
  - Use transaction-like semantics for batch operations
  - Provide detailed import progress and error reporting
  - Add import validation and integrity checks
  - Store import state for recovery

##### Network Connectivity Issues

- **Risk**: URL-based content ingestion may fail due to network issues
- **Impact**: Low-Medium - Some content sources unavailable
- **Mitigation**:
  - Implement retry logic with exponential backoff
  - Provide clear error messages for network failures
  - Add timeout configurations for network operations
  - Support offline content preparation
  - Cache successful downloads when possible

## Architecture Decision Records (ADRs)

### ADR-001: Vector Database Selection - ChromaDB vs Qdrant

**Date**: 2025-10-12 | **Status**: Accepted

**Context**: The system requires a vector database to store and search document embeddings for the RAG pipeline. Two main options were considered: ChromaDB and Qdrant.

**Decision**: Use ChromaDB as the vector database for v1.

**Rationale**:

- **Resource Efficiency**: Embedded mode runs as Python library (~100-200MB vs Qdrant's 500MB+ overhead)
- **Simplicity**: Single-process deployment, no separate server to manage
- **Pi5 Optimization**: Better suited for resource-constrained single-board computers
- **Storage**: SQLite backend provides reliable, file-based persistence
- **Proven**: Successfully used in the reference implementation
- **Dependencies**: Fewer external dependencies, simpler setup

**Consequences**: Simpler deployment and maintenance, lower resource usage on Pi5, single point of failure (embedded in application), migration path available if scaling needs change.

### ADR-002: LLM Execution Strategy - CPU vs NPU

**Date**: 2025-10-12 | **Status**: Accepted

**Context**: The system needs to run LLM inference locally. Options considered include CPU-only execution, NPU acceleration (Hailo-10H), and hybrid approaches.

**Decision**: Use CPU-only execution via llama-cpp-python for v1, with NPU support planned for future milestones.

**Rationale**:

- **Simplicity**: Well-established toolchain with llama.cpp and Python bindings
- **Compatibility**: Works on both Pi5 and AMD64 without hardware dependencies
- **Ecosystem**: Large community, extensive model support, good documentation
- **Development Speed**: Faster iteration without hardware-specific complications

**Consequences**: Longer inference times on Pi5 (acceptable for v1 use case), higher power consumption during inference, simpler development and testing workflow, clear upgrade path for NPU integration in future milestones.

### ADR-003: Deployment Architecture - Embedded vs Service-Based

**Date**: 2025-10-12 | **Status**: Accepted

**Context**: The system architecture needs to balance ease of deployment, resource efficiency, and maintainability. Considered approaches include Docker containers, separate services (e.g., external Ollama), and embedded components.

**Decision**: Use a single Python process with embedded LLM and vector database, deployed via APT package with systemd service management.

**Rationale**:

- **Deployment Simplicity**: Single APT package installation with `sudo apt install ./local-rag.deb`
- **Resource Efficiency**: No inter-process communication overhead, shared memory space
- **Reliability**: Fewer points of failure, simpler dependency management
- **User Experience**: One command installation, standard systemd service management
- **Cross-platform**: Same architecture works on Pi5 and AMD64

**Consequences**: Easier user installation and maintenance, slightly less modular than service-based approach, all components share same process lifecycle, future modularization possible if needed.

### ADR-004: LLM Integration - Ollama vs llama-cpp-python

**Date**: 2025-10-12 | **Status**: Accepted

**Context**: The system needs to integrate with LLM inference. Two primary options were considered: using Ollama as an external service or embedding llama-cpp-python directly in the application.

**Decision**: Use llama-cpp-python directly embedded in the Python application.

**Rationale**:

- **Deployment Simplicity**: No external service dependency, single process deployment
- **Resource Efficiency**: No network overhead, direct memory access, shared process space
- **Developer Experience**: Native Python API, familiar patterns, good documentation
- **Cross-platform**: Pre-built wheels for both ARM64 (Pi5) and AMD64
- **Control**: Fine-grained control over model loading, inference parameters, and memory management

**Consequences**: Simpler deployment and user experience, better resource utilization on Pi5, more complex model management (no Ollama's model download features), direct dependency on llama-cpp-python stability.

## CI/CD and Automation Strategy

### Pipeline Architecture

The Local RAG system uses GitHub Actions for comprehensive CI/CD automation, focusing on APT package builds rather than Docker containers, with multi-architecture support for ARM64 (Pi5) and AMD64 systems.

#### Pipeline Stages

1. **Code Quality & Security** (Parallel execution)
2. **Testing** (Unit + Integration + System)
3. **Build Validation** (APT Package Generation)
4. **Release Management** (Automated Deployment)

#### Trigger Events

- **Pull Requests**: Full validation pipeline with quality gates
- **Main Branch Push**: Build + Test + Package creation
- **Release Tags**: Full deployment pipeline with publication
- **Manual Dispatch**: On-demand builds with architecture selection

### GitHub Actions Workflows

#### Pull Request Validation (`pr-validation.yml`)

**Triggers**: All pull requests to main branch, excluding documentation-only changes

**Matrix Strategy**: Python 3.11 on ubuntu-latest (AMD64) for PR validation

**Job Definitions**:

- **Code Quality Job**:
  - Linting (flake8), formatting (black), import sorting (isort)
  - Type checking (mypy), documentation validation (Google style)
- **Security Job**:
  - Security scanning (bandit), dependency vulnerability check (safety)
  - License compliance (pip-licenses), static analysis (CodeQL)
- **Testing Job**:
  - Unit tests (pytest with coverage), integration tests (mock dependencies)
  - API tests (FastAPI TestClient), configuration validation
- **Build Validation Job**:
  - Python compilation validation, test APT package build
  - Dependency resolution check, systemd service file validation

#### Automated Package Builds (`build-packages.yml`)

**Triggers**: Main branch pushes, release publications, manual dispatch

**Build Matrix**:

- ARM64: Cross-compilation on ubuntu-latest with emulation
- AMD64: Native compilation on ubuntu-latest

**Build Process**:

1. **Environment Setup**: Ubuntu 22.04, Python 3.11, cross-compilation tools
2. **Source Preparation**: Git checkout, version detection, dependency installation
3. **APT Package Build**: Source package creation, binary package compilation
4. **Quality Assurance**: Package installation test, service validation, smoke tests
5. **Artifact Management**: Upload to GitHub Actions (90-day retention for branches, permanent for releases)

#### Release Management (`release.yml`)

**Process**:

1. **Package Publication**: Download artifacts, GPG signing, GitHub release upload
2. **Repository Management**: Update custom APT repository index
3. **Documentation Deployment**: API docs (Sphinx), user docs (MkDocs), GitHub Pages
4. **Notification**: Automated release notifications and changelog generation

### APT Package Build Process

#### Package Specifications

**Debian Control File**:

- Source: local-rag
- Architecture: any (ARM64/AMD64 support)
- Dependencies: Python 3.11, systemd, managed Python dependencies
- Maintainer: Local RAG Team

**Installation Scripts**:

- **Post-Installation**: User creation, directory setup, permission configuration
- **Service Management**: systemd service enable/start, dependency installation
- **Configuration**: Default config file placement, environment setup

**Service Configuration**: systemd unit file with proper user/group isolation, restart policies, environment management

#### Cross-Architecture Support

- **ARM64 on AMD64**: QEMU user emulation for cross-compilation
- **Build Optimization**: ccache for compilation, pip cache for packages, parallel builds
- **Validation**: Package testing in target architecture emulated environments

### Testing Automation

#### Test Categories

- **Unit Tests**: pytest with 80% coverage minimum, <2 minutes execution
- **Integration Tests**: Component interaction with Docker containers, <5 minutes
- **System Tests**: Full workflow validation with APT packages, <10 minutes
- **Performance Tests**: pytest-benchmark with memory/response time thresholds

#### Test Execution Strategy

- **Parallel Execution**: Test categories in parallel jobs
- **Test Data Management**: Shared document corpus, deterministic scenarios
- **Failure Handling**: Immediate PR status updates, artifact collection, retry logic

### Quality Gates and Automation

#### Pre-Merge Requirements (Blocking)

1. All tests pass with coverage threshold (80% minimum)
2. Security scan shows no high/critical vulnerabilities
3. Package build succeeds for target architectures
4. Code quality meets linting and formatting standards
5. Documentation builds without errors
6. Manual code review by maintainer

#### Automated Code Maintenance

- **Dependency Management**: Dependabot updates, security patches, version pinning
- **Code Quality**: Pre-commit hooks (black/isort), automated formatting
- **Documentation**: Docstring validation, type hint enforcement

### Repository and Distribution

#### Custom APT Repository

**Structure**:

```text
apt-repo/
├── dists/stable/            # Release distributions
├── pool/main/l/local-rag/   # Package files (.deb)
└── gpg/public.key           # GPG signing key
```

**Management**:

- **Automated Updates**: Package uploads trigger index regeneration
- **GPG Signing**: All packages and metadata cryptographically signed
- **Multi-Architecture**: Separate binary indexes for ARM64/AMD64
- **CDN Distribution**: GitHub Pages for global package distribution

#### Release Channels

- **Stable Channel**: Tagged releases (v1.0.0), full testing, long-term support
- **Testing Channel**: Main branch builds, automated testing only, early access

### Development Workflow Integration

#### Local Development

- **Pre-commit Hooks**: Automated quality checks before commit
- **Local Testing Scripts**:
  - `scripts/test-quick.sh`: Rapid feedback for development
  - `scripts/test-ci-local.sh`: Full CI simulation before push

#### Contribution Process

1. Fork and branch (standard GitHub flow)
2. Local testing with quick validation scripts
3. Full validation before push
4. Pull request with automated CI validation
5. Manual review and automated merge

#### Release Process

1. Version tagging with semantic versioning (v1.0.0)
2. Automated multi-architecture package building
3. Full validation in clean environments
4. Repository update and documentation publishing
5. Release announcements and changelog generation

### Monitoring and Performance

#### Build Monitoring

- **GitHub Status Checks**: PR blocking for failed builds
- **Performance Tracking**: Build duration, cache hit rates, resource usage
- **Success Rate**: Historical build success rate monitoring

#### Security and Compliance

- **Vulnerability Scanning**: Daily dependency scans
- **Security Advisories**: Automated tracking and response
- **License Compliance**: Automated license policy validation

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

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

**Structure Decision**: Single project structure chosen because the system is designed as a monolithic Python application with embedded services (LLM, vector DB, web UI) running in a single service managed by systemd (may use multiple processes or threads). This aligns with the requirement for easy deployment and resource efficiency on constrained hardware like Raspberry Pi 5.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation                  | Why Needed         | Simpler Alternative Rejected Because |
| -------------------------- | ------------------ | ------------------------------------ |
| [e.g., 4th project]        | [current need]     | [why 3 projects insufficient]        |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient]  |
