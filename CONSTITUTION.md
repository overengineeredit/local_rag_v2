# Project Constitution

## Project Principles

### Core Values
1. **Privacy First**: All data processing and inference must happen locally without external dependencies
2. **Resource Efficiency**: Optimize for constrained hardware (Pi5) while maintaining functionality  
3. **Simplicity Over Complexity**: Choose simple, maintainable solutions over feature-rich but complex ones
4. **Cross-Platform Compatibility**: Support both ARM64 (Pi5) and AMD64 architectures equally
5. **Specification-Driven Development**: All changes must align with documented specifications

### Technical Standards
1. **Code Quality**: Maintain >85% test coverage with comprehensive unit, integration, and BDD tests
2. **Performance**: Meet documented performance targets (cold start 3-5min, warm queries 1-3min on Pi5)
3. **Documentation**: All public APIs and configuration options must be documented
4. **Error Handling**: Provide clear, actionable error messages with recovery guidance
5. **Resource Limits**: Implement configurable limits to prevent resource exhaustion

### Development Guidelines
1. **Incremental Development**: Prefer small, focused changes linked to specific milestones
2. **Testing Before Merging**: All code changes must pass CI/CD pipeline
3. **Specification Alignment**: Changes that deviate from specs require explicit ADR documentation
4. **User Experience**: Optimize for ease of installation and operation by non-technical users
5. **Backwards Compatibility**: Maintain API stability within major versions

### Architectural Constraints
1. **Single Process**: Maintain embedded architecture with FastAPI, llama-cpp-python, and ChromaDB
2. **APT Distribution**: Use Debian packages for deployment, not containers or manual installation
3. **Local-Only**: No cloud dependencies for core functionality (internet only for model downloads)
4. **Systemd Integration**: Follow standard Linux service patterns for lifecycle management
5. **Configuration Management**: Centralize configuration in `/etc/local-rag/config.yaml`

### Quality Gates
1. **Performance**: System must handle 100+ documents without degradation
2. **Reliability**: 99%+ uptime during normal operation
3. **Usability**: Installation completed in under 5 minutes on clean Pi5 systems
4. **Maintainability**: Code changes require minimal context switching between modules
5. **Security**: Follow secure coding practices and document security considerations

## Compliance and Exceptions

### Exception Process
When project constraints conflict with these principles:
1. Document the conflict in an ADR (Architecture Decision Record)
2. Provide clear rationale for the exception
3. Define acceptance criteria for future alignment
4. Update relevant specifications to reflect decisions

### Review Schedule
- **Weekly**: Performance metrics and resource usage review
- **Monthly**: Code quality and test coverage assessment  
- **Quarterly**: Architecture alignment and principle adherence review
- **Per-Release**: Full specification compliance audit

## Change Management

### Specification Changes
All changes to project specifications require:
1. Updated ADR documenting the decision
2. Impact assessment on existing code and documentation
3. Migration plan for existing users
4. Updated test scenarios reflecting new requirements

### Principle Evolution
This constitution may evolve but changes require:
1. Clear justification for the change
2. Impact assessment on project direction
3. Stakeholder consensus on the modification
4. Historical record of previous principles