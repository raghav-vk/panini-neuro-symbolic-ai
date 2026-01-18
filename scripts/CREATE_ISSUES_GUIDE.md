# Guide: Creating GitHub Issues

This guide explains how to create all 26 GitHub issues for the Paninian Engine project.

## Prerequisites

1. **Install GitHub CLI**: https://cli.github.com/
   ```bash
   brew install gh  # macOS
   # or
   sudo apt install gh  # Linux
   ```

2. **Authenticate with GitHub**:
   ```bash
   gh auth login
   ```

3. **Verify access**:
   ```bash
   gh repo view raghav-vk/panini-neuro-symbolic-ai
   ```

## Step-by-Step Process

### Step 1: Create GitHub Labels

**Important**: Labels must be created before issues, otherwise issue creation will fail.

```bash
# Preview labels (dry run)
python3 scripts/setup_github_labels.py --dry-run

# Create all labels
python3 scripts/setup_github_labels.py
```

This creates 40+ labels including:
- Stage labels: `stage-1`, `stage-2`, `stage-3`
- Type labels: `dataset`, `feature`, `enhancement`, `testing`, etc.
- Domain labels: `morphology`, `translation`, `sandhi`, etc.
- Technology labels: `pytorch`, `vidyut`, etc.

### Step 2: Create GitHub Issues

Once labels are created, create the issues:

```bash
# Preview issues (dry run)
python3 scripts/create_github_issues.py --dry-run

# Create all 26 issues
python3 scripts/create_github_issues.py
```

### Alternative: Create Issues in Batches

If you prefer to create issues in smaller batches:

```bash
# Stage 1 issues (1-5)
python3 scripts/create_github_issues.py --start 0 --end 5

# Stage 2 issues (6-10)
python3 scripts/create_github_issues.py --start 5 --end 10

# Stage 3 issues (11-12)
python3 scripts/create_github_issues.py --start 10 --end 12

# Validation & Testing (13-15)
python3 scripts/create_github_issues.py --start 12 --end 15

# Training & Evaluation (16-19)
python3 scripts/create_github_issues.py --start 15 --end 19

# Input Processing (20-24)
python3 scripts/create_github_issues.py --start 19 --end 24

# Infrastructure (25-26)
python3 scripts/create_github_issues.py --start 24 --end 26
```

## Troubleshooting

### Error: "label not found"

**Solution**: Run the label setup script first:
```bash
python3 scripts/setup_github_labels.py
```

### Error: "GitHub CLI not authenticated"

**Solution**: Authenticate with GitHub:
```bash
gh auth login
```

### Error: "Permission denied"

**Solution**: Ensure you have write access to the repository. If you're a collaborator, check your permissions.

### Some labels missing

**Solution**: The script now handles missing labels gracefully. It will create the issue and skip missing labels. You can add them manually later or run the label setup script again.

## Manual Issue Creation

If the script doesn't work, you can create issues manually:

1. Go to: https://github.com/raghav-vk/panini-neuro-symbolic-ai/issues/new
2. Copy issue template from `.github/ISSUES.md`
3. Paste and customize
4. Add labels manually (they should exist after running setup_github_labels.py)
5. Submit

## Verification

After creating issues, verify they were created:

```bash
# List all issues
gh issue list

# View a specific issue
gh issue view <issue-number>
```

## Issue Management

### Update an Issue

```bash
gh issue edit <issue-number> --add-label "new-label"
gh issue edit <issue-number> --body "Updated description"
```

### Close an Issue

```bash
gh issue close <issue-number>
```

### Reopen an Issue

```bash
gh issue reopen <issue-number>
```

---

*Create Issues Guide - Project Panini*  
*Last Updated: January 16, 2026*
