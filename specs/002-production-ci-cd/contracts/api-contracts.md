# API Contracts: Production CI/CD and APT Package Building

**Feature**: 002-production-ci-cd  
**Created**: 2025-11-01  
**Status**: Design Complete  

## Overview

This document defines the API contracts, interfaces, and integration points for the production CI/CD infrastructure. These contracts ensure reliable integration between CI/CD components and maintain compatibility with existing 001-local-rag-mvp systems.

## GitHub Actions Workflow Contracts

### Build Workflow Interface

**Workflow**: `.github/workflows/build-packages.yml`

#### Input Contract

```yaml
# Workflow dispatch inputs
inputs:
  architecture:
    type: choice
    required: false
    default: 'all'
    options: ['amd64', 'arm64', 'all']
    description: 'Target architecture for package building'
    
  force_rebuild:
    type: boolean
    required: false
    default: false
    description: 'Force rebuild even if no changes detected'
```

#### Output Contract

```yaml
# Workflow outputs available to dependent workflows
outputs:
  package_amd64_path:
    description: "Path to built AMD64 package"
    value: "artifacts/local-rag_${version}_amd64.deb"
    
  package_arm64_path:
    description: "Path to built ARM64 package"
    value: "artifacts/local-rag_${version}_arm64.deb"
    
  build_success:
    description: "Overall build success status"
    value: ${{ steps.build.outcome == 'success' }}
    
  validation_status:
    description: "Package validation results"
    value: ${{ steps.validate.outputs.status }}
```

#### Environment Contract

```yaml
# Required environment variables
environment:
  required:
    GITHUB_TOKEN: 
      type: string
      description: "GitHub Actions token for artifact access"
      source: "automatic"
      
  optional:
    BUILD_CACHE_KEY:
      type: string
      description: "Custom cache key for dependencies"
      default: "${{ runner.os }}-build-${{ hashFiles('requirements.txt') }}"
      
    PARALLEL_BUILDS:
      type: boolean  
      description: "Enable parallel architecture builds"
      default: true
```

### Release Workflow Interface

**Workflow**: `.github/workflows/release.yml`

#### Trigger Contract

```yaml
# Release workflow triggers
triggers:
  push:
    tags:
      - 'v[0-9]+.[0-9]+.[0-9]+'  # Semantic versioning only
      - 'v[0-9]+.[0-9]+.[0-9]+-*'  # Pre-release tags
      
  workflow_dispatch:
    inputs:
      tag:
        type: string
        required: true
        description: 'Release tag (must match v*.*.* pattern)'
```

#### Output Contract

```yaml
# Release artifacts contract
artifacts:
  packages:
    - name: "${package_name}_${version}_amd64.deb"
      architecture: "amd64"
      content_type: "application/vnd.debian.binary-package"
      required: true
      
    - name: "${package_name}_${version}_arm64.deb"
      architecture: "arm64"
      content_type: "application/vnd.debian.binary-package"
      required: true
      
  signatures:
    - name: "${package_name}_${version}_amd64.deb.asc"
      content_type: "application/pgp-signature"
      required: false  # Optional based on GPG configuration
      
  metadata:
    - name: "checksums.txt"
      content_type: "text/plain"
      required: true
      format: "SHA256 *filename"
```

## Package Building Script Contracts

### Local Build Script Interface

**Script**: `scripts/build-local.sh`

#### Command Line Interface

```bash
# Usage contract
./scripts/build-local.sh [OPTIONS] [ARCHITECTURE]

# Options
--arch ARCH        Target architecture (amd64|arm64|all)
--clean           Clean build environment before building
--validate        Run validation after building
--output DIR      Output directory for packages
--verbose         Enable verbose output
--help           Show help message

# Exit codes
0    Success
1    General error
2    Invalid arguments
3    Build failure
4    Validation failure
```

#### Environment Requirements

```bash
# Required environment for local builds
REQUIRED_TOOLS=(
    "dpkg-buildpackage"
    "lintian" 
    "docker"  # For validation testing
)

OPTIONAL_TOOLS=(
    "qemu-user-static"  # For cross-compilation
    "binfmt-support"    # For QEMU integration
)

# Environment variables
export DEBIAN_FRONTEND=noninteractive
export BUILD_ARCH=${ARCH:-$(dpkg --print-architecture)}
export PACKAGE_NAME="local-rag"
```

#### Output Contract

```bash
# Build artifacts structure
output/
├── local-rag_${version}_${arch}.deb
├── local-rag_${version}_${arch}.deb.buildinfo
├── local-rag_${version}_${arch}.changes
└── validation/
    ├── lintian.log
    ├── installation.log
    └── service-test.log
```

## Package Validation Contracts

### Lintian Validation Interface

#### Configuration Contract

```yaml
# Lintian validation requirements
lintian:
  policy_level: "pedantic"
  
  required_passes:
    - no_errors: true
    - no_warnings: false  # Warnings allowed but logged
    
  suppressed_tags:
    - "package-name-doesnt-match-sonames"  # Not applicable
    
  output_format: "json"
  fail_on: ["error"]
```

#### Results Contract

```json
{
  "package": "local-rag_1.0.0_amd64.deb",
  "validation_timestamp": "2025-11-01T12:00:00Z",
  "policy_version": "4.6.0",
  "results": {
    "errors": 0,
    "warnings": 2,
    "info": 5,
    "experimental": 0
  },
  "tags": [
    {
      "level": "warning",
      "tag": "binary-without-manpage",
      "description": "Binary without manual page"
    }
  ],
  "overall_status": "passed"
}
```

### Installation Testing Interface

#### Test Environment Contract

```yaml
# Installation test requirements
test_environments:
  required:
    - image: "ubuntu:22.04"
      architecture: "amd64"
      
    - image: "ubuntu:22.04" 
      architecture: "arm64"
      platform: "linux/arm64"
      
  optional:
    - image: "debian:12"
      architecture: "amd64"
```

#### Test Sequence Contract

```bash
# Required test sequence
1. Package Installation
   dpkg -i ${package_path}
   apt-get install -f  # Fix dependencies if needed
   
2. Service Verification  
   systemctl --user start local-rag
   systemctl --user is-active local-rag
   
3. Health Check
   timeout 30 curl -f http://localhost:8000/health
   
4. Cleanup
   systemctl --user stop local-rag
   dpkg -r local-rag
```

#### Results Contract

```json
{
  "test_run_id": "test_20251101_120000",
  "package": "local-rag_1.0.0_amd64.deb",
  "environment": "ubuntu:22.04",
  "timestamp": "2025-11-01T12:00:00Z",
  "results": {
    "installation": {
      "status": "passed",
      "duration_seconds": 45,
      "exit_code": 0
    },
    "service_startup": {
      "status": "passed", 
      "duration_seconds": 12,
      "pid": 12345
    },
    "health_check": {
      "status": "passed",
      "response_time_ms": 250,
      "response_code": 200
    }
  },
  "overall_status": "passed"
}
```

## Integration Contracts with Existing Systems

### TDD Workflow Integration

#### Script Integration Contract

```bash
# Integration with existing TDD scripts
scripts/tdd-cycle.sh:
  # Added step: package validation
  post_test_hook: "scripts/build-local.sh --validate"
  
scripts/test-ci-local.sh:
  # Include package building in CI simulation
  additional_steps: ["package_build", "package_validate"]
```

#### Performance Contract

```yaml
# Performance requirements for TDD integration
performance:
  local_build_time:
    max_seconds: 300  # 5 minutes for local builds
    target_seconds: 180  # 3 minutes target
    
  validation_time:
    max_seconds: 120  # 2 minutes for validation
    target_seconds: 60  # 1 minute target
    
  total_tdd_overhead:
    max_percent: 25  # Max 25% increase in TDD cycle time
```

### Existing Service Integration

#### Systemd Service Contract

```ini
# Integration with existing config/local-rag.service
[Unit]
Description=Local RAG Service
After=network.target

[Service]
Type=simple
User=local-rag
Group=local-rag
WorkingDirectory=/opt/local-rag
ExecStart=/opt/local-rag/bin/local-rag
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Configuration Compatibility

```yaml
# Configuration file compatibility requirements
compatibility:
  config_formats:
    - yaml: "local-rag.yaml"  # Primary configuration
    - env: ".env"  # Environment overrides
    
  config_locations:
    system: "/etc/local-rag/"
    user: "~/.config/local-rag/"
    application: "/opt/local-rag/config/"
    
  migration_strategy: "backward_compatible"
```

## Error Handling Contracts

### Build Failure Interface

#### Error Categories

```yaml
# Standardized error categories and codes
error_categories:
  build_errors:
    code_range: [1000, 1999]
    examples:
      1001: "Dependency resolution failed"
      1002: "Compilation error"
      1003: "Cross-compilation setup failed"
      
  validation_errors:
    code_range: [2000, 2999]
    examples:
      2001: "Lintian policy violation"
      2002: "Installation test failed"
      2003: "Service startup failed"
      
  infrastructure_errors:
    code_range: [3000, 3999]
    examples:
      3001: "GitHub Actions runner failure"
      3002: "Artifact storage failure"
      3003: "Network connectivity issue"
```

#### Error Response Format

```json
{
  "error": {
    "code": 2002,
    "category": "validation_errors",
    "message": "Package installation test failed",
    "details": {
      "package": "local-rag_1.0.0_arm64.deb",
      "environment": "ubuntu:22.04",
      "command": "dpkg -i local-rag_1.0.0_arm64.deb",
      "exit_code": 1,
      "stderr": "dependency problems prevent configuration"
    },
    "timestamp": "2025-11-01T12:00:00Z",
    "context": {
      "workflow_run": "123456789",
      "job": "build-arm64",
      "step": "validate-package"
    }
  }
}
```

### Retry and Recovery Contracts

#### Retry Policy

```yaml
# Retry behavior for different failure types
retry_policies:
  transient_failures:
    max_retries: 3
    backoff: "exponential"
    base_delay: 5  # seconds
    max_delay: 60  # seconds
    
  infrastructure_failures:
    max_retries: 2
    backoff: "linear"
    delay: 30  # seconds
    
  validation_failures:
    max_retries: 1  # Limited retries for deterministic failures
```

## Monitoring and Observability Contracts

### Metrics Interface

#### Prometheus Metrics Contract

```yaml
# Required metrics for monitoring
metrics:
  - name: "cicd_build_duration_seconds"
    type: "histogram"
    labels: ["architecture", "result", "branch"]
    description: "Time taken to build packages"
    
  - name: "cicd_validation_result"
    type: "counter"
    labels: ["validation_type", "result", "architecture"]
    description: "Package validation results"
    
  - name: "cicd_artifact_size_bytes"
    type: "gauge"
    labels: ["architecture", "package_name"]
    description: "Size of generated packages"
```

#### Health Check Interface

```yaml
# Health check endpoints for CI/CD monitoring
health_checks:
  build_pipeline:
    endpoint: "GET /github/actions/status"
    expected_response: 200
    timeout_seconds: 10
    
  artifact_storage:
    endpoint: "HEAD /artifacts/latest"
    expected_response: 200
    timeout_seconds: 5
```

## Versioning and Compatibility

### API Version Contract

```yaml
# Contract versioning strategy
api_version: "v1"

compatibility:
  backward_compatible_changes:
    - Adding optional parameters
    - Adding optional response fields
    - Adding new error codes
    
  breaking_changes:
    - Removing required parameters
    - Changing response structure
    - Modifying error code meanings
    
versioning_strategy: "semantic"  # Major.Minor.Patch
```

### Migration Contract

```yaml
# Migration support for contract changes
migration:
  deprecation_period: "90 days"
  
  notification_methods:
    - GitHub issue
    - Documentation update
    - Workflow warnings
    
  backward_compatibility: "one_major_version"
```

This comprehensive contract specification ensures reliable integration between all CI/CD components while maintaining compatibility with the existing 001-local-rag-mvp foundation and providing clear upgrade paths for future enhancements.
