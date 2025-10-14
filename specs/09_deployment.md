# Deployment Strategy

## Target Environment
- **Hardware**: Raspberry Pi 5 (8GB RAM recommended)
- **OS**: Debian 12 (Bookworm) ARM64
- **Storage**: 64GB+ microSD (Class 10 or better)
- **Network**: WiFi or Ethernet (for initial setup only)

## APT Package Deployment
- **Package Format**: Debian (.deb) package for ARM64 and AMD64
- **Installation**: Single command `sudo apt install ./local-rag.deb`
- **Service Management**: systemd service for lifecycle management
- **Dependencies**: Automatically handled via APT package dependencies
- **Configuration**: `/etc/local-rag/config.yaml`
- **Data Storage**: 
  - `/var/lib/local-rag/chromadb/`: ChromaDB database files
  - `/var/lib/local-rag/content/`: Source content files
  - `/var/lib/local-rag/models/`: LLM model files
- **Logs**: systemd journal + optional file output in `/var/log/local-rag/`

## Installation Process
1. **Prerequisites**: None (dependencies handled by APT)
2. **Download Package**: Download latest `.deb` file for your architecture (ARM64 for Pi5, AMD64 for x86)
3. **Install**: `sudo apt install ./local-rag_1.0.0_arm64.deb`
4. **Model Setup**: Download LLM model files
   - Models stored in `/var/lib/local-rag/models/`
   - Default: DeepSeek-R1-distill-qwen 1.5B GGUF format (Q4 quantized)
   - Use `local-rag download-model deepseek-r1-distill-qwen-1.5b` command
5. **Configuration**: Edit `/etc/local-rag/config.yaml` if needed
6. **Service Start**: `sudo systemctl enable --now local-rag`
7. **Verification**: `curl http://localhost:8080/health` or `local-rag status`

## Resource Requirements
- **RAM**: 6GB minimum, 8GB recommended (for 1.5B parameter model + ChromaDB + OS overhead)
- **Storage**: 8GB for application, 4GB for model, 16GB+ for content/vectors in ChromaDB
- **CPU**: All 4 cores for LLM inference via llama-cpp-python (ChromaDB operations use minimal CPU)
- **Power**: 5V/5A PSU recommended for sustained CPU load during inference
- **Dependencies**: None (self-contained deployment)

## Security Considerations
- No external network access required after setup
- Data stored locally on device in `/var/lib/local-rag/`
- Web UI accessible only on local network (localhost:8080)
- No user authentication (single-user device)
- Standard Unix file permissions for data protection
- systemd service runs as dedicated `local-rag` user (non-root)

## Service Management
- **Start**: `sudo systemctl start local-rag`
- **Stop**: `sudo systemctl stop local-rag`
- **Enable on boot**: `sudo systemctl enable local-rag`
- **Status**: `sudo systemctl status local-rag`
- **Logs**: `sudo journalctl -u local-rag -f`
- **Configuration reload**: `sudo systemctl reload local-rag`

## Monitoring & Maintenance
- Log rotation via systemd journal (default retention)
- Health check endpoint: `GET /health`
- Status command: `local-rag status`
- Automatic restart on failure (systemd RestartSec=10)
- Manual backup/restore: `local-rag backup/restore` commands

## CI/CD and Automation

### GitHub Actions Workflows

#### 1. Pull Request Validation (`pr-validation.yml`)
- **Triggers**: Pull requests to main branch
- **Jobs**:
  - **Code Quality** (parallel):
    - Python linting (flake8, black, isort)
    - Type checking (mypy)
    - Security scanning (bandit, safety)
  - **Testing** (parallel):
    - Unit tests with coverage (pytest)
    - Integration tests with mocked dependencies
    - API endpoint validation
  - **Build Validation** (parallel):
    - APT package build test (both architectures)
    - Python compilation validation
    - Configuration schema validation

#### 2. Automated Builds (`build-packages.yml`)
- **Triggers**: 
  - Push to main branch
  - Release tags (v*)
  - Manual dispatch
- **Matrix Strategy**: ARM64, AMD64 architectures
- **Build Steps**:
  1. Environment setup with Python 3.11
  2. Dependency installation and caching
  3. Source code compilation and validation
  4. APT package creation with `dpkg-buildpackage`
  5. Package testing in clean containers
  6. Artifact upload to GitHub Releases

#### 3. Release Management (`release.yml`)
- **Triggers**: Release tag creation (v*)
- **Automated Tasks**:
  - APT package generation for both architectures
  - GitHub Release creation with changelog
  - Package signing with GPG keys
  - Upload to custom APT repository
  - Documentation deployment

### APT Package Build Process

#### Package Structure
```
local-rag_1.0.0-1_arm64.deb
├── DEBIAN/
│   ├── control          # Package metadata
│   ├── postinst         # Post-installation script
│   ├── prerm           # Pre-removal script
│   └── postrm          # Post-removal script
├── usr/
│   ├── local/
│   │   └── bin/
│   │       └── local-rag*    # Main executable
│   └── lib/
│       └── python3.11/
│           └── site-packages/
│               └── guide/    # Application code
├── etc/
│   ├── local-rag/
│   │   └── config.yaml       # Default configuration
│   └── systemd/
│       └── system/
│           └── local-rag.service
└── var/
    └── lib/
        └── local-rag/       # Data directory
```

#### Build Dependencies
- **Build Tools**: `build-essential`, `debhelper`, `dh-python`
- **Python**: `python3.11-dev`, `python3-pip`, `python3-venv`
- **System**: `pkg-config`, `cmake` (for llama-cpp-python)

#### Package Validation
- **Lintian**: Debian package policy compliance
- **Package Testing**: Installation/removal in clean containers
- **Service Validation**: systemd service start/stop functionality

### Automated Testing Strategy

#### 1. Unit Test Automation
- **Framework**: pytest with coverage reporting
- **Coverage Threshold**: Minimum 80% code coverage
- **Mock Strategy**: External dependencies (LLM models, vector DB)
- **Execution**: Parallel testing with pytest-xdist
- **Coverage Reports**: Uploaded to codecov.io

#### 2. Integration Test Pipeline
- **Container Testing**: Docker-based test environments
- **Service Validation**: systemd service lifecycle testing
- **API Testing**: FastAPI endpoint functionality
- **Cross-Architecture**: ARM64 emulation via QEMU

#### 3. Quality Gates
- **Pre-Merge Requirements**:
  1. All tests pass with 80%+ coverage
  2. Security scan shows no high-severity issues
  3. Package builds succeed for both architectures
  4. Code quality meets formatting standards
  5. Configuration schema validation passes

### Repository and Distribution

#### Custom APT Repository
- **Hosting**: GitHub Pages with APT repository structure
- **GPG Signing**: Package integrity and authenticity
- **Release Channels**: 
  - `stable`: Tagged releases only
  - `testing`: Main branch automatic builds

#### Installation Instructions
```bash
# Add repository GPG key
curl -fsSL https://username.github.io/local-rag-apt/gpg | sudo gpg --dearmor -o /usr/share/keyrings/local-rag.gpg

# Add repository source
echo "deb [signed-by=/usr/share/keyrings/local-rag.gpg] https://username.github.io/local-rag-apt stable main" | sudo tee /etc/apt/sources.list.d/local-rag.list

# Install package
sudo apt update
sudo apt install local-rag
```

### Automation Scripts

#### Local CI Testing
- **Script**: `scripts/test-ci-local.sh`
- **Purpose**: Full CI simulation locally before push
- **Stages**: Lint → Security → Build → Test → Package

#### Quick Testing
- **Script**: `scripts/test-quick.sh`
- **Purpose**: Fast feedback during development
- **Checks**: Format → Syntax → Import → Basic functionality

### Monitoring and Alerting
- **Build Status**: GitHub status checks block PR merging
- **Security Alerts**: Dependabot for dependency vulnerabilities
- **Release Notifications**: Automatic changelog generation
