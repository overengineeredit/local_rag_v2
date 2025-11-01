# Quick Start: Production CI/CD and APT Package Building

**Feature**: 002-production-ci-cd  
**Created**: 2025-11-01  
**Prerequisites**: Completed 001-local-rag-mvp feature  

## Overview

This guide provides a fast-track approach to implementing production CI/CD infrastructure for automated APT package building. Follow this guide if you need to quickly establish package building capabilities for ARM64 and AMD64 architectures.

## Prerequisites Check

Before starting, ensure you have:

- [ ] **Completed MVP**: 001-local-rag-mvp feature fully implemented and tested
- [ ] **GitHub Repository**: With Actions enabled and appropriate permissions
- [ ] **Debian Packaging**: Existing `packaging/debian/` structure in place
- [ ] **Test Coverage**: 90%+ test coverage maintained from MVP phase
- [ ] **Hardware Access**: ARM64 device (Pi5) for final validation testing

## Critical Path Implementation

### Phase 1: Minimum Viable CI/CD (Week 1)

**Goal**: Get automated package building working for both architectures

#### Day 1-2: Core Build Workflow

1. **Create Build Workflow**:
   ```bash
   mkdir -p .github/workflows
   # Create build-packages.yml with matrix strategy
   ```

2. **Key Components to Implement**:
   - Build matrix for `[ubuntu-latest]` runner with `strategy.matrix.arch: [amd64, arm64]`
   - QEMU setup for ARM64 cross-compilation
   - dpkg-buildpackage execution with architecture flags
   - Basic artifact upload

3. **Validation**:
   - Packages build without errors
   - Both architectures produce installable .deb files
   - Build completes within 30 minutes

#### Day 3-5: Package Validation

1. **Implement lintian Validation**:
   ```bash
   # Add to workflow
   sudo apt-get install lintian
   lintian --check *.deb
   ```

2. **Basic Installation Testing**:
   - Container-based clean environment testing
   - Service startup verification
   - Health check validation

3. **Validation**:
   - lintian reports no errors
   - Packages install successfully in clean Ubuntu 22.04
   - Service starts and passes basic health checks

### Phase 2: Local Development Support (Days 6-7)

**Goal**: Enable developers to test builds locally

#### Quick Local Build Script

Create `scripts/build-local.sh`:

```bash
#!/bin/bash
# Quick local package building
set -e

ARCH=${1:-amd64}
echo "Building for architecture: $ARCH"

# Setup cross-compilation if needed
if [ "$ARCH" = "arm64" ] && [ "$(uname -m)" = "x86_64" ]; then
    echo "Setting up QEMU for cross-compilation..."
    sudo apt-get update
    sudo apt-get install -y qemu-user-static binfmt-support
fi

# Build package
dpkg-buildpackage -us -uc -a$ARCH

# Basic validation
if command -v lintian >/dev/null; then
    echo "Running lintian validation..."
    lintian ../*.deb
fi

echo "Build completed successfully for $ARCH"
```

### Phase 3: Essential Release Automation (Optional, Week 2)

**Goal**: Automated releases for tagged versions

#### Minimal Release Workflow

If release automation is needed immediately:

1. **Create `.github/workflows/release.yml`**:
   - Trigger on tag creation (`refs/tags/v*`)
   - Build packages using existing workflow
   - Create GitHub release with packages as assets

2. **Version Tagging Strategy**:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

## Fast Implementation Checklist

### Week 1 Essentials
- [ ] **T036**: Basic GitHub Actions build workflow operational
- [ ] **T037**: Cross-compilation working for ARM64
- [ ] **T038**: Package validation with lintian passing
- [ ] **T039**: Local build script available for developers

### Week 2 Production-Ready (Optional)
- [ ] **T040**: Release workflow for tagged versions
- [ ] **T041**: GPG signing (can be added later)
- [ ] **T042**: Basic installation documentation

## Common Pitfalls and Solutions

### Build Issues

**Problem**: Cross-compilation fails with dependency errors  
**Solution**: Use `--host-arch` flag and ensure build-essential is available for target architecture

**Problem**: QEMU emulation is slow  
**Solution**: Acceptable for CI/CD - optimize later; priority is functional builds

**Problem**: Package installation fails  
**Solution**: Check systemd service dependencies and file permissions in `packaging/debian/`

### GitHub Actions Issues

**Problem**: Runner out of disk space  
**Solution**: Clean up unnecessary files, use artifact retention policies

**Problem**: Build timeout after 30 minutes  
**Solution**: Optimize build steps, use caching for dependencies

## Validation Commands

### Test Package Installation

```bash
# AMD64 testing
docker run --rm -it ubuntu:22.04 bash
# Inside container:
apt update && apt install -y ./local-rag_*.deb
systemctl --user start local-rag

# ARM64 testing (on actual Pi5)
sudo apt install -y ./local-rag_*arm64.deb
sudo systemctl start local-rag
sudo systemctl status local-rag
```

### Verify Package Quality

```bash
# Check package contents
dpkg -c local-rag_*.deb

# Validate policy compliance  
lintian local-rag_*.deb

# Test service functionality
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"text": "test query"}'
```

## Success Criteria

**Minimum Viable**: 
- Packages build automatically for both architectures
- Packages install successfully on target systems  
- Service starts and basic functionality works

**Production Ready**:
- All builds pass validation without errors
- Local development workflow established
- Release automation functional (if needed)

## Next Steps After Quick Start

1. **Enhance Testing**: Implement comprehensive test suite (T043)
2. **Add Monitoring**: Set up build performance tracking (T044)  
3. **Improve Documentation**: Complete user and developer guides (T042, T046)
4. **Security Hardening**: Add GPG signing and security scanning (T041)

## Troubleshooting

### Debug Build Failures

```bash
# Check GitHub Actions logs
# Look for common patterns:
# - Missing dependencies
# - Architecture-specific issues  
# - Timeout problems
# - Permission errors

# Local debugging
scripts/build-local.sh amd64
scripts/build-local.sh arm64
```

### Get Help

- **Review**: Full specification in `spec.md`
- **Planning**: Detailed implementation in `plan.md`
- **Tasks**: Complete task breakdown in `tasks.md`
- **Existing Code**: Reference 001-local-rag-mvp implementation patterns

## Time Estimates

- **Day 1-2**: Core build workflow implementation
- **Day 3-4**: Package validation and testing
- **Day 5**: Local build scripts and integration
- **Day 6-7**: Documentation and final validation
- **Week 2**: Release automation (if needed immediately)

**Total**: 5-10 days for production-ready CI/CD infrastructure
