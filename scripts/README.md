# Scripts Directory

This directory contains utility scripts for the Paninian Engine project.

## generate_toy_dataset.py

Generates a toy dataset of 50+ English-to-Sanskrit sentence pairs with complete grammatical breakdowns for the Proof of Concept (POC) training experiment.

### Usage

```bash
python3 scripts/generate_toy_dataset.py
```

### Output

Creates `datasets/toy_dataset.jsonl` with training examples in the following format:

```json
{
  "id": 1,
  "instruction": "Translate this English sentence to Sanskrit using correct case endings (Vibhakti) according to Panini's rules.",
  "input": "The boy reads the book",
  "output": "Baalah pustakam pathati",
  "output_devanagari": "[Devanagari: Baalah pustakam pathati]",
  "karaka": {
    "karta": {
      "word": "boy",
      "sanskrit": "Baalah",
      "case": "nominative",
      "vibhakti": "prathama"
    },
    "karma": {
      "word": "book",
      "sanskrit": "pustakam",
      "case": "accusative",
      "vibhakti": "dvitiya"
    },
    "kriya": {
      "word": "reads",
      "root": "√path",
      "tense": "present",
      "person": 3,
      "number": "singular"
    }
  },
  "grammar_notes": "Karta (Agent): 'boy' → Baalah (nominative case, prathama); Karma (Object): 'book' → pustakam (accusative case, dvitiya); Kriya (Verb): 'reads' → √path → present, 3rd person, singular",
  "stage": "karaka",
  "complexity": "medium"
}
```

### Features

- **53 sentence pairs** covering various grammatical structures
- **Complete Karaka breakdown**: Karta, Karma, Karana, Sampradana, Apadana, Adhikarana
- **Grammar notes**: Detailed explanations of case endings and verb forms
- **Complexity levels**: Simple, medium, and complex sentences
- **Stage 2 format**: Ready for Karaka (Syntax & Translation) training

### Sentence Types Included

1. **Simple Subject-Verb**: "The boy reads"
2. **Subject-Verb-Object**: "The boy reads the book"
3. **With Location (Adhikarana)**: "The sun rises in the east"
4. **With Recipient (Sampradana)**: "The boy gives a book to the teacher"
5. **With Source (Apadana)**: "The student comes from the school"
6. **With Instrument (Karana)**: "The king rules with justice"
7. **Plural subjects**: "The students read books"

### Next Steps

After generating the dataset:

1. **Review the dataset**:
   ```bash
   cat datasets/toy_dataset.jsonl | jq .
   ```

2. **Use for training**: This dataset is ready for Stage 2 (Karaka) training experiments

3. **Validate grammar**: Check that all case endings follow Panini's rules

---

*Scripts Directory - Project Panini*  
*Last Updated: January 16, 2026*
