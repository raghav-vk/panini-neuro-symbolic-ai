#!/usr/bin/env python3
"""
Example usage of the Sandhi Generator

This script demonstrates how to use the SandhiGenerator to create
training data for the Sanskrit language model.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from generator.sandhi_generator import SandhiGenerator


def main():
    """Run example Sandhi generation."""
    print("=" * 60)
    print("Project Panini - Sandhi Generator Example")
    print("=" * 60)
    print()
    
    # Initialize generator
    generator = SandhiGenerator()
    
    # Example 1: Basic Sandhi application
    print("Example 1: Basic Sandhi Application")
    print("-" * 60)
    test_cases = [
        ("Deva", "Alaya"),
        ("Rama", "Ayana"),
        ("Krishna", "Arjuna"),
        ("Ganga", "Uttara"),
    ]
    
    for word1, word2 in test_cases:
        combined = generator.apply_sandhi(word1, word2)
        print(f"  {word1} + {word2} = {combined}")
    
    print()
    
    # Example 2: Generate training pairs
    print("Example 2: Generate Training Data Pairs")
    print("-" * 60)
    word_pairs = [("Deva", "Alaya"), ("Rama", "Ayana")]
    examples = generator.generate_training_pairs(word_pairs, output_format="jsonl")
    
    for i, example in enumerate(examples, 1):
        print(f"\n  Example {i}:")
        print(f"    Instruction: {example['instruction']}")
        print(f"    Input: {example['input']}")
        print(f"    Output: {example['output']}")
    
    print()
    
    # Example 3: Generate dataset
    print("Example 3: Generate Dataset")
    print("-" * 60)
    print("  Generating 5 training examples...")
    examples = generator.generate_dataset(num_samples=5)
    print(f"  Generated {len(examples)} examples")
    print(f"  First example output: {examples[0]['output']}")
    
    print()
    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
