# Issue #1 Implementation: Sandhi Generator

## Overview

This document describes the implementation of the Sandhi Generator module, which addresses the core requirement from the project documentation: generating synthetic Sanskrit training data by applying Sandhi (euphonic combination) rules.

## Problem Statement

From the project documentation (Step 2: The "Sandhi" Synthetic Generator):

> Sanskrit is agglutinative; words stick together. LLMs struggle with this.
> 
> **The Script:** Write a Python script that takes two valid words (e.g., Deva + Alaya) and applies the Sandhi rule to create the combined form (Devalaya).
> 
> **The Dataset:** Generate 100,000 pairs of Input: "Deva Alaya" -> Target: "Devalaya".
> 
> **Why:** This "pre-teaches" the model tokenization logic before it even tries to understand meaning.

## Solution

### Implementation

Created a comprehensive Sandhi Generator module with the following components:

1. **Core Module**: `src/generator/sandhi_generator.py`
   - `SandhiGenerator` class with Sandhi rule application
   - Support for multiple output formats (JSONL, ChatML, dict)
   - Dataset generation capabilities
   - Validation functions

2. **Test Suite**: `tests/test_sandhi_generator.py`
   - Comprehensive unit tests
   - Integration tests
   - Edge case handling
   - File I/O testing

3. **Example Script**: `examples/sandhi_example.py`
   - Demonstrates usage patterns
   - Shows different output formats

4. **Documentation**:
   - Module README: `src/generator/README.md`
   - Testing guide: `tests/README.md`

### Key Features

#### 1. Sandhi Rule Application

```python
from generator.sandhi_generator import SandhiGenerator

generator = SandhiGenerator()
result = generator.apply_sandhi("Deva", "Alaya")
# Returns: "Devalaya"
```

#### 2. Training Data Generation

The generator creates training examples in multiple formats:

**JSONL Format** (for fine-tuning):
```json
{
  "instruction": "Apply Sandhi rules to combine these Sanskrit words.",
  "input": "Deva + Alaya",
  "output": "Devalaya"
}
```

**ChatML Format** (for conversational models):
```json
{
  "messages": [
    {"role": "user", "content": "Combine these Sanskrit words using Sandhi: Deva + Alaya"},
    {"role": "assistant", "content": "Devalaya"}
  ]
}
```

#### 3. Dataset Generation

```python
# Generate 1000 training examples
examples = generator.generate_dataset(num_samples=1000)

# Save to file
generator.generate_dataset(
    num_samples=1000,
    output_file="datasets/sandhi_training.jsonl"
)
```

## Files Created

1. **`src/generator/sandhi_generator.py`** (249 lines)
   - Main implementation with SandhiGenerator class
   - Rule mappings and word combination logic
   - Dataset generation functions

2. **`tests/test_sandhi_generator.py`** (200+ lines)
   - 15+ test cases covering:
     - Known combinations
     - Error handling
     - Multiple output formats
     - File I/O
     - Integration tests

3. **`tests/__init__.py`**
   - Package initialization

4. **`examples/sandhi_example.py`**
   - Usage examples and demonstrations

5. **`src/generator/README.md`**
   - API documentation
   - Usage examples
   - Future enhancements

6. **`tests/README.md`**
   - Testing guide
   - How to run tests
   - Writing new tests

## Testing

### Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_sandhi_generator.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage

The test suite includes:

- ✅ Known Sandhi combinations (Deva + Alaya -> Devalaya)
- ✅ Multiple word pair combinations
- ✅ Error handling (empty words, None values)
- ✅ Multiple output formats (JSONL, ChatML, dict)
- ✅ Dataset generation
- ✅ File I/O operations
- ✅ Validation functions
- ✅ Integration tests
- ✅ Large dataset generation

## Usage Examples

### Example 1: Basic Sandhi Application

```python
from generator.sandhi_generator import SandhiGenerator

generator = SandhiGenerator()

# Test known combinations
test_cases = [
    ("Deva", "Alaya"),
    ("Rama", "Ayana"),
    ("Krishna", "Arjuna"),
]

for word1, word2 in test_cases:
    combined = generator.apply_sandhi(word1, word2)
    print(f"{word1} + {word2} = {combined}")
```

### Example 2: Generate Training Dataset

```python
# Generate 100,000 training examples
examples = generator.generate_dataset(
    num_samples=100000,
    output_file="datasets/sandhi_100k.jsonl"
)

print(f"Generated {len(examples)} training examples")
```

### Example 3: Custom Word Pairs

```python
# Use your own word pairs
word_pairs = [
    ("Deva", "Alaya"),
    ("Rama", "Ayana"),
    # ... more pairs
]

examples = generator.generate_training_pairs(
    word_pairs,
    output_format="jsonl"
)
```

## Future Enhancements

1. **Vidyut Integration**: Connect with Vidyut Rust library for comprehensive Paninian rule coverage
2. **Advanced Sandhi Rules**: Implement more complex rules (Visarga, Anusvara, etc.)
3. **Automatic Word Generation**: Generate words from Dhatupatha (root lexicon)
4. **Grammar Validation**: Validate combinations using Ashtadhyayi rules
5. **Performance Optimization**: Optimize for large-scale dataset generation (100k+ examples)

## Dependencies

Added to `requirements.txt`:
- `pytest>=7.4.0` - Testing framework
- `pytest-cov>=4.1.0` - Coverage reporting

## Verification

To verify the implementation:

1. **Check syntax**:
   ```bash
   python3 -m py_compile src/generator/sandhi_generator.py
   python3 -m py_compile tests/test_sandhi_generator.py
   ```

2. **Run example**:
   ```bash
   python3 examples/sandhi_example.py
   ```

3. **Run tests** (after installing pytest):
   ```bash
   pytest tests/test_sandhi_generator.py -v
   ```

## Status

✅ **Implementation Complete**

- Core Sandhi generator module implemented
- Comprehensive test suite created
- Documentation provided
- Example scripts included
- Ready for integration with Vidyut and training pipeline

---

*Issue #1 Implementation - Project Panini*  
*Last Updated: January 16, 2026*
