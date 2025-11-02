# TDD Workflow Guide

This project enforces strict Test-Driven Development (TDD) as outlined in the Project Constitution.

## 🔴 RED → 🟢 GREEN → 🔄 REFACTOR

### Core Principle

**NEVER write implementation code without a failing test first.**

## Quick Start

```bash
# 1. Check current status
./scripts/tdd-status.sh

# 2. See next task  
./scripts/tdd-task.sh

# 3. Complete TDD cycle for implementation tasks
./scripts/tdd-cycle.sh T015 tests/unit/test_vector_store.py src/guide/vector_store.py
```

## Scripts Available

| Script | Purpose |
|--------|---------|
| `./scripts/tdd-status.sh` | Dashboard showing TDD progress, coverage, and violations |
| `./scripts/tdd-task.sh [task_id]` | Shows current/next task with TDD guidance |
| `./scripts/tdd-cycle.sh <task_id> <test_file> <impl_file>` | Enforces full TDD cycle |
| `./scripts/test-quick.sh` | Quick validation before commits |
| `./scripts/test-ci-local.sh` | Full CI simulation |

## Workflow Steps

### For Test Tasks

1. **Write failing tests** that describe expected behavior
2. **Run tests** to confirm they fail (RED phase)
3. **Commit the failing tests**

```bash
# Example
git add tests/unit/test_vector_store.py
git commit -m "T015: Add failing tests for Document entity model"
```

### For Implementation Tasks

1. **Ensure tests exist and are failing**
2. **Use TDD cycle script** for automated workflow
3. **Write minimal code** to make tests pass (GREEN phase)
4. **Refactor** while keeping tests green
5. **Commit implementation**

```bash
# Automated TDD cycle
./scripts/tdd-cycle.sh T015 tests/unit/test_vector_store.py src/guide/vector_store.py
```

## Manual TDD Cycle

If you prefer manual control:

### 1. RED Phase

```bash
# Write failing test
vim tests/unit/test_module.py

# Confirm test fails
pytest tests/unit/test_module.py -v

# Should see failures - this is good!
```

### 2. GREEN Phase

```bash
# Write minimal implementation
vim src/guide/module.py

# Run test until it passes
pytest tests/unit/test_module.py -v

# Should see passing tests
```

### 3. REFACTOR Phase

```bash
# Clean up code while keeping tests green
vim src/guide/module.py
vim tests/unit/test_module.py

# Ensure tests still pass
pytest tests/unit/test_module.py -v
```

### 4. Commit

```bash
git add tests/unit/test_module.py src/guide/module.py
git commit -m "T015: Implement Document entity with TDD"
```

## Quality Gates

### Pre-commit Hook

Automatically runs before each commit:

- ✅ Code formatting (black, isort)
- ✅ Linting (ruff)
- ✅ Test validation
- ✅ TDD compliance check

### Coverage Requirements

- **Minimum**: 80% test coverage
- **Target**: 90% test coverage
- **Check**: `./scripts/tdd-status.sh`

### TDD Violations

The system detects:

- ❌ Source files without corresponding test files
- ❌ Implementation committed before tests
- ❌ Failing tests in main branch
- ❌ Regressions introduced

## File Naming Conventions

```
src/guide/vector_store.py     → tests/unit/test_vector_store.py
src/guide/llm_interface.py    → tests/unit/test_llm_interface.py
src/guide/content_manager.py  → tests/unit/test_content_manager.py
```

## Integration Tests

For complex workflows:

```
tests/integration/test_document_api.py      # API contract tests
tests/integration/test_rag_workflow.py      # End-to-end workflows
tests/integration/test_service_management.py # System integration
```

## Best Practices

### 1. Write Descriptive Test Names

```python
def test_document_model_validates_required_fields():
    """Document should raise ValidationError when required fields missing."""
    
def test_vector_store_handles_connection_failures_with_retry():
    """VectorStore should retry failed connections with exponential backoff."""
```

### 2. Test Behavior, Not Implementation

```python
# Good - tests behavior
def test_content_manager_deduplicates_identical_content():
    result = content_manager.import_content([doc1, doc2])  # same content
    assert result.duplicate_count == 1

# Bad - tests implementation details  
def test_content_manager_calls_sha256_hash():
    with mock.patch('hashlib.sha256') as mock_hash:
        content_manager.import_content([doc1])
        mock_hash.assert_called()
```

### 3. Use Arrange-Act-Assert Pattern

```python
def test_query_returns_relevant_documents():
    # Arrange
    documents = [create_test_document("content about AI")]
    vector_store.add_documents(documents)
    
    # Act
    results = vector_store.query("artificial intelligence")
    
    # Assert
    assert len(results) == 1
    assert "AI" in results[0].content
```

## Troubleshooting

### Tests Passing Before Implementation

```bash
# This indicates TDD violation
./scripts/tdd-cycle.sh T015 tests/unit/test_module.py src/guide/module.py
# Error: Tests are passing before implementation!
```

**Solution**: Review tests to ensure they actually test the unimplemented functionality.

### Pre-commit Hook Failing

```bash
# Check what's failing
git commit -m "message"
# Error: TDD Violation: No test file found for src/guide/module.py
```

**Solution**: Create the corresponding test file first.

### Coverage Below Target

```bash
./scripts/tdd-status.sh
# Coverage: 65% (below 85% target)
```

**Solution**: Add more comprehensive tests for uncovered code paths.

## Emergency Override

⚠️ **Use sparingly and document reasoning**

```bash
# Skip pre-commit hook (not recommended)
git commit --no-verify -m "emergency fix"

# Skip specific tests temporarily
pytest -k "not test_broken_function"
```

Always follow up with proper TDD fixes!

## References

- [Project Constitution](../CONSTITUTION.md) - TDD requirements
- [Tasks Documentation](../specs/001-local-rag-mvp/tasks.md) - Task-specific TDD guidance
- [Test Strategy](../specs/08_testing_strategy.md) - Comprehensive testing approach