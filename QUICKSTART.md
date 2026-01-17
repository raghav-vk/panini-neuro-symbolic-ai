# Quick Start Guide: Compile and Test

This guide will help you set up, compile, and test the Sandhi Generator module.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- (Optional) Virtual environment (recommended)

## Step 1: Set Up Environment

### Option A: Using Virtual Environment (Recommended)

```bash
# Navigate to project directory
cd panini-neuro-symbolic-ai

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### Option B: System-wide Installation

```bash
cd panini-neuro-symbolic-ai
```

## Step 2: Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install only testing dependencies
pip install pytest>=7.4.0 pytest-cov>=4.1.0
```

## Step 3: Verify Installation

### Check Python Syntax

```bash
# Check main module syntax
python3 -m py_compile src/generator/sandhi_generator.py

# Check test file syntax
python3 -m py_compile tests/test_sandhi_generator.py

# Check example script syntax
python3 -m py_compile examples/sandhi_example.py
```

If all commands complete without errors, the syntax is valid.

## Step 4: Run Tests

### Run All Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with detailed output
pytest tests/ -vv

# Run with output capture disabled (see print statements)
pytest tests/ -v -s
```

### Run Specific Test File

```bash
# Run only Sandhi generator tests
pytest tests/test_sandhi_generator.py -v
```

### Run Specific Test

```bash
# Run a specific test function
pytest tests/test_sandhi_generator.py::TestSandhiGenerator::test_apply_sandhi_known_combination -v
```

### Run Tests with Coverage

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=term

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html

# View HTML report (opens in browser)
open htmlcov/index.html  # macOS
# xdg-open htmlcov/index.html  # Linux
```

## Step 5: Run Example Script

```bash
# Run the example script
python3 examples/sandhi_example.py
```

Expected output:
```
============================================================
Project Panini - Sandhi Generator Example
============================================================

Example 1: Basic Sandhi Application
------------------------------------------------------------
  Deva + Alaya = Devalaya
  Rama + Ayana = Ramanayana
  ...
```

## Step 6: Interactive Testing

### Python REPL

```bash
# Start Python interpreter
python3

# In Python:
>>> import sys
>>> sys.path.insert(0, 'src')
>>> from generator.sandhi_generator import SandhiGenerator
>>> gen = SandhiGenerator()
>>> gen.apply_sandhi("Deva", "Alaya")
'Devalaya'
>>> exit()
```

## Common Issues and Solutions

### Issue: `ModuleNotFoundError: No module named 'pytest'`

**Solution:**
```bash
pip install pytest pytest-cov
```

### Issue: `ImportError: cannot import name 'SandhiGenerator'`

**Solution:**
Make sure you're in the project root directory and the `src` directory is in the Python path:
```bash
# From project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python3 -c "from generator.sandhi_generator import SandhiGenerator; print('OK')"
```

### Issue: Permission errors when creating `__pycache__`

**Solution:**
This is usually a sandbox/permission issue. The code will still work, but you may need to run with appropriate permissions or adjust directory permissions.

### Issue: Tests fail with `AssertionError`

**Solution:**
1. Check that you're using Python 3.10+
2. Verify all dependencies are installed
3. Run tests with `-vv` flag for more details:
   ```bash
   pytest tests/ -vv
   ```

## Test Output Examples

### Successful Test Run

```
tests/test_sandhi_generator.py::TestSandhiGenerator::test_apply_sandhi_known_combination PASSED
tests/test_sandhi_generator.py::TestSandhiGenerator::test_apply_sandhi_multiple_known_combinations PASSED
tests/test_sandhi_generator.py::TestSandhiGenerator::test_apply_sandhi_empty_words PASSED
...
======================== 15 passed in 0.05s ========================
```

### With Coverage

```
tests/test_sandhi_generator.py::TestSandhiGenerator::test_apply_sandhi_known_combination PASSED
...
---------- coverage: platform darwin, python 3.10.0 -----------
Name                              Stmts   Miss  Cover
-----------------------------------------------------
src/generator/sandhi_generator.py    150      5    97%
-----------------------------------------------------
TOTAL                               150      5    97%
======================== 15 passed in 0.08s ========================
```

## Continuous Testing

### Watch Mode (requires pytest-watch)

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests automatically on file changes
ptw tests/
```

## Next Steps

After successful testing:

1. **Review test coverage**: Aim for >90% coverage
2. **Run example script**: Verify real-world usage
3. **Generate dataset**: Test with larger sample sizes
4. **Integrate with Vidyut**: Connect to Rust library for advanced rules

## Quick Reference

```bash
# Full test suite
pytest tests/ -v

# Single test file
pytest tests/test_sandhi_generator.py -v

# With coverage
pytest tests/ --cov=src --cov-report=term

# Run example
python3 examples/sandhi_example.py

# Syntax check
python3 -m py_compile src/generator/sandhi_generator.py
```

---

*Quick Start Guide - Project Panini*  
*Last Updated: January 16, 2026*
