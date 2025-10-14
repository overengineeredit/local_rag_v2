# Configuration Management

## Environment Variables
- `CONFIG_PATH`: Path to configuration file (default: /etc/local-rag/config.yaml)
- `DATA_DIR`: Data directory path (default: /var/lib/local-rag)
- `LOG_LEVEL`: Logging level (default: INFO)
- `API_HOST`: FastAPI bind address (default: 127.0.0.1)
- `API_PORT`: FastAPI port (default: 8080)
- `QUANTIZATION_FORMAT`: INT4, INT8, or FP16 (default: INT4)
- `LLM_MODEL_PATH`: Path to GGUF model file (default: /var/lib/local-rag/models/deepseek-r1-distill-qwen-1.5b.Q4_K_M.gguf)
- `LLM_CONTEXT_SIZE`: Context window size for llama-cpp-python (default: 2048)
- `LLM_N_THREADS`: Number of CPU threads for inference (default: 4)
- `LLM_N_GPU_LAYERS`: Number of layers to offload to GPU (default: 0, CPU only)
- `LLM_TEMPERATURE`: Sampling temperature (default: 0.7)
- `LLM_TOP_P`: Top-p sampling (default: 0.9)
- `MAX_RAM_MB`: Maximum RAM usage in MB (default: 8192, 6144 minimum for Pi5)
- `MAX_DISK_GB`: Maximum disk usage in GB (default: 32)
- `LOG_TO_FILE`: true/false (default: true)
- `LOG_ROTATION_SIZE_MB`: Log file rotation size (default: 100)
- `CHROMADB_PATH`: ChromaDB database file path (default: /var/lib/local-rag/chromadb)
- `LLM_MODEL`: Model name identifier (default: deepseek-r1-distill-qwen-1.5b)
- `CHUNK_SIZE`: Content chunk size for vectorization (default: 512)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 50)
- `MAX_CONTEXT_LENGTH`: Max context for LLM (default: 1MB)

## Configuration Files
- `/etc/local-rag/config.yaml`: Main configuration file
- `/etc/local-rag/models.json`: Available LLM models and their specs
- `/etc/local-rag/logging.yaml`: Logging configuration

## CLI Commands (via installed package)
- `local-rag status`: Check service status and health
- `local-rag reset-db`: Reset ChromaDB database
- `local-rag import <path>`: Import content from file or directory
- `local-rag download-model <model>`: Download and install LLM model
- `local-rag backup <path>`: Backup data to specified path
- `local-rag restore <path>`: Restore data from backup
- All CLI commands integrate with systemd service and provide user-friendly output

## APT Package Configuration
- Debian package with proper dependencies
- systemd service unit file
- Postinstall scripts for user/directory creation
- Configuration templates and defaults
