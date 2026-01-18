# GitHub Issues Summary

This document provides an overview of all 26 GitHub issues created for community contribution to the Paninian Engine project.

## Quick Stats

- **Total Issues**: 26
- **Stage 1 (Dhatu-Patha)**: 5 issues
- **Stage 2 (Karaka)**: 5 issues
- **Stage 3 (Kavya)**: 2 issues
- **Validation & Testing**: 3 issues
- **Training & Evaluation**: 4 issues
- **Input Processing**: 5 issues
- **Infrastructure**: 2 issues

## Issue Breakdown

### Stage 1: Dhatu-Patha (Morphology) Dataset

| # | Title | Labels | Focus |
|---|-------|--------|-------|
| 1 | Extract and Parse Dhatu from Ashtadhyayi Repository | `stage-1`, `dataset`, `good-first-issue` | Data extraction |
| 2 | Generate Verb Conjugation Examples | `stage-1`, `dataset`, `morphology` | Verb forms |
| 3 | Generate Noun Declension Examples | `stage-1`, `dataset`, `morphology` | Noun forms |
| 4 | Integrate Vidyut for Accurate Form Generation | `stage-1`, `enhancement`, `vidyut` | Rule engine |
| 5 | Generate Sandhi Rule Training Examples | `stage-1`, `dataset`, `sandhi` | Word combination |

### Stage 2: Karaka (Syntax & Translation) Dataset

| # | Title | Labels | Focus |
|---|-------|--------|-------|
| 6 | Create English-Sanskrit Parallel Corpus Parser | `stage-2`, `dataset`, `translation` | Corpus parsing |
| 7 | Implement Karaka Extractor for English | `stage-2`, `feature`, `nlp` | Semantic parsing |
| 8 | Generate Karaka-Vibhakti Mapping Examples | `stage-2`, `dataset`, `syntax` | Case mapping |
| 9 | Create English-to-Sanskrit Translation Dataset | `stage-2`, `dataset`, `translation` | Translation data |
| 10 | Implement Transliteration Normalization | `stage-2`, `feature`, `transliteration` | Script handling |

### Stage 3: Kavya (Style & Essay Writing) Dataset

| # | Title | Labels | Focus |
|---|-------|--------|-------|
| 11 | Parse Classical Sanskrit Literature | `stage-3`, `dataset`, `literature` | Text parsing |
| 12 | Generate Long-Context Training Examples | `stage-3`, `dataset`, `long-context` | Long-form data |

### Validation & Testing

| # | Title | Labels | Focus |
|---|-------|--------|-------|
| 13 | Create Grammar Validation Tool | `validation`, `testing`, `grammar` | Rule checking |
| 14 | Create Test Dataset for Model Evaluation | `testing`, `dataset`, `evaluation` | Test data |
| 15 | Implement Dataset Quality Checks | `validation`, `quality`, `automation` | Quality assurance |

### Training & Evaluation

| # | Title | Labels | Focus |
|---|-------|--------|-------|
| 16 | Implement Stage 1 Training Script | `training`, `stage-1`, `pytorch` | Training pipeline |
| 17 | Implement Stage 2 Training Script | `training`, `stage-2`, `pytorch` | Weighted loss |
| 18 | Implement Stage 3 Training Script | `training`, `stage-3`, `pytorch` | Long-context |
| 19 | Create Model Evaluation Framework | `testing`, `evaluation`, `metrics` | Evaluation |

### Input Processing Layers

| # | Title | Labels | Focus |
|---|-------|--------|-------|
| 20 | Implement Language & Script Detection | `feature`, `input-processing` | Detection |
| 21 | Implement Path A (Constructor) Pipeline | `feature`, `path-a`, `constructor` | Translation |
| 22 | Implement Path B (Auditor) Pipeline | `feature`, `path-b`, `auditor` | Validation |
| 23 | Implement Script Converter | `feature`, `script-conversion` | Script conversion |
| 24 | Create Inference Interface | `feature`, `interface`, `inference` | User interface |

### Infrastructure

| # | Title | Labels | Focus |
|---|-------|--------|-------|
| 25 | Create Comprehensive Documentation | `documentation`, `good-first-issue` | Docs |
| 26 | Set Up CI/CD Pipeline | `devops`, `ci-cd`, `automation` | Automation |

## Good First Issues

These issues are marked as `good-first-issue` and are great starting points:

1. **Issue #1**: Extract and Parse Dhatu from Ashtadhyayi Repository
2. **Issue #6**: Create English-Sanskrit Parallel Corpus Parser
3. **Issue #11**: Parse Classical Sanskrit Literature
4. **Issue #25**: Create Comprehensive Documentation

## Priority Order

### Phase 1: Foundation (Issues 1-5, 13-15)
- Dataset generation infrastructure
- Validation tools
- Quality checks

### Phase 2: Training Data (Issues 6-12)
- Complete dataset generation for all stages
- Data validation

### Phase 3: Training (Issues 16-19)
- Training scripts
- Evaluation framework

### Phase 4: Integration (Issues 20-24)
- Input processing
- Dual-path pipelines
- User interface

### Phase 5: Infrastructure (Issues 25-26)
- Documentation
- CI/CD

## How to Contribute

1. **Browse Issues**: https://github.com/raghav-vk/panini-neuro-symbolic-ai/issues
2. **Pick an Issue**: Choose one that matches your skills
3. **Comment**: Let others know you're working on it
4. **Fork & Branch**: Create a feature branch
5. **Implement**: Write code and tests
6. **Submit PR**: Create pull request with reference to issue

## Creating Issues

Use the provided script:

```bash
# Preview issues
python3 scripts/create_github_issues.py --dry-run

# Create all issues
python3 scripts/create_github_issues.py
```

Or create manually using templates in `.github/ISSUES.md`.

---

*Issues Summary - Project Panini*  
*Last Updated: January 16, 2026*
