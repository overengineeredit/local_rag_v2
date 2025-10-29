# Product Requirements

## Core

1. **Local inference** only; no internet dependency for generation.
2. **Streaming tokens** to UI for immediate responsiveness.
3. **Battery‑friendly**: low idle draw, predictable thermal envelope.
4. **Resilience**: survive ungraceful power loss without corrupting state.

## Functional

- Accept a **textual prompt** from the user via web UI (FastAPI backend).
- Use `llama-cpp-python` for local LLM inference (GGUF models).
- Ingest plain text, HTML, and URLs (batch, file, or folder) into ChromaDB.
- Use ChromaDB (embedded, SQLite backend) for vector storage.
- Store metadata: title, source, date, hash (for deduplication).
- Deduplicate on content hash; log duplicates and import summary.
- Support content updates without full re-import.
- Provide soft delete functionality for content management.
- Package as a `.deb` for apt-based installation on ARM64 and AMD64.
- Provide a systemd service for starting/stopping the app.
- All configuration in `/etc/local-rag/config.yaml`.
- Models stored in `/var/lib/local-rag/models/`.

## Non-Functional

- **Performance**:
  - Cold start (first query): 3-5 minutes for first token
  - Warm queries: 1-3 minutes for first token, reading-speed thereafter
  - Desktop/AMD64: Sub-second to 30 seconds (reference comparison)
- **UI**: Works on 720p screens (Chrome/Firefox).
- **Logging**: JSON format, configurable levels, disk + stdout, with rotation.
- **Resource limits**: Configurable RAM/disk usage with graceful backoff.
- **Health checks**: API endpoint (`/health`) and CLI command for system status.
- **Knowledge base management**: CLI commands for reset and content operations (all via API).
- **Cross-platform**: Support ARM64 (Pi5) and AMD64 architectures.

## Acceptance Tests

- **Content ingestion**: Load text files, URLs, and HTML into vector database.
- **Deduplication**: Detect and log duplicate content during import.
- **Content management**: Update existing content without duplication.
- **RAG retrieval**: Query system about loaded content with relevant responses.
- **LLM integration**: Generate coherent responses using retrieved context.
- **Web UI**: Functional interface for queries and basic system interaction.
- **System service**: Proper systemd integration with start/stop/status.
