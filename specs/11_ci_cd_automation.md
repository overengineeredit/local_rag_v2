# CI/CD and Automation Strategy

## Overview
This document defines the Continuous Integration and Continuous Deployment (CI/CD) strategy for the Local RAG system, focusing on automated builds for APT packages rather than Docker containers, and comprehensive test automation integrated with GitHub's pull request workflow.

## CI/CD Pipeline Architecture

### Pipeline Stages
1. **Code Quality & Security** (Parallel)
2. **Testing** (Unit + Integration)
3. **Build Validation** (APT Package Generation)
4. **Release Management** (Automated Deployment)

### Trigger Events
- **Pull Requests**: Full validation pipeline
- **Main Branch Push**: Build + Test + Package creation
- **Release Tags**: Full deployment pipeline
- **Manual Dispatch**: On-demand builds

## GitHub Actions Workflows

### 1. Pull Request Validation (`pr-validation.yml`)

#### Triggers
```yaml
on:
  pull_request:
    branches: [main]
    paths-ignore: ['docs/**', '*.md']
```

#### Jobs Matrix
```yaml
strategy:
  matrix:
    python-version: ['3.11']
    architecture: ['ubuntu-latest']  # AMD64 for PR validation
```

#### Job Definitions

##### Code Quality Job
- **Linting**: flake8 with configuration for Python 3.11
- **Formatting**: black --check with line length 100
- **Import Sorting**: isort --check-only with profile black
- **Type Checking**: mypy with strict mode enabled
- **Documentation**: Ensure docstrings meet Google style

##### Security Job
- **Security Scanning**: bandit for security anti-patterns
- **Dependency Check**: safety for known vulnerabilities  
- **License Compliance**: pip-licenses for license validation
- **SAST**: CodeQL for static application security testing

##### Testing Job
- **Unit Tests**: pytest with coverage reporting
- **Integration Tests**: Mock-based tests for external dependencies
- **API Tests**: FastAPI TestClient for endpoint validation
- **Configuration Tests**: Schema validation for YAML/TOML configs

##### Build Validation Job
- **Python Compilation**: py_compile for syntax validation
- **Package Creation**: Test APT package build process
- **Dependency Resolution**: Verify requirements.txt consistency
- **Service Validation**: systemd service file syntax check

### 2. Automated Package Builds (`build-packages.yml`)

#### Triggers
```yaml
on:
  push:
    branches: [main]
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      architecture:
        description: 'Architecture to build'
        required: true
        default: 'both'
        type: choice
        options: ['arm64', 'amd64', 'both']
```

#### Build Matrix Strategy
```yaml
strategy:
  matrix:
    include:
      - architecture: arm64
        runner: ubuntu-latest
        cross-compile: true
      - architecture: amd64  
        runner: ubuntu-latest
        cross-compile: false
```

#### Build Steps

##### Environment Setup
- Ubuntu 22.04 with Python 3.11
- Cross-compilation tools for ARM64 (when needed)
- APT package development tools
- Caching for pip dependencies and build artifacts

##### Source Preparation
- Checkout source code with full history
- Version detection from git tags
- Source tarball creation for Debian packaging
- Dependency installation and validation

##### APT Package Build
```bash
# Install build dependencies
sudo apt-get update
sudo apt-get install -y build-essential debhelper dh-python python3.11-dev

# Create source package
python3 setup.py sdist

# Build binary package
dpkg-buildpackage -b -uc -us --host-arch=$ARCH

# Validate package
lintian ../local-rag_*.deb
```

##### Quality Assurance
- Package installation test in clean container
- Service start/stop functionality validation
- Basic smoke tests for core functionality
- Package metadata validation

##### Artifact Management
- Upload packages to GitHub Actions artifacts
- Retention: 90 days for branch builds, permanent for releases
- Naming: `local-rag_{version}_{architecture}.deb`

### 3. Release Management (`release.yml`)

#### Triggers
```yaml
on:
  release:
    types: [published]
```

#### Release Pipeline

##### Package Publication
- Download build artifacts from successful builds
- GPG signing of packages with release key
- Upload to GitHub release assets
- Update custom APT repository index

##### Documentation Deployment
- Generate API documentation with Sphinx
- Build user documentation with MkDocs
- Deploy to GitHub Pages
- Update package installation instructions

##### Notification and Verification
- Slack/Discord notification for successful releases
- Automated testing of published packages
- Update package repository metadata
- Generate release changelog from commit history

## APT Package Build Process

### Package Specifications

#### Control File (`debian/control`)
```
Source: local-rag
Section: misc
Priority: optional
Maintainer: Local RAG Team <email@domain.com>
Build-Depends: debhelper (>= 11), python3.11-dev, python3-pip
Standards-Version: 4.5.1

Package: local-rag
Architecture: any
Depends: python3.11, python3-pip, systemd, ${python3:Depends}
Description: Local RAG system for document question answering
 A CPU-optimized RAG system using ChromaDB and llama-cpp-python
 for local document question answering without external dependencies.
```

#### Installation Scripts

##### Post-Installation (`debian/postinst`)
```bash
#!/bin/bash
set -e

# Create local-rag user
useradd --system --home /var/lib/local-rag --shell /bin/false local-rag || true

# Create directories
mkdir -p /var/lib/local-rag/{content,models,chromadb}
mkdir -p /var/log/local-rag
mkdir -p /etc/local-rag

# Set permissions
chown -R local-rag:local-rag /var/lib/local-rag
chown -R local-rag:local-rag /var/log/local-rag

# Install Python dependencies
pip3 install --system /usr/local/lib/local-rag/requirements.txt

# Enable and start service
systemctl daemon-reload
systemctl enable local-rag
systemctl start local-rag
```

#### Service Configuration
```ini
[Unit]
Description=Local RAG System
After=network.target
Wants=network.target

[Service]
Type=exec
User=local-rag
Group=local-rag
ExecStart=/usr/local/bin/local-rag serve
WorkingDirectory=/var/lib/local-rag
Environment=LOCAL_RAG_CONFIG=/etc/local-rag/config.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Cross-Architecture Support

#### ARM64 Build on AMD64
- QEMU user emulation for cross-compilation
- Cross-compiler toolchain setup
- Native library compilation for target architecture
- Package validation in ARM64 emulated environment

#### Build Optimization
- Parallel compilation with all available cores
- ccache for C/C++ compilation caching
- pip cache for Python package downloads
- Docker layer caching for consistent environments

## Testing Automation

### Test Categories

#### Unit Tests
- **Framework**: pytest with coverage
- **Scope**: Individual functions and classes
- **Mocking**: External dependencies (LLM models, ChromaDB)
- **Coverage Target**: 80% minimum, 90% preferred
- **Execution Time**: <2 minutes

#### Integration Tests  
- **Framework**: pytest with Docker containers
- **Scope**: Component interaction testing
- **Real Dependencies**: Embedded ChromaDB, mock LLM
- **Test Data**: Predefined document sets
- **Execution Time**: <5 minutes

#### System Tests
- **Framework**: pytest with systemd
- **Scope**: Full application workflow
- **Environment**: Clean container with APT package
- **Validation**: Service lifecycle, API responses
- **Execution Time**: <10 minutes

#### Performance Tests
- **Framework**: pytest-benchmark
- **Scope**: Query response times, memory usage
- **Benchmarks**: Document ingestion, query processing
- **Thresholds**: <5s query response, <2GB memory
- **Execution**: Optional on PRs, required for releases

### Test Execution Strategy

#### Parallel Execution
- Test categories run in parallel jobs
- Within categories, parallel test execution
- Hardware constraints considered for Pi5 emulation

#### Test Data Management
- Shared test document corpus
- Deterministic test scenarios
- Version-controlled test data sets
- Cleanup after test execution

#### Failure Handling
- Immediate failure reporting to PR status
- Test artifact collection (logs, dumps)
- Retry mechanism for flaky tests
- Quarantine for consistently failing tests

## Quality Gates and Automation

### Pre-Merge Requirements

#### Automated Checks (Blocking)
1. **All tests pass** with coverage threshold
2. **Security scan** shows no high/critical vulnerabilities  
3. **Package build** succeeds for target architectures
4. **Code quality** meets linting and formatting standards
5. **Documentation** builds without errors

#### Manual Review Requirements
- Code review by maintainer
- Architecture changes require design review
- Security-sensitive changes require security review

### Automated Code Maintenance

#### Dependency Management
- **Dependabot**: Automated dependency updates
- **Security Patches**: Automatic security update PRs
- **Version Pinning**: Controlled dependency upgrades
- **License Compliance**: Automated license checking

#### Code Quality Enforcement
- **Automatic Formatting**: Pre-commit hooks for black/isort
- **Import Organization**: Automated import sorting
- **Documentation**: Automated docstring validation
- **Type Hints**: Enforcement of type annotations

### Performance Monitoring

#### Build Performance
- Pipeline execution time tracking
- Build cache hit rate monitoring
- Resource usage during builds
- Historical performance trending

#### Package Quality Metrics
- Package size monitoring and alerting
- Installation time benchmarking  
- Service startup time measurement
- Memory usage profiling

## Repository and Distribution

### Custom APT Repository

#### Repository Structure
```
apt-repo/
├── dists/
│   └── stable/
│       ├── Release
│       ├── Release.gpg
│       └── main/
│           └── binary-arm64/
│               ├── Packages
│               ├── Packages.gz
│               └── Release
├── pool/
│   └── main/
│       └── l/
│           └── local-rag/
│               ├── local-rag_1.0.0-1_arm64.deb
│               └── local-rag_1.0.0-1_amd64.deb
└── gpg/
    └── public.key
```

#### Repository Management
- **Automated Updates**: Package uploads trigger index updates
- **GPG Signing**: All packages and repository metadata signed
- **Multi-Architecture**: Separate binary indexes for each architecture
- **CDN Distribution**: GitHub Pages for global distribution

#### Installation Documentation
- **Repository Setup**: One-time GPG key and source configuration
- **Package Installation**: Standard APT workflow
- **Version Management**: Stable/testing channel selection
- **Troubleshooting**: Common installation issues and solutions

### Release Channels

#### Stable Channel
- **Source**: Tagged releases only (v1.0.0, v1.1.0, etc.)
- **Testing**: Full test suite + manual validation
- **Support**: Long-term support and security updates
- **Frequency**: Monthly or feature-driven releases

#### Testing Channel  
- **Source**: Main branch automatic builds
- **Testing**: Automated test suite only
- **Purpose**: Early access to features
- **Frequency**: Every main branch commit

## Monitoring and Alerting

### Build Monitoring
- **GitHub Status Checks**: PR blocking for failed builds
- **Build Duration**: Alert on unusually long builds
- **Success Rate**: Historical build success rate tracking
- **Resource Usage**: Build resource consumption monitoring

### Security Monitoring
- **Vulnerability Scanning**: Daily scans of dependencies
- **Security Advisories**: Automated tracking of security issues
- **Compliance**: License and security policy compliance
- **Incident Response**: Automated security incident workflow

### Performance Alerting
- **Package Size**: Alert on significant size increases
- **Test Performance**: Alert on performance regression
- **Service Health**: Monitoring of deployed package health
- **User Feedback**: Integration with issue tracking for user reports

## Development Workflow Integration

### Local Development
- **Pre-commit Hooks**: Automated code quality checks
- **Local Testing**: Scripts for full CI simulation
- **Quick Feedback**: Fast local test suite for development
- **Environment Setup**: Automated development environment setup

### Contribution Process
1. **Fork and Branch**: Standard GitHub flow
2. **Local Testing**: `scripts/test-quick.sh` for rapid feedback
3. **Full Validation**: `scripts/test-ci-local.sh` before push
4. **Pull Request**: Automated CI validation
5. **Review and Merge**: Manual review + automated merge

### Release Process
1. **Version Tagging**: Semantic versioning (v1.0.0)
2. **Automated Building**: Multi-architecture package creation
3. **Testing**: Full validation in clean environments
4. **Publication**: Repository update and documentation
5. **Notification**: Release announcements and changelogs