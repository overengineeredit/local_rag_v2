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
- Systemd service lifecycle management and graceful shutdown
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
- Document embedding generation and storage with dual hash system
- Similarity search and retrieval operations
- Metadata management (title, source_uri, source_hash, content_hash, timestamps)
- Collection management and database integrity checks
- Backup and restore functionality

**`content_manager.py` - Content Processing Pipeline**

- Document ingestion from files, URLs, and HTML sources
- Content preprocessing, normalization, and chunking (512 tokens, 50 overlap)
- Dual hash calculation: source_hash (URI + metadata + content), content_hash (content only)
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
- `API_PORT`: FastAPI port (default: `8080`, configurable to avoid conflicts with MeshtasticD, development servers, web proxies)

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
  port: 8080                    # Configurable: use 8081, 8082, or 9080 to avoid conflicts
  cors_origins: ["http://localhost:8080"]

logging:
  level: "INFO"
  file: "/var/log/local-rag/app.log"
  stdout: true
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
4. **Metadata Generation**: Extract title, calculate dual hash system, timestamp
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
- No authentication required for v1 (single-user device model)
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
  - Choose well-reviewed models (default: deepseek-r1-distill-qwen-1.5b.Q4_K_M.gguf)
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

#### Test Categories and Framework

##### Unit Tests (pytest)

- **Core Functionality**:
  - Content ingestion (file, HTML, URL parsing with various input formats)
  - Deduplication (hash-based duplicate detection across content types)
  - Metadata extraction (title, source, date extraction from documents)
  - Vector operations (ChromaDB CRUD operations and embedding generation)
  - LLM interface (llama-cpp-python integration, token streaming, error handling)
  - Configuration (YAML/TOML parsing, environment variable override)

- **Service Layer**:
  - Content Manager (document processing, chunking, storage)
  - Vector Store (ChromaDB operations, query functionality)
  - LLM Interface (model loading, inference, response streaming)
  - Web Interface (FastAPI endpoint functionality)
  - CLI Interface (command parsing, execution, output formatting)

- **Configuration**: pytest with coverage (80% minimum, 90% preferred), pytest-xdist for parallel execution, comprehensive mocking for external dependencies

##### Integration Tests

- **Component Integration**:
  - API-CLI integration (CLI commands calling API endpoints)
  - LLM-Vector integration (embedding generation and storage)
  - Web-Service integration (FastAPI routes with service layer)
  - Configuration integration (end-to-end configuration loading)

- **Service Integration**:
  - ChromaDB integration (database operations with real ChromaDB instance)
  - Model integration (LLM loading and inference, mocked for CI)
  - File system integration (content loading from various sources)
  - Health check integration (component health monitoring)

- **Error Scenario Testing**:
  - Network failures (timeouts, connection errors)
  - Resource limits (disk full, memory limits, large files)
  - Corrupted data (malformed content and configurations)
  - Service failures (graceful degradation and error reporting)

##### System Tests

- **End-to-End Workflows**:
  - Content loading (import folder → verify storage → query content)
  - Query processing (load content → ask question → verify relevant response)
  - Content management (update content → verify changes reflected)
  - Service lifecycle (start → health check → stop → restart)

- **Performance Testing**:
  - Load testing (import 100+ documents, measure time and memory)
  - Query performance (response time under various content loads)
  - Concurrent usage (multiple simultaneous queries and imports)
  - Resource usage (memory, CPU, disk usage under normal operation)

- **APT Package Testing**:
  - Installation (package installation on clean systems)
  - Service management (systemd service start/stop/restart)
  - Configuration (default configuration and overrides)
  - Upgrade/removal (package upgrade and clean removal)

#### BDD Tests (pytest-bdd)

**Content Loading Scenarios**:

```gherkin
Scenario: Load folder of text files
  Given a folder containing text files
  When I run the content import command
  Then all files should be indexed in ChromaDB
  And metadata should be extracted correctly

Scenario: Handle duplicate content
  Given existing content in the system
  When I import the same content again
  Then duplicates should be detected and skipped
  And the total count should remain unchanged
```

**Query Processing Scenarios**:

```gherkin
Scenario: User asks question about loaded content
  Given content has been loaded into the system
  When I submit a query about the content
  Then I should receive a relevant response
  And the response should include source citations

Scenario: Handle LLM service failure
  Given the LLM service is unavailable
  When I submit a query
  Then I should receive an appropriate error message
  And the system should remain stable
```

**Content Management Scenarios**:

```gherkin
Scenario: Update existing content
  Given content exists in the system
  When I update the source content
  And re-import the content
  Then the updated version should be indexed
  And old versions should be removed

Scenario: Resume interrupted import
  Given an import process was interrupted
  When I restart the import
  Then the process should resume from the last checkpoint
  And all content should be imported successfully
```

#### Test Data Management

**Synthetic Test Data**:

- Text files (20+ documents, various sizes 1KB-1MB)
- HTML files (different structures, encoding, malformed HTML)
- URL lists (working links, broken links, redirect scenarios)
- Large files (edge cases for memory and processing limits)
- Unicode content (international characters, special symbols)

**Real-World Test Data**:

- Technical documentation samples
- News articles, blog posts, academic papers
- Mixed content (text, HTML, markdown files)
- Duplicate scenarios (identical content in different formats)

#### Test Execution Strategy

- **Parallel Execution**: Test categories in parallel jobs, pytest-xdist within categories
- **Test Data Management**: Shared document corpus, deterministic scenarios, version-controlled test data
- **Failure Handling**: Immediate PR status updates, artifact collection, retry logic for flaky tests
- **Performance Benchmarks**:
  - Import speed: 10 documents/minute minimum for text files
  - Query response: <5 seconds for typical queries
  - Memory usage: <2GB total system memory usage
  - Startup time: <30 seconds from service start to ready

#### CI/CD Test Integration

**Pull Request Testing**:

- Fast feedback (essential tests <5 minutes)
- Coverage reporting posted to PR
- Quality gates (tests must pass before merge)
- Parallel execution across multiple jobs

**Test Automation Tools**:

- pytest (primary testing framework)
- pytest-cov (coverage reporting)
- pytest-xdist (parallel test execution)
- pytest-bdd (behavior-driven development tests)
- pytest-mock (enhanced mocking capabilities)
- pytest-benchmark (performance testing)

**Test Environment Management**:

- Clean environments for each test run
- Consistent dependency versions
- Test isolation (no interference or shared state)
- Proper resource cleanup after execution

**Continuous Monitoring**:

- Test performance tracking (execution time trends)
- Flaky test detection and quarantine
- Coverage trends monitoring
- Automated failure analysis and categorization

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

✅ **CONSTITUTION DEFINED**: Local RAG System Constitution v1.0.0 established with 5 core principles:

- **I. Privacy-First Architecture**: ✅ ALIGNED - System designed for local-only processing, no external data transmission
- **II. Resource Efficiency**: ✅ ALIGNED - Pi5 constraints (<6GB RAM) explicitly addressed in technical requirements
- **III. Local-Only Operation**: ✅ ALIGNED - Offline capability and no cloud dependencies are core requirements
- **IV. Single Process Architecture**: ✅ ALIGNED - FastAPI + llama-cpp-python + ChromaDB embedded design
- **V. Testing Excellence**: ✅ ALIGNED - TDD methodology with >85% coverage requirement established

**COMPLIANCE STATUS**: All implementation plans align with constitutional principles. No violations requiring justification.

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

## Deployment Strategy

### Target Environment and Requirements

#### Hardware Requirements

- **Primary Target**: Raspberry Pi 5 (8GB RAM recommended)
- **Secondary Target**: AMD64 systems (desktop/server)
- **Storage**: 64GB+ microSD (Class 10 or better) for Pi5, SSD recommended for AMD64
- **Network**: WiFi or Ethernet (required only for initial setup and model downloads)

#### Resource Requirements

- **RAM**: 6GB minimum, 8GB recommended (1.5B parameter model + ChromaDB + OS overhead)
- **Storage**:
  - 8GB for application components
  - 4GB for default GGUF model files
  - 16GB+ for content storage and vector embeddings
- **CPU**: All available cores utilized for LLM inference via llama-cpp-python
- **Power**: 5V/5A PSU recommended for sustained CPU load during inference
- **Dependencies**: Self-contained deployment with no external dependencies

#### Operating System Support

- **Primary**: Debian 12 (Bookworm) ARM64 for Raspberry Pi 5
- **Secondary**: Ubuntu 22.04 LTS, Debian 12 on AMD64 architectures
- **Package Format**: Debian (.deb) packages for both ARM64 and AMD64

### Installation Process

#### Standard APT Installation

1. **Download Package**: Get architecture-specific `.deb` file

   ```bash
   # For Raspberry Pi 5 (ARM64)
   wget https://github.com/user/repo/releases/latest/download/local-rag_1.0.0_arm64.deb
   
   # For AMD64 systems
   wget https://github.com/user/repo/releases/latest/download/local-rag_1.0.0_amd64.deb
   ```

2. **Install Package**: Single command installation with dependency resolution

   ```bash
   sudo apt install ./local-rag_1.0.0_arm64.deb
   ```

3. **Model Setup**: Download and configure LLM model

   ```bash
   # Download default model (deepseek-r1-distill-qwen-1.5b.Q4_K_M.gguf)
   sudo local-rag download-model deepseek-r1-distill-qwen-1.5b.Q4_K_M.gguf
   
   # Or manually place GGUF files in /var/lib/local-rag/models/
   ```

4. **Configuration**: Edit system configuration if needed

   ```bash
   sudo nano /etc/local-rag/config.yaml
   # Change port if 8080 conflicts with other services (MeshtasticD, development servers, web proxies)
   # Example: port: 8081
   ```

5. **Service Management**: Enable and start the service

   ```bash
   sudo systemctl enable --now local-rag
   ```

6. **Verification**: Confirm system health

   ```bash
   # API health check
   curl http://localhost:8080/health
   
   # CLI status check  
   local-rag status
   ```

#### Repository-Based Installation

For easier updates and management:

```bash
# Add GPG key for package verification
curl -fsSL https://username.github.io/local-rag-apt/gpg | sudo gpg --dearmor -o /usr/share/keyrings/local-rag.gpg

# Add custom APT repository
echo "deb [signed-by=/usr/share/keyrings/local-rag.gpg] https://username.github.io/local-rag-apt stable main" | sudo tee /etc/apt/sources.list.d/local-rag.list

# Install via APT
sudo apt update
sudo apt install local-rag
```

### File System Layout

#### Application Components

```text
/usr/local/bin/local-rag              # Main executable
/usr/lib/python3.11/site-packages/guide/  # Application code
/etc/local-rag/config.yaml            # System configuration
/etc/systemd/system/local-rag.service # systemd service definition
```

#### Data and Storage

```text
/var/lib/local-rag/                   # Application data directory
├── chromadb/                         # Vector database files
├── content/                          # Source content cache
├── models/                           # LLM model files
└── backups/                          # System backups
```

#### Logging and Monitoring

```text
/var/log/local-rag/                   # Application logs (optional)
systemd journal                       # Primary logging via journalctl
```

### Service Management

#### systemd Service Configuration

The system runs as a dedicated systemd service with proper isolation:

```ini
[Unit]
Description=Local RAG System
After=network.target
Wants=network.target

[Service]
Type=exec
User=local-rag
Group=local-rag
ExecStart=/usr/local/bin/local-rag serve
WorkingDirectory=/var/lib/local-rag
Environment=LOCAL_RAG_CONFIG=/etc/local-rag/config.yaml
Restart=always
RestartSec=10
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

#### Service Operations

```bash
# Start service
sudo systemctl start local-rag

# Stop service  
sudo systemctl stop local-rag

# Enable auto-start on boot
sudo systemctl enable local-rag

# Check service status
sudo systemctl status local-rag

# View service logs
sudo journalctl -u local-rag -f

# Reload configuration without restart
sudo systemctl reload local-rag
```

### Security Considerations

#### Access Control and Network Security

- **Local Access Only**: Web interface binds to localhost:8080 by default
- **No External Dependencies**: No internet access required after initial setup
- **Firewall Friendly**: No inbound ports required, outbound only for initial model downloads

#### System Security

- **Dedicated User**: Service runs as non-root `local-rag` user
- **File Permissions**: Standard Unix permissions protect data files
- **Process Isolation**: systemd provides process and resource isolation
- **No Authentication**: Single-user device model, secured by physical access

#### Data Security

- **Local Storage**: All data remains on device in `/var/lib/local-rag/`
- **No Cloud Dependencies**: Complete data sovereignty
- **Backup Control**: User controls all backup and recovery processes

### Monitoring and Maintenance

#### Health Monitoring

```bash
# API health endpoint
curl http://localhost:8080/health

# CLI health check
local-rag status

# Detailed system information
local-rag info --verbose
```

#### Log Management

```bash
# View real-time logs
sudo journalctl -u local-rag -f

# View recent logs with context
sudo journalctl -u local-rag --since "1 hour ago"

# Export logs for debugging
sudo journalctl -u local-rag --since yesterday > local-rag.log
```

#### Backup and Recovery

```bash
# Create system backup
local-rag backup --output /path/to/backup.tar.gz

# Restore from backup
local-rag restore --input /path/to/backup.tar.gz

# Export content only
local-rag export-content --format json --output content-backup.json
```

#### Maintenance Operations

```bash
# Update model files
local-rag update-model --model deepseek-r1-distill-qwen-1.5b.Q4_K_M.gguf

# Rebuild vector database
local-rag rebuild-vectors --confirm

# Clean temporary files
local-rag cleanup --temp-files

# Vacuum database
local-rag vacuum --chromadb
```

### Package Structure and Dependencies

#### APT Package Contents

```text
local-rag_1.0.0-1_arm64.deb
├── DEBIAN/
│   ├── control                    # Package metadata and dependencies
│   ├── postinst                   # Post-installation script
│   ├── prerm                      # Pre-removal script
│   └── postrm                     # Post-removal script
├── usr/local/bin/local-rag        # Main executable
├── etc/local-rag/config.yaml      # Default configuration
├── etc/systemd/system/local-rag.service  # Service definition
└── var/lib/local-rag/             # Data directory structure
```

#### Package Dependencies

Automatically resolved via APT:

- `python3.11` - Python runtime
- `python3-pip` - Package management
- `systemd` - Service management
- `curl` - Health check utilities

#### Installation Scripts

**Post-Installation (`postinst`)**:

```bash
#!/bin/bash
# Create dedicated user and group
useradd --system --home /var/lib/local-rag --shell /bin/false local-rag

# Set directory permissions
chown -R local-rag:local-rag /var/lib/local-rag
chmod 755 /var/lib/local-rag

# Install Python dependencies
pip3 install --system -r /usr/share/local-rag/requirements.txt

# Enable service (but don't start automatically)
systemctl daemon-reload
systemctl enable local-rag
```

**Pre-Removal (`prerm`)**:

```bash
#!/bin/bash
# Stop service before removal
systemctl stop local-rag
systemctl disable local-rag
```

### Troubleshooting and Support

#### Common Installation Issues

1. **Insufficient Storage**: Ensure 32GB+ available space
2. **Model Download Failures**: Check internet connectivity and retry
3. **Service Start Failures**: Verify configuration file syntax
4. **Port Conflicts**: Default port 8080 may conflict with MeshtasticD, development servers, or web proxies
   - Edit `/etc/local-rag/config.yaml` and change `api.port` to 8081, 8082, or 9080
   - Restart service: `sudo systemctl restart local-rag`
   - Update CORS origins to match: `cors_origins: ["http://localhost:8081"]`

#### Performance Optimization

1. **Memory Management**: Adjust `max_ram_mb` in config for system constraints
2. **CPU Optimization**: Configure `threads` setting for available cores  
3. **Storage Performance**: Use SSD instead of microSD for better I/O
4. **Model Selection**: Choose smaller models for resource-constrained systems

#### Recovery Procedures

1. **Service Recovery**: `sudo systemctl restart local-rag`
2. **Configuration Reset**: Restore default config from `/usr/share/local-rag/config.yaml.example`
3. **Database Corruption**: Use `local-rag rebuild-vectors` to recreate embeddings
4. **Complete Reset**: Purge package and reinstall with `apt purge local-rag`

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation                  | Why Needed         | Simpler Alternative Rejected Because |
| -------------------------- | ------------------ | ------------------------------------ |
| Multi-architecture CI/CD (ARM64 + AMD64) | Pi5 is ARM64, desktops are AMD64 - different binary architectures require separate compilation | Single-architecture insufficient: Pi5 users cannot run AMD64 binaries, desktop users cannot run ARM64 binaries. Cross-compilation complexity is unavoidable for hardware compatibility. |
