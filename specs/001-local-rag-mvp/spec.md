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

**Why this priority**: Easy installation and service management is essential for user adoption and operational reliability.

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
- **FR-007**: System MUST store metadata including title, source URI, timestamps, and dual hash system for deduplication and change detection
- **FR-008**: System MUST implement dual hash strategy: source_hash (URI + metadata + content) for change detection and content_hash (content only) for cross-source deduplication
- **FR-009**: System MUST detect content updates at source and provide update mechanisms without requiring full re-import
- **FR-010**: System MUST support content updates by comparing source metadata (mtime, etag) and re-importing only changed content
- **FR-011**: System MUST provide soft delete functionality for content management
- **FR-012**: System MUST package as .deb for apt-based installation on ARM64 and AMD64
- **FR-013**: System MUST provide systemd service for starting/stopping the application
- **FR-014**: System MUST store all configuration in `/etc/local-rag/config.yaml`
- **FR-015**: System MUST store models in `/var/lib/local-rag/models/`
- **FR-016**: System MUST provide health check API endpoint (`/health`) and CLI command
- **FR-017**: System MUST implement CLI commands for content operations communicating via API
- **FR-018**: System MUST be battery-friendly with low idle power draw and thermal management to prevent hardware damage
- **FR-019**: System MUST survive ungraceful power loss without corrupting state
- **FR-020**: System MUST support both ARM64 (Pi5) and AMD64 architectures
- **FR-021**: System MUST implement JSON-formatted logging with configurable levels and rotation

### Non-Functional Requirements

#### Performance Requirements

- **NFR-001**: Performance - Cold start (first query) MUST complete first token within 3-5 minutes on Pi5
- **NFR-002**: Performance - Warm queries MUST complete first token within 1-3 minutes on Pi5, reading-speed streaming thereafter
- **NFR-003**: Performance - Desktop/AMD64 MUST achieve first token within 5 seconds (P50), 15 seconds (P95), with 30 seconds maximum timeout (reference comparison)
- **NFR-004**: Resource Limits - Memory usage MUST stay under 6GB on Pi5, configurable for other systems
- **NFR-005**: Storage Performance - System MUST scale predictably with content (100+ documents, 2K-10K words each)
- **NFR-006**: Thermal Management - System MUST monitor CPU temperature via /sys/class/thermal/thermal_zone*/temp, throttle inference threads when >75°C, and halt processing when >85°C with user notification

#### User Interface Requirements

- **NFR-007**: UI Compatibility - System MUST work on 720p screens using Chrome/Firefox browsers
- **NFR-008**: UI Responsiveness - Web interface MUST remain responsive during LLM inference
- **NFR-009**: Stream Display - Response tokens MUST stream to UI for immediate user feedback

#### System Quality Requirements

- **NFR-010**: Logging - System MUST use JSON format with configurable levels, disk + stdout output, with rotation
- **NFR-011**: Resource Management - System MUST provide configurable RAM/disk usage limits with graceful backoff
- **NFR-012**: Monitoring - System MUST provide health checks via API endpoint and CLI command  
- **NFR-013**: Reliability - System MUST handle component failures gracefully with user-friendly error messages
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
- **Model**: GGUF-format LLM stored locally and loaded via llama-cpp-python
- **Configuration**: YAML-based settings for LLM parameters, vector DB settings, API configuration, and logging options

## Success Criteria *(mandatory)*

## Success Criteria and Acceptance *(mandatory)*

### Measurable Outcomes

#### Functional Success Metrics

- **SC-001**: Users can complete system installation via single APT command on clean Pi5/AMD64 Debian-based systems within 5 minutes
- **SC-002**: System handles 100+ documents (2K-10K words each) without performance degradation  
- **SC-003**: System achieves 90% successful completion rate for core workflow: document import completes without errors AND queries against imported content return responses with source citations within performance targets
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
