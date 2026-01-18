# GitHub Issues for Community Contribution

This document contains issue templates for the Paninian Engine project. Use these to create issues on GitHub.

---

## Stage 1: Dhatu-Patha (Morphology) Dataset

### Issue #1: Extract and Parse Dhatu (Verb Roots) from Ashtadhyayi Repository

**Labels:** `stage-1`, `dataset`, `good-first-issue`, `data-engineering`

**Description:**
Extract verb roots (dhatu) from the [ashtadhyayi-com/data](https://github.com/ashtadhyayi-com/data) repository and create a structured dataset.

**Tasks:**
- [ ] Clone/access ashtadhyayi-com/data repository
- [ ] Parse dhatu data from `dhatu/` directory
- [ ] Extract root, gana, meaning, and other metadata
- [ ] Create structured JSON/CSV output
- [ ] Validate data quality
- [ ] Document data format

**Acceptance Criteria:**
- All dhatu entries extracted and structured
- Data validated for completeness
- Documentation provided

**References:**
- [ashtadhyayi-com/data](https://github.com/ashtadhyayi-com/data)
- Stage 1 requirements in `docs/approach-to-solution.md`

---

### Issue #2: Generate Verb Conjugation Examples from Dhatu

**Labels:** `stage-1`, `dataset`, `morphology`

**Description:**
Generate training examples for verb conjugation (Tinganta) using extracted dhatu data.

**Tasks:**
- [ ] Use extracted dhatu data
- [ ] Generate examples for all tenses (Present, Past, Future)
- [ ] Generate examples for all persons (1st, 2nd, 3rd)
- [ ] Generate examples for all numbers (Singular, Plural)
- [ ] Format: `Root: √gam + Tense: Present + Person: 3rd + Number: Singular → Gacchati`
- [ ] Include applicable Panini sutra numbers
- [ ] Generate 10,000+ examples

**Acceptance Criteria:**
- 10,000+ verb conjugation examples generated
- All combinations covered
- Output in Stage 1 JSONL format
- Sutra numbers included

---

### Issue #3: Generate Noun Declension Examples

**Labels:** `stage-1`, `dataset`, `morphology`

**Description:**
Generate training examples for noun declension (Subanta) from pratipadika (noun bases).

**Tasks:**
- [ ] Extract/common pratipadika list
- [ ] Generate examples for all cases (8 Vibhakti)
- [ ] Generate examples for all numbers (Singular, Dual, Plural)
- [ ] Generate examples for all genders (Masculine, Feminine, Neuter)
- [ ] Format: `Pratipadika: Rama + Case: Nominative + Number: Singular → Ramah`
- [ ] Include applicable Panini sutra numbers
- [ ] Generate 5,000+ examples

**Acceptance Criteria:**
- 5,000+ noun declension examples generated
- All case/number/gender combinations covered
- Output in Stage 1 JSONL format

---

### Issue #4: Integrate Vidyut for Accurate Form Generation

**Labels:** `stage-1`, `enhancement`, `vidyut`, `integration`

**Description:**
Replace simplified form generation with Vidyut Rust library for accurate Paninian form generation.

**Tasks:**
- [ ] Research Vidyut Python bindings (pyo3)
- [ ] Create Python wrapper for Vidyut
- [ ] Integrate with dataset generation script
- [ ] Replace simplified generation logic
- [ ] Validate generated forms
- [ ] Update documentation

**Acceptance Criteria:**
- Vidyut integrated successfully
- All forms generated using actual Paninian rules
- Performance acceptable for large-scale generation

**References:**
- [Vidyut Project](https://github.com/ambuda-org/vidyut)

---

### Issue #5: Generate Sandhi Rule Training Examples

**Labels:** `stage-1`, `dataset`, `sandhi`

**Description:**
Generate training examples for Sandhi (euphonic combination) rules.

**Tasks:**
- [ ] Use existing SandhiGenerator (from Issue #1)
- [ ] Generate 100,000+ Sandhi examples
- [ ] Cover all major Sandhi rules
- [ ] Include both transliterated and Devanagari formats
- [ ] Format: `Input: "Deva Alaya" → Output: "Devalaya"`
- [ ] Include rule explanations

**Acceptance Criteria:**
- 100,000+ Sandhi examples generated
- All major rules covered
- Output in Stage 1 JSONL format

---

## Stage 2: Karaka (Syntax & Translation) Dataset

### Issue #6: Create English-Sanskrit Parallel Corpus Parser

**Labels:** `stage-2`, `dataset`, `translation`, `good-first-issue`

**Description:**
Create a parser to extract English-Sanskrit sentence pairs from existing corpora.

**Tasks:**
- [ ] Research available English-Sanskrit corpora
  - IIT Bombay English-Sanskrit Corpus
  - Samskrita Bharati texts
  - Other available sources
- [ ] Create parser for corpus format
- [ ] Extract sentence pairs
- [ ] Validate translation quality
- [ ] Structure data for training

**Acceptance Criteria:**
- Parser extracts sentence pairs successfully
- Data validated for quality
- Ready for Karaka analysis

---

### Issue #7: Implement Karaka (Semantic Role) Extractor for English

**Labels:** `stage-2`, `feature`, `nlp`, `semantic-parsing`

**Description:**
Implement semantic role extraction (Karaka) from English sentences for Path A (Constructor).

**Tasks:**
- [ ] Research semantic role labeling (SRL) tools
- [ ] Implement Karaka extraction:
  - Karta (Agent/Actor)
  - Karma (Object)
  - Karana (Instrument)
  - Sampradana (Recipient)
  - Apadana (Source)
  - Adhikarana (Location)
- [ ] Map to Sanskrit semantic roles
- [ ] Create training examples with Karaka annotations

**Acceptance Criteria:**
- Karaka extraction working for English sentences
- Accurate mapping to Sanskrit roles
- Examples generated with annotations

---

### Issue #8: Generate Karaka-Vibhakti Mapping Examples

**Labels:** `stage-2`, `dataset`, `syntax`

**Description:**
Generate training examples showing correct Karaka to Vibhakti (case ending) mapping.

**Tasks:**
- [ ] Create examples for each Karaka type
- [ ] Show correct Vibhakti for each semantic role
- [ ] Include incorrect examples (for error learning)
- [ ] Format: `Karta (Agent) → Nominative (Prathama)`
- [ ] Generate 50,000+ examples

**Acceptance Criteria:**
- All Karaka-Vibhakti mappings covered
- 50,000+ examples generated
- Incorrect examples included for contrastive learning

---

### Issue #9: Create English-to-Sanskrit Translation Dataset

**Labels:** `stage-2`, `dataset`, `translation`

**Description:**
Create comprehensive English-to-Sanskrit translation dataset with grammatical breakdowns.

**Tasks:**
- [ ] Use parallel corpus from Issue #6
- [ ] Add Karaka analysis (from Issue #7)
- [ ] Add Vibhakti annotations
- [ ] Include grammar notes
- [ ] Format in Stage 2 JSONL format
- [ ] Generate 100,000+ examples

**Acceptance Criteria:**
- 100,000+ translation examples
- Complete grammatical breakdowns
- Ready for Stage 2 training

---

### Issue #10: Implement Transliteration Normalization

**Labels:** `stage-2`, `feature`, `transliteration`

**Description:**
Implement transliteration scheme detection and normalization (IAST, ITRANS, Harvard-Kyoto, etc.).

**Tasks:**
- [ ] Research transliteration schemes
- [ ] Implement scheme detection
- [ ] Create normalization to IAST
- [ ] Support conversion between schemes
- [ ] Add to Path A (Constructor) pipeline

**Acceptance Criteria:**
- Multiple transliteration schemes supported
- Automatic detection working
- Normalization accurate

---

## Stage 3: Kavya (Style & Essay Writing) Dataset

### Issue #11: Parse Classical Sanskrit Literature

**Labels:** `stage-3`, `dataset`, `literature`, `good-first-issue`

**Description:**
Parse and structure classical Sanskrit texts (Kalidasa, Panchatantra, Hitopadesha) for Stage 3 training.

**Tasks:**
- [ ] Identify sources (GRETIL, cltk, etc.)
- [ ] Create parser for classical texts
- [ ] Extract long-form passages
- [ ] Clean and structure data
- [ ] Add metadata (author, work, style)

**Acceptance Criteria:**
- Classical texts parsed and structured
- Ready for Stage 3 training
- Metadata included

**References:**
- [GRETIL](http://gretil.sub.uni-goettingen.de/gretil.html)
- [cltk](https://github.com/cltk/cltk)

---

### Issue #12: Generate Long-Context Training Examples

**Labels:** `stage-3`, `dataset`, `long-context`

**Description:**
Generate training examples for long-form Sanskrit generation (essays, paragraphs).

**Tasks:**
- [ ] Use parsed classical literature
- [ ] Create prompt-response pairs
- [ ] Format: `"Write about truth" → [Long-form Sanskrit text]`
- [ ] Include style annotations
- [ ] Generate 10,000+ examples

**Acceptance Criteria:**
- 10,000+ long-form examples
- Various styles represented
- Ready for Stage 3 training

---

## Dataset Verification & Validation

### Issue #13: Create Grammar Validation Tool

**Labels:** `validation`, `testing`, `grammar`

**Description:**
Create a tool to validate that generated Sanskrit forms follow Panini's rules.

**Tasks:**
- [ ] Integrate with Vidyut or create rule checker
- [ ] Validate verb conjugations
- [ ] Validate noun declensions
- [ ] Check Sandhi applications
- [ ] Generate validation reports

**Acceptance Criteria:**
- Validation tool working
- Can validate all form types
- Reports generated

---

### Issue #14: Create Test Dataset for Model Evaluation

**Labels:** `testing`, `dataset`, `evaluation`

**Description:**
Create a gold-standard test dataset for evaluating model performance.

**Tasks:**
- [ ] Create test cases for each stage
- [ ] Include edge cases
- [ ] Include error cases (for validation testing)
- [ ] Create evaluation metrics
- [ ] Document test cases

**Acceptance Criteria:**
- Comprehensive test dataset
- Covers all stages
- Evaluation metrics defined

---

### Issue #15: Implement Dataset Quality Checks

**Labels:** `validation`, `quality`, `automation`

**Description:**
Implement automated quality checks for generated datasets.

**Tasks:**
- [ ] Check for duplicates
- [ ] Validate format consistency
- [ ] Check grammar correctness
- [ ] Verify completeness
- [ ] Generate quality reports

**Acceptance Criteria:**
- Automated checks working
- Quality reports generated
- Issues flagged automatically

---

## Model Training & Testing

### Issue #16: Implement Stage 1 Training Script

**Labels:** `training`, `stage-1`, `pytorch`

**Description:**
Create training script for Stage 1: Dhatu-Patha using Unsloth and LoRA.

**Tasks:**
- [ ] Set up Unsloth framework
- [ ] Configure LoRA adapters
- [ ] Create data loader for Stage 1 format
- [ ] Implement training loop
- [ ] Add logging (W&B/TensorBoard)
- [ ] Test on toy dataset

**Acceptance Criteria:**
- Training script working
- Can train on Stage 1 dataset
- Metrics logged

---

### Issue #17: Implement Stage 2 Training Script

**Labels:** `training`, `stage-2`, `pytorch`

**Description:**
Create training script for Stage 2: Karaka with weighted loss for Vibhakti errors.

**Tasks:**
- [ ] Extend Stage 1 training script
- [ ] Implement weighted loss function
- [ ] Heavy penalty for wrong case endings
- [ ] Create data loader for Stage 2 format
- [ ] Test on toy dataset

**Acceptance Criteria:**
- Training script with weighted loss
- Vibhakti errors heavily penalized
- Can train on Stage 2 dataset

---

### Issue #18: Implement Stage 3 Training Script

**Labels:** `training`, `stage-3`, `pytorch`, `long-context`

**Description:**
Create training script for Stage 3: Kavya with long-context support.

**Tasks:**
- [ ] Extend training script for long contexts
- [ ] Configure context window
- [ ] Create data loader for Stage 3 format
- [ ] Implement style-aware training
- [ ] Test on classical literature

**Acceptance Criteria:**
- Long-context training working
- Style preservation
- Can train on Stage 3 dataset

---

### Issue #19: Create Model Evaluation Framework

**Labels:** `testing`, `evaluation`, `metrics`

**Description:**
Create comprehensive evaluation framework for all stages.

**Tasks:**
- [ ] Implement evaluation metrics
- [ ] Create evaluation scripts
- [ ] Test on gold-standard dataset
- [ ] Generate evaluation reports
- [ ] Compare against baselines

**Acceptance Criteria:**
- Evaluation framework complete
- All metrics implemented
- Reports generated

---

## Input Processing Layers

### Issue #20: Implement Language & Script Detection

**Labels:** `feature`, `input-processing`, `detection`

**Description:**
Implement automatic detection of input language and script (English, transliterated Sanskrit, Devanagari).

**Tasks:**
- [ ] Create language detection model/rule-based system
- [ ] Detect script (transliterated vs Devanagari)
- [ ] Normalize input
- [ ] Route to appropriate path (A or B)
- [ ] Test with various inputs

**Acceptance Criteria:**
- Accurate language detection
- Script detection working
- Proper routing implemented

---

### Issue #21: Implement Path A (Constructor) Pipeline

**Labels:** `feature`, `path-a`, `constructor`, `translation`

**Description:**
Implement complete Path A pipeline: English/Transliterated → Sanskrit.

**Tasks:**
- [ ] Integrate semantic parser (Karaka extractor)
- [ ] Integrate root mapper
- [ ] Integrate Paninian assembler
- [ ] Add script conversion
- [ ] Test end-to-end

**Acceptance Criteria:**
- Path A pipeline complete
- Handles English and transliterated input
- Produces grammatically correct Sanskrit

---

### Issue #22: Implement Path B (Auditor) Pipeline

**Labels:** `feature`, `path-b`, `auditor`, `validation`

**Description:**
Implement complete Path B pipeline: Sanskrit → Validation & Correction.

**Tasks:**
- [ ] Integrate Sanskrit parser
- [ ] Integrate rule validator
- [ ] Integrate correction engine
- [ ] Add explanation generation
- [ ] Test with various inputs

**Acceptance Criteria:**
- Path B pipeline complete
- Validates Sanskrit grammar
- Suggests corrections with explanations

---

### Issue #23: Implement Script Converter (Transliteration ↔ Devanagari)

**Labels:** `feature`, `script-conversion`, `transliteration`

**Description:**
Implement bidirectional conversion between transliteration and Devanagari scripts.

**Tasks:**
- [ ] Research transliteration libraries
- [ ] Implement IAST ↔ Devanagari conversion
- [ ] Support multiple transliteration schemes
- [ ] Add to both Path A and Path B
- [ ] Test accuracy

**Acceptance Criteria:**
- Accurate script conversion
- Multiple schemes supported
- Integrated into pipelines

---

### Issue #24: Create Inference Interface (Streamlit/FastAPI)

**Labels:** `feature`, `interface`, `inference`, `ui`

**Description:**
Create user interface for the Paninian Engine (web app or API).

**Tasks:**
- [ ] Choose interface (Streamlit or FastAPI)
- [ ] Implement input handling
- [ ] Integrate Path A and Path B
- [ ] Add output formatting
- [ ] Create user-friendly UI

**Acceptance Criteria:**
- Interface working
- Both paths accessible
- User-friendly design

---

## Additional Issues

### Issue #25: Create Comprehensive Documentation

**Labels:** `documentation`, `good-first-issue`

**Description:**
Create comprehensive documentation for contributors and users.

**Tasks:**
- [ ] API documentation
- [ ] Usage examples
- [ ] Architecture diagrams
- [ ] Training guides
- [ ] Contribution guidelines

**Acceptance Criteria:**
- Complete documentation
- Easy to follow
- Examples included

---

### Issue #26: Set Up CI/CD Pipeline

**Labels:** `devops`, `ci-cd`, `automation`

**Description:**
Set up continuous integration and deployment pipeline.

**Tasks:**
- [ ] GitHub Actions workflows
- [ ] Automated testing
- [ ] Dataset validation
- [ ] Model training checks
- [ ] Deployment automation

**Acceptance Criteria:**
- CI/CD pipeline working
- Tests automated
- Quality checks in place

---

## How to Use These Issues

1. Copy the issue template
2. Go to https://github.com/raghav-vk/panini-neuro-symbolic-ai/issues/new
3. Paste the template
4. Add appropriate labels
5. Submit the issue

Or use the GitHub CLI:
```bash
gh issue create --title "Issue Title" --body-file issue_template.md --label "stage-1,dataset"
```

---

*GitHub Issues Template - Project Panini*  
*Last Updated: January 16, 2026*
