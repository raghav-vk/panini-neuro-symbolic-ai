# Stage 1: Dhatu-Patha Dataset Generation Guide

This guide explains how to generate Stage 1 training datasets using data from the [ashtadhyayi-com/data](https://github.com/ashtadhyayi-com/data) repository.

## Overview

Stage 1: Dhatu-Patha (Morphology) focuses on word formation from roots:
- **Verb conjugation (Tinganta)**: Root + Tense + Person + Number → Verb form
- **Noun declension (Subanta)**: Pratipadika + Case + Number → Noun form
- **Sandhi rules**: Word combination

## Data Source

The [ashtadhyayi-com/data](https://github.com/ashtadhyayi-com/data) repository contains:
- **`dhatu/`**: Verb roots (dhatu) with gana classifications
- **`sutraani/`**: Panini's sutras (rules) from Ashtadhyayi
- **`shabda/`**: Word forms and their derivations
- **`ganapath/`**: Gana classifications
- **`kosha/`**: Dictionary entries

## Usage

### Basic Usage

```bash
python3 scripts/generate_stage1_dataset.py
```

This will:
1. Clone/update the ashtadhyayi-com/data repository
2. Extract dhatu (verb roots), sutras (rules), and shabda (word forms)
3. Generate training examples in Stage 1 format
4. Save to `datasets/stage1_dhatupatha.jsonl`

### Output Format

Each example follows the Stage 1 format:

```json
{
  "id": 1,
  "instruction": "Generate the Sanskrit verb form from the root and grammatical specifications.",
  "input": "Root: √gam + Tense: Present + Person: 3rd + Number: Singular",
  "output": "Gacchati",
  "root": "√gam",
  "tense": "Present",
  "person": 3,
  "number": "Singular",
  "rules_applied": ["3.1.68", "3.1.77"],
  "stage": "dhatupatha",
  "type": "verb_conjugation"
}
```

### Verb Conjugation Examples

The script generates examples for:
- **Tenses**: Present, Past, Future
- **Persons**: 1st, 2nd, 3rd
- **Numbers**: Singular, Plural
- **Roots**: From ashtadhyayi-com/data or common roots

### Noun Declension Examples

The script generates examples for:
- **Cases**: Nominative, Accusative, Instrumental, Dative, Ablative, Genitive, Locative, Vocative
- **Numbers**: Singular, Dual, Plural
- **Genders**: Masculine, Feminine, Neuter

## Repository Structure

The ashtadhyayi-com/data repository structure:

```
ashtadhyayi-com/data/
├── dhatu/          # Verb roots
│   ├── *.json      # Dhatu data in JSON format
│   └── *.txt       # Dhatu data in text format
├── sutraani/       # Panini's sutras
│   ├── *.json      # Sutra data
│   └── *.txt       # Sutra text
├── shabda/         # Word forms
│   └── *.json      # Shabda derivations
├── ganapath/       # Gana classifications
└── kosha/          # Dictionary
```

## Integration with Vidyut

**Important**: The current script uses simplified form generation. For production:

1. **Integrate Vidyut**: Use the Vidyut Rust library for accurate form generation
2. **Python Bindings**: Create pyo3 bindings to call Vidyut from Python
3. **Rule Application**: Use actual Paninian rules from sutraani data

### Example Vidyut Integration (Future)

```python
from vidyut_bindings import VidyutEngine

engine = VidyutEngine()
form = engine.generate_verb_form(
    root="√gam",
    tense="present",
    person=3,
    number="singular"
)
# Returns: "gacchati"
```

## Customization

### Adjusting Example Counts

Edit the script to change maximum examples:

```python
examples = generator.generate_dataset(
    max_verb_examples=50000,  # Increase verb examples
    max_noun_examples=25000   # Increase noun examples
)
```

### Adding More Roots

Add custom dhatu to the generator:

```python
custom_dhatu = [
    {"root": "√your_root", "meaning": "your meaning", "gana": "1"}
]
generator.dhatu_list.extend(custom_dhatu)
```

## Data Validation

After generation, validate the dataset:

```bash
# Check format
cat datasets/stage1_dhatupatha.jsonl | jq . | head -50

# Count examples
wc -l datasets/stage1_dhatupatha.jsonl

# Check verb vs noun distribution
cat datasets/stage1_dhatupatha.jsonl | jq -r '.type' | sort | uniq -c
```

## Next Steps

1. **Review Generated Forms**: Validate that generated forms are correct
2. **Integrate Vidyut**: Replace simplified generation with Vidyut
3. **Scale Up**: Generate millions of examples for full training
4. **Add Sandhi Examples**: Include Sandhi rule examples
5. **Training**: Use dataset for Stage 1 training experiment

## References

- [ashtadhyayi-com/data Repository](https://github.com/ashtadhyayi-com/data)
- [Ashtadhyayi.com Website](https://ashtadhyayi.com)
- [Vidyut Project](https://github.com/ambuda-org/vidyut) - Rust-based Paninian engine

---

*Stage 1 Dataset Generation Guide - Project Panini*  
*Last Updated: January 16, 2026*
