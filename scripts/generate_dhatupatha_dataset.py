#!/usr/bin/env python3
"""
Stage 1: Dhatu-Patha Dataset Generator

Extracts data from ashtadhyayi-com/data repository and generates
morphology training examples (verb conjugation, noun declension, etc.)

Repository: https://github.com/ashtadhyayi-com/data
"""

import json
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import re


class AshtadhyayiDataExtractor:
    """
    Extracts and processes data from ashtadhyayi-com/data repository
    for Stage 1: Dhatu-Patha (Morphology) training.
    """
    
    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize extractor.
        
        Args:
            repo_path: Path to cloned ashtadhyayi-com/data repository.
                      If None, will clone it automatically.
        """
        self.repo_path = repo_path or "data/ashtadhyayi-data"
        self.repo_url = "https://github.com/ashtadhyayi-com/data.git"
        
    def ensure_repo(self):
        """Clone repository if it doesn't exist."""
        repo_dir = Path(self.repo_path)
        
        if not repo_dir.exists():
            print(f"Cloning ashtadhyayi-com/data repository...")
            repo_dir.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "clone", self.repo_url, str(repo_dir)],
                check=True
            )
            print(f"✓ Repository cloned to {repo_dir}")
        else:
            print(f"✓ Repository found at {repo_dir}")
            # Update if needed
            print("Updating repository...")
            subprocess.run(
                ["git", "-C", str(repo_dir), "pull"],
                check=False  # Don't fail if already up to date
            )
    
    def extract_dhatu(self) -> List[Dict]:
        """
        Extract verb roots (dhatu) from the repository.
        
        Returns:
            List of dhatu dictionaries with root, meaning, gana, etc.
        """
        dhatu_dir = Path(self.repo_path) / "dhatu"
        
        if not dhatu_dir.exists():
            print(f"⚠ Warning: dhatu directory not found at {dhatu_dir}")
            return []
        
        dhatu_list = []
        
        # Look for JSON or text files in dhatu directory
        for file_path in dhatu_dir.rglob("*"):
            if file_path.is_file():
                if file_path.suffix in ['.json', '.txt', '.md']:
                    try:
                        if file_path.suffix == '.json':
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                if isinstance(data, list):
                                    dhatu_list.extend(data)
                                elif isinstance(data, dict):
                                    dhatu_list.append(data)
                        else:
                            # Parse text files
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                # Extract dhatu patterns
                                dhatu_list.extend(self._parse_dhatu_text(content))
                    except Exception as e:
                        print(f"⚠ Error parsing {file_path}: {e}")
        
        print(f"✓ Extracted {len(dhatu_list)} dhatu entries")
        return dhatu_list
    
    def _parse_dhatu_text(self, content: str) -> List[Dict]:
        """Parse dhatu from text content."""
        dhatu_list = []
        
        # Common patterns for dhatu notation
        # Format: root_number gana meaning
        # Example: "गम् 1 गतौ" (gam, gana 1, meaning: to go)
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Try to extract dhatu information
            # This is a simplified parser - adjust based on actual format
            parts = line.split()
            if len(parts) >= 2:
                dhatu = {
                    "root": parts[0],
                    "gana": parts[1] if len(parts) > 1 else "1",
                    "meaning": " ".join(parts[2:]) if len(parts) > 2 else ""
                }
                dhatu_list.append(dhatu)
        
        return dhatu_list
    
    def extract_sutras(self) -> List[Dict]:
        """
        Extract Panini's sutras (rules) from the repository.
        
        Returns:
            List of sutra dictionaries with number, text, meaning, etc.
        """
        sutra_dir = Path(self.repo_path) / "sutraani"
        
        if not sutra_dir.exists():
            print(f"⚠ Warning: sutraani directory not found at {sutra_dir}")
            return []
        
        sutra_list = []
        
        # Look for JSON or text files
        for file_path in sutra_dir.rglob("*"):
            if file_path.is_file():
                if file_path.suffix in ['.json', '.txt', '.md']:
                    try:
                        if file_path.suffix == '.json':
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                if isinstance(data, list):
                                    sutra_list.extend(data)
                                elif isinstance(data, dict):
                                    sutra_list.append(data)
                        else:
                            # Parse text files
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                sutra_list.extend(self._parse_sutra_text(content))
                    except Exception as e:
                        print(f"⚠ Error parsing {file_path}: {e}")
        
        print(f"✓ Extracted {len(sutra_list)} sutras")
        return sutra_list
    
    def _parse_sutra_text(self, content: str) -> List[Dict]:
        """Parse sutras from text content."""
        sutra_list = []
        
        # Common patterns: "1.1.1 text" or "1.1.1: text"
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Match sutra number pattern (e.g., "1.1.1", "1.2.3")
            match = re.match(r'(\d+\.\d+\.\d+)[:\.]\s*(.+)', line)
            if match:
                sutra = {
                    "number": match.group(1),
                    "text": match.group(2).strip(),
                    "adhyaya": match.group(1).split('.')[0],
                    "pada": match.group(1).split('.')[1],
                    "sutra": match.group(1).split('.')[2]
                }
                sutra_list.append(sutra)
        
        return sutra_list
    
    def extract_shabda(self) -> List[Dict]:
        """
        Extract word forms (shabda) from the repository.
        
        Returns:
            List of word form dictionaries.
        """
        shabda_dir = Path(self.repo_path) / "shabda"
        
        if not shabda_dir.exists():
            print(f"⚠ Warning: shabda directory not found at {shabda_dir}")
            return []
        
        shabda_list = []
        
        for file_path in shabda_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix == '.json':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            shabda_list.extend(data)
                        elif isinstance(data, dict):
                            shabda_list.append(data)
                except Exception as e:
                    print(f"⚠ Error parsing {file_path}: {e}")
        
        print(f"✓ Extracted {len(shabda_list)} shabda entries")
        return shabda_list


class Stage1DatasetGenerator:
    """
    Generates Stage 1: Dhatu-Patha training dataset from extracted data.
    """
    
    def __init__(self, dhatu_list: List[Dict], sutra_list: List[Dict]):
        """
        Initialize generator.
        
        Args:
            dhatu_list: List of verb roots
            sutra_list: List of Panini's sutras
        """
        self.dhatu_list = dhatu_list
        self.sutra_list = sutra_list
        
        # Common verb conjugations to generate
        self.tense_person_number = [
            ("Present", 1, "Singular"),
            ("Present", 2, "Singular"),
            ("Present", 3, "Singular"),
            ("Present", 1, "Plural"),
            ("Present", 2, "Plural"),
            ("Present", 3, "Plural"),
            ("Past", 1, "Singular"),
            ("Past", 3, "Singular"),
            ("Future", 1, "Singular"),
            ("Future", 3, "Singular"),
        ]
        
        # Common noun declensions
        self.cases = ["Nominative", "Accusative", "Instrumental", "Dative", "Ablative", "Genitive", "Locative", "Vocative"]
        self.numbers = ["Singular", "Dual", "Plural"]
    
    def generate_verb_examples(self, max_examples: int = 10000) -> List[Dict]:
        """
        Generate verb conjugation examples.
        
        Args:
            max_examples: Maximum number of examples to generate
            
        Returns:
            List of training examples
        """
        examples = []
        
        # Use common dhatu or generate from list
        common_dhatu = [
            {"root": "√gam", "meaning": "to go", "gana": "1"},
            {"root": "√path", "meaning": "to read", "gana": "1"},
            {"root": "√likh", "meaning": "to write", "gana": "1"},
            {"root": "√da", "meaning": "to give", "gana": "3"},
            {"root": "√kri", "meaning": "to do", "gana": "8"},
            {"root": "√bhu", "meaning": "to be", "gana": "1"},
            {"root": "√as", "meaning": "to be", "gana": "2"},
            {"root": "√dris", "meaning": "to see", "gana": "1"},
            {"root": "√shru", "meaning": "to hear", "gana": "1"},
            {"root": "√vac", "meaning": "to speak", "gana": "2"},
        ]
        
        # Use provided dhatu or fallback to common ones
        dhatu_to_use = self.dhatu_list[:50] if self.dhatu_list else common_dhatu
        
        for dhatu in dhatu_to_use:
            root = dhatu.get("root", dhatu.get("dhatu", "√gam"))
            if not root.startswith("√"):
                root = "√" + root
            
            for tense, person, number in self.tense_person_number:
                # Generate Sanskrit form (simplified - in production use Vidyut)
                sanskrit_form = self._generate_verb_form(root, tense, person, number)
                
                if sanskrit_form:
                    example = {
                        "instruction": "Generate the Sanskrit verb form from the root and grammatical specifications.",
                        "input": f"Root: {root} + Tense: {tense} + Person: {person}rd + Number: {number}",
                        "output": sanskrit_form,
                        "root": root,
                        "tense": tense,
                        "person": person,
                        "number": number,
                        "rules_applied": self._get_applicable_rules(root, tense, person, number),
                        "stage": "dhatupatha",
                        "type": "verb_conjugation"
                    }
                    examples.append(example)
                    
                    if len(examples) >= max_examples:
                        return examples
        
        return examples
    
    def _generate_verb_form(self, root: str, tense: str, person: int, number: str) -> Optional[str]:
        """
        Generate verb form from root and specifications.
        This is a simplified version - in production, use Vidyut.
        """
        # Remove √ prefix
        root_base = root.replace("√", "")
        
        # Simplified conjugation rules (basic patterns)
        # In production, this should use Vidyut or proper Paninian rules
        
        if tense == "Present":
            if root_base == "gam":
                # √gam → gacchati (present, 3rd, singular)
                if person == 3 and number == "Singular":
                    return "gacchati"
                elif person == 1 and number == "Singular":
                    return "gacchami"
                elif person == 2 and number == "Singular":
                    return "gacchasi"
            elif root_base == "path":
                if person == 3 and number == "Singular":
                    return "pathati"
                elif person == 1 and number == "Singular":
                    return "pathami"
            elif root_base == "likh":
                if person == 3 and number == "Singular":
                    return "likhati"
            elif root_base == "da":
                if person == 3 and number == "Singular":
                    return "dadati"
            elif root_base == "kri":
                if person == 3 and number == "Singular":
                    return "karoti"
            elif root_base == "bhu":
                if person == 3 and number == "Singular":
                    return "bhavati"
            elif root_base == "as":
                if person == 3 and number == "Singular":
                    return "asti"
            elif root_base == "dris":
                if person == 3 and number == "Singular":
                    return "pashyati"
            elif root_base == "shru":
                if person == 3 and number == "Singular":
                    return "shrunoti"
            elif root_base == "vac":
                if person == 3 and number == "Singular":
                    return "vakti"
        
        # Fallback: return None if form cannot be generated
        # In production, this should always generate a form using Vidyut
        return None
    
    def _get_applicable_rules(self, root: str, tense: str, person: int, number: str) -> List[str]:
        """
        Get applicable Panini sutras for this conjugation.
        Returns list of sutra numbers.
        """
        # Simplified - in production, use actual rule engine
        rules = []
        
        if tense == "Present":
            rules.append("3.1.68")  # Present tense marker
            rules.append("3.1.77")  # Personal endings
        
        # Add more rules based on root and form
        return rules
    
    def generate_noun_examples(self, max_examples: int = 5000) -> List[Dict]:
        """
        Generate noun declension examples.
        
        Args:
            max_examples: Maximum number of examples to generate
            
        Returns:
            List of training examples
        """
        examples = []
        
        # Common pratipadika (noun bases)
        pratipadika_list = [
            {"base": "Rama", "gender": "masculine", "meaning": "Rama"},
            {"base": "Baala", "gender": "masculine", "meaning": "boy"},
            {"base": "Pustaka", "gender": "neuter", "meaning": "book"},
            {"base": "Griha", "gender": "neuter", "meaning": "house"},
            {"base": "Balaa", "gender": "feminine", "meaning": "girl"},
            {"base": "Nara", "gender": "masculine", "meaning": "man"},
            {"base": "Stri", "gender": "feminine", "meaning": "woman"},
            {"base": "Acharya", "gender": "masculine", "meaning": "teacher"},
        ]
        
        for pratipadika in pratipadika_list:
            base = pratipadika["base"]
            gender = pratipadika["gender"]
            
            for case in self.cases:
                for number in self.numbers:
                    # Generate declension (simplified)
                    declension = self._generate_noun_form(base, case, number, gender)
                    
                    if declension:
                        example = {
                            "instruction": "Generate the Sanskrit noun form from the base and grammatical specifications.",
                            "input": f"Pratipadika: {base} + Case: {case} + Number: {number} + Gender: {gender}",
                            "output": declension,
                            "pratipadika": base,
                            "case": case,
                            "number": number,
                            "gender": gender,
                            "rules_applied": self._get_noun_rules(case, number, gender),
                            "stage": "dhatupatha",
                            "type": "noun_declension"
                        }
                        examples.append(example)
                        
                        if len(examples) >= max_examples:
                            return examples
        
        return examples
    
    def _generate_noun_form(self, base: str, case: str, number: str, gender: str) -> Optional[str]:
        """
        Generate noun form from base and specifications.
        Simplified version - use Vidyut in production.
        """
        # Simplified declension patterns
        # In production, use proper Paninian rules via Vidyut
        
        if case == "Nominative" and number == "Singular":
            if gender == "masculine":
                return base + "h" if base.endswith("a") else base
            elif gender == "neuter":
                return base + "m" if base.endswith("a") else base
            elif gender == "feminine":
                return base if base.endswith("aa") else base + "aa"
        
        elif case == "Accusative" and number == "Singular":
            if gender == "masculine":
                return base + "m" if base.endswith("a") else base
            elif gender == "neuter":
                return base + "m" if base.endswith("a") else base
            elif gender == "feminine":
                return base + "m" if base.endswith("aa") else base
        
        elif case == "Instrumental" and number == "Singular":
            return base + "ena" if base.endswith("a") else base
        
        # Add more cases as needed
        return None
    
    def _get_noun_rules(self, case: str, number: str, gender: str) -> List[str]:
        """Get applicable sutras for noun declension."""
        rules = []
        
        # Simplified - add actual rule numbers
        if case == "Nominative":
            rules.append("2.3.46")  # Nominative case
        elif case == "Accusative":
            rules.append("2.3.2")  # Accusative case
        
        return rules
    
    def generate_dataset(self, output_file: str = "datasets/stage1_dhatupatha.jsonl", 
                        max_verb_examples: int = 10000,
                        max_noun_examples: int = 5000) -> List[Dict]:
        """
        Generate complete Stage 1 dataset.
        
        Args:
            output_file: Output JSONL file path
            max_verb_examples: Maximum verb conjugation examples
            max_noun_examples: Maximum noun declension examples
            
        Returns:
            List of all training examples
        """
        print("Generating Stage 1: Dhatu-Patha dataset...")
        print("=" * 70)
        
        all_examples = []
        
        # Generate verb examples
        print(f"\n1. Generating verb conjugation examples (max: {max_verb_examples})...")
        verb_examples = self.generate_verb_examples(max_verb_examples)
        print(f"   ✓ Generated {len(verb_examples)} verb examples")
        all_examples.extend(verb_examples)
        
        # Generate noun examples
        print(f"\n2. Generating noun declension examples (max: {max_noun_examples})...")
        noun_examples = self.generate_noun_examples(max_noun_examples)
        print(f"   ✓ Generated {len(noun_examples)} noun examples")
        all_examples.extend(noun_examples)
        
        # Write to file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, example in enumerate(all_examples, 1):
                example["id"] = i
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        print(f"\n✓ Total examples generated: {len(all_examples)}")
        print(f"✓ Saved to: {output_path}")
        
        # Statistics
        verb_count = sum(1 for e in all_examples if e.get("type") == "verb_conjugation")
        noun_count = sum(1 for e in all_examples if e.get("type") == "noun_declension")
        
        print(f"\nDataset Statistics:")
        print(f"  Verb conjugations: {verb_count}")
        print(f"  Noun declensions: {noun_count}")
        
        return all_examples


def main():
    """Main function to generate Stage 1 dataset."""
    print("=" * 70)
    print("Stage 1: Dhatu-Patha Dataset Generator")
    print("Using data from: https://github.com/ashtadhyayi-com/data")
    print("=" * 70)
    print()
    
    # Initialize extractor
    extractor = AshtadhyayiDataExtractor()
    
    # Ensure repository is available
    extractor.ensure_repo()
    
    # Extract data
    print("\nExtracting data from repository...")
    dhatu_list = extractor.extract_dhatu()
    sutra_list = extractor.extract_sutras()
    shabda_list = extractor.extract_shabda()
    
    print(f"\nExtraction Summary:")
    print(f"  Dhatu (verb roots): {len(dhatu_list)}")
    print(f"  Sutras (rules): {len(sutra_list)}")
    print(f"  Shabda (word forms): {len(shabda_list)}")
    
    # Generate dataset
    print("\n" + "=" * 70)
    generator = Stage1DatasetGenerator(dhatu_list, sutra_list)
    examples = generator.generate_dataset(
        max_verb_examples=10000,
        max_noun_examples=5000
    )
    
    print("\n" + "=" * 70)
    print("✓ Stage 1 dataset generation complete!")
    print("=" * 70)
    print("\nNote: This is a simplified generator.")
    print("For production, integrate with Vidyut for accurate form generation.")
    print("\nNext steps:")
    print("1. Review generated dataset")
    print("2. Validate forms using Vidyut or manual checking")
    print("3. Use for Stage 1 training experiment")


if __name__ == "__main__":
    main()
