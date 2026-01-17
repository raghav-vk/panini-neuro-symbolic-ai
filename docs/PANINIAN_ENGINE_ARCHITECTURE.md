# Paninian Engine Architecture: Dual-Path Neuro-Symbolic System

**Version:** 2.1  
**Last Updated:** January 16, 2026  
**Core Concept:** English/Transliterated Sanskrit/Devanagari Input → Paninian Logic → Perfect Sanskrit Output

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [The Dual-Path Pipeline](#the-dual-path-pipeline)
3. [Path A: The Constructor (English → Sanskrit)](#path-a-the-constructor-english--sanskrit)
4. [Path B: The Auditor (Sanskrit → Validation)](#path-b-the-auditor-sanskrit--validation)
5. [Curriculum Learning Strategy](#curriculum-learning-strategy)
6. [System Architecture](#system-architecture)
7. [Implementation Details](#implementation-details)

---

## 🎯 Executive Summary

The **Paninian Engine** is a Neuro-Symbolic system that doesn't just predict the next word—it constructs language according to strict Paninian rules. The system operates as:

1. **Translator** for English inputs → Perfect Sanskrit output
2. **Processor** for transliterated Sanskrit (Roman script) → Validated/corrected Sanskrit
3. **Validator** for Sanskrit inputs (both transliterated and Devanagari) → Grammar correction and validation

**Input Support:**
- **English**: "The boy reads the book"
- **Transliterated Sanskrit**: "Ramah griham gacchati" (Sanskrit in Roman script - IAST, ITRANS, etc.)
- **Devanagari Sanskrit**: "रामः गृहं गच्छति" (Sanskrit in Devanagari script)

**Output Options:**
- Transliterated Sanskrit (IAST, ITRANS, etc.)
- Devanagari Sanskrit
- Both scripts simultaneously

Unlike standard translation systems that map statistical patterns, the Paninian Engine translates **Intent-to-Structure**, ensuring grammatically perfect output that follows Panini's Ashtadhyayi rules.

---

## 🔀 The Dual-Path Pipeline

The system detects input language and script, then routes through the correct "cognitive path":

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT DETECTION LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input: "The boy reads the book"        →  [Language: English]  │
│  Input: "Ramah griham gacchati"         →  [Language: Sanskrit]│
│                                          [Script: Transliterated]│
│  Input: "रामः गृहं गच्छति"              →  [Language: Sanskrit]│
│                                          [Script: Devanagari]   │
│                                                                  │
└────────────────────┬────────────────────┬─────────────────────┘
                      │                     │
                      ▼                     ▼
        ┌─────────────────────┐  ┌─────────────────────┐
        │   PATH A:            │  │   PATH B:            │
        │   CONSTRUCTOR        │  │   AUDITOR            │
        │   (English →        │  │   (Sanskrit →        │
        │    Sanskrit)        │  │    Validation)       │
        │                      │  │   (Handles both     │
        │   • English          │  │    transliterated   │
        │   • Transliterated   │  │    & Devanagari)    │
        │     Sanskrit        │  │                      │
        └─────────────────────┘  └─────────────────────┘
```

---

## 🏗️ Path A: The Constructor (English/Transliterated Sanskrit → Sanskrit)

### Problem Statement

Standard translation (like Google Translate) maps **Statistical English** to **Statistical Sanskrit**. It often fails at grammar (e.g., wrong Vibhakti/case endings).

Additionally, users may input Sanskrit sentences in **English transliteration** (Roman script), which also needs to be processed correctly.

### Solution: Intent-to-Structure Translation

We don't translate sentence-to-sentence. We translate **Intent-to-Structure**.

### Input Types

Path A handles two types of input:

1. **English Sentences**: "The boy reads the book"
2. **Transliterated Sanskrit**: "Ramah griham gacchati" (Sanskrit in Roman script)

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              PATH A: CONSTRUCTOR PIPELINE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input Type Detection:                                           │
│  ├─ "The boy reads the book" → [English]                      │
│  └─ "Ramah griham gacchati" → [Transliterated Sanskrit]        │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Branch: English Input                                    │  │
│  │  │                                                        │  │
│  │  │  Step 1: Semantic Parsing (Karaka Extraction)        │  │
│  │  │  ├─ Actor (Karta): "boy" → Baalah                    │  │
│  │  │  ├─ Object (Karma): "book" → Pustakam                │  │
│  │  │  ├─ Action (Kriya): "reads" → Pathati                 │  │
│  │  │  └─ Voice: Active (Kartari Prayoga)                   │  │
│  │  │                                                        │  │
│  │  │  Step 2: Root Mapping                                 │  │
│  │  │  ├─ "reads" → Root: √path (to read)                  │  │
│  │  │  ├─ "boy" → Pratipadika: Baala                        │  │
│  │  │  └─ "book" → Pratipadika: Pustaka                     │  │
│  │  │                                                        │  │
│  │  └─→ Continue to Step 3                                   │  │
│  │                                                             │  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Branch: Transliterated Sanskrit Input                    │  │
│  │  │                                                        │  │
│  │  │  Step 1: Transliteration Normalization                │  │
│  │  │  ├─ Detect transliteration scheme (IAST/ITRANS/etc)  │  │
│  │  │  ├─ Normalize to standard format                      │  │
│  │  │  └─ "Ramah griham gacchati" → [Normalized]           │  │
│  │  │                                                        │  │
│  │  │  Step 2: Sanskrit Parsing                             │  │
│  │  │  ├─ Tokenize: ["Ramah", "griham", "gacchati"]        │  │
│  │  │  ├─ Parse cases: Nominative, Accusative, Verb         │  │
│  │  │  └─ Extract Karaka relationships                       │  │
│  │  │                                                        │  │
│  │  └─→ Continue to Step 3                                   │  │
│  │                                                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Step 3: Paninian Assembly                                │  │
│  │  ├─ Apply Vibhakti rules:                                 │  │
│  │  │   • Karta (Actor) → Nominative (Prathama)             │  │
│  │  │   • Karma (Object) → Accusative (Dvitiya)             │  │
│  │  ├─ Apply Verb conjugation:                               │  │
│  │  │   • √path + Present + 3rd Person + Singular            │  │
│  │  │   → Pathati                                            │  │
│  │  └─ Apply Sandhi rules:                                   │  │
│  │     • Baalah + pustakam → Baalah pustakam                │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Step 4: Script Conversion (Optional)                    │  │
│  │  ├─ Convert to Devanagari: "रामः गृहं गच्छति"          │  │
│  │  └─ Or keep in transliteration: "Ramah griham gacchati" │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│  Output: "Baalah pustakam pathati" (or "बालः पुस्तकं पठति")   │
│         (Grammatically perfect Sanskrit)                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. Input Type Detector

Detects and classifies input:
- **English**: Natural English sentences
- **Transliterated Sanskrit**: Sanskrit in Roman script (IAST, ITRANS, etc.)
- **Devanagari Sanskrit**: Sanskrit in Devanagari script

#### 2. Semantic Parser (Karaka Extractor)

Extracts semantic roles from English:
- **Karta** (Actor/Agent): Who performs the action
- **Karma** (Object): What is acted upon
- **Karana** (Instrument): With what
- **Sampradana** (Recipient): To whom
- **Apadana** (Source): From where
- **Adhikarana** (Location): Where

#### 3. Transliteration Processor

For transliterated Sanskrit input:
- **Normalization**: Detect and normalize transliteration scheme (IAST, ITRANS, Harvard-Kyoto, etc.)
- **Parsing**: Tokenize and parse Sanskrit text in Roman script
- **Validation**: Check if transliteration is valid Sanskrit

#### 4. Root Mapper

Maps words to Sanskrit roots:
- **English → Sanskrit**: Verbs → Dhatu, Nouns → Pratipadika
- **Transliterated Sanskrit**: Direct mapping (already Sanskrit)
- Uses bilingual dictionary + context

#### 5. Paninian Assembly Engine

Applies Ashtadhyayi rules:
- **Vibhakti Rules**: Case endings based on Karaka
- **Tinganta Rules**: Verb conjugation
- **Sandhi Rules**: Word combination
- **Samasa Rules**: Compound formation

#### 6. Script Converter

Converts output to desired script:
- **Devanagari**: "रामः गृहं गच्छति"
- **Transliteration**: "Ramah griham gacchati" (IAST)
- **Both**: Provide output in multiple scripts

---

## 🔍 Path B: The Auditor (Sanskrit → Validation)

### Problem Statement

User types: `Ramena griham gacchati` (incorrect grammar)

**Note:** Input can be in either:
- **Transliterated Sanskrit**: "Ramena griham gacchati" (Roman script)
- **Devanagari Sanskrit**: "रमेण गृहं गच्छति" (Devanagari script)

### Solution: Deconstruction → Rule Check → Correction

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              PATH B: AUDITOR PIPELINE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input: "Ramena griham gacchati" (or "रमेण गृहं गच्छति")        │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Step 1: Script Detection & Normalization                │  │
│  │  ├─ Detect script: Transliterated or Devanagari          │  │
│  │  ├─ If Devanagari: Convert to transliteration (IAST)     │  │
│  │  └─ Normalize to standard format                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Step 2: Deconstruction                                    │  │
│  │  ├─ Tokenize: ["Ramena", "griham", "gacchati"]           │  │
│  │  ├─ Parse cases:                                          │  │
│  │  │   • Ramena → Instrumental (Tritiya)                    │  │
│  │  │   • griham → Accusative (Dvitiya)                     │  │
│  │  │   • gacchati → Active voice, 3rd person, singular     │  │
│  │  └─ Extract Karaka relationships                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Step 3: Rule Check (Paninian Validation)                │  │
│  │  ├─ Check: Agent of active verb (gacchati)               │  │
│  │  ├─ Rule: Must be in Nominative (Prathama)                │  │
│  │  ├─ Found: Ramena (Instrumental/Tritiya)                  │  │
│  │  └─ Conflict: ❌ Rule violation detected                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Step 4: Correction Suggestion                            │  │
│  │  ├─ Correct form: Ramah (Nominative)                      │  │
│  │  ├─ Apply Sandhi: Ramah + griham → Ramah griham          │  │
│  │  └─ Output: "Ramah griham gacchati"                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Step 5: Script Conversion (Optional)                     │  │
│  │  ├─ Convert to Devanagari: "रामः गृहं गच्छति"            │  │
│  │  └─ Or keep in transliteration: "Ramah griham gacchati" │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│  Output: "Ramah griham gacchati" (or "रामः गृहं गच्छति")       │
│         (Corrected with explanation)                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. Script Detector & Converter

- Detects input script (Transliterated or Devanagari)
- Converts Devanagari to transliteration for processing
- Normalizes transliteration schemes (IAST, ITRANS, etc.)

#### 2. Sanskrit Parser

- Tokenizes Sanskrit text (both scripts)
- Identifies case endings (Vibhakti)
- Extracts verb forms (Tinganta)
- Parses compound words (Samasa)

#### 3. Rule Validator

Checks against Paninian rules:
- **Karaka-Vibhakti Mapping**: Correct case for semantic role
- **Verb-Agreement**: Person, number, gender agreement
- **Sandhi Rules**: Proper word combination
- **Samasa Rules**: Valid compound formation

#### 4. Correction Engine

Suggests corrections:
- Identifies rule violations
- Proposes correct forms
- Explains the error
- Provides alternative constructions
- Outputs in user's preferred script (transliteration or Devanagari)

---

## 📚 Curriculum Learning Strategy

The model learns in three stages, mimicking how a student learns Sanskrit:

### Stage 1: The "Dhatu-Patha" (Morphology)

**Goal:** Teach the model how to build words from roots.

**Data:** Millions of synthetic pairs generated by Rust engine (Vidyut).

**Example:**
```
Input:  Root: √gam + Tense: Present + Person: 3rd + Number: Singular
Output: Gacchati
```

**Why:** This "hard-wires" the grammar tables into the model's weights.

**Training Focus:**
- Verb conjugation (Tinganta)
- Noun declension (Subanta)
- Sandhi rules
- Basic sentence structure

**Dataset Size:** 1-5 million examples

---

### Stage 2: The "Karaka" (Syntax & Translation)

**Goal:** Teach the model sentence construction and English mapping.

**Data:** Parallel Corpus (English-Sanskrit).

**Sources:**
- IIT Bombay English-Sanskrit Corpus
- Samskrita Bharati texts
- Manually curated translation pairs

**Example:**
```
Input:  "The boy reads the book"
Output: "Baalah pustakam pathati"
```

**Training Constraint:** Heavily penalize the model during training if it uses the wrong case ending.

**Training Focus:**
- Karaka-Vibhakti mapping
- English-to-Sanskrit translation
- Semantic role extraction
- Sentence structure

**Dataset Size:** 100K-500K examples

---

### Stage 3: The "Kavya" (Style & Essay Writing)

**Goal:** Evolve from sentences to Essays/Novels.

**Data:** Classical literature:
- The Panchatantra
- Hitopadesha
- Kalidasa's works (Meghaduta, Raghuvamsha)

**Task:** Long-Context Generation

**Example:**
```
Prompt: "Write a paragraph about the importance of truth."
Output: [Long-form Sanskrit text in Kalidasa's style]
```

**Mechanism:** The model uses the vocabulary of Kalidasa but the strict grammar structure learned in Stage 1.

**Training Focus:**
- Stylistic variation
- Long-form generation
- Literary devices
- Contextual coherence

**Dataset Size:** 50K-200K examples

---

## 🏛️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PANINIAN ENGINE SYSTEM                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              INPUT PROCESSING LAYER                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │   English    │  │ Transliterated│  │  Devanagari │   │  │
│  │  │   Input     │  │   Sanskrit   │  │   Sanskrit  │   │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │  │
│  │         │                │                 │          │  │
│  │         ▼                ▼                 ▼          │  │
│  │  ┌──────────────────────────────────────────────┐     │  │
│  │  │  Language & Script Detection & Routing        │     │  │
│  │  │  ├─ Detect: English / Transliterated /       │     │  │
│  │  │  │          Devanagari                        │     │  │
│  │  │  └─ Route to appropriate path                 │     │  │
│  │  └──────────────────────────────────────────────┘     │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          │                                      │
│         ┌────────────────┴────────────────┐                   │
│         │                                  │                    │
│         ▼                                  ▼                    │
│  ┌──────────────────┐        ┌──────────────────┐            │
│  │  PATH A:          │        │  PATH B:         │            │
│  │  CONSTRUCTOR      │        │  AUDITOR         │            │
│  │                   │        │                  │            │
│  │  ┌──────────────┐ │        │  ┌──────────────┐│            │
│  │  │  Semantic    │ │        │  │  Sanskrit    ││            │
│  │  │  Parser      │ │        │  │  Parser      ││            │
│  │  └──────┬───────┘ │        │  └──────┬───────┘│            │
│  │         │          │        │         │        │            │
│  │         ▼          │        │         ▼        │            │
│  │  ┌──────────────┐  │        │  ┌──────────────┐│            │
│  │  │  Root        │  │        │  │  Rule        ││            │
│  │  │  Mapper      │  │        │  │  Validator   ││            │
│  │  └──────┬───────┘  │        │  └──────┬───────┘│            │
│  │         │           │        │         │        │            │
│  │         ▼           │        │         ▼        │            │
│  │  ┌──────────────┐   │        │  ┌──────────────┐│            │
│  │  │  Paninian    │   │        │  │  Correction  ││            │
│  │  │  Assembly    │   │        │  │  Engine     ││            │
│  │  └──────┬───────┘   │        │  └──────┬───────┘│            │
│  │         │            │        │         │        │            │
│  └─────────┼────────────┘        └─────────┼────────┘            │
│            │                               │                     │
│            └───────────────┬───────────────┘                     │
│                            ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              OUTPUT LAYER                                  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Perfect Sanskrit + Grammar Explanation              │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Training Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              CURRICULUM LEARNING PIPELINE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  STAGE 1: Dhatu-Patha (Morphology)                       │  │
│  │  ├─ Synthetic data from Vidyut                          │  │
│  │  ├─ Focus: Word formation from roots                     │  │
│  │  └─ Output: Model understands grammar tables            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  STAGE 2: Karaka (Syntax & Translation)                    │  │
│  │  ├─ Parallel corpus (English-Sanskrit)                   │  │
│  │  ├─ Focus: Sentence construction & translation          │  │
│  │  └─ Output: Model can translate English → Sanskrit       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  STAGE 3: Kavya (Style & Essay Writing)                  │  │
│  │  ├─ Classical literature (Kalidasa, etc.)                │  │
│  │  ├─ Focus: Long-form generation & style                   │  │
│  │  └─ Output: Model can write essays in Sanskrit           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementation Details

### Component Structure

```
paninian_engine/
├── input_processor/
│   ├── language_detector.py      # Detect English vs Sanskrit
│   ├── script_detector.py         # Detect transliteration vs Devanagari
│   └── router.py                 # Route to Path A or B
│
├── path_a_constructor/
│   ├── semantic_parser.py        # Extract Karaka from English
│   ├── transliteration_processor.py # Process transliterated Sanskrit
│   ├── root_mapper.py            # Map English → Sanskrit roots
│   ├── paninian_assembler.py      # Apply rules & assemble
│   └── script_converter.py        # Convert to Devanagari/transliteration
│
├── path_b_auditor/
│   ├── script_converter.py       # Convert Devanagari ↔ transliteration
│   ├── sanskrit_parser.py        # Parse Sanskrit text (both scripts)
│   ├── rule_validator.py         # Check Paninian rules
│   └── correction_engine.py      # Suggest corrections
│
├── training/
│   ├── stage1_dhatupatha.py      # Morphology training
│   ├── stage2_karaka.py          # Syntax & translation training
│   └── stage3_kavya.py           # Style & essay training
│
└── core/
    ├── paninian_rules.py          # Ashtadhyayi rule engine
    └── vidyut_bindings.py         # Rust library bindings
```

### Training Data Format

**Stage 1 (Dhatu-Patha):**
```json
{
  "input": "Root: √gam + Tense: Present + Person: 3rd + Number: Singular",
  "output": "Gacchati",
  "rules_applied": ["3.1.68", "7.3.78"],
  "stage": "dhatupatha"
}
```

**Stage 2 (Karaka):**
```json
{
  "input": "The boy reads the book",
  "output": "Baalah pustakam pathati",
  "output_devanagari": "बालः पुस्तकं पठति",
  "karaka": {
    "karta": {"word": "boy", "case": "nominative", "sanskrit": "Baalah"},
    "karma": {"word": "book", "case": "accusative", "sanskrit": "pustakam"}
  },
  "stage": "karaka"
}
```

**Note:** Input can also be transliterated Sanskrit:
```json
{
  "input": "Ramah griham gacchati",
  "input_type": "transliterated_sanskrit",
  "output": "Ramah griham gacchati",
  "output_devanagari": "रामः गृहं गच्छति",
  "validation": "correct",
  "stage": "karaka"
}
```

**Stage 3 (Kavya):**
```json
{
  "input": "Write a paragraph about the importance of truth.",
  "output": "[Long-form Sanskrit text...]",
  "style": "kalidasa",
  "stage": "kavya"
}
```

---

## 🎯 Key Innovations

1. **Intent-to-Structure Translation**: Not statistical mapping, but rule-based construction
2. **Dual-Path Architecture**: Separate paths for translation and validation
3. **Multi-Script Support**: Handles English, transliterated Sanskrit, and Devanagari Sanskrit
4. **Curriculum Learning**: Three-stage progression from morphology to style
5. **Paninian Rule Enforcement**: Grammar correctness guaranteed by symbolic rules
6. **Neuro-Symbolic Hybrid**: Neural network learns patterns, symbolic engine enforces rules
7. **Flexible Input/Output**: Accepts and outputs in multiple scripts (transliteration or Devanagari)

---

*Paninian Engine Architecture Version 2.0*  
*Last Updated: January 16, 2026*  
*Project Panini Engineering Team*
