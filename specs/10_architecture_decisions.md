# Architecture Decision Records (ADRs)

## ADR-001: Vector Database Selection - ChromaDB vs Qdrant

**Date**: 2025-10-12

**Status**: Accepted

**Context**: 
The system requires a vector database to store and search document embeddings for the RAG pipeline. Two main options were considered: ChromaDB and Qdrant.

**Decision**: 
Use ChromaDB as the vector database for v1.

**Rationale**:

**ChromaDB Advantages:**
- **Resource Efficiency**: Embedded mode runs as Python library (~100-200MB vs Qdrant's 500MB+ overhead)
- **Simplicity**: Single-process deployment, no separate server to manage
- **Pi5 Optimization**: Better suited for resource-constrained single-board computers
- **Storage**: SQLite backend provides reliable, file-based persistence
- **Proven**: Successfully used in the reference implementation ("A Local RAG on a RasPi")
- **Dependencies**: Fewer external dependencies, simpler Docker setup

**Qdrant Disadvantages for This Use Case:**
- **Resource Overhead**: Requires separate server process, higher memory usage
- **Complexity**: Additional networking, service management, and configuration
- **Over-engineering**: Performance benefits not needed for 100s of documents
- **Pi5 Constraints**: Competes with LLM for limited CPU/RAM resources

**Consequences**:
- Simpler deployment and maintenance
- Lower resource usage on Pi5
- Single point of failure (embedded in application)
- Migration path available if scaling needs change

**Future Considerations**:
- Qdrant remains an option for future scaling requirements
- Easy migration path exists due to similar APIs
- Performance monitoring will inform future decisions

---

## ADR-002: LLM Execution Strategy - CPU vs NPU

**Date**: 2025-10-12

**Status**: Accepted

**Context**: 
The system needs to run LLM inference locally. Options considered include CPU-only execution, NPU acceleration (Hailo-10H), and hybrid approaches.

**Decision**: 
Use CPU-only execution via llama-cpp-python for v1, with NPU support planned for future milestones.

**Rationale**:

**CPU Execution Advantages:**
- **Simplicity**: Well-established toolchain with llama.cpp and Python bindings
- **Compatibility**: Works on both Pi5 and AMD64 without hardware dependencies
- **Ecosystem**: Large community, extensive model support, good documentation
- **Development Speed**: Faster iteration without hardware-specific complications

**NPU Challenges for v1:**
- **Complexity**: Additional hardware dependency and driver requirements
- **Limited Support**: Fewer models and tools support Hailo acceleration
- **Development Time**: Longer integration and testing cycles
- **Portability**: Reduces cross-platform compatibility

**Consequences**:
- Longer inference times on Pi5 (acceptable for v1 use case)
- Higher power consumption during inference
- Simpler development and testing workflow
- Clear upgrade path for NPU integration in future milestones

**Future Considerations**:
- NPU integration planned for milestone 4-5
- Will evaluate performance gains vs complexity trade-offs
- May support both CPU and NPU modes for user choice

---

## ADR-003: Deployment Architecture - Embedded vs Service-Based

**Date**: 2025-10-12

**Status**: Accepted

**Context**: 
The system architecture needs to balance ease of deployment, resource efficiency, and maintainability. Considered approaches include Docker containers, separate services (e.g., external Ollama), and embedded components.

**Decision**: 
Use a single Python process with embedded LLM and vector database, deployed via APT package with systemd service management.

**Rationale**:

**Embedded Architecture Advantages:**
- **Deployment Simplicity**: Single APT package installation with `sudo apt install ./local-rag.deb`
- **Resource Efficiency**: No inter-process communication overhead, shared memory space
- **Reliability**: Fewer points of failure, simpler dependency management
- **User Experience**: One command installation, standard systemd service management
- **Cross-platform**: Same architecture works on Pi5 and AMD64

**Service-Based Disadvantages:**
- **Complexity**: Multiple services to install, configure, and manage
- **Resource Overhead**: Network communication, separate process memory overhead
- **Installation Friction**: Users must manage multiple components and configurations
- **Networking Issues**: Docker-to-host communication complications on Pi5

**Implementation Details:**
- Single Python process containing FastAPI, llama-cpp-python, and ChromaDB
- Systemd service for lifecycle management
- Configuration via `/etc/local-rag/config.yaml`
- Data storage in `/var/lib/local-rag/`
- Logs via systemd journal and optional file output

**Consequences**:
- Easier user installation and maintenance
- Slightly less modular than service-based approach
- All components share same process lifecycle
- Future modularization possible if needed

**Future Considerations**:
- Plugin architecture can provide modularity within single process
- Performance monitoring will inform need for service separation
- Container deployment option can be added later if requested

---

## ADR-004: LLM Integration - Ollama vs llama-cpp-python

**Date**: 2025-10-12

**Status**: Accepted

**Context**: 
The system needs to integrate with LLM inference. Two primary options were considered: using Ollama as an external service or embedding llama-cpp-python directly in the application.

**Decision**: 
Use llama-cpp-python directly embedded in the Python application.

**Rationale**:

**llama-cpp-python Advantages:**
- **Deployment Simplicity**: No external service dependency, single process deployment
- **Resource Efficiency**: No network overhead, direct memory access, shared process space
- **Developer Experience**: Native Python API, familiar patterns, good documentation
- **Cross-platform**: Pre-built wheels for both ARM64 (Pi5) and AMD64
- **Control**: Fine-grained control over model loading, inference parameters, and memory management

**Ollama Disadvantages for This Use Case:**
- **Service Complexity**: Requires separate service installation and management
- **Network Overhead**: HTTP API calls add latency and complexity
- **Resource Usage**: Additional process overhead on resource-constrained Pi5
- **Installation Friction**: Users must install and configure two separate components

**Technical Implementation:**
- Direct integration with llama-cpp-python Python bindings
- Model files stored in `/var/lib/local-rag/models/`
- Configurable inference parameters via config file
- Streaming token generation for responsive UI
- Error handling and retry logic within application

**Consequences**:
- Simpler deployment and user experience
- Better resource utilization on Pi5
- More complex model management (no Ollama's model download features)
- Direct dependency on llama-cpp-python stability

**Future Considerations**:
- Can add Ollama support as alternative backend if requested
- Model management tools may be needed for user convenience
- Performance comparison with Ollama can inform future decisions

---

## ADR-005: CI/CD Build Environment - Debian Containers vs Ubuntu Runners

**Date**: 2025-11-02

**Status**: Accepted

**Context**:
The CI/CD pipeline for automated APT package building requires a reliable environment that supports cross-compilation for both AMD64 and ARM64 architectures. Initial implementation used Ubuntu 24.04 (noble) runners, but encountered repository conflicts when attempting ARM64 cross-compilation setup.

**Decision**:
Use Debian 12 (bookworm) containers within GitHub Actions runners for package building instead of native Ubuntu 24.04 environments.

**Rationale**:

**Debian Container Advantages:**

- **Repository Consistency**: Native APT repositories with proper ARM64 cross-compilation support
- **Package Building Compatibility**: Native Debian environment matches target deployment systems
- **Toolchain Reliability**: Complete dpkg-buildpackage ecosystem without Ubuntu-specific modifications
- **Dependency Resolution**: Proper multi-arch dependency handling without repository conflicts
- **Environment Isolation**: Containerized builds ensure consistent, reproducible environments
- **Cross-Compilation Support**: Mature ARM64 toolchain integration in Debian ecosystem

**Ubuntu 24.04 Disadvantages for This Use Case:**

- **Repository Conflicts**: ARM64 packages not available in security.ubuntu.com repositories
- **Cross-Compilation Issues**: `dpkg --add-architecture arm64` causes 404 errors on package updates
- **Toolchain Complexity**: Additional configuration required for cross-compilation setup
- **Environment Drift**: Differences between build environment and target deployment systems

**Technical Implementation:**

- Container configuration: `debian:12` with `--privileged` options
- Native APT package management without sudo requirements
- QEMU emulation within container for ARM64 builds
- Complete Debian package building toolchain (debhelper, lintian, dpkg-dev)
- Artifact generation and validation within isolated container environment

**Consequences**:

- More reliable and predictable build environment
- Better compatibility with target Debian-based deployment systems
- Slightly increased build complexity due to container setup
- Improved cross-compilation success rate
- Consistent package validation using native Debian tools

**Future Considerations**:

- Monitor container performance vs native runner performance
- Consider sbuild for even more isolated package building if needed
- Evaluate upgrade path to newer Debian versions as they become available
- Potential optimization with multi-stage container builds for caching
