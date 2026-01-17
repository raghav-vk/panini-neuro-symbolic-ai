# Sandhi Generator Module

This module implements the Sandhi (euphonic combination) rule engine for generating synthetic Sanskrit training data.

## Overview

The Sandhi Generator is a core component of Project Panini's data factory. It applies Paninian grammar rules to combine Sanskrit words, generating grammatically perfect training examples for the language model.

## Features

- **Sandhi Rule Application**: Combines two Sanskrit words using phonetic rules
- **Multiple Output Formats**: Supports JSONL, ChatML, and dict formats
- **Dataset Generation**: Generates large-scale training datasets
- **Validation**: Validates Sandhi combinations against expected results

## Usage

### Basic Usage

```python
from generator.sandhi_generator import SandhiGenerator

# Initialize generator
generator = SandhiGenerator()

# Apply Sandhi to combine words
result = generator.apply_sandhi("Deva", "Alaya")
print(result)  # Output: "Devalaya"
```

### Generate Training Pairs

```python
# Generate training examples
word_pairs = [("Deva", "Alaya"), ("Rama", "Ayana")]
examples = generator.generate_training_pairs(word_pairs, output_format="jsonl")

for example in examples:
    print(example)
    # {
    #   "instruction": "Apply Sandhi rules to combine these Sanskrit words.",
    #   "input": "Deva + Alaya",
    #   "output": "Devalaya"
    # }
```

### Generate Dataset

```python
# Generate 1000 training examples
examples = generator.generate_dataset(num_samples=1000)

# Save to file
generator.generate_dataset(
    num_samples=1000,
    output_file="datasets/sandhi_training.jsonl"
)
```

## API Reference

### `SandhiGenerator`

#### Methods

- `apply_sandhi(word1: str, word2: str) -> str`
  - Applies Sandhi rules to combine two words
  - Returns the combined form

- `generate_training_pairs(word_pairs: List[Tuple[str, str]], output_format: str = "jsonl") -> List[Dict]`
  - Generates training examples from word pairs
  - Supports formats: "jsonl", "chatml", "dict"

- `generate_dataset(num_samples: int, output_file: Optional[str] = None) -> List[Dict]`
  - Generates a dataset of training examples
  - Optionally saves to JSONL file

- `validate_sandhi(word1: str, word2: str, expected: str) -> bool`
  - Validates that Sandhi application produces expected result

## Testing

Run tests with pytest:

```bash
pytest tests/test_sandhi_generator.py -v
```

## Future Enhancements

- Integration with Vidyut Rust library for comprehensive rule coverage
- Support for more complex Sandhi rules (Visarga, Anusvara, etc.)
- Automatic word generation from Dhatupatha (root lexicon)
- Grammar validation using Ashtadhyayi rules

---

*Sandhi Generator Module - Project Panini*  
*Last Updated: January 16, 2026*
