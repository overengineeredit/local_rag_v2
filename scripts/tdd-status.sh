#!/bin/bash

# TDD Status Dashboard - Shows current TDD progress and test coverage
# Usage: ./scripts/tdd-status.sh

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
    echo -e "${PURPLE}  TDD STATUS DASHBOARD${NC}"
    echo -e "${PURPLE}======================================${NC}"
}

print_section() {
    echo -e "${BLUE}$1${NC}"
    echo "$(printf '%.0s-' {1..40})"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

print_header

# 1. Task Progress
print_section "TASK PROGRESS"

TASKS_FILE="specs/001-local-rag-mvp/tasks.md"
if [ -f "$TASKS_FILE" ]; then
    TOTAL_TASKS=$(grep -c "^- \[" "$TASKS_FILE" || echo "0")
    COMPLETED_TASKS=$(grep -c "^- \[x\]" "$TASKS_FILE" || echo "0")
    REMAINING_TASKS=$((TOTAL_TASKS - COMPLETED_TASKS))
    
    echo "📋 Total Tasks: $TOTAL_TASKS"
    echo "✅ Completed: $COMPLETED_TASKS"
    echo "⏳ Remaining: $REMAINING_TASKS"
    
    if [ $TOTAL_TASKS -gt 0 ]; then
        PROGRESS=$((COMPLETED_TASKS * 100 / TOTAL_TASKS))
        echo "📊 Progress: $PROGRESS%"
    fi
    
    # Find next task
    NEXT_TASK=$(grep -n "^- \[ \]" "$TASKS_FILE" | head -1 | cut -d: -f2-)
    if [ -n "$NEXT_TASK" ]; then
        echo "🎯 Next Task: $NEXT_TASK"
    else
        print_success "All tasks completed!"
    fi
else
    print_error "Tasks file not found: $TASKS_FILE"
fi

echo ""

# 2. Test Coverage
print_section "TEST COVERAGE"

if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        print_warning "No virtual environment found"
    fi
fi

# Install coverage tools if needed
pip install -q pytest pytest-cov >/dev/null 2>&1

# Run coverage analysis
if pytest --cov=src/guide --cov-report=term-missing --quiet >/dev/null 2>&1; then
    print_success "Test suite runs successfully"
    
    # Get coverage percentage
    COVERAGE=$(pytest --cov=src/guide --cov-report=term-missing --quiet 2>/dev/null | grep "TOTAL" | awk '{print $4}' | sed 's/%//')
    
    if [ -n "$COVERAGE" ]; then
        echo "📊 Coverage: $COVERAGE%"
        
        if [ "$COVERAGE" -ge 85 ]; then
            print_success "Coverage meets target (85%+)"
        elif [ "$COVERAGE" -ge 70 ]; then
            print_warning "Coverage below target ($COVERAGE% < 85%)"
        else
            print_error "Coverage critically low ($COVERAGE% < 70%)"
        fi
    fi
else
    print_error "Test suite has failures"
fi

echo ""

# 3. TDD Health Check
print_section "TDD HEALTH CHECK"

# Check for test files
TEST_COUNT=$(find tests/ -name "test_*.py" | wc -l)
SRC_COUNT=$(find src/guide/ -name "*.py" -not -name "__*" | wc -l)

echo "🧪 Test Files: $TEST_COUNT"
echo "📄 Source Files: $SRC_COUNT"

if [ $TEST_COUNT -ge $SRC_COUNT ]; then
    print_success "Good test-to-source ratio"
else
    print_warning "Consider adding more test coverage"
fi

# Check for TDD violations (source files without tests)
echo ""
echo "🔍 TDD Violations Check:"
VIOLATIONS=0

for src_file in src/guide/*.py; do
    if [ "$src_file" = "src/guide/__init__.py" ]; then
        continue
    fi
    
    module_name=$(basename "$src_file" .py)
    test_file="tests/unit/test_${module_name}.py"
    
    if [ ! -f "$test_file" ]; then
        print_error "Missing test file for $(basename "$src_file")"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

if [ $VIOLATIONS -eq 0 ]; then
    print_success "No TDD violations found"
else
    print_error "$VIOLATIONS TDD violations detected"
fi

echo ""

# 4. Git Status
print_section "GIT STATUS"

if git status --porcelain | grep -q .; then
    print_warning "Uncommitted changes present:"
    git status --short
    echo ""
    print_info "Use TDD workflow scripts before committing:"
    echo "   ./scripts/tdd-task.sh    # See current task"
    echo "   ./scripts/tdd-cycle.sh   # Complete TDD cycle"
else
    print_success "Working directory clean"
fi

echo ""

# 5. Recommendations
print_section "RECOMMENDATIONS"

if [ $VIOLATIONS -gt 0 ]; then
    echo "🔧 Create missing test files for TDD compliance"
fi

if [ -n "$COVERAGE" ] && [ "$COVERAGE" -lt 85 ]; then
    echo "📈 Improve test coverage to meet 85% target"
fi

if [ $REMAINING_TASKS -gt 0 ]; then
    echo "⏭️  Continue with next task: ./scripts/tdd-task.sh"
fi

echo "🔄 Run this dashboard anytime: ./scripts/tdd-status.sh"

echo ""
print_header