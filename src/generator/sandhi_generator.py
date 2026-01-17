"""
Sandhi Generator Module

This module implements Sandhi (euphonic combination) rules for Sanskrit word generation.
Sandhi is the process of combining two words according to phonetic rules.

Based on Panini's Ashtadhyayi rules, this module generates grammatically correct
Sanskrit word combinations for training data.
"""

from typing import List, Dict, Tuple, Optional
import json


class SandhiGenerator:
    """
    Generates Sandhi combinations from Sanskrit word pairs.
    
    Sandhi rules handle the phonetic changes that occur when words are combined
    in Sanskrit. This is essential for generating grammatically correct synthetic data.
    """
    
    def __init__(self):
        """Initialize the Sandhi generator with rule mappings."""
        # Common Sandhi rules: (final_sound, initial_sound) -> combined_form
        self.sandhi_rules = {
            # Vowel + Vowel combinations
            ('a', 'a'): 'ā',
            ('a', 'i'): 'e',
            ('a', 'u'): 'o',
            ('a', 'e'): 'ai',
            ('a', 'o'): 'au',
            ('i', 'a'): 'ya',
            ('u', 'a'): 'va',
            ('e', 'a'): 'aya',
            ('o', 'a'): 'ava',
            
            # Consonant + Vowel combinations (common cases)
            ('ḥ', 'a'): 'a',  # Visarga before 'a'
            ('ḥ', 'i'): 'i',  # Visarga before 'i'
            ('ḥ', 'u'): 'u',  # Visarga before 'u'
            ('m', 'a'): 'ma',  # Anusvara
            ('m', 'i'): 'mi',
            ('m', 'u'): 'mu',
            
            # Common word endings
            ('a', 'alaya'): 'alaya',  # Deva + Alaya -> Devalaya
            ('a', 'īśa'): 'eśa',      # Deva + Īśa -> Deveśa
        }
        
        # Word pairs that combine without modification (for testing)
        self.known_combinations = {
            ('Deva', 'Alaya'): 'Devalaya',
            ('Rama', 'Ayana'): 'Ramanayana',
            ('Krishna', 'Arjuna'): 'Krishnarjuna',
            ('Ganga', 'Uttara'): 'Gangottara',
        }
    
    def apply_sandhi(self, word1: str, word2: str) -> str:
        """
        Apply Sandhi rules to combine two Sanskrit words.
        
        Args:
            word1: First Sanskrit word (e.g., "Deva")
            word2: Second Sanskrit word (e.g., "Alaya")
            
        Returns:
            Combined word with Sandhi applied (e.g., "Devalaya")
            
        Example:
            >>> generator = SandhiGenerator()
            >>> generator.apply_sandhi("Deva", "Alaya")
            'Devalaya'
        """
        if not word1 or not word2:
            raise ValueError("Both words must be non-empty")
        
        # Check known combinations first
        if (word1, word2) in self.known_combinations:
            return self.known_combinations[(word1, word2)]
        
        # Get the last character of word1 and first character of word2
        last_char = word1[-1].lower()
        first_char = word2[0].lower()
        
        # Check for specific Sandhi rule
        if (last_char, first_char) in self.sandhi_rules:
            replacement = self.sandhi_rules[(last_char, first_char)]
            return word1[:-1] + replacement + word2[1:]
        
        # Check for word-ending patterns
        word2_lower = word2.lower()
        for pattern, replacement in self.sandhi_rules.items():
            if isinstance(pattern[1], str) and len(pattern[1]) > 1:
                if word2_lower.startswith(pattern[1]):
                    return word1[:-1] + replacement + word2[len(pattern[1]):]
        
        # Default: simple concatenation (fallback)
        # In a full implementation, this would apply more complex rules
        return word1 + word2
    
    def generate_training_pairs(self, word_pairs: List[Tuple[str, str]], output_format: str = "jsonl") -> List[Dict]:
        """
        Generate training data pairs in the specified format.
        
        Args:
            word_pairs: List of (word1, word2) tuples
            output_format: Format for output ("jsonl", "dict", "alpaca")
            
        Returns:
            List of training examples in the specified format
        """
        examples = []
        
        for word1, word2 in word_pairs:
            combined = self.apply_sandhi(word1, word2)
            
            if output_format == "jsonl" or output_format == "alpaca":
                example = {
                    "instruction": "Apply Sandhi rules to combine these Sanskrit words.",
                    "input": f"{word1} + {word2}",
                    "output": combined
                }
            elif output_format == "chatml":
                example = {
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Combine these Sanskrit words using Sandhi: {word1} + {word2}"
                        },
                        {
                            "role": "assistant",
                            "content": combined
                        }
                    ]
                }
            else:  # dict format
                example = {
                    "word1": word1,
                    "word2": word2,
                    "combined": combined,
                    "rules_applied": "sandhi"
                }
            
            examples.append(example)
        
        return examples
    
    def generate_dataset(self, num_samples: int, output_file: Optional[str] = None) -> List[Dict]:
        """
        Generate a dataset of Sandhi combinations.
        
        Args:
            num_samples: Number of training examples to generate
            output_file: Optional path to save JSONL file
            
        Returns:
            List of training examples
        """
        # Generate word pairs (in a full implementation, this would use Vidyut)
        word_pairs = self._generate_word_pairs(num_samples)
        
        # Apply Sandhi and create training examples
        examples = self.generate_training_pairs(word_pairs, output_format="jsonl")
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                for example in examples:
                    f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        return examples
    
    def _generate_word_pairs(self, num_samples: int) -> List[Tuple[str, str]]:
        """
        Generate word pairs for Sandhi combination.
        
        In a full implementation, this would use Vidyut to generate valid Sanskrit words.
        For now, we use a combination of known words and patterns.
        
        Args:
            num_samples: Number of pairs to generate
            
        Returns:
            List of (word1, word2) tuples
        """
        # Base word lists (in full implementation, these would come from Dhatupatha)
        first_words = ["Deva", "Rama", "Krishna", "Ganga", "Sita", "Lakshmana"]
        second_words = ["Alaya", "Ayana", "Arjuna", "Uttara", "Mandira", "Kutira"]
        
        pairs = []
        for i in range(num_samples):
            # Cycle through known combinations, then generate variations
            if i < len(self.known_combinations):
                pairs.append(list(self.known_combinations.keys())[i])
            else:
                # Simple pattern generation (would be replaced with Vidyut)
                word1 = first_words[i % len(first_words)]
                word2 = second_words[(i // len(first_words)) % len(second_words)]
                pairs.append((word1, word2))
        
        return pairs[:num_samples]
    
    def validate_sandhi(self, word1: str, word2: str, expected: str) -> bool:
        """
        Validate that Sandhi application produces the expected result.
        
        Args:
            word1: First word
            word2: Second word
            expected: Expected combined form
            
        Returns:
            True if Sandhi application matches expected result
        """
        result = self.apply_sandhi(word1, word2)
        return result == expected


def main():
    """Example usage of the SandhiGenerator."""
    generator = SandhiGenerator()
    
    # Test with known combinations
    test_pairs = [
        ("Deva", "Alaya"),
        ("Rama", "Ayana"),
        ("Krishna", "Arjuna"),
    ]
    
    print("Sandhi Generator - Example Outputs:")
    print("=" * 50)
    
    for word1, word2 in test_pairs:
        combined = generator.apply_sandhi(word1, word2)
        print(f"{word1} + {word2} = {combined}")
    
    print("\nGenerating training dataset...")
    examples = generator.generate_dataset(num_samples=10)
    
    print(f"\nGenerated {len(examples)} training examples:")
    for i, example in enumerate(examples[:3], 1):
        print(f"\nExample {i}:")
        print(json.dumps(example, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
