# Tasks: Local RAG System

**Input**: Design documents from `/specs/001-local-rag-mvp/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included based on acceptance scenarios in the specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Development Milestones

This project follows a 4-milestone development strategy with concrete deliverables and success criteria for each phase:

### Milestone 1: Core Infrastructure and MVP (4-6 weeks)

**Goal**: Basic working system with essential RAG functionality

**Deliverables**:

- Single Python application with embedded LLM and vector DB
- APT package for installation on Pi5 and AMD64
- Systemd service integration
- Basic web UI for queries
- Content ingestion via CLI

**Definition of Done**:

- [ ] `.deb` package installs cleanly on Pi5 and AMD64
- [ ] `systemctl start local-rag` launches the service successfully
- [ ] Web UI accessible at `http://localhost:8080`
- [ ] Can ingest text files via CLI command
- [ ] Can query system about ingested content with coherent responses
- [ ] Health check API endpoint returns system status
- [ ] Basic error handling with user-friendly messages
- [ ] Logging configured with rotation

**Maps to Phases**: Phase 1 (Setup) + Phase 2 (Foundational) + Phase 3 (US1) + Phase 4 (US2)

### Milestone 2: Content Management and Robustness (3-4 weeks)

**Goal**: Robust content operations with deduplication and metadata

**Deliverables**:

- Advanced content ingestion (URLs, HTML, batches)
- Deduplication and metadata management
- Content update/delete operations
- Import progress and resumability
- Resource limit enforcement

**Definition of Done**:

- [ ] Can import content from URLs and HTML files
- [ ] Batch import from folders with progress reporting
- [ ] Duplicate content detected and logged appropriately
- [ ] Existing content can be updated without duplication
- [ ] Content can be soft-deleted via CLI
- [ ] Import operations can be resumed after interruption
- [ ] Resource limits prevent system overload
- [ ] Import summaries show success/failure counts
- [ ] Metadata properly stored and searchable

**Maps to Phases**: Phase 5 (US3) + Phase 6 (US4)

### Milestone 3: Testing and Developer Experience (2-3 weeks)

**Goal**: Comprehensive testing and documentation for maintainability

**Deliverables**:

- Unit test suite with high coverage
- BDD acceptance tests
- Developer documentation
- Architecture diagrams
- Contribution guidelines

**Definition of Done**:

- [ ] Unit tests cover all core modules (>85% coverage)
- [ ] BDD tests validate all user scenarios
- [ ] Integration tests verify API and CLI functionality
- [ ] Architecture diagrams generated
- [ ] API documentation auto-generated
- [ ] Developer setup instructions documented
- [ ] Code follows consistent style and documentation standards
- [ ] CI/CD pipeline builds and tests both architectures

**Maps to Phases**: Phase 7 (Polish & Cross-Cutting - Testing Focus)

### Milestone 4: Performance and User Experience (2-3 weeks)

**Goal**: Optimize performance and improve user interface

**Deliverables**:

- Performance optimizations for Pi5
- Enhanced web UI with better UX
- Streaming response display
- Error handling improvements
- Configuration validation

**Definition of Done**:

- [ ] Response times optimized for Pi5 constraints
- [ ] Web UI shows streaming responses in real-time
- [ ] Error messages are clear and actionable
- [ ] Configuration validation prevents startup issues
- [ ] System remains responsive under load
- [ ] Memory usage stays within configured limits
- [ ] UI works well on 720p displays

**Maps to Phases**: Phase 7 (Polish & Cross-Cutting - Performance/UX Focus)

---

## Milestone-to-Phase Mapping

- **Milestone 1** → **Phases 1-4** (Setup + Foundational + US1 + US2) - MVP Core
- **Milestone 2** → **Phases 5-6** (US3 + US4) - Content Management
- **Milestone 3** → **Phase 7** (Polish & Cross-Cutting - Testing Focus)
- **Milestone 4** → **Phase 7** (Polish & Cross-Cutting - Performance/UX Focus)

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/guide/`, `tests/` at repository root
- Paths follow the structure defined in plan.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan in src/guide/
- [X] T002 Initialize Python project with FastAPI, llama-cpp-python, ChromaDB dependencies in pyproject.toml
- [X] T003 [P] Configure ruff linting and formatting tools in pyproject.toml
- [X] T004 [P] Create systemd service configuration in config/local-rag.service
- [X] T005 [P] Setup APT packaging structure in packaging/debian/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Setup ChromaDB embedded configuration and initialization in src/guide/vector_store.py
- [X] T007 [P] Implement configuration management with YAML loading in src/guide/__init__.py
- [X] T008 [P] Implement comprehensive JSON-formatted logging system per FR-021: JSON format with required fields (timestamp, level, module, message, request_id) and optional fields (user_id, duration_ms, error_code, context); configurable levels (DEBUG/INFO/WARN/ERROR); disk output to /var/log/local-rag/app.log + stdout; 10MB max size with 5 backup files rotation; integration with FastAPI request logging and basic infrastructure setup in src/guide/main.py
- [X] T009 [P] Create base FastAPI application structure in src/guide/main.py
- [x] T009a [P] Implement thermal monitoring infrastructure per NFR-006: discover available thermal zones by scanning `/sys/class/thermal/thermal_zone*/temp`, select primary zone (thermal_zone0) with fallback to highest numbered zone if zone0 unavailable, read temperature every 30 seconds using 3-sample rolling average (collections.deque(maxlen=3) with arithmetic mean), trigger alerts at >75°C average, halt processing at >85°C average with user notification and automatic resume when average drops below 70°...
- [x] T009b [P] Implement model management infrastructure per FR-015: model download validation, GGUF file integrity checks, model storage in /var/lib/local-rag/models/, default model setup in src/guide/llm_interface.py
- [ ] T009c [P] Implement model storage directory creation and management per FR-015: create /var/lib/local-rag/models/ with proper permissions, validate directory writability, implement model file organization and cleanup in src/guide/llm_interface.py
- [ ] T009d [P] Implement model download and validation system per FR-015: download default model if missing, verify GGUF file integrity, handle download failures with retry logic, provide download progress reporting in src/guide/llm_interface.py
- [X] T010 Create error handling middleware and exception classes in src/guide/web_interface.py
- [X] T011 [P] Setup health check infrastructure for all components in src/guide/web_interface.py
- [X] T011a [P] Implement health check API endpoint per FR-016: JSON response with component status (LLM model loaded, ChromaDB connectivity, disk space %, memory usage %, overall system health) accessible at GET /health in src/guide/web_interface.py
- [x] T011b [P] Implement health check CLI command per FR-016: `local-rag status` with human-readable output, `--verbose` flag for detailed diagnostics, communicate with API endpoint for data in src/guide/cli.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic Document Query RAG (Priority: P1) 🎯 MVP

**Goal**: Users can upload text documents and ask questions about their content, receiving relevant answers generated using local LLM with retrieved context.

**Independent Test**: Upload a text file, ask a question about its content, and receive a relevant generated response that demonstrates retrieval-augmented generation.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [P] [US1] Contract test for document upload endpoint in tests/integration/test_document_api.py
- [ ] T013 [P] [US1] Contract test for query endpoint with streaming response in tests/integration/test_query_api.py
- [ ] T014 [P] [US1] Integration test for complete RAG workflow in tests/integration/test_rag_workflow.py

### Implementation for User Story 1

- [ ] T015 [P] [US1] Create Document entity model in src/guide/vector_store.py
- [ ] T016 [P] [US1] Create DocumentChunk entity model in src/guide/vector_store.py
- [ ] T017 [P] [US1] Create Query entity model in src/guide/llm_interface.py
- [ ] T018 [US1] Implement VectorStore class with ChromaDB operations in src/guide/vector_store.py (depends on T015, T016): ChromaDB client initialization with /var/lib/local-rag/chromadb persist directory, connection retry logic with exponential backoff, collection management with metadata schema validation, embedding CRUD operations with error handling
- [ ] T019 [US1] Implement LLMInterface class with llama-cpp-python integration in src/guide/llm_interface.py (depends on T017): model loading from /var/lib/local-rag/models/ with GGUF validation, inference parameter management (temperature, top-p, context_size), token streaming with interrupt capability, memory management and model lifecycle
- [ ] T020 [US1] Implement basic content processing and chunking in src/guide/content_manager.py
- [ ] T021 [US1] Implement document upload API endpoint in src/guide/web_interface.py
- [ ] T022 [US1] Implement query API endpoint with streaming response in src/guide/web_interface.py
- [ ] T023 [US1] Create basic web UI for document upload and querying in src/guide/web_interface.py
- [ ] T024 [US1] Add dual hash system: source_hash (URI + metadata + content) and content_hash (content only) in src/guide/content_manager.py
- [ ] T025 [US1] Add source attribution to query responses in src/guide/llm_interface.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - System Installation and Management (Priority: P1)

**Goal**: Users can install the system via APT package manager and manage it as a systemd service on both Raspberry Pi 5 (ARM64) and AMD64 systems.

**Independent Test**: Install the .deb package on a clean system, start the service, and verify it's accessible at localhost:8080.

### Tests for User Story 2

- [ ] T026 [P] [US2] Integration test for systemd service lifecycle in tests/integration/test_service_management.py
- [ ] T027 [P] [US2] Integration test for APT package installation in tests/integration/test_package_install.py
- [ ] T028 [P] [US2] Health check endpoint validation test in tests/integration/test_health_api.py

### Implementation for User Story 2

- [ ] T029 [P] [US2] Create debian package control files in packaging/debian/control
- [ ] T030 [P] [US2] Create package installation scripts in packaging/debian/postinst and packaging/debian/prerm
- [ ] T031 [P] [US2] Create systemd service file with proper configuration in config/local-rag.service
- [ ] T032 [US2] Implement systemd service management commands in src/guide/cli.py
- [ ] T033 [US2] Implement health check API endpoint in src/guide/web_interface.py
- [ ] T034 [US2] Create default configuration file template in config/config.yaml.example
- [ ] T035 [US2] Add proper daemon mode and signal handling in src/guide/main.py
- [ ] T036 [US2] Setup package build automation scripts in packaging/scripts/: build.sh for dpkg-buildpackage execution, architecture detection (ARM64/AMD64), dependency resolution validation. Validation criteria: successful .deb generation, lintian clean package validation, installability verification via apt-get install simulation
- [ ] T037 [US2] Configure cross-architecture build for ARM64 and AMD64 in packaging/: GitHub Actions workflow with qemu-user-static for ARM64 emulation, separate .deb generation for each architecture, package testing on target platforms. Validation criteria: clean installation on Ubuntu 22.04/Debian 12, service startup verification, health check endpoint responsiveness

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Batch Content Import with Change Detection (Priority: P2)

**Goal**: Users can import content from multiple sources (files, URLs, HTML) in batch operations with automatic change detection, deduplication, and progress tracking.

**Independent Test**: Import a folder of documents, modify some files, re-import, and verify only changed content is re-processed with accurate change detection.

### Tests for User Story 3

- [ ] T038 [P] [US3] Contract test for batch import API endpoint in tests/integration/test_batch_import_api.py
- [ ] T039 [P] [US3] Integration test for URL content processing and change detection in tests/integration/test_url_import.py
- [ ] T040 [P] [US3] Integration test for dual hash deduplication and update detection in tests/integration/test_change_detection.py
- [ ] T041 [P] [US3] Integration test for update checking without re-import in tests/integration/test_update_check.py
- [ ] T041a [P] [US3] Acceptance test for progress tracking during batch import in tests/integration/test_progress_tracking.py
- [ ] T041b [P] [US3] Acceptance test for import resumability after interruption in tests/integration/test_resumable_import.py
- [ ] T041c [P] [US3] Acceptance test for cross-source deduplication validation in tests/integration/test_deduplication_validation.py

### Implementation for User Story 3

- [ ] T042 [P] [US3] Implement source metadata extraction (mtime, etag, last-modified) in src/guide/content_manager.py
- [ ] T043 [P] [US3] Create URL content processor with header-based change detection in src/guide/content_manager.py
- [ ] T044 [P] [US3] Create HTML content processor with metadata preservation in src/guide/content_manager.py
- [ ] T045 [P] [US3] Implement update checking API endpoint (/documents/check-updates) in src/guide/web_interface.py
- [ ] T046 [US3] Implement batch import with dual hash system in src/guide/content_manager.py
- [ ] T047 [US3] Implement source update API endpoint (/documents/update-sources) in src/guide/web_interface.py
- [ ] T048 [US3] Add resumable import capability with state persistence in src/guide/content_manager.py
- [ ] T049 [US3] Implement import summary with change/duplicate/unchanged categorization in src/guide/content_manager.py
- [ ] T050 [US3] Add CLI commands for update checking and selective re-import in src/guide/cli.py
- [ ] T051 [US3] Add progress tracking UI for batch operations and update status in src/guide/web_interface.py
- [ ] T051a [US3] Implement import checkpoint system for resumability every 10 documents in src/guide/content_manager.py
- [ ] T051b [US3] Implement detailed import summary with categorization (new/updated/unchanged/failed) in src/guide/content_manager.py
- [ ] T051c [US3] Add content metadata extraction validation (title, source URI, timestamps) in src/guide/content_manager.py

**Checkpoint**: All core import functionality should now be independently functional

---

## Phase 6: User Story 4 - Content Management Operations (Priority: P3)

**Goal**: Users can manage their knowledge base by viewing, updating, and deleting content through CLI commands with full API integration.

**Independent Test**: Add content, list it, update it, and soft-delete it through CLI operations.

### Tests for User Story 4

- [ ] T052 [P] [US4] Contract test for content listing API in tests/integration/test_content_list_api.py
- [ ] T053 [P] [US4] Contract test for content soft-delete API in tests/integration/test_content_delete_api.py
- [ ] T054 [P] [US4] Integration test for CLI content management in tests/integration/test_cli_content.py
- [ ] T054a [P] [US4] Acceptance test for content metadata display with timestamps in tests/integration/test_content_metadata.py
- [ ] T054b [P] [US4] Acceptance test for soft-deleted content exclusion from queries in tests/integration/test_soft_delete_exclusion.py
- [ ] T054c [P] [US4] Acceptance test for system reset with confirmation in tests/integration/test_system_reset.py

### Implementation for User Story 4

- [ ] T055 [P] [US4] Implement document listing API endpoint with status filtering in src/guide/web_interface.py
- [ ] T056 [P] [US4] Implement document deletion (soft delete) API endpoint in src/guide/web_interface.py
- [ ] T057 [P] [US4] Implement document detail view API endpoint with source metadata in src/guide/web_interface.py
- [ ] T058 [US4] Implement CLI commands for listing documents with update status in src/guide/cli.py
- [ ] T059 [US4] Implement CLI commands for soft-deleting documents in src/guide/cli.py
- [ ] T060 [US4] Implement CLI command for system reset in src/guide/cli.py
- [ ] T061 [US4] Add content management UI pages with update tracking in src/guide/web_interface.py
- [ ] T062 [US4] Implement document status filtering and search in src/guide/vector_store.py
- [ ] T062a [US4] Implement document metadata display with creation/update timestamps in src/guide/web_interface.py
- [ ] T062b [US4] Add content source tracking and attribution display in src/guide/vector_store.py
- [ ] T062c [US4] Implement comprehensive content statistics reporting in src/guide/cli.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T063 [P] Add comprehensive error handling with user-friendly messages: HTTP 4xx/5xx responses, LLM inference failures, file I/O errors, ChromaDB connection issues - all with actionable guidance across all modules
- [ ] T064 [P] Implement resource monitoring and limits: RAM usage tracking, disk space monitoring, configurable thresholds with graceful degradation in src/guide/main.py
- [ ] T065 [P] Add performance optimizations for Pi5 constraints: model loading optimization, memory pooling, inference threading tuning to meet NFR-001 targets (4 minutes P50, 5 minutes P95 cold start; 90 seconds P50, 3 minutes P95 warm queries) across all components
- [ ] T066 [P] Create comprehensive unit tests: >85% code coverage, all core functions tested, mock external dependencies in tests/unit/ for all core modules
- [ ] T066a [P] Create performance validation tests for NFR-001/NFR-002: Pi5 cold start timing (4 minutes P50, 5 minutes P95), warm query timing (90 seconds P50, 3 minutes P95), AMD64 timing (5 seconds P50, 15 seconds P95), baseline hardware verification (CPU temp <70°C, single concurrent query, 2-3 document context) in tests/integration/test_performance_benchmarks.py
- [ ] T067 [P] Security hardening and input validation: SQL injection prevention, XSS protection, file path sanitization, content size limits across all endpoints
- [ ] T068 [P] Documentation updates and API documentation generation: OpenAPI spec generation, inline code documentation, user guide updates
- [ ] T069 Run quickstart.md validation and end-to-end testing
- [ ] T070 [P] Add metrics and monitoring endpoints per NFR-012 (monitoring requirement) and health check infrastructure in src/guide/web_interface.py (CPU usage, memory consumption, query count, response times, document count, inference duration)
- [ ] T071 [P] Implement configuration validation and startup checks in src/guide/main.py
- [ ] T072 [P] Add power-loss resilience testing and corruption recovery validation
- [ ] T072a [P] Create comprehensive edge case integration test suite covering all FR-022 through FR-030 scenarios in tests/integration/test_comprehensive_edge_cases.py: disk space exhaustion, model corruption, power loss recovery, soft-delete exclusion, memory failures, large documents, database corruption, malicious content, and port conflicts with end-to-end validation

### Edge Case Handling Tasks

- [ ] T073 [P] Implement disk space monitoring and graceful degradation per FR-022: check available space before import operations, warn at 90% capacity, halt imports at 95% capacity with user notification in src/guide/content_manager.py. Success criteria: disk usage monitoring active, warnings logged and displayed, import halted appropriately
- [ ] T073a [P] Add edge case test for disk space exhaustion during import in tests/integration/test_disk_space_edge_cases.py
- [ ] T074 [P] Add corrupted model file detection and recovery guidance per FR-023: GGUF header validation, file size verification, clear error messages with model redownload instructions in src/guide/llm_interface.py. Success criteria: corrupted files detected on startup, recovery guidance provided, model redownload functionality working
- [ ] T074a [P] Add edge case test for corrupted model file handling in tests/integration/test_model_corruption_edge_cases.py
- [ ] T075 [P] Implement graceful power loss recovery with atomic operations per FR-024: use ChromaDB transactions, verify database integrity on startup, implement rollback for incomplete operations in src/guide/vector_store.py. Success criteria: database integrity preserved after power loss, automatic recovery functional, incomplete operations cleaned up
- [ ] T075a [P] Add edge case test for power loss during document processing in tests/integration/test_power_loss_edge_cases.py
- [ ] T076 [P] Add handling for soft-deleted content queries per FR-025: filter deleted content from search results, log access attempts, provide "content unavailable" messages in src/guide/vector_store.py. Success criteria: deleted content excluded from queries, appropriate user feedback provided, access attempts logged
- [ ] T076a [P] Add edge case test for soft-deleted content query exclusion in tests/integration/test_soft_delete_edge_cases.py
- [ ] T077 [P] Implement LLM memory failure detection and fallback strategies per FR-026: catch OOM exceptions, reduce model parameters, provide clear memory requirement guidance in src/guide/llm_interface.py. Success criteria: OOM exceptions caught gracefully, fallback strategies functional, clear guidance provided to user
- [ ] T077a [P] Add edge case test for insufficient memory scenarios in tests/integration/test_memory_failure_edge_cases.py
- [ ] T078 [P] Add large document chunking with context window management per FR-027: enforce maximum chunk size limits, implement sliding window overlap, handle documents exceeding context limits in src/guide/content_manager.py. Success criteria: large documents chunked properly, context limits enforced, overlapping chunks created correctly
- [ ] T078a [P] Add edge case test for very large document processing in tests/integration/test_large_document_edge_cases.py
- [ ] T079 [P] Implement ChromaDB corruption detection and repair procedures per FR-028: database integrity checks, backup restoration, rebuild vector index capability in src/guide/vector_store.py. Success criteria: corruption detected automatically, repair procedures functional, backup/restore working correctly
- [ ] T079a [P] Add edge case test for database corruption scenarios in tests/integration/test_database_corruption_edge_cases.py
- [ ] T080 [P] Add malicious content detection and sanitization during import per FR-029: file size limits (max 100MB), content type validation, malformed encoding detection in src/guide/content_manager.py. Success criteria: file size limits enforced, content types validated, malformed content rejected safely
- [ ] T080a [P] Add edge case test for malicious content handling in tests/integration/test_malicious_content_edge_cases.py
- [ ] T081 [P] Implement configurable API port binding per FR-030: allow port configuration via config file and environment variables, detect port conflicts, provide clear error messages for unavailable ports in src/guide/main.py. Success criteria: port configurable, conflicts detected, clear error guidance provided
- [ ] T081a [P] Add edge case test for port conflict scenarios in tests/integration/test_port_conflict_edge_cases.py

- [ ] T081 [P] Implement configurable API port binding per FR-030: allow port configuration via config file and environment variables, detect port conflicts, provide clear error messages for unavailable ports in src/guide/main.py. Success criteria: port configurable, conflicts detected, clear error guidance provided

### Power and Thermal Management Tasks

- [ ] T082 [P] Implement power consumption monitoring with idle/peak thresholds per FR-018 and Constitution Principle II (Resource Efficiency): monitor CPU usage, track power states, implement <5W idle and <25W peak thresholds, provide power usage reporting in src/guide/main.py
- [ ] T083 [P] Implement battery-friendly operation per FR-018 and Constitution Principle II (Resource Efficiency): reduce background processing during idle, implement CPU frequency scaling coordination, optimize inference scheduling for power efficiency in src/guide/llm_interface.py
- [ ] T084 [P] Add thermal monitoring integration with inference control per Constitution Principle II (Resource Efficiency): use thermal data from T009a, implement thread reduction at >75°C (reduce by 50%), pause inference at >85°C, resume when temperature drops below 70°C in src/guide/llm_interface.py
- [ ] T085 [P] Implement inference throttling and halt mechanisms for thermal protection per Constitution Principle II (Resource Efficiency) in src/guide/llm_interface.py
- [ ] T086 [P] Add power-efficient idle mode with reduced background processing per Constitution Principle II (Resource Efficiency) in src/guide/main.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 and US2 are both P1 priority and can proceed in parallel (if staffed)
  - US3 (P2) can start after Foundational but may benefit from US1 completion
  - US4 (P3) can start after Foundational but may benefit from US1/US3 completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Independent of US1 but both needed for complete MVP
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Benefits from US1 content processing foundation
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Benefits from US1/US3 content management APIs

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before UI/CLI integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 and US2 can start in parallel (both P1)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for document upload endpoint in tests/integration/test_document_api.py"
Task: "Contract test for query endpoint with streaming response in tests/integration/test_query_api.py"
Task: "Integration test for complete RAG workflow in tests/integration/test_rag_workflow.py"

# Launch all models for User Story 1 together:
Task: "Create Document entity model in src/guide/vector_store.py"
Task: "Create DocumentChunk entity model in src/guide/vector_store.py"
Task: "Create Query entity model in src/guide/llm_interface.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Core RAG functionality)
4. Complete Phase 4: User Story 2 (System management)
5. **STOP and VALIDATE**: Test complete system installation and RAG workflow
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Core RAG works
3. Add User Story 2 → Test independently → Full MVP deployment ready
4. Add User Story 3 → Test independently → Advanced import capabilities
5. Add User Story 4 → Test independently → Complete content management
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Core RAG)
   - Developer B: User Story 2 (System management)
   - Developer C: User Story 3 (Batch import) - after US1 foundation
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- MVP = US1 + US2 (Core RAG + System management)
- Focus on P1 stories first for fastest user value
