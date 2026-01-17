# How to Compile and Test

## Quick Start (3 Steps)

### 1. Install Dependencies

```bash
cd panini-neuro-symbolic-ai
pip install pytest pytest-cov
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run Quick Test Script

```bash
./test_quick.sh
```

This will:
- ✓ Check Python syntax
- ✓ Test module imports
- ✓ Verify basic functionality
- ✓ Run full test suite (if pytest is installed)

### 3. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term
```

---

## Detailed Instructions

### Compile (Syntax Check)

Python doesn't require compilation, but you can verify syntax:

```bash
# Check main module
python3 -m py_compile src/generator/sandhi_generator.py

# Check test file
python3 -m py_compile tests/test_sandhi_generator.py

# Check example script
python3 -m py_compile examples/sandhi_example.py
```

**Expected Output:** No output means success (Python exits silently on success).

### Test

#### Option 1: Quick Test Script (Recommended)

```bash
./test_quick.sh
```

#### Option 2: Manual Testing

**Test Module Import:**
```bash
python3 -c "import sys; sys.path.insert(0, 'src'); from generator.sandhi_generator import SandhiGenerator; print('OK')"
```

**Test Basic Functionality:**
```bash
python3 -c "import sys; sys.path.insert(0, 'src'); from generator.sandhi_generator import SandhiGenerator; g = SandhiGenerator(); print(g.apply_sandhi('Deva', 'Alaya'))"
# Expected output: Devalaya
```

**Run Example Script:**
```bash
python3 examples/sandhi_example.py
```

#### Option 3: Full Test Suite

```bash
# Install pytest first
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_sandhi_generator.py -v

# Run specific test
pytest tests/test_sandhi_generator.py::TestSandhiGenerator::test_apply_sandhi_known_combination -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html  # View coverage report
```

---

## Test Results

### Successful Output

When you run `./test_quick.sh`, you should see:

```
==========================================
Project Panini - Quick Test Script
==========================================

1. Checking Python version...
   Python 3.9.6

2. Checking Python syntax...
   ✓ src/generator/sandhi_generator.py - Syntax OK
   ✓ tests/test_sandhi_generator.py - Syntax OK
   ✓ examples/sandhi_example.py - Syntax OK

3. Testing module import...
   ✓ Module imports successfully

4. Testing basic functionality...
   ✓ Sandhi application works: Deva + Alaya = Devalaya

5. Checking for pytest...
   ✓ pytest 7.4.0

6. Running tests...
   tests/test_sandhi_generator.py::TestSandhiGenerator::test_apply_sandhi_known_combination PASSED
   ...
   ======================== 15 passed in 0.05s ========================

==========================================
Quick test completed!
==========================================
```

### Pytest Output

When running `pytest tests/ -v`, you should see:

```
tests/test_sandhi_generator.py::TestSandhiGenerator::test_apply_sandhi_known_combination PASSED
tests/test_sandhi_generator.py::TestSandhiGenerator::test_apply_sandhi_multiple_known_combinations PASSED
tests/test_sandhi_generator.py::TestSandhiGenerator::test_apply_sandhi_empty_words PASSED
tests/test_sandhi_generator.py::TestSandhiGenerator::test_generate_training_pairs_jsonl_format PASSED
...
======================== 15 passed in 0.05s ========================
```

---

## Troubleshooting

### Issue: `pytest: command not found`

**Solution:**
```bash
pip install pytest pytest-cov
```

### Issue: `ModuleNotFoundError: No module named 'generator'`

**Solution:**
Make sure you're in the project root directory:
```bash
cd panini-neuro-symbolic-ai
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Issue: Permission denied on `test_quick.sh`

**Solution:**
```bash
chmod +x test_quick.sh
```

### Issue: Syntax errors

**Solution:**
- Ensure Python 3.10+ is installed
- Check file encoding (should be UTF-8)
- Verify no hidden characters in files

---

## Next Steps

After successful compilation and testing:

1. **Review test coverage**: Aim for >90%
2. **Run example script**: `python3 examples/sandhi_example.py`
3. **Generate dataset**: Test with larger sample sizes
4. **Integrate with Vidyut**: Connect to Rust library for advanced rules

---

## Quick Reference

```bash
# Quick test (all-in-one)
./test_quick.sh

# Syntax check
python3 -m py_compile src/generator/sandhi_generator.py

# Run tests
pytest tests/ -v

# Run example
python3 examples/sandhi_example.py

# Interactive test
python3
>>> import sys; sys.path.insert(0, 'src')
>>> from generator.sandhi_generator import SandhiGenerator
>>> g = SandhiGenerator()
>>> g.apply_sandhi("Deva", "Alaya")
'Devalaya'
```

---

*Compile and Test Guide - Project Panini*  
*Last Updated: January 16, 2026*
