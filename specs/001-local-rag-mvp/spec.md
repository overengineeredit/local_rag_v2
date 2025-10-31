# Feature Specification: Local RAG System

**Feature Branch**: `001-local-rag-mvp`  
**Created**: 2025-10-28  
**Status**: Draft  
**Input**: User description: "Local RAG system with embedded LLM and vector store"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Document Query RAG (Priority: P1)

A user can upload text documents to the system and ask questions about their content, receiving relevant answers generated using local LLM with retrieved context.

**Why this priority**: This is the core RAG functionality that delivers the primary value proposition - private, local knowledge querying.

**Independent Test**: Can be fully tested by uploading a text file, asking a question about its content, and receiving a relevant generated response that demonstrates retrieval-augmented generation.

**Acceptance Scenarios**:

1. **Given** system is running and healthy, **When** user uploads a text file via web UI, **Then** file is processed and stored in vector database with success confirmation
2. **Given** documents are loaded in the system, **When** user submits a question via web interface, **Then** system returns a streaming response based on retrieved relevant content
3. **Given** user asks a question, **When** system processes the query, **Then** response includes context from uploaded documents and shows source attribution

---

### User Story 2 - System Installation and Management (Priority: P1)

A user can install the system via APT package manager and manage it as a systemd service on both Raspberry Pi 5 (ARM64) and AMD64 systems.

**Why this priority**: Easy installation and systemd service management is essential for user adoption and operational reliability.

**Independent Test**: Can be fully tested by installing the .deb package on a clean system, starting the service, and verifying it's accessible at localhost:8080.

**Acceptance Scenarios**:

1. **Given** a clean Pi5 or AMD64 Debian-based system (Ubuntu, Debian, Raspberry Pi OS), **When** user installs the .deb package, **Then** all dependencies are resolved and service is ready to start
2. **Given** package is installed, **When** user runs `systemctl start local-rag`, **Then** service starts successfully and is accessible at <http://localhost:8080>
3. **Given** service is running, **When** user runs health check, **Then** system reports all components (LLM, vector DB, API) as healthy

---

### User Story 3 - Batch Content Import with Change Detection (Priority: P2)

A user can import content from multiple sources (files, URLs, HTML) in batch operations with automatic change detection, deduplication, and progress tracking.

**Why this priority**: Efficient content management with update detection is crucial for building useful knowledge bases, but not needed for basic MVP functionality.

**Independent Test**: Can be fully tested by importing a folder of documents, modifying some files, re-importing, and verifying only changed content is re-processed with accurate change detection.

**Acceptance Scenarios**:

1. **Given** a folder containing text files, html files, and URLs, **When** user runs batch import command, **Then** all content is processed with progress reporting and both change detection and cross-source deduplication working correctly
2. **Given** content has been imported previously, **When** source files are modified and re-import runs, **Then** only changed content is re-processed based on source metadata comparison (mtime, etag)
3. **Given** identical content exists from different sources, **When** import runs, **Then** content_hash deduplication prevents duplicate embeddings while maintaining separate source tracking
4. **Given** user wants to check for updates, **When** update check runs, **Then** system identifies outdated sources without re-importing and provides detailed change information

---

### User Story 4 - Content Management Operations (Priority: P3)

A user can manage their knowledge base by viewing, updating, and deleting content through CLI commands with full API integration.

**Why this priority**: Advanced content management improves user experience but is not essential for core RAG functionality.

**Independent Test**: Can be fully tested by adding content, listing it, updating it, and soft-deleting it through CLI operations.

**Acceptance Scenarios**:

1. **Given** content exists in the system, **When** user lists content via CLI, **Then** all documents are shown with metadata (title, source, create date, updated date, status)
2. **Given** user wants to remove content, **When** user runs delete command, **Then** content is soft-deleted and excluded from future queries
3. **Given** system needs reset, **When** user runs reset command, **Then** all content and embeddings are cleared with confirmation

---

### Edge Cases

- What happens when the system runs out of disk space during document import?
- How does the system handle corrupted or inaccessible model files on startup?
- What occurs when the system loses power during document processing or query generation?
- How does the system behave when asked about content that was soft-deleted?
- What happens when the LLM model fails to load due to insufficient memory?
- How does the system handle very large documents that exceed context windows?
- What occurs when ChromaDB database becomes corrupted or inaccessible?
- How does the system respond to malformed or malicious content during import?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST perform local inference only without internet dependency for generation
- **FR-002**: System MUST stream response tokens to UI for immediate responsiveness
- **FR-003**: System MUST accept textual prompts from users via web UI (FastAPI backend)
- **FR-004**: System MUST use llama-cpp-python for local LLM inference with GGUF models
- **FR-005**: System MUST ingest plain text, HTML, and URLs (batch, file, or folder) into ChromaDB
- **FR-006**: System MUST use ChromaDB with embedded SQLite backend for vector storage
- **FR-007**: System MUST store metadata including title, source URI, timestamps for content management
- **FR-008**: System MUST implement dual hash system: source_hash (SHA-256 of URI + metadata + content, e.g., `https://example.com/doc.txt` + `last-modified:2025-10-30` + content) for change detection and content_hash (SHA-256 of normalized content only) for cross-source deduplication. Content normalization algorithm: (1) Convert encoding to UTF-8, (2) Normalize line endings to \n, (3) Strip leading/trailing whitespace from each line, (4) Remove empty lines at start/end of document, (5) Ensure single final newline. Example: same article from RSS feed and direct URL will have different source_hash but identical content_hash after normalization.
- **FR-009**: System MUST detect content updates at source and provide update mechanisms without requiring full re-import
- **FR-010**: System MUST support content updates by comparing source metadata (mtime, etag) and re-importing only changed content
- **FR-011**: System MUST provide soft delete functionality for content management
- **FR-012**: System MUST package as .deb for apt-based installation on ARM64 and AMD64
- **FR-013**: System MUST provide systemd service for starting/stopping the application
- **FR-014**: System MUST store all configuration in `/etc/local-rag/config.yaml`
- **FR-015**: System MUST store models in `/var/lib/local-rag/models/`
- **FR-016**: System MUST provide health check capabilities via API endpoint (`/health`) returning JSON status of all components (LLM model, ChromaDB, disk space, memory usage) and corresponding CLI command (`local-rag status`) with human-readable output and detailed diagnostics option (`--verbose`)
- **FR-017**: System MUST implement CLI commands for content operations communicating via API
- **FR-018**: System MUST be battery-friendly with power consumption under 5W during idle operation and under 25W during inference, implementing thermal management to prevent hardware damage
- **FR-019**: System MUST survive ungraceful power loss without corrupting state using: (1) ChromaDB ACID transactions for all write operations, (2) Write-ahead logging (WAL) for configuration changes, (3) Atomic file operations for model downloads with .tmp suffix during transfer, (4) Database integrity validation on startup with automatic repair, (5) Import operation checkpointing every 10 documents for resumability, and (6) Configuration file backup before modifications with automatic rollback on corruption detection
- **FR-020**: System MUST support both ARM64 (Pi5) and AMD64 architectures
- **FR-021**: System MUST implement JSON-formatted logging with configurable levels, disk + stdout output, and rotation. JSON schema MUST include: `timestamp` (ISO 8601), `level` (DEBUG/INFO/WARN/ERROR), `module` (component name), `message` (log content), `request_id` (for API tracing), optional `user_id`, `duration_ms` (for operations), `error_code` (for errors), and `context` (additional metadata). Log retention MUST be 5 files of 10MB each with automatic rotation.

#### Edge Case Requirements

- **FR-022**: System MUST monitor available disk space and halt document import when <5% space remaining, resuming when >10% space available
- **FR-023**: System MUST validate GGUF model file integrity on startup using file size and header validation, providing clear recovery instructions for corrupted files
- **FR-024**: System MUST implement atomic database operations with automatic rollback for incomplete transactions, ensuring no data corruption during power loss
- **FR-025**: System MUST exclude soft-deleted content from all query results and provide "content unavailable" messages when deleted content is referenced
- **FR-026**: System MUST detect insufficient memory for LLM loading and provide clear guidance on memory requirements and model alternatives
- **FR-027**: System MUST chunk documents exceeding context windows using sliding overlap technique, ensuring no content loss for large documents
- **FR-028**: System MUST detect ChromaDB corruption on startup and provide automatic repair procedures with backup restoration capability
- **FR-029**: System MUST validate content during import with file size limits (100MB max), content type validation, and malformed encoding detection
- **FR-030**: System MUST provide configurable API port to avoid conflicts with other services (MeshtasticD, development servers, web proxies)

### Non-Functional Requirements

#### Performance Requirements

- **NFR-001**: Performance - Cold start (first query after system boot) MUST complete first token within 4 minutes (P50), 5 minutes (P95) on Pi5 with standardized baseline conditions: (1) System idle state verified by <5% CPU usage for 60 seconds measured via `/proc/stat`, (2) Single concurrent query with no background imports, (3) 2-3 document context retrieval (512-token chunks), (4) Measurement from query submission to first token via FastAPI response streaming, (5) Test environment: clean Pi5 8GB, 64GB Class 10 microSD, adequate cooling maintaining <70°C, (6) Measured over 20 query samples with median (P50) and 95th percentile (P95) calculation
- **NFR-002**: Performance - Warm queries (subsequent queries after initial model load) MUST complete first token within 90 seconds (P50), 3 minutes (P95) on Pi5 with standardized baseline conditions: (1) Model already loaded in memory verified by successful prior query completion, (2) CPU temperature <70°C measured via `/sys/class/thermal/thermal_zone0/temp`, (3) Single concurrent query with no background processing, (4) Measurement methodology identical to NFR-001, (5) Test with same hardware configuration as NFR-001, (6) Streaming response continues at reading speed (1-5 tokens/second) after first token
- **NFR-003**: Performance - Desktop/AMD64 MUST achieve first token within 5 seconds (P50), 15 seconds (P95) with standardized baseline conditions: (1) Hardware specification: Intel/AMD CPU 4+ cores 2.5GHz+, 16GB+ DDR4 RAM, NVMe SSD with >500MB/s sequential read, (2) CPU temperature <60°C measured via hardware monitoring, (3) Single concurrent query with clean system state, (4) Measurement methodology identical to NFR-001/NFR-002, (5) 30 seconds maximum timeout (P99) with graceful failure, (6) Test environment: Ubuntu 22.04 LTS, no competing processes >5% CPU
- **NFR-004**: Resource Limits - Memory usage MUST stay under 6GB on Pi5, configurable for other systems
- **NFR-005**: Storage Performance - System MUST scale predictably with content (100+ documents, 2K-10K words each) with less than 5% performance degradation per 100 additional documents measured against baseline of 10 documents and linear storage growth. Performance metrics: query response time (first token latency), document ingestion speed, and memory usage during retrieval operations
- **NFR-006**: Thermal Management - System MUST monitor CPU temperature via /sys/class/thermal/thermal_zone*/temp every 30 seconds with 3-sample rolling average (arithmetic mean of last 3 readings), throttle inference threads when average >75°C, and halt processing when average >85°C with user notification. During throttling, temperature monitoring continues at same 30-second intervals to enable timely recovery when temperature drops below 70°C.

#### User Interface Requirements

- **NFR-007**: UI Compatibility - System MUST work on 720p screens using Chrome/Firefox browsers
- **NFR-008**: UI Responsiveness - Web interface MUST remain responsive during LLM inference
- **NFR-009**: Stream Display - Response tokens MUST stream to UI for immediate user feedback

#### System Quality Requirements

- **NFR-011**: Resource Management - System MUST provide configurable RAM/disk usage limits with graceful backoff
- **NFR-012**: Monitoring - System MUST provide health checks via API endpoint and CLI command  
- **NFR-013**: Reliability - System MUST handle component failures gracefully with user-friendly error messages: LLM inference failures (retry 3x with exponential backoff), ChromaDB corruption (attempt repair, fallback to read-only), model loading failures (clear error with path validation), network timeouts during URL import (continue with other sources). Error messages must include specific problem description and actionable recovery steps.
- **NFR-014**: Power Resilience - System MUST survive ungraceful power loss without state corruption
- **NFR-015**: Battery Efficiency - System MUST maintain low idle power draw for battery-powered operation

#### Security and Maintenance Requirements

- **NFR-016**: Security - System MUST validate and sanitize all user inputs and file paths
- **NFR-017**: Access Control - System MUST bind to localhost by default for single-user security
- **NFR-018**: Maintainability - System MUST follow modular design with clear interfaces between components
- **NFR-019**: Cross-Platform - System MUST support both ARM64 (Pi5) and AMD64 architectures consistently

### Key Entities

- **Document**: Represents ingested content with metadata including id, title, source, content_hash, timestamp, chunk_count, and status
- **Chunk**: Vector-embedded piece of document content stored in ChromaDB with similarity search capabilities
- **Query**: User-submitted textual prompt that triggers retrieval and generation workflow
- **Model**: GGUF-format LLM stored locally and loaded via llama-cpp-python (default: deepseek-r1-distill-qwen-1.5b.Q4_K_M.gguf)
- **Configuration**: YAML-based settings for LLM parameters, vector DB settings, API configuration, and logging options

## Success Criteria *(mandatory)*

## Success Criteria and Acceptance *(mandatory)*

### Measurable Outcomes

#### Functional Success Metrics

- **SC-001**: Users can complete system installation via single APT command on clean Pi5/AMD64 Debian-based systems within 5 minutes
- **SC-002**: System handles 100+ documents (2K-10K words each) without performance degradation  
- **SC-003**: System achieves 90% successful completion rate for core workflow measured over 100 query attempts within 24-hour period where success = (document import completes without exceptions + stored in ChromaDB + query returns relevant response + response includes source attribution + completed within performance targets); failure = any step fails or times out
- **SC-004**: Content change detection achieves 100% accuracy for file modifications (mtime) and web content updates (etag/last-modified headers)
- **SC-005**: Update checking completes within 30 seconds for 100+ sources and accurately identifies changed vs unchanged content
- **SC-006**: System recovers gracefully from power loss without data corruption or requiring manual repair

#### Performance Success Metrics

- **SC-007**: Query responses achieve target performance: Pi5 cold start 3-5 minutes, warm queries 1-3 minutes for first token
- **SC-008**: Desktop/AMD64 achieves first token within 5 seconds for 50% of queries, within 15 seconds for 95% of queries, with maximum 30-second timeout
- **SC-009**: Memory usage remains under 6GB on Pi5 systems during typical operation
- **SC-010**: Web UI remains responsive on 720p displays across Chrome and Firefox browsers
- **SC-011**: Health check endpoint responds within 5 seconds and accurately reports component status

#### Reliability Success Metrics

- **SC-012**: System maintains 99%+ uptime during normal operation without manual intervention  
- **SC-013**: Thermal throttling prevents hardware damage on Pi5 during sustained operation
- **SC-014**: Import operations can be resumed after interruption without data loss
- **SC-015**: All components fail gracefully with informative error messages and recovery guidance
- **SC-016**: Edge case handling achieves 100% detection rate for critical scenarios: disk space exhaustion, model corruption, power loss recovery, and memory failures
- **SC-017**: System correctly excludes soft-deleted content from query results with appropriate user feedback
- **SC-018**: ChromaDB corruption is automatically detected and repaired without data loss
