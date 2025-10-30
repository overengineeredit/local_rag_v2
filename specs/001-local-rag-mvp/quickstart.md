# Quickstart Guide: Local RAG System

**Branch**: `001-local-rag-mvp` | **Date**: 2025-10-28
**Target Users**: Developers, System Administrators, End Users

## Prerequisites

### System Requirements

- **Hardware**: Raspberry Pi 5 (4GB+ RAM) or AMD64 Linux system (4GB+ RAM)
- **OS**: Ubuntu 22.04 LTS, Debian 12, or compatible APT-based distribution
- **Storage**: 10GB+ available space (more for large document collections)
- **Network**: Internet connection for initial installation and model download

### Dependencies (Auto-installed)

- Python 3.11+
- SystemD (for service management)
- APT package manager

## Installation

### Quick Install (Recommended)

```bash
# Download and install the latest release
wget https://github.com/overengineeredit/local_rag_v2/releases/latest/download/local-rag_1.0.0_arm64.deb
sudo apt install ./local-rag_1.0.0_arm64.deb

# For AMD64 systems:
# wget https://github.com/overengineeredit/local_rag_v2/releases/latest/download/local-rag_1.0.0_amd64.deb
# sudo apt install ./local-rag_1.0.0_amd64.deb
```

### Configuration

The default configuration is located at `/etc/local-rag/config.yaml`:

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

### Model Download

Download a compatible GGUF model (example using a small efficient model):

```bash
# Create models directory if not exists
sudo mkdir -p /var/lib/local-rag/models

# Download a small, efficient model (adjust URL for your preferred model)
sudo wget -O /var/lib/local-rag/models/deepseek-r1-distill-qwen-1.5b.Q4_K_M.gguf \
  "https://huggingface.co/microsoft/DeepSeek-R1-Distill-Qwen-1.5B-GGUF/resolve/main/deepseek-r1-distill-qwen-1.5b.Q4_K_M.gguf"

# Set proper ownership
sudo chown -R local-rag:local-rag /var/lib/local-rag/
```

## Service Management

### Start the Service

```bash
# Enable and start the service
sudo systemctl enable local-rag
sudo systemctl start local-rag

# Check service status
sudo systemctl status local-rag
```

### Verify Installation

```bash
# Check if the API is responding
curl http://localhost:8080/health

# Expected response:
# {"status":"healthy","components":{"llm":{"status":"healthy"},"vector_db":{"status":"healthy"},"api":{"status":"healthy"}},"timestamp":"2025-10-28T10:30:00Z"}
```

### Access Web Interface

Open your web browser and navigate to: <http://localhost:8080>

## Basic Usage

### Command Line Interface

The system includes a comprehensive CLI for content management:

```bash
# Import a document
local-rag import --file /path/to/document.txt

# Import from URL
local-rag import --url https://example.com/article.html

# Batch import from folder
local-rag import --folder /path/to/documents/

# Check for updates without re-importing
local-rag check-updates

# List all documents with update status
local-rag list --show-updates

# Update only sources that have changed
local-rag update --changed-only

# Force update specific source
local-rag update --source https://example.com/article.html --force

# Ask a question
local-rag query "What is the main topic of the uploaded documents?"

# Check system health
local-rag health

# Reset the knowledge base (removes all documents)
local-rag reset --confirm
```

### Web Interface Usage

1. **Navigate to <http://localhost:8080>** in your browser
2. **Upload Documents**: Use the upload form to add text files, HTML files, or enter URLs
3. **Ask Questions**: Type your question in the query box
4. **View Responses**: Watch as the AI generates streaming responses based on your documents
5. **Manage Content**: View, update, or delete documents through the management interface

### API Integration

For programmatic access, use the REST API:

```bash
# Upload a document
curl -X POST -F "file=@document.txt" http://localhost:8080/documents

# Submit a query
curl -X POST -H "Content-Type: application/json" \
  -d '{"text":"What is machine learning?"}' \
  http://localhost:8080/query

# List documents with status filtering
curl "http://localhost:8080/documents?status=active"

# Check for content updates
curl -X POST -H "Content-Type: application/json" \
  -d '{}' \
  http://localhost:8080/documents/check-updates

# Update sources with changes
curl -X POST -H "Content-Type: application/json" \
  -d '{"force_update": false}' \
  http://localhost:8080/documents/update-sources
```

## First Steps Tutorial

### 1. Upload Your First Document

Create a sample document:

```bash
cat > ~/sample.txt << EOF
Local RAG systems enable private, offline question-answering using your own documents.
They combine retrieval-augmented generation with local language models.
This approach ensures data privacy while providing intelligent document search capabilities.
The system can process various file formats including text, HTML, and web URLs.
EOF
```

Upload it via CLI:

```bash
local-rag import --file ~/sample.txt --title "RAG Introduction"
```

### 2. Ask Your First Question

```bash
local-rag query "What are the benefits of local RAG systems?"
```

Expected response should reference data privacy and offline capabilities from your uploaded document.

### 3. Explore the Web Interface

1. Visit <http://localhost:8080>
2. Try uploading another document through the web interface
3. Ask questions and observe the streaming response
4. Check the document management section

## Performance Optimization

### Raspberry Pi 5 Specific

```bash
# Optimize for Pi5 - edit config file
sudo nano /etc/local-rag/config.yaml

# Recommended Pi5 settings:
llm:
  threads: 4          # Use all 4 cores
  context_size: 1024  # Smaller context for memory efficiency
  max_tokens: 256     # Shorter responses to reduce processing time

# Restart service after changes
sudo systemctl restart local-rag
```

### Memory Management

Monitor memory usage:

```bash
# Check system memory
free -h

# Check local-rag memory usage
sudo systemctl status local-rag

# View logs for memory warnings
sudo journalctl -u local-rag -f
```

## Troubleshooting

### Common Issues

**Service won't start:**

```bash
# Check logs
sudo journalctl -u local-rag -n 50

# Common causes:
# - Model file not found or corrupted
# - Insufficient memory
# - Port 8080 already in use
```

**Slow responses:**

- Reduce `context_size` and `max_tokens` in config
- Ensure sufficient RAM available
- Consider using a smaller/quantized model

**Import failures:**

```bash
# Check file permissions
ls -la /var/lib/local-rag/

# Check disk space
df -h /var/lib/local-rag/

# View detailed error logs
sudo tail -f /var/log/local-rag/app.log
```

### Getting Help

- **Logs**: `/var/log/local-rag/app.log`
- **Configuration**: `/etc/local-rag/config.yaml`
- **Data Directory**: `/var/lib/local-rag/`
- **Service Status**: `sudo systemctl status local-rag`

### Health Monitoring

```bash
# Automated health check
local-rag health --json

# Monitor service continuously
watch -n 5 'curl -s http://localhost:8080/health | jq'
```

## Next Steps

1. **Import your document collection** using batch import
2. **Customize the configuration** for your hardware and use case
3. **Explore API integration** for custom applications
4. **Set up monitoring** and log rotation for production use
5. **Backup your data** (`/var/lib/local-rag/`) regularly

## Security Considerations

- **Network Access**: By default, the service only binds to localhost (127.0.0.1)
- **File Permissions**: Ensure proper ownership of data directories
- **Model Security**: Only use trusted GGUF model files
- **Input Validation**: All user inputs are validated and sanitized

For production deployments, consider:

- Setting up reverse proxy with HTTPS
- Implementing rate limiting
- Regular security updates via APT package manager
