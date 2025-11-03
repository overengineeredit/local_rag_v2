# Solution Design

## Architecture Overview

The system consists of a single Python process managed by systemd, containing all necessary components:

```
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

## Module Breakdown

### Core Modules

**`main.py`**
- Application entry point and FastAPI app initialization
- Health check endpoints and system status
- Configuration loading and validation

**`llm_interface.py`**
- llama-cpp-python integration
- Model loading and inference management
- Token streaming and response generation
- Error handling and retry logic

**`vector_store.py`**
- ChromaDB initialization and management
- Document embedding and storage
- Similarity search and retrieval
- Metadata management and deduplication

**`content_manager.py`**
- Document ingestion from files, URLs, and HTML
- Content preprocessing and chunking
- Import/update/delete operations
- Deduplication logic and import summaries

**`web_interface.py`**
- FastAPI routes for web UI and API
- User query handling and response streaming
- Administrative endpoints (health, reset, content management)
- Error handling and user feedback

**`cli.py`**
- Command-line interface for system operations
- API client for communicating with FastAPI backend
- Health checks, content management, and system reset
- User-friendly error reporting

### Configuration

**Environment Variables:**
- `CONFIG_PATH`: Path to configuration file (default: `/etc/local-rag/config.yaml`)
- `DATA_DIR`: Data directory path (default: `/var/lib/local-rag`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

**Configuration File Structure:**
```yaml
llm:
  model_path: "/var/lib/local-rag/models/deepseek-r1-distill-qwen-1.5b.Q4_K_M.gguf"
  context_size: 2048
  threads: 4
  max_tokens: 512

vector_db:
  persist_directory: "/var/lib/local-rag/chromadb"
  collection_name: "documents"

api:
  host: "127.0.0.1"
  port: 8080

logging:
  level: "INFO"
  file: "/var/log/local-rag/app.log"
  max_size: "10MB"
  backup_count: 5
```

## Data Flow

### Content Ingestion
1. User provides files/URLs via CLI or API
2. Content is processed and chunked appropriately
3. Embeddings generated for each chunk
4. Content hash calculated for deduplication
5. Chunks stored in ChromaDB with metadata
6. Import summary logged and returned

### Query Processing
1. User submits query via web interface
2. Query embedding generated
3. ChromaDB performs similarity search
4. Relevant chunks retrieved and ranked
5. Context assembled and sent to LLM
6. Response tokens streamed back to user

## Metadata Schema

**Document Metadata:**
```python
{
    "id": "uuid4_string",
    "title": "Document Title",
    "source": "file_path_or_url", 
    "content_hash": "sha256_hex",
    "timestamp": "2025-10-12T10:30:00Z",
    "chunk_count": 5,
    "status": "active|deleted"
}
```

## Deduplication Strategy

**Content-based deduplication using SHA-256 hashes:**
- Calculate hash of normalized content (whitespace trimmed)
- Check existing hashes before embedding
- Log duplicate detection with source information
- Update metadata if source or timestamp differs
- Maintain reference count for multi-source documents

## Error Handling

**LLM Errors:**
- Retry failed inference up to 3 times
- Log detailed error information
- Return user-friendly error messages
- Graceful degradation if model unavailable

**Vector DB Errors:**
- Validate ChromaDB connection on startup
- Handle corruption with graceful fallback
- Provide clear error messages for storage issues

**Content Import Errors:**
- Continue processing other files if one fails
- Log failed imports with specific error details
- Provide resumable import capability
- Report import summary with success/failure counts

## Security

**Authentication**: None required for v1 (single-user device)
**Input Validation**: Sanitize all user inputs and file paths
**Resource Limits**: Configurable limits to prevent resource exhaustion
**Logs**: Avoid logging sensitive user queries in production mode

### CI/CD Security Scanning

**Security Scanner**: pip-audit (PyPA official tool)
- Scans Python dependencies for known vulnerabilities
- Configured with `--skip-editable` to exclude local development packages
- Focus on critical vulnerabilities: code execution, privilege escalation, SQL injection
- Exit code handling: 0 = no vulnerabilities, 1 = vulnerabilities found (analyzed for criticality)

**Vulnerability Management**:
- Critical vulnerabilities block builds and deployments
- Non-critical vulnerabilities logged for review but don't block development
- Security reports generated and stored as build artifacts
- Regular dependency updates automated where possible

## CI/CD Workflow Architecture

### Branch-Specific Workflow Strategy

**Development Workflows** (Feature Branches):
- **pr-validation.yml**: Fast feedback on code quality, security, and tests
- **ci.yml**: Comprehensive testing without heavy builds
- Target: 2-4 minute feedback time
- Focus: Linting, type checking, unit tests, security scanning

**Production Workflows** (Main Branch):
- **build-packages.yml**: Full package building for both AMD64 and ARM64
- Target: 15-20 minute complete build and validation
- Focus: Cross-compilation, package validation, artifact generation

**Manual Override**:
- workflow_dispatch available for debugging and testing
- Architecture selection (amd64, arm64, all)
- Force rebuild and validation options

### Security Integration

**Development Security**:

- pip-audit vulnerability scanning on all branches
- Critical vulnerability detection (code execution, privilege escalation)
- Security reports as build artifacts

**Production Security**:

- Full dependency security validation
- Package integrity verification
- GPG signing preparation (future milestone)

## Testing Strategy

**Unit Tests**: All core modules with mocked dependencies
**Integration Tests**: End-to-end API and CLI functionality
**BDD Tests**: User scenarios with clear acceptance criteria
**Performance Tests**: Resource usage and response time validation

## Future Extensibility

**Modular Design**: Clear interfaces between components
**Plugin Architecture**: Hooks for new content types and processors
**Configuration**: Environment-based settings for easy customization
**API Versioning**: RESTful API design for backward compatibility