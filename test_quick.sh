#!/bin/bash
# Quick test script for Sandhi Generator
# Usage: ./test_quick.sh

set -e  # Exit on error

echo "=========================================="
echo "Project Panini - Quick Test Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "1. Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1)
echo "   $PYTHON_VERSION"
echo ""

# Check syntax
echo "2. Checking Python syntax..."
if python3 -m py_compile src/generator/sandhi_generator.py 2>/dev/null; then
    echo -e "   ${GREEN}✓${NC} src/generator/sandhi_generator.py - Syntax OK"
else
    echo -e "   ${RED}✗${NC} src/generator/sandhi_generator.py - Syntax Error"
    exit 1
fi

if python3 -m py_compile tests/test_sandhi_generator.py 2>/dev/null; then
    echo -e "   ${GREEN}✓${NC} tests/test_sandhi_generator.py - Syntax OK"
else
    echo -e "   ${RED}✗${NC} tests/test_sandhi_generator.py - Syntax Error"
    exit 1
fi

if python3 -m py_compile examples/sandhi_example.py 2>/dev/null; then
    echo -e "   ${GREEN}✓${NC} examples/sandhi_example.py - Syntax OK"
else
    echo -e "   ${RED}✗${NC} examples/sandhi_example.py - Syntax Error"
    exit 1
fi
echo ""

# Test import
echo "3. Testing module import..."
if python3 -c "import sys; sys.path.insert(0, 'src'); from generator.sandhi_generator import SandhiGenerator; print('OK')" 2>/dev/null; then
    echo -e "   ${GREEN}✓${NC} Module imports successfully"
else
    echo -e "   ${RED}✗${NC} Module import failed"
    exit 1
fi
echo ""

# Test basic functionality
echo "4. Testing basic functionality..."
RESULT=$(python3 -c "import sys; sys.path.insert(0, 'src'); from generator.sandhi_generator import SandhiGenerator; g = SandhiGenerator(); print(g.apply_sandhi('Deva', 'Alaya'))" 2>/dev/null)
if [ "$RESULT" = "Devalaya" ]; then
    echo -e "   ${GREEN}✓${NC} Sandhi application works: Deva + Alaya = Devalaya"
else
    echo -e "   ${RED}✗${NC} Sandhi application failed: Expected 'Devalaya', got '$RESULT'"
    exit 1
fi
echo ""

# Check if pytest is available
echo "5. Checking for pytest..."
if python3 -m pytest --version >/dev/null 2>&1; then
    PYTEST_VERSION=$(python3 -m pytest --version 2>&1)
    echo -e "   ${GREEN}✓${NC} $PYTEST_VERSION"
    echo ""
    echo "6. Running tests..."
    python3 -m pytest tests/test_sandhi_generator.py -v --tb=short
    echo ""
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "   ${YELLOW}⚠${NC} pytest not installed. Install with: pip install pytest pytest-cov"
    echo ""
    echo "   To run tests, first install pytest:"
    echo "   pip install pytest pytest-cov"
    echo ""
    echo "   Then run: pytest tests/ -v"
fi

echo ""
echo "=========================================="
echo "Quick test completed!"
echo "=========================================="
