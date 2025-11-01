#!/bin/bash

# TDD Cycle Script - Enforces Test-Driven Development workflow
# Usage: ./scripts/tdd-cycle.sh <task_id> <test_file> <implementation_file>
# Example: ./scripts/tdd-cycle.sh T015 tests/unit/test_vector_store.py src/guide/vector_store.py

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

print_header() {
    echo -e "${PURPLE}======================================${NC}"
    echo -e "${PURPLE}  TDD CYCLE: $1${NC}"
    echo -e "${PURPLE}======================================${NC}"
}

print_step() {
    echo -e "${BLUE}[STEP $1]${NC} $2"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check arguments
if [ $# -ne 3 ]; then
    print_error "Usage: $0 <task_id> <test_file> <implementation_file>"
    print_info "Example: $0 T015 tests/unit/test_vector_store.py src/guide/vector_store.py"
    exit 1
fi

TASK_ID=$1
TEST_FILE=$2
IMPL_FILE=$3

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

print_header "Task $TASK_ID TDD Cycle"

# Check if files exist
if [ ! -f "$TEST_FILE" ]; then
    print_error "Test file does not exist: $TEST_FILE"
    print_info "Create the test file first with failing tests for the functionality"
    exit 1
fi

print_step "1" "Validating test environment..."

# Ensure virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    print_warning "No virtual environment detected. Activating..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
fi

# Install dependencies
pip install -q pytest pytest-cov pytest-xdist

print_step "2" "RED PHASE - Running tests (should FAIL)..."

# Run tests - expect them to fail
if pytest "$TEST_FILE" -v --tb=short; then
    print_error "❌ TDD VIOLATION: Tests are passing before implementation!"
    print_error "This violates the TDD cycle. Tests should fail first."
    print_info "Review your tests to ensure they properly test the functionality"
    print_info "that hasn't been implemented yet."
    exit 1
else
    print_success "✅ RED PHASE: Tests are failing as expected"
fi

print_step "3" "Waiting for implementation..."
print_info "Now implement the minimal code in $IMPL_FILE to make tests pass"
print_info "Press ENTER when ready to test implementation..."
read -r

print_step "4" "GREEN PHASE - Running tests (should PASS)..."

# Run tests - expect them to pass now
if pytest "$TEST_FILE" -v --tb=short; then
    print_success "✅ GREEN PHASE: Tests are now passing!"
else
    print_error "❌ Tests are still failing. Continue implementing until tests pass."
    print_info "Re-run: $0 $TASK_ID $TEST_FILE $IMPL_FILE"
    exit 1
fi

print_step "5" "Running related tests to ensure no regressions..."

# Run all unit tests to ensure no breakage
if pytest tests/unit/ -x --tb=short; then
    print_success "✅ No regressions detected in unit tests"
else
    print_error "❌ Regression detected! Fix before proceeding."
    exit 1
fi

print_step "6" "Code quality checks..."

# Format and lint the implementation
if [ -f "$IMPL_FILE" ]; then
    black "$IMPL_FILE" "$TEST_FILE"
    isort "$IMPL_FILE" "$TEST_FILE"
    
    if ! ruff check "$IMPL_FILE" "$TEST_FILE" --quiet; then
        print_error "Linting issues found. Fix before committing."
        exit 1
    fi
    print_success "✅ Code quality checks passed"
fi

print_step "7" "REFACTOR PHASE - Optional cleanup..."
print_info "Review the code for any refactoring opportunities"
print_info "If you refactor, tests should still pass"
print_info "Press ENTER to continue to commit phase..."
read -r

print_step "8" "Final test run before commit..."

# Final test run
if pytest "$TEST_FILE" -v; then
    print_success "✅ Final tests passing"
else
    print_error "❌ Tests broken during refactor. Fix before committing."
    exit 1
fi

print_step "9" "Git commit preparation..."

# Add files to git
git add "$TEST_FILE"
if [ -f "$IMPL_FILE" ]; then
    git add "$IMPL_FILE"
fi

# Create commit message
COMMIT_MSG="$TASK_ID: Implement $(basename "$IMPL_FILE" .py) with TDD

- Add failing tests in $TEST_FILE
- Implement minimal code to pass tests in $IMPL_FILE
- All tests passing, no regressions detected

TDD Cycle: RED → GREEN → REFACTOR ✅"

print_info "Commit message prepared:"
echo "$COMMIT_MSG"
echo ""
print_info "Commit? (y/N)"
read -r CONFIRM

if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
    git commit -m "$COMMIT_MSG"
    print_success "✅ Changes committed successfully!"
    
    print_info "Push to remote? (y/N)"
    read -r PUSH_CONFIRM
    
    if [ "$PUSH_CONFIRM" = "y" ] || [ "$PUSH_CONFIRM" = "Y" ]; then
        git push
        print_success "✅ Changes pushed to remote!"
    fi
else
    print_info "Commit skipped. Files staged for manual commit."
fi

print_header "TDD CYCLE COMPLETE"
print_success "Task $TASK_ID completed successfully!"
print_info "Ready for next task in the TDD cycle."