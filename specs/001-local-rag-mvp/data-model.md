# Data Model: Local RAG System

**Branch**: `001-local-rag-mvp` | **Date**: 2025-10-28
**Phase**: 1 - Design and Contracts

## Core Entities

### Document

Represents an ingested content item with associated metadata and change tracking.

**Fields**:
- `id: str` - UUID4 string identifier
- `title: str` - Document title (extracted or provided)
- `source_uri: str` - Original file path or URL (normalized)
- `source_hash: str` - SHA-256 hash of source URI + metadata + content (detects updates)
- `content_hash: str` - SHA-256 hash of normalized content only (cross-source deduplication)
- `source_metadata: dict` - Source-specific metadata (mtime, etag, size, etc.)
- `ingestion_timestamp: datetime` - ISO 8601 timestamp of first ingestion
- `last_updated: datetime` - ISO 8601 timestamp of last content update
- `last_checked: datetime` - ISO 8601 timestamp of last source check
- `chunk_count: int` - Number of chunks created from document
- `status: str` - Enum: "active" | "deleted" | "outdated"
- `update_available: bool` - True if source has newer content (checked but not imported)
- `additional_metadata: dict` - User-defined key-value metadata

**Validation Rules**:
- `id` must be valid UUID4 format
- `source_hash` must be valid SHA-256 hex string (64 characters)
- `content_hash` must be valid SHA-256 hex string (64 characters)
- `source_uri` must be valid file:// or http(s):// URI format
- `status` must be one of allowed enum values: "active", "deleted", "outdated"
- `chunk_count` must be positive integer
- All timestamp fields must be valid ISO 8601 format
- `source_metadata` must contain appropriate fields based on source type

**Relationships**:
- One-to-many with DocumentChunk entities
- Referenced by QueryResult for source attribution

### DocumentChunk

Represents a vector-embedded segment of document content stored in ChromaDB.

**Fields**:
- `id: str` - UUID4 string identifier  
- `document_id: str` - Foreign key to parent Document
- `content: str` - Actual text content of the chunk
- `embedding: List[float]` - Vector embedding (managed by ChromaDB)
- `start_offset: int` - Character offset within original document
- `end_offset: int` - End character offset within original document
- `chunk_index: int` - Sequential index within document (0-based)

**Validation Rules**:
- `document_id` must reference existing Document
- `content` cannot be empty string
- `start_offset` must be >= 0
- `end_offset` must be > start_offset
- `chunk_index` must be >= 0

**Relationships**:
- Many-to-one with Document entity
- Referenced by QueryResult for context assembly

### Query

Represents a user-submitted question or prompt.

**Fields**:
- `id: str` - UUID4 string identifier
- `text: str` - User's query text
- `timestamp: datetime` - ISO 8601 timestamp of submission
- `embedding: List[float]` - Query vector embedding
- `response_text: str` - Generated response text
- `response_tokens: int` - Number of tokens in response
- `processing_time_ms: int` - Total processing time in milliseconds
- `retrieved_chunks: List[str]` - List of chunk IDs used for context

**Validation Rules**:
- `text` cannot be empty or whitespace-only
- `processing_time_ms` must be >= 0
- `response_tokens` must be >= 0
- `retrieved_chunks` must contain valid chunk IDs

**Relationships**:
- References DocumentChunk entities via retrieved_chunks
- One-to-many with QueryResult for detailed retrieval info

### Configuration

Represents system configuration settings loaded from YAML.

**Fields**:
- `llm.model_path: str` - Path to GGUF model file
- `llm.context_size: int` - LLM context window size
- `llm.threads: int` - Number of CPU threads for inference
- `llm.max_tokens: int` - Maximum tokens per response
- `vector_db.persist_directory: str` - ChromaDB data directory
- `vector_db.collection_name: str` - ChromaDB collection name
- `api.host: str` - API server bind address
- `api.port: int` - API server port
- `logging.level: str` - Log level (DEBUG, INFO, WARN, ERROR)
- `logging.file: str` - Log file path
- `logging.max_size: str` - Max log file size
- `logging.backup_count: int` - Number of log file backups

**Validation Rules**:
- `llm.model_path` must point to accessible GGUF file
- `llm.context_size` must be > 0 and <= model maximum
- `llm.threads` must be > 0 and <= CPU count
- `api.port` must be valid port number (1-65535)
- `logging.level` must be valid logging level
- All directory paths must be writable by application

## State Transitions

### Document Lifecycle

```
[New] -> [Processing] -> [Active] -> [Deleted]
                    |       ^           |
                    v       |           v
               [Failed] ----+      [Archived]
```

**Transitions**:
- New -> Processing: Document submitted for ingestion
- Processing -> Active: Document successfully processed and embedded
- Processing -> Failed: Document processing encountered error
- Active -> Deleted: User soft-deletes document
- Failed -> Processing: User retries failed document
- Deleted -> Archived: Cleanup process removes from active queries

### Query Processing States

```
[Submitted] -> [Embedding] -> [Retrieving] -> [Generating] -> [Complete]
                    |              |             |              |
                    v              v             v              v
                [Failed]      [Failed]      [Failed]      [Failed]
```

**Transitions**:
- Submitted -> Embedding: Query text converted to vector
- Embedding -> Retrieving: Similar chunks found in ChromaDB
- Retrieving -> Generating: Context assembled for LLM
- Generating -> Complete: Response tokens streamed to user
- Any state -> Failed: Error occurred during processing

## Data Persistence

### ChromaDB Collections

**documents**: Main collection for document chunks
- Embeddings: Dense vectors for semantic search
- Metadata: document_id, chunk_index, start_offset, end_offset
- Documents: Original chunk text content

### SQLite Metadata (via ChromaDB)

**document_metadata**: Document-level information
- Stored as ChromaDB metadata but queryable
- Indexed on content_hash for deduplication
- Indexed on status for active/deleted filtering

### Configuration Files

**System Configuration**: `/etc/local-rag/config.yaml`
- YAML format with environment variable substitution
- Validated on startup with comprehensive error messages
- Default values embedded in application

**Model Storage**: `/var/lib/local-rag/models/`
- GGUF model files downloaded or provided by user
- Symlinks supported for shared model storage
- Automatic model integrity checking on load

## Data Access Patterns

### Content Ingestion
1. Calculate source metadata (mtime for files, etag/last-modified for URLs)
2. Calculate source_hash from URI + metadata + content for change detection
3. Calculate content_hash from normalized content only for cross-source deduplication
4. Check for existing source_hash to detect if content needs updating
5. Check for existing content_hash to identify cross-source duplicates
6. Create Document entity with both hash types and metadata
7. Split content into chunks with overlap
8. Generate embeddings for each chunk
9. Store chunks in ChromaDB with metadata linking to document

### Update Detection and Re-Import
1. For existing sources, fetch current source metadata
2. Calculate new source_hash with current metadata
3. Compare with stored source_hash to detect changes
4. If different, mark document as "outdated" and optionally auto-update
5. Preserve content_hash history for rollback capabilities
6. Update embeddings only for changed content

### Cross-Source Deduplication
1. Generate content_hash for new content
2. Search existing documents by content_hash
3. If match found, link sources instead of duplicating embeddings
4. Track multiple source_uri values for same content
5. Update last_checked timestamp for all linked sources

### Query Processing
1. Generate embedding for user query text
2. Perform similarity search in ChromaDB (unchanged)
3. Filter results by document status ("active" only, exclude "deleted" and "outdated")
4. Retrieve top-k most relevant chunks
5. Assemble context from chunk content with source attribution
6. Generate response using LLM with context
7. Store query and response for analytics

### Content Management
1. List operations query by status, source_uri, or content_hash
2. Update operations can refresh from source or modify metadata
3. Delete operations mark as soft-deleted ("deleted" status)
4. Check-updates operations compare stored vs current source metadata
5. Reset operations clear all collections and reset state