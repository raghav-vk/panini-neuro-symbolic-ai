#!/usr/bin/env python3
"""
Script to create GitHub issues for the Paninian Engine project.

This script uses the GitHub CLI (gh) to create issues from templates.
Make sure you have GitHub CLI installed and authenticated.
"""

import subprocess
import json
from pathlib import Path


ISSUES = [
    {
        "title": "Extract and Parse Dhatu (Verb Roots) from Ashtadhyayi Repository",
        "body": """Extract verb roots (dhatu) from the [ashtadhyayi-com/data](https://github.com/ashtadhyayi-com/data) repository and create a structured dataset.

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
- Stage 1 requirements in `docs/approach-to-solution.md`""",
        "labels": ["stage-1", "dataset", "good-first-issue", "data-engineering"]
    },
    {
        "title": "Generate Verb Conjugation Examples from Dhatu",
        "body": """Generate training examples for verb conjugation (Tinganta) using extracted dhatu data.

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
- Sutra numbers included""",
        "labels": ["stage-1", "dataset", "morphology"]
    },
    {
        "title": "Generate Noun Declension Examples",
        "body": """Generate training examples for noun declension (Subanta) from pratipadika (noun bases).

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
- Output in Stage 1 JSONL format""",
        "labels": ["stage-1", "dataset", "morphology"]
    },
    {
        "title": "Integrate Vidyut for Accurate Form Generation",
        "body": """Replace simplified form generation with Vidyut Rust library for accurate Paninian form generation.

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
- [Vidyut Project](https://github.com/ambuda-org/vidyut)""",
        "labels": ["stage-1", "enhancement", "vidyut", "integration"]
    },
    {
        "title": "Generate Sandhi Rule Training Examples",
        "body": """Generate training examples for Sandhi (euphonic combination) rules.

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
- Output in Stage 1 JSONL format""",
        "labels": ["stage-1", "dataset", "sandhi"]
    },
    {
        "title": "Create English-Sanskrit Parallel Corpus Parser",
        "body": """Create a parser to extract English-Sanskrit sentence pairs from existing corpora.

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
- Ready for Karaka analysis""",
        "labels": ["stage-2", "dataset", "translation", "good-first-issue"]
    },
    {
        "title": "Implement Karaka (Semantic Role) Extractor for English",
        "body": """Implement semantic role extraction (Karaka) from English sentences for Path A (Constructor).

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
- Examples generated with annotations""",
        "labels": ["stage-2", "feature", "nlp", "semantic-parsing"]
    },
    {
        "title": "Generate Karaka-Vibhakti Mapping Examples",
        "body": """Generate training examples showing correct Karaka to Vibhakti (case ending) mapping.

**Tasks:**
- [ ] Create examples for each Karaka type
- [ ] Show correct Vibhakti for each semantic role
- [ ] Include incorrect examples (for error learning)
- [ ] Format: `Karta (Agent) → Nominative (Prathama)`
- [ ] Generate 50,000+ examples

**Acceptance Criteria:**
- All Karaka-Vibhakti mappings covered
- 50,000+ examples generated
- Incorrect examples included for contrastive learning""",
        "labels": ["stage-2", "dataset", "syntax"]
    },
    {
        "title": "Create English-to-Sanskrit Translation Dataset",
        "body": """Create comprehensive English-to-Sanskrit translation dataset with grammatical breakdowns.

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
- Ready for Stage 2 training""",
        "labels": ["stage-2", "dataset", "translation"]
    },
    {
        "title": "Implement Transliteration Normalization",
        "body": """Implement transliteration scheme detection and normalization (IAST, ITRANS, Harvard-Kyoto, etc.).

**Tasks:**
- [ ] Research transliteration schemes
- [ ] Implement scheme detection
- [ ] Create normalization to IAST
- [ ] Support conversion between schemes
- [ ] Add to Path A (Constructor) pipeline

**Acceptance Criteria:**
- Multiple transliteration schemes supported
- Automatic detection working
- Normalization accurate""",
        "labels": ["stage-2", "feature", "transliteration"]
    },
    {
        "title": "Parse Classical Sanskrit Literature",
        "body": """Parse and structure classical Sanskrit texts (Kalidasa, Panchatantra, Hitopadesha) for Stage 3 training.

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
- [cltk](https://github.com/cltk/cltk)""",
        "labels": ["stage-3", "dataset", "literature", "good-first-issue"]
    },
    {
        "title": "Generate Long-Context Training Examples",
        "body": """Generate training examples for long-form Sanskrit generation (essays, paragraphs).

**Tasks:**
- [ ] Use parsed classical literature
- [ ] Create prompt-response pairs
- [ ] Format: `"Write about truth" → [Long-form Sanskrit text]`
- [ ] Include style annotations
- [ ] Generate 10,000+ examples

**Acceptance Criteria:**
- 10,000+ long-form examples
- Various styles represented
- Ready for Stage 3 training""",
        "labels": ["stage-3", "dataset", "long-context"]
    },
    {
        "title": "Create Grammar Validation Tool",
        "body": """Create a tool to validate that generated Sanskrit forms follow Panini's rules.

**Tasks:**
- [ ] Integrate with Vidyut or create rule checker
- [ ] Validate verb conjugations
- [ ] Validate noun declensions
- [ ] Check Sandhi applications
- [ ] Generate validation reports

**Acceptance Criteria:**
- Validation tool working
- Can validate all form types
- Reports generated""",
        "labels": ["validation", "testing", "grammar"]
    },
    {
        "title": "Create Test Dataset for Model Evaluation",
        "body": """Create a gold-standard test dataset for evaluating model performance.

**Tasks:**
- [ ] Create test cases for each stage
- [ ] Include edge cases
- [ ] Include error cases (for validation testing)
- [ ] Create evaluation metrics
- [ ] Document test cases

**Acceptance Criteria:**
- Comprehensive test dataset
- Covers all stages
- Evaluation metrics defined""",
        "labels": ["testing", "dataset", "evaluation"]
    },
    {
        "title": "Implement Dataset Quality Checks",
        "body": """Implement automated quality checks for generated datasets.

**Tasks:**
- [ ] Check for duplicates
- [ ] Validate format consistency
- [ ] Check grammar correctness
- [ ] Verify completeness
- [ ] Generate quality reports

**Acceptance Criteria:**
- Automated checks working
- Quality reports generated
- Issues flagged automatically""",
        "labels": ["validation", "quality", "automation"]
    },
    {
        "title": "Implement Stage 1 Training Script",
        "body": """Create training script for Stage 1: Dhatu-Patha using Unsloth and LoRA.

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
- Metrics logged""",
        "labels": ["training", "stage-1", "pytorch"]
    },
    {
        "title": "Implement Stage 2 Training Script",
        "body": """Create training script for Stage 2: Karaka with weighted loss for Vibhakti errors.

**Tasks:**
- [ ] Extend Stage 1 training script
- [ ] Implement weighted loss function
- [ ] Heavy penalty for wrong case endings
- [ ] Create data loader for Stage 2 format
- [ ] Test on toy dataset

**Acceptance Criteria:**
- Training script with weighted loss
- Vibhakti errors heavily penalized
- Can train on Stage 2 dataset""",
        "labels": ["training", "stage-2", "pytorch"]
    },
    {
        "title": "Implement Stage 3 Training Script",
        "body": """Create training script for Stage 3: Kavya with long-context support.

**Tasks:**
- [ ] Extend training script for long contexts
- [ ] Configure context window
- [ ] Create data loader for Stage 3 format
- [ ] Implement style-aware training
- [ ] Test on classical literature

**Acceptance Criteria:**
- Long-context training working
- Style preservation
- Can train on Stage 3 dataset""",
        "labels": ["training", "stage-3", "pytorch", "long-context"]
    },
    {
        "title": "Create Model Evaluation Framework",
        "body": """Create comprehensive evaluation framework for all stages.

**Tasks:**
- [ ] Implement evaluation metrics
- [ ] Create evaluation scripts
- [ ] Test on gold-standard dataset
- [ ] Generate evaluation reports
- [ ] Compare against baselines

**Acceptance Criteria:**
- Evaluation framework complete
- All metrics implemented
- Reports generated""",
        "labels": ["testing", "evaluation", "metrics"]
    },
    {
        "title": "Implement Language & Script Detection",
        "body": """Implement automatic detection of input language and script (English, transliterated Sanskrit, Devanagari).

**Tasks:**
- [ ] Create language detection model/rule-based system
- [ ] Detect script (transliterated vs Devanagari)
- [ ] Normalize input
- [ ] Route to appropriate path (A or B)
- [ ] Test with various inputs

**Acceptance Criteria:**
- Accurate language detection
- Script detection working
- Proper routing implemented""",
        "labels": ["feature", "input-processing", "detection"]
    },
    {
        "title": "Implement Path A (Constructor) Pipeline",
        "body": """Implement complete Path A pipeline: English/Transliterated → Sanskrit.

**Tasks:**
- [ ] Integrate semantic parser (Karaka extractor)
- [ ] Integrate root mapper
- [ ] Integrate Paninian assembler
- [ ] Add script conversion
- [ ] Test end-to-end

**Acceptance Criteria:**
- Path A pipeline complete
- Handles English and transliterated input
- Produces grammatically correct Sanskrit""",
        "labels": ["feature", "path-a", "constructor", "translation"]
    },
    {
        "title": "Implement Path B (Auditor) Pipeline",
        "body": """Implement complete Path B pipeline: Sanskrit → Validation & Correction.

**Tasks:**
- [ ] Integrate Sanskrit parser
- [ ] Integrate rule validator
- [ ] Integrate correction engine
- [ ] Add explanation generation
- [ ] Test with various inputs

**Acceptance Criteria:**
- Path B pipeline complete
- Validates Sanskrit grammar
- Suggests corrections with explanations""",
        "labels": ["feature", "path-b", "auditor", "validation"]
    },
    {
        "title": "Implement Script Converter (Transliteration ↔ Devanagari)",
        "body": """Implement bidirectional conversion between transliteration and Devanagari scripts.

**Tasks:**
- [ ] Research transliteration libraries
- [ ] Implement IAST ↔ Devanagari conversion
- [ ] Support multiple transliteration schemes
- [ ] Add to both Path A and Path B
- [ ] Test accuracy

**Acceptance Criteria:**
- Accurate script conversion
- Multiple schemes supported
- Integrated into pipelines""",
        "labels": ["feature", "script-conversion", "transliteration"]
    },
    {
        "title": "Create Inference Interface (Streamlit/FastAPI)",
        "body": """Create user interface for the Paninian Engine (web app or API).

**Tasks:**
- [ ] Choose interface (Streamlit or FastAPI)
- [ ] Implement input handling
- [ ] Integrate Path A and Path B
- [ ] Add output formatting
- [ ] Create user-friendly UI

**Acceptance Criteria:**
- Interface working
- Both paths accessible
- User-friendly design""",
        "labels": ["feature", "interface", "inference", "ui"]
    },
    {
        "title": "Create Comprehensive Documentation",
        "body": """Create comprehensive documentation for contributors and users.

**Tasks:**
- [ ] API documentation
- [ ] Usage examples
- [ ] Architecture diagrams
- [ ] Training guides
- [ ] Contribution guidelines

**Acceptance Criteria:**
- Complete documentation
- Easy to follow
- Examples included""",
        "labels": ["documentation", "good-first-issue"]
    },
    {
        "title": "Set Up CI/CD Pipeline",
        "body": """Set up continuous integration and deployment pipeline.

**Tasks:**
- [ ] GitHub Actions workflows
- [ ] Automated testing
- [ ] Dataset validation
- [ ] Model training checks
- [ ] Deployment automation

**Acceptance Criteria:**
- CI/CD pipeline working
- Tests automated
- Quality checks in place""",
        "labels": ["devops", "ci-cd", "automation"]
    },
]


def create_issue(issue_data: dict, dry_run: bool = False):
    """Create a GitHub issue using GitHub CLI."""
    title = issue_data["title"]
    body = issue_data["body"]
    labels = issue_data["labels"]
    
    if dry_run:
        print(f"\n[DRY RUN] Would create issue:")
        print(f"  Title: {title}")
        print(f"  Labels: {', '.join(labels)}")
        print(f"  Body length: {len(body)} chars")
        return
    
    # Create issue first without labels
    cmd = [
        "gh", "issue", "create",
        "--title", title,
        "--body", body
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        issue_url = result.stdout.strip()
        issue_number = issue_url.split('/')[-1]
        
        # Add labels one by one (skip if label doesn't exist)
        labels_added = []
        for label in labels:
            try:
                subprocess.run(
                    ["gh", "issue", "edit", issue_number, "--add-label", label],
                    capture_output=True,
                    text=True,
                    check=True
                )
                labels_added.append(label)
            except subprocess.CalledProcessError:
                # Label doesn't exist, skip it
                print(f"    ⚠ Label '{label}' not found, skipping")
        
        print(f"✓ Created issue: {issue_url}")
        if labels_added:
            print(f"  Labels: {', '.join(labels_added)}")
        return issue_url
    except subprocess.CalledProcessError as e:
        print(f"✗ Error creating issue '{title}': {e.stderr}")
        return None


def main():
    """Main function to create all issues."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create GitHub issues for Paninian Engine project")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (don't actually create issues)")
    parser.add_argument("--start", type=int, default=0, help="Start from issue index")
    parser.add_argument("--end", type=int, help="End at issue index")
    parser.add_argument("--single", type=int, help="Create only a single issue by index")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("GitHub Issues Creator for Paninian Engine")
    print("=" * 70)
    print()
    
    if args.dry_run:
        print("⚠ DRY RUN MODE - No issues will be created")
        print()
    
    # Check if GitHub CLI is available
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Error: GitHub CLI (gh) not found or not authenticated")
        print("  Install: https://cli.github.com/")
        print("  Authenticate: gh auth login")
        return
    
    # Determine which issues to create
    if args.single is not None:
        issues_to_create = [ISSUES[args.single]]
    else:
        end = args.end if args.end is not None else len(ISSUES)
        issues_to_create = ISSUES[args.start:end]
    
    print(f"Creating {len(issues_to_create)} issue(s)...")
    print()
    
    created = []
    failed = []
    
    for i, issue_data in enumerate(issues_to_create, start=args.start + 1):
        print(f"[{i}/{len(ISSUES)}] {issue_data['title']}")
        result = create_issue(issue_data, dry_run=args.dry_run)
        
        if result:
            created.append(result)
        else:
            failed.append(issue_data['title'])
    
    print()
    print("=" * 70)
    if args.dry_run:
        print("DRY RUN COMPLETE")
    else:
        print(f"✓ Created: {len(created)} issue(s)")
        if failed:
            print(f"✗ Failed: {len(failed)} issue(s)")
    print("=" * 70)
    
    if created:
        print("\nCreated issues:")
        for url in created:
            print(f"  - {url}")


if __name__ == "__main__":
    main()
