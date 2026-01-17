"""
Test cases for Sandhi Generator Module

Tests the Sandhi rule application and training data generation functionality.
"""

import pytest
import json
import os
import tempfile
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from generator.sandhi_generator import SandhiGenerator


class TestSandhiGenerator:
    """Test suite for SandhiGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create a SandhiGenerator instance for testing."""
        return SandhiGenerator()
    
    def test_apply_sandhi_known_combination(self, generator):
        """Test Sandhi application with known word pairs."""
        # Test case from issue #1: Deva + Alaya -> Devalaya
        result = generator.apply_sandhi("Deva", "Alaya")
        assert result == "Devalaya", f"Expected 'Devalaya', got '{result}'"
    
    def test_apply_sandhi_multiple_known_combinations(self, generator):
        """Test multiple known Sandhi combinations."""
        test_cases = [
            ("Deva", "Alaya", "Devalaya"),
            ("Rama", "Ayana", "Ramanayana"),
            ("Krishna", "Arjuna", "Krishnarjuna"),
            ("Ganga", "Uttara", "Gangottara"),
        ]
        
        for word1, word2, expected in test_cases:
            result = generator.apply_sandhi(word1, word2)
            assert result == expected, f"{word1} + {word2} should be {expected}, got {result}"
    
    def test_apply_sandhi_empty_words(self, generator):
        """Test that empty words raise ValueError."""
        with pytest.raises(ValueError, match="Both words must be non-empty"):
            generator.apply_sandhi("", "Alaya")
        
        with pytest.raises(ValueError, match="Both words must be non-empty"):
            generator.apply_sandhi("Deva", "")
        
        with pytest.raises(ValueError, match="Both words must be non-empty"):
            generator.apply_sandhi("", "")
    
    def test_apply_sandhi_none_words(self, generator):
        """Test that None words raise TypeError."""
        with pytest.raises((TypeError, AttributeError)):
            generator.apply_sandhi(None, "Alaya")
        
        with pytest.raises((TypeError, AttributeError)):
            generator.apply_sandhi("Deva", None)
    
    def test_generate_training_pairs_jsonl_format(self, generator):
        """Test training pair generation in JSONL format."""
        word_pairs = [("Deva", "Alaya"), ("Rama", "Ayana")]
        examples = generator.generate_training_pairs(word_pairs, output_format="jsonl")
        
        assert len(examples) == 2
        assert "instruction" in examples[0]
        assert "input" in examples[0]
        assert "output" in examples[0]
        assert examples[0]["input"] == "Deva + Alaya"
        assert examples[0]["output"] == "Devalaya"
    
    def test_generate_training_pairs_chatml_format(self, generator):
        """Test training pair generation in ChatML format."""
        word_pairs = [("Deva", "Alaya")]
        examples = generator.generate_training_pairs(word_pairs, output_format="chatml")
        
        assert len(examples) == 1
        assert "messages" in examples[0]
        assert len(examples[0]["messages"]) == 2
        assert examples[0]["messages"][0]["role"] == "user"
        assert examples[0]["messages"][1]["role"] == "assistant"
        assert examples[0]["messages"][1]["content"] == "Devalaya"
    
    def test_generate_training_pairs_dict_format(self, generator):
        """Test training pair generation in dict format."""
        word_pairs = [("Deva", "Alaya")]
        examples = generator.generate_training_pairs(word_pairs, output_format="dict")
        
        assert len(examples) == 1
        assert examples[0]["word1"] == "Deva"
        assert examples[0]["word2"] == "Alaya"
        assert examples[0]["combined"] == "Devalaya"
        assert examples[0]["rules_applied"] == "sandhi"
    
    def test_generate_dataset(self, generator):
        """Test dataset generation."""
        num_samples = 5
        examples = generator.generate_dataset(num_samples)
        
        assert len(examples) == num_samples
        assert all("instruction" in ex for ex in examples)
        assert all("input" in ex for ex in examples)
        assert all("output" in ex for ex in examples)
    
    def test_generate_dataset_with_file_output(self, generator):
        """Test dataset generation with file output."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            examples = generator.generate_dataset(num_samples=3, output_file=tmp_path)
            
            # Verify file was created
            assert os.path.exists(tmp_path)
            
            # Verify file contents
            with open(tmp_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                assert len(lines) == 3
                
                # Verify each line is valid JSON
                for line in lines:
                    example = json.loads(line)
                    assert "instruction" in example
                    assert "input" in example
                    assert "output" in example
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_validate_sandhi_correct(self, generator):
        """Test Sandhi validation with correct expected result."""
        assert generator.validate_sandhi("Deva", "Alaya", "Devalaya") is True
    
    def test_validate_sandhi_incorrect(self, generator):
        """Test Sandhi validation with incorrect expected result."""
        assert generator.validate_sandhi("Deva", "Alaya", "WrongResult") is False
    
    def test_generate_word_pairs(self, generator):
        """Test word pair generation."""
        pairs = generator._generate_word_pairs(10)
        
        assert len(pairs) == 10
        assert all(isinstance(pair, tuple) for pair in pairs)
        assert all(len(pair) == 2 for pair in pairs)
        assert all(isinstance(pair[0], str) and isinstance(pair[1], str) for pair in pairs)
    
    def test_generate_training_pairs_large_dataset(self, generator):
        """Test generation of larger dataset."""
        word_pairs = [("Deva", "Alaya")] * 100
        examples = generator.generate_training_pairs(word_pairs)
        
        assert len(examples) == 100
        assert all(ex["output"] == "Devalaya" for ex in examples)
    
    def test_sandhi_generator_initialization(self, generator):
        """Test that generator initializes with correct attributes."""
        assert hasattr(generator, 'sandhi_rules')
        assert hasattr(generator, 'known_combinations')
        assert isinstance(generator.sandhi_rules, dict)
        assert isinstance(generator.known_combinations, dict)
        assert len(generator.known_combinations) > 0


class TestSandhiGeneratorIntegration:
    """Integration tests for SandhiGenerator."""
    
    @pytest.fixture
    def generator(self):
        """Create a SandhiGenerator instance for testing."""
        return SandhiGenerator()
    
    def test_end_to_end_pipeline(self, generator):
        """Test complete pipeline from word pairs to JSONL file."""
        # Generate word pairs
        word_pairs = generator._generate_word_pairs(5)
        
        # Generate training examples
        examples = generator.generate_training_pairs(word_pairs, output_format="jsonl")
        
        # Verify structure
        assert len(examples) == 5
        for example in examples:
            assert "instruction" in example
            assert "input" in example
            assert "+" in example["input"]  # Should contain the separator
            assert "output" in example
            assert len(example["output"]) > 0  # Output should not be empty
    
    def test_jsonl_file_format(self, generator):
        """Test that generated JSONL file is properly formatted."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            generator.generate_dataset(num_samples=3, output_file=tmp_path)
            
            # Read and verify JSONL format
            with open(tmp_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    assert line, f"Line {line_num} is empty"
                    
                    # Should be valid JSON
                    example = json.loads(line)
                    assert isinstance(example, dict)
                    assert "instruction" in example
                    assert "input" in example
                    assert "output" in example
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
