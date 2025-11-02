#!/bin/bash

# Quick Test Script - Fast feedback during development
# Run this for quick checks before the full CI simulation

set -e

echo "⚡ Quick Test - Fast Feedback Loop"
echo "=================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Check for virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    print_warning "No virtual environment detected. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    print_status "Created and activated virtual environment"
else
    print_status "Using existing virtual environment: $VIRTUAL_ENV"
fi

# Install development dependencies if needed
print_status "Installing development dependencies..."
pip install -q ruff || {
    print_error "Failed to install development dependencies"
    exit 1
}

# Quick format check
print_status "Quick format check..."
if ! ruff format --check src/ tests/ 2>/dev/null; then
    print_warning "Code formatting issues found. Auto-fixing..."
    ruff format src/ tests/
    print_success "Code formatted with ruff"
else
    print_success "Code formatting is correct"
fi

# Use ruff for import sorting and linting (replaces isort)
print_status "Running ruff checks (import sorting + linting)..."
if ! ruff check src/ tests/ --quiet; then
    print_warning "Ruff issues found. Auto-fixing..."
    ruff check --fix src/ tests/
    print_success "Code fixed with ruff"
else
    print_success "Ruff checks passed"
fi

# Quick syntax check
print_status "Quick syntax check..."
if ! python -m py_compile src/guide/*.py; then
    print_error "Python syntax errors found"
    exit 1
fi
print_success "Syntax check passed"

# Quick import test
print_status "Quick import test..."
python -c "
import sys
sys.path.insert(0, 'src')
try:
    import guide
    print('✅ Package imports successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
" || exit 1

# Configuration validation
print_status "Configuration validation..."
if [ -f "src/guide/config/defaults.yaml" ]; then
    python -c "
import yaml
import sys
try:
    with open('src/guide/config/defaults.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print('✅ Configuration schema valid')
except Exception as e:
    print(f'❌ Configuration schema invalid: {e}')
    sys.exit(1)
    "
else
    print_warning "Configuration file not found - will be created during implementation"
fi

print_success "🎉 Quick test completed successfully!"
print_status "Your code is ready for development or the full CI test"
print_status "Next: Run './scripts/test-ci-local.sh' for full validation"