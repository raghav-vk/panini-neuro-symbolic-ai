# GitHub Issues Management

This directory contains templates and scripts for managing GitHub issues for the Paninian Engine project.

## Files

- **`ISSUES.md`**: Complete list of all issue templates with descriptions
- **`scripts/create_github_issues.py`**: Script to automatically create issues using GitHub CLI

## Creating Issues

### Option 1: Using the Script (Recommended)

The script uses GitHub CLI to create issues automatically:

```bash
# Dry run (preview without creating)
python3 scripts/create_github_issues.py --dry-run

# Create all 26 issues
python3 scripts/create_github_issues.py

# Create specific issues
python3 scripts/create_github_issues.py --start 0 --end 5  # Issues 1-5
python3 scripts/create_github_issues.py --single 0        # Only issue 1
```

**Prerequisites:**
- Install GitHub CLI: https://cli.github.com/
- Authenticate: `gh auth login`
- Ensure you have write access to the repository

### Option 2: Manual Creation

1. Go to https://github.com/raghav-vk/panini-neuro-symbolic-ai/issues/new
2. Copy issue template from `.github/ISSUES.md`
3. Paste and customize
4. Add labels
5. Submit

## Issue Categories

### Stage 1: Dhatu-Patha (Morphology) - Issues #1-5
- Dataset generation for word formation
- Verb conjugation and noun declension
- Sandhi rules
- Vidyut integration

### Stage 2: Karaka (Syntax & Translation) - Issues #6-10
- English-Sanskrit translation
- Semantic role extraction
- Karaka-Vibhakti mapping
- Transliteration support

### Stage 3: Kavya (Style & Essays) - Issues #11-12
- Classical literature parsing
- Long-context generation

### Validation & Testing - Issues #13-15
- Grammar validation tools
- Test dataset creation
- Quality checks

### Training & Evaluation - Issues #16-19
- Training scripts for all stages
- Evaluation framework

### Input Processing - Issues #20-24
- Language/script detection
- Path A (Constructor) pipeline
- Path B (Auditor) pipeline
- Script conversion
- User interface

### Infrastructure - Issues #25-26
- Documentation
- CI/CD pipeline

## Labels

Issues are tagged with appropriate labels:
- `stage-1`, `stage-2`, `stage-3`: Training stage
- `dataset`: Dataset creation
- `feature`: New feature
- `enhancement`: Improvement
- `testing`: Testing related
- `validation`: Validation/verification
- `training`: Model training
- `good-first-issue`: Good for new contributors
- `data-engineering`: Data processing
- `morphology`: Word formation
- `translation`: Translation related
- `nlp`: Natural language processing
- And more...

---

*GitHub Issues Management - Project Panini*  
*Last Updated: January 16, 2026*
