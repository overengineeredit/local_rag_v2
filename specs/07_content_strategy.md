# Content Strategy

## Content Types Supported
1. **Plain Text Files** (.txt, .md)
   - Extract title from first line or filename
   - Store file modification date as metadata
   
2. **HTML Files** (.html, .htm)
   - Extract title from `<title>` tag or filename
   - Strip HTML tags, preserve text structure
   - Store file modification date as metadata
   
3. **URLs** (via file lists)
   - Extract title from HTTP response `<title>` tag
   - Store HTTP Last-Modified header or crawl date
   - Handle common content types (text/html, text/plain)

## Content Processing Pipeline
1. **Ingestion**: Read file/URL, extract raw content
2. **Normalization**: Strip whitespace, normalize encoding (UTF-8)
3. **Metadata Extraction**: Title, source, date, content hash (SHA256)
4. **Chunking**: Split into 512-token chunks with 50-token overlap
5. **Vectorization**: Generate embeddings using ChromaDB DefaultEmbeddingFunction
6. **Storage**: Store in ChromaDB with metadata and vector

## Deduplication Rules
- Primary key: `hash` (SHA256 of normalized content)
- If hash exists: log as duplicate, skip import
- If source/title change but hash same: update metadata only
- If hash changes: update content and vectors

## Content Limits
- Max document size: 10MB
- Max documents per import batch: 1000
- Max total documents: 10,000 (configurable)
- Expected dataset: 100s of 2K-10K documents

## Update Strategy
- Incremental updates based on file modification date
- Soft delete: mark as deleted, don't remove vectors
- Resumable imports: checkpoint progress every 100 documents
