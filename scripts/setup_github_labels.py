#!/usr/bin/env python3
"""
Setup GitHub labels for the Paninian Engine project.

Creates all necessary labels before creating issues.
"""

import subprocess
import json

# Define all labels with colors
LABELS = [
    # Stage labels
    {"name": "stage-1", "color": "0052cc", "description": "Stage 1: Dhatu-Patha (Morphology)"},
    {"name": "stage-2", "color": "0e8a16", "description": "Stage 2: Karaka (Syntax & Translation)"},
    {"name": "stage-3", "color": "b60205", "description": "Stage 3: Kavya (Style & Essays)"},
    
    # Type labels
    {"name": "dataset", "color": "1d76db", "description": "Dataset creation or processing"},
    {"name": "feature", "color": "0e8a16", "description": "New feature"},
    {"name": "enhancement", "color": "a2eeef", "description": "Enhancement or improvement"},
    {"name": "bug", "color": "d73a4a", "description": "Bug fix"},
    {"name": "documentation", "color": "0075ca", "description": "Documentation"},
    {"name": "testing", "color": "f9d0c4", "description": "Testing related"},
    {"name": "validation", "color": "fbca04", "description": "Validation or verification"},
    {"name": "training", "color": "c5def5", "description": "Model training"},
    {"name": "devops", "color": "5319e7", "description": "DevOps or infrastructure"},
    
    # Domain labels
    {"name": "morphology", "color": "c2e0c6", "description": "Morphology (word formation)"},
    {"name": "translation", "color": "bfd4f2", "description": "Translation related"},
    {"name": "syntax", "color": "bfe5bf", "description": "Syntax and grammar"},
    {"name": "sandhi", "color": "d4c5f9", "description": "Sandhi rules"},
    {"name": "transliteration", "color": "fad8c7", "description": "Transliteration handling"},
    {"name": "nlp", "color": "c7def8", "description": "Natural language processing"},
    {"name": "semantic-parsing", "color": "e99695", "description": "Semantic role parsing"},
    {"name": "literature", "color": "fbcb04", "description": "Classical literature"},
    {"name": "long-context", "color": "d93f0b", "description": "Long-context generation"},
    {"name": "grammar", "color": "0e8a16", "description": "Grammar rules"},
    {"name": "quality", "color": "fbca04", "description": "Data quality"},
    {"name": "automation", "color": "1d76db", "description": "Automation"},
    {"name": "evaluation", "color": "b60205", "description": "Model evaluation"},
    {"name": "metrics", "color": "0052cc", "description": "Evaluation metrics"},
    {"name": "input-processing", "color": "c2e0c6", "description": "Input processing"},
    {"name": "detection", "color": "bfd4f2", "description": "Language/script detection"},
    {"name": "path-a", "color": "0e8a16", "description": "Path A: Constructor"},
    {"name": "constructor", "color": "0e8a16", "description": "Constructor pipeline"},
    {"name": "path-b", "color": "b60205", "description": "Path B: Auditor"},
    {"name": "auditor", "color": "b60205", "description": "Auditor pipeline"},
    {"name": "script-conversion", "color": "1d76db", "description": "Script conversion"},
    {"name": "interface", "color": "a2eeef", "description": "User interface"},
    {"name": "inference", "color": "c5def5", "description": "Model inference"},
    {"name": "ui", "color": "f9d0c4", "description": "User interface"},
    
    # Technology labels
    {"name": "pytorch", "color": "ee0701", "description": "PyTorch"},
    {"name": "vidyut", "color": "fbca04", "description": "Vidyut integration"},
    {"name": "integration", "color": "0052cc", "description": "Integration"},
    {"name": "ci-cd", "color": "5319e7", "description": "CI/CD pipeline"},
    
    # Contributor labels
    {"name": "good-first-issue", "color": "7057ff", "description": "Good for newcomers"},
    {"name": "data-engineering", "color": "1d76db", "description": "Data engineering"},
]


def create_label(label_data: dict, dry_run: bool = False):
    """Create a GitHub label."""
    name = label_data["name"]
    color = label_data["color"]
    description = label_data.get("description", "")
    
    if dry_run:
        print(f"  [DRY RUN] Would create label: {name} (#{color})")
        return True
    
    # Check if label exists
    try:
        result = subprocess.run(
            ["gh", "label", "view", name],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print(f"  ✓ Label '{name}' already exists")
            return True
    except:
        pass
    
    # Create label
    cmd = [
        "gh", "label", "create", name,
        "--color", color
    ]
    
    if description:
        cmd.extend(["--description", description])
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"  ✓ Created label: {name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Error creating label '{name}': {e.stderr}")
        return False


def main():
    """Main function to create all labels."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup GitHub labels for Paninian Engine")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (don't actually create labels)")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("GitHub Labels Setup for Paninian Engine")
    print("=" * 70)
    print()
    
    if args.dry_run:
        print("⚠ DRY RUN MODE - No labels will be created")
        print()
    
    # Check if GitHub CLI is available
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Error: GitHub CLI (gh) not found or not authenticated")
        print("  Install: https://cli.github.com/")
        print("  Authenticate: gh auth login")
        return
    
    print(f"Creating {len(LABELS)} label(s)...")
    print()
    
    created = 0
    failed = 0
    
    for label_data in LABELS:
        name = label_data["name"]
        if create_label(label_data, dry_run=args.dry_run):
            created += 1
        else:
            failed += 1
    
    print()
    print("=" * 70)
    if args.dry_run:
        print("DRY RUN COMPLETE")
    else:
        print(f"✓ Created/Verified: {created} label(s)")
        if failed > 0:
            print(f"✗ Failed: {failed} label(s)")
    print("=" * 70)
    
    if not args.dry_run:
        print("\n✓ Labels are now ready for issue creation!")
        print("  Run: python3 scripts/create_github_issues.py")


if __name__ == "__main__":
    main()
