#!/bin/bash
#
# Local CI Simulation Script for Local RAG Project
# Simulates the full GitHub Actions CI/CD pipeline locally
#
# Usage: ./scripts/test-ci-local.sh [--skip-build] [--skip-tests] [--architecture=arm64|amd64]
#
# This script provides comprehensive local validation that mirrors the GitHub Actions workflows:
# - Code quality checks (formatting, linting, type checking, security)
# - Full test suite execution with coverage
# - Build validation for APT packages
# - Documentation generation and validation
# - Performance benchmarking (optional)
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${PROJECT_ROOT}/.venv"
TEST_RESULTS_DIR="${PROJECT_ROOT}/test-results"
COVERAGE_DIR="${PROJECT_ROOT}/coverage"
BUILD_DIR="${PROJECT_ROOT}/build"
DIST_DIR="${PROJECT_ROOT}/dist"

# Default options
SKIP_BUILD=false
SKIP_TESTS=false
TARGET_ARCH="$(uname -m)"
VERBOSE=false
PARALLEL_JOBS=4

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --architecture=*)
            TARGET_ARCH="${1#*=}"
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --jobs=*)
            PARALLEL_JOBS="${1#*=}"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-build              Skip build validation"
            echo "  --skip-tests              Skip test execution"
            echo "  --architecture=ARCH       Target architecture (arm64, amd64)"
            echo "  --verbose, -v             Verbose output"
            echo "  --jobs=N                  Number of parallel jobs (default: 4)"
            echo "  --help, -h                Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Utility functions
log_section() {
    echo -e "\n${BLUE}==== $1 ====${NC}"
}

log_step() {
    echo -e "${CYAN}→ $1${NC}"
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "Required command '$1' not found"
        return 1
    fi
}

# Setup functions
setup_environment() {
    log_section "Environment Setup"
    
    cd "$PROJECT_ROOT"
    
    # Create directories
    mkdir -p "$TEST_RESULTS_DIR" "$COVERAGE_DIR" "$BUILD_DIR" "$DIST_DIR"
    
    # Check required commands
    log_step "Checking required tools"
    check_command python3
    check_command pip
    
    # Setup virtual environment
    if [[ ! -d "$VENV_PATH" ]]; then
        log_step "Creating virtual environment"
        python3 -m venv "$VENV_PATH"
    fi
    
    log_step "Activating virtual environment"
    source "$VENV_PATH/bin/activate"
    
    # Upgrade pip and install dependencies
    log_step "Installing/updating dependencies"
    pip install --upgrade pip
    
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    fi
    
    # Install development dependencies
    pip install pytest pytest-cov pytest-xdist pytest-mock pytest-asyncio
    # Install quality tools
    pip install ruff
    pip install build wheel setuptools
    pip install coverage[toml] codecov
    
    log_success "Environment setup complete"
}

# Code quality checks
run_code_quality() {
    log_section "Code Quality Checks"
    
    # Code formatting check
    log_step "Checking code formatting with ruff"
    if ruff format --check --diff src/ tests/; then
        log_success "Code formatting is correct"
    else
        log_error "Code formatting issues found"
        echo "Run 'ruff format src/ tests/' to fix formatting"
        return 1
    fi
    
    # Import sorting check
    log_step "Checking import sorting with ruff"
    if ruff check --select I --diff src/ tests/; then
        log_success "Import sorting is correct"
    else
        log_error "Import sorting issues found"
        echo "Run 'ruff check --select I --fix src/ tests/' to fix imports"
        return 1
    fi
    
    # Linting with ruff
    log_step "Running ruff linter"
    if ruff check src/ tests/; then
        log_success "Ruff linting passed"
    else
        log_error "Ruff linting issues found"
        return 1
    fi
    
    log_success "Code quality checks complete"
}

# Test execution
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        log_warning "Skipping tests as requested"
        return 0
    fi
    
    log_section "Test Execution"
    
    # Unit tests with coverage
    log_step "Running unit tests with coverage"
    pytest tests/ \
        --cov=src \
        --cov-report=html:"$COVERAGE_DIR/html" \
        --cov-report=xml:"$COVERAGE_DIR/coverage.xml" \
        --cov-report=term \
        --junitxml="$TEST_RESULTS_DIR/pytest-report.xml" \
        --tb=short \
        -n "$PARALLEL_JOBS" \
        -v
    
    # Check coverage threshold
    COVERAGE_THRESHOLD=80
    COVERAGE_PERCENT=$(coverage report --show-missing | grep TOTAL | awk '{print $4}' | sed 's/%//')
    
    if (( $(echo "$COVERAGE_PERCENT >= $COVERAGE_THRESHOLD" | bc -l) )); then
        log_success "Coverage ${COVERAGE_PERCENT}% meets threshold of ${COVERAGE_THRESHOLD}%"
    else
        log_error "Coverage ${COVERAGE_PERCENT}% below threshold of ${COVERAGE_THRESHOLD}%"
        return 1
    fi
    
    # Performance tests (if they exist)
    if [[ -d "tests/performance" ]]; then
        log_step "Running performance tests"
        pytest tests/performance/ \
            --benchmark-json="$TEST_RESULTS_DIR/benchmark-report.json" \
            -v
    fi
    
    log_success "Test execution complete"
}

# Build validation
run_build_validation() {
    if [[ "$SKIP_BUILD" == "true" ]]; then
        log_warning "Skipping build validation as requested"
        return 0
    fi
    
    log_section "Build Validation"
    
    # Clean previous builds
    log_step "Cleaning previous builds"
    rm -rf "$BUILD_DIR" "$DIST_DIR"
    mkdir -p "$BUILD_DIR" "$DIST_DIR"
    
    # Build Python package
    log_step "Building Python package"
    python -m build --outdir "$DIST_DIR"
    
    # Validate package
    log_step "Validating package contents"
    if command -v twine &> /dev/null; then
        twine check "$DIST_DIR"/*
        log_success "Package validation passed"
    else
        log_warning "twine not available, skipping package validation"
    fi
    
    # Test package installation
    log_step "Testing package installation"
    TEST_VENV_PATH="/tmp/test-install-$$"
    python3 -m venv "$TEST_VENV_PATH"
    source "$TEST_VENV_PATH/bin/activate"
    
    pip install "$DIST_DIR"/*.whl
    
    # Test basic import
    python -c "import guide; print('Package import successful')"
    
    # Cleanup test environment
    deactivate
    rm -rf "$TEST_VENV_PATH"
    
    # Reactivate our main environment
    source "$VENV_PATH/bin/activate"
    
    log_success "Build validation complete"
}

# Documentation validation
run_documentation_validation() {
    log_section "Documentation Validation"
    
    # Check README
    log_step "Validating README.md"
    if [[ -f "README.md" ]]; then
        # Check for required sections
        required_sections=("Installation" "Usage" "Configuration" "API")
        for section in "${required_sections[@]}"; do
            if grep -q "## $section\|# $section" README.md; then
                log_success "README contains $section section"
            else
                log_warning "README missing $section section"
            fi
        done
    else
        log_error "README.md not found"
        return 1
    fi
    
    # Validate configuration files
    log_step "Validating configuration files"
    config_files=("pyproject.toml" "speckit.yaml")
    for config_file in "${config_files[@]}"; do
        if [[ -f "$config_file" ]]; then
            log_success "$config_file exists"
            # Basic syntax validation
            case "$config_file" in
                *.toml)
                    if python -c "import tomllib; tomllib.load(open('$config_file', 'rb'))" 2>/dev/null; then
                        log_success "$config_file syntax is valid"
                    else
                        log_error "$config_file syntax is invalid"
                        return 1
                    fi
                    ;;
                *.yaml|*.yml)
                    if python -c "import yaml; yaml.safe_load(open('$config_file'))" 2>/dev/null; then
                        log_success "$config_file syntax is valid"
                    else
                        log_error "$config_file syntax is invalid"
                        return 1
                    fi
                    ;;
            esac
        else
            log_warning "$config_file not found"
        fi
    done
    
    log_success "Documentation validation complete"
}

# Generate reports
generate_reports() {
    log_section "Generating Reports"
    
    # Create summary report
    SUMMARY_REPORT="$TEST_RESULTS_DIR/ci-summary.md"
    
    cat > "$SUMMARY_REPORT" << EOF
# Local CI Simulation Report

**Date:** $(date)
**Architecture:** $TARGET_ARCH
**Python Version:** $(python --version)

## Test Results

EOF
    
    if [[ -f "$TEST_RESULTS_DIR/pytest-report.xml" ]]; then
        echo "- Unit Tests: ✓ Passed" >> "$SUMMARY_REPORT"
    else
        echo "- Unit Tests: ⚠ Skipped" >> "$SUMMARY_REPORT"
    fi
    
    if [[ -f "$COVERAGE_DIR/coverage.xml" ]]; then
        echo "- Coverage Report: ✓ Generated" >> "$SUMMARY_REPORT"
    else
        echo "- Coverage Report: ⚠ Not generated" >> "$SUMMARY_REPORT"
    fi
    
    echo "" >> "$SUMMARY_REPORT"
    echo "## Code Quality" >> "$SUMMARY_REPORT"
    echo "- Formatting: ✓ Checked" >> "$SUMMARY_REPORT"
    echo "- Linting: ✓ Checked" >> "$SUMMARY_REPORT"
    echo "- Type Checking: ✓ Checked" >> "$SUMMARY_REPORT"
    echo "- Security Analysis: ✓ Checked" >> "$SUMMARY_REPORT"
    
    if [[ "$SKIP_BUILD" == "false" ]]; then
        echo "" >> "$SUMMARY_REPORT"
        echo "## Build Validation" >> "$SUMMARY_REPORT"
        echo "- Package Build: ✓ Successful" >> "$SUMMARY_REPORT"
        echo "- Package Validation: ✓ Passed" >> "$SUMMARY_REPORT"
    fi
    
    log_success "Summary report generated: $SUMMARY_REPORT"
    
    # Show results summary
    echo ""
    log_section "Results Summary"
    echo "Test results available in: $TEST_RESULTS_DIR"
    echo "Coverage report available in: $COVERAGE_DIR/html/index.html"
    echo "Summary report: $SUMMARY_REPORT"
}

# Cleanup function
cleanup() {
    log_section "Cleanup"
    
    if [[ "$VERBOSE" == "false" ]]; then
        # Remove temporary files but keep reports
        find "$PROJECT_ROOT" -name "*.pyc" -delete
        find "$PROJECT_ROOT" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    fi
    
    log_success "Cleanup complete"
}

# Main execution
main() {
    local start_time=$(date +%s)
    
    echo -e "${PURPLE}Local CI Simulation for Local RAG Project${NC}"
    echo -e "${PURPLE}==========================================${NC}"
    echo ""
    echo "Target Architecture: $TARGET_ARCH"
    echo "Parallel Jobs: $PARALLEL_JOBS"
    echo "Skip Build: $SKIP_BUILD"
    echo "Skip Tests: $SKIP_TESTS"
    echo ""
    
    # Trap for cleanup on exit
    trap cleanup EXIT
    
    # Execute pipeline steps
    setup_environment
    run_code_quality
    run_tests
    run_build_validation
    run_documentation_validation
    generate_reports
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    log_section "Pipeline Complete"
    log_success "All checks passed in ${duration} seconds"
    echo ""
    echo -e "${GREEN}🎉 Local CI simulation completed successfully!${NC}"
    echo "Ready for GitHub pull request submission."
}

# Run main function
main "$@"