#!/bin/bash

# Task-based TDD Helper - Shows current task and guides TDD workflow
# Usage: ./scripts/tdd-task.sh [task_id]

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
    echo -e "${PURPLE}  TDD TASK GUIDE${NC}"
    echo -e "${PURPLE}======================================${NC}"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_step() {
    echo -e "${YELLOW}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

TASKS_FILE="specs/001-local-rag-mvp/tasks.md"

if [ ! -f "$TASKS_FILE" ]; then
    print_error "Tasks file not found: $TASKS_FILE"
    exit 1
fi

print_header

if [ $# -eq 0 ]; then
    print_info "Finding next uncompleted task..."
    
    # Find next uncompleted task
    NEXT_TASK=$(grep -n "^- \[ \]" "$TASKS_FILE" | head -1)
    
    if [ -z "$NEXT_TASK" ]; then
        print_success "🎉 All tasks appear to be completed!"
        exit 0
    fi
    
    TASK_LINE=$(echo "$NEXT_TASK" | cut -d: -f1)
    TASK_CONTENT=$(echo "$NEXT_TASK" | cut -d: -f2-)
    
    # Extract task ID from content
    TASK_ID=$(echo "$TASK_CONTENT" | grep -o 'T[0-9][0-9][0-9][a-z]*' | head -1)
    
    print_info "Next uncompleted task found:"
    echo "$TASK_CONTENT"
    echo ""
    
else
    TASK_ID=$1
    print_info "Looking up task: $TASK_ID"
    
    # Find the specific task
    TASK_LINE=$(grep -n "$TASK_ID" "$TASKS_FILE" | head -1)
    
    if [ -z "$TASK_LINE" ]; then
        print_error "Task $TASK_ID not found in $TASKS_FILE"
        exit 1
    fi
    
    TASK_CONTENT=$(echo "$TASK_LINE" | cut -d: -f2-)
    print_info "Task found:"
    echo "$TASK_CONTENT"
    echo ""
fi

# Extract test and implementation files from task content
if echo "$TASK_CONTENT" | grep -q "tests/"; then
    TEST_FILE=$(echo "$TASK_CONTENT" | grep -o 'tests/[^[:space:]]*\.py' | head -1)
fi

if echo "$TASK_CONTENT" | grep -q "src/guide/"; then
    IMPL_FILE=$(echo "$TASK_CONTENT" | grep -o 'src/guide/[^[:space:]]*\.py' | head -1)
fi

# Determine task type and TDD approach
IS_TEST_TASK=false
IS_IMPL_TASK=false

if echo "$TASK_CONTENT" | grep -qE "(test|Test)"; then
    IS_TEST_TASK=true
fi

if echo "$TASK_CONTENT" | grep -qE "(Implement|Create.*in src/)"; then
    IS_IMPL_TASK=true
fi

echo -e "${BLUE}TDD GUIDANCE FOR $TASK_ID:${NC}"
echo "================================"

if $IS_TEST_TASK; then
    print_step "1. This is a TEST task - Write FAILING tests first"
    print_info "Create test file: ${TEST_FILE:-'[extract from task description]'}"
    print_info "Write tests that describe the expected behavior"
    print_info "Ensure tests FAIL when run (no implementation yet)"
    echo ""
    print_step "2. Run tests to confirm they fail:"
    echo "   pytest ${TEST_FILE:-'<test_file>'} -v"
    echo ""
    print_step "3. When tests fail as expected, mark task complete and move to implementation"
    
elif $IS_IMPL_TASK; then
    print_step "1. This is an IMPLEMENTATION task - Tests should already exist"
    if [ -n "$TEST_FILE" ] && [ -f "$TEST_FILE" ]; then
        print_success "✅ Test file exists: $TEST_FILE"
    else
        print_error "❌ Test file missing or not found: ${TEST_FILE:-'unknown'}"
        print_info "Create tests first before implementing!"
        exit 1
    fi
    
    print_step "2. Verify tests are currently failing:"
    echo "   pytest ${TEST_FILE:-'<test_file>'} -v"
    echo ""
    print_step "3. Implement minimal code to make tests pass"
    print_info "Implementation file: ${IMPL_FILE:-'[extract from task description]'}"
    echo ""
    print_step "4. Use TDD cycle script for full workflow:"
    echo "   ./scripts/tdd-cycle.sh $TASK_ID ${TEST_FILE:-'<test_file>'} ${IMPL_FILE:-'<impl_file>'}"
    
else
    print_info "This appears to be a setup/configuration task"
    print_step "1. Complete the task as described"
    print_step "2. Run quick validation:"
    echo "   ./scripts/test-quick.sh"
    print_step "3. Commit changes with clear message"
fi

echo ""
print_info "After completing this task:"
echo "   - Mark as [x] in $TASKS_FILE"
echo "   - Run ./scripts/test-quick.sh for quick validation"
echo "   - Commit and push changes"
echo "   - Run this script again for next task"