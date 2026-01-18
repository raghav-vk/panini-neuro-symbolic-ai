#!/usr/bin/env python3
"""
Toy Dataset Generator for Paninian Engine POC

Generates 50 simple English-to-Sanskrit sentence pairs with grammatical breakdowns
for the first training experiment (Stage 2: Karaka - Syntax & Translation).

This dataset demonstrates Intent-to-Structure translation following Panini's rules.
"""

import json
from typing import List, Dict, Tuple
from pathlib import Path


class ToyDatasetGenerator:
    """
    Generates a toy dataset of English-to-Sanskrit sentence pairs
    with complete grammatical breakdowns.
    """
    
    def __init__(self):
        """Initialize with predefined sentence templates."""
        # Simple sentence templates: (English, Sanskrit, Karaka breakdown)
        self.sentence_templates = [
            # Subject-Verb sentences (Karta + Kriya)
            ("The boy reads", "Baalah pathati", {
                "karta": {"word": "boy", "sanskrit": "Baalah", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "reads", "root": "√path", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The girl writes", "Balaa likhati", {
                "karta": {"word": "girl", "sanskrit": "Balaa", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "writes", "root": "√likh", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The student studies", "Chhatrah pathati", {
                "karta": {"word": "student", "sanskrit": "Chhatrah", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "studies", "root": "√path", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The teacher teaches", "Acharyah shikshayati", {
                "karta": {"word": "teacher", "sanskrit": "Acharyah", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "teaches", "root": "√shiksh", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The man goes", "Narah gacchati", {
                "karta": {"word": "man", "sanskrit": "Narah", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "goes", "root": "√gam", "tense": "present", "person": 3, "number": "singular"}
            }),
            
            # Subject-Verb-Object sentences (Karta + Karma + Kriya)
            ("The boy reads the book", "Baalah pustakam pathati", {
                "karta": {"word": "boy", "sanskrit": "Baalah", "case": "nominative", "vibhakti": "prathama"},
                "karma": {"word": "book", "sanskrit": "pustakam", "case": "accusative", "vibhakti": "dvitiya"},
                "kriya": {"word": "reads", "root": "√path", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The girl writes a letter", "Balaa patram likhati", {
                "karta": {"word": "girl", "sanskrit": "Balaa", "case": "nominative", "vibhakti": "prathama"},
                "karma": {"word": "letter", "sanskrit": "patram", "case": "accusative", "vibhakti": "dvitiya"},
                "kriya": {"word": "writes", "root": "√likh", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The student reads the text", "Chhatrah grantham pathati", {
                "karta": {"word": "student", "sanskrit": "Chhatrah", "case": "nominative", "vibhakti": "prathama"},
                "karma": {"word": "text", "sanskrit": "grantham", "case": "accusative", "vibhakti": "dvitiya"},
                "kriya": {"word": "reads", "root": "√path", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The teacher teaches Sanskrit", "Acharyah samskritam shikshayati", {
                "karta": {"word": "teacher", "sanskrit": "Acharyah", "case": "nominative", "vibhakti": "prathama"},
                "karma": {"word": "Sanskrit", "sanskrit": "samskritam", "case": "accusative", "vibhakti": "dvitiya"},
                "kriya": {"word": "teaches", "root": "√shiksh", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The man sees the house", "Narah griham pashyati", {
                "karta": {"word": "man", "sanskrit": "Narah", "case": "nominative", "vibhakti": "prathama"},
                "karma": {"word": "house", "sanskrit": "griham", "case": "accusative", "vibhakti": "dvitiya"},
                "kriya": {"word": "sees", "root": "√dris", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The woman cooks food", "Stri annam pacati", {
                "karta": {"word": "woman", "sanskrit": "Stri", "case": "nominative", "vibhakti": "prathama"},
                "karma": {"word": "food", "sanskrit": "annam", "case": "accusative", "vibhakti": "dvitiya"},
                "kriya": {"word": "cooks", "root": "√pac", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The child plays", "Balah kridati", {
                "karta": {"word": "child", "sanskrit": "Balah", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "plays", "root": "√krid", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The child plays with a ball", "Balah kandukena kridati", {
                "karta": {"word": "child", "sanskrit": "Balah", "case": "nominative", "vibhakti": "prathama"},
                "karana": {"word": "ball", "sanskrit": "kandukena", "case": "instrumental", "vibhakti": "tritiya"},
                "kriya": {"word": "plays", "root": "√krid", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The king rules", "Raja shasati", {
                "karta": {"word": "king", "sanskrit": "Raja", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "rules", "root": "√shas", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The king rules the kingdom", "Raja rajyam shasati", {
                "karta": {"word": "king", "sanskrit": "Raja", "case": "nominative", "vibhakti": "prathama"},
                "karma": {"word": "kingdom", "sanskrit": "rajyam", "case": "accusative", "vibhakti": "dvitiya"},
                "kriya": {"word": "rules", "root": "√shas", "tense": "present", "person": 3, "number": "singular"}
            }),
            
            # Sentences with location (Adhikarana)
            ("The sun rises in the east", "Suryah purvasyam dishi udeti", {
                "karta": {"word": "sun", "sanskrit": "Suryah", "case": "nominative", "vibhakti": "prathama"},
                "adhikarana": {"word": "east", "sanskrit": "purvasyam dishi", "case": "locative", "vibhakti": "saptami"},
                "kriya": {"word": "rises", "root": "√ud", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The moon shines in the sky", "Chandramah akashe bhasati", {
                "karta": {"word": "moon", "sanskrit": "Chandramah", "case": "nominative", "vibhakti": "prathama"},
                "adhikarana": {"word": "sky", "sanskrit": "akashe", "case": "locative", "vibhakti": "saptami"},
                "kriya": {"word": "shines", "root": "√bhas", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The bird sits on the tree", "Pakshi vrkshe tishthati", {
                "karta": {"word": "bird", "sanskrit": "Pakshi", "case": "nominative", "vibhakti": "prathama"},
                "adhikarana": {"word": "tree", "sanskrit": "vrkshe", "case": "locative", "vibhakti": "saptami"},
                "kriya": {"word": "sits", "root": "√stha", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The fish swims in the water", "Matsyah jale plavati", {
                "karta": {"word": "fish", "sanskrit": "Matsyah", "case": "nominative", "vibhakti": "prathama"},
                "adhikarana": {"word": "water", "sanskrit": "jale", "case": "locative", "vibhakti": "saptami"},
                "kriya": {"word": "swims", "root": "√plu", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The man lives in the house", "Narah grihe vasati", {
                "karta": {"word": "man", "sanskrit": "Narah", "case": "nominative", "vibhakti": "prathama"},
                "adhikarana": {"word": "house", "sanskrit": "grihe", "case": "locative", "vibhakti": "saptami"},
                "kriya": {"word": "lives", "root": "√vas", "tense": "present", "person": 3, "number": "singular"}
            }),
            
            # Sentences with recipient (Sampradana)
            ("The boy gives a book to the teacher", "Baalah acharyaya pustakam dadati", {
                "karta": {"word": "boy", "sanskrit": "Baalah", "case": "nominative", "vibhakti": "prathama"},
                "karma": {"word": "book", "sanskrit": "pustakam", "case": "accusative", "vibhakti": "dvitiya"},
                "sampradana": {"word": "teacher", "sanskrit": "acharyaya", "case": "dative", "vibhakti": "chaturthi"},
                "kriya": {"word": "gives", "root": "√da", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The student asks a question to the teacher", "Chhatrah acharyaya prashnam prichchhati", {
                "karta": {"word": "student", "sanskrit": "Chhatrah", "case": "nominative", "vibhakti": "prathama"},
                "karma": {"word": "question", "sanskrit": "prashnam", "case": "accusative", "vibhakti": "dvitiya"},
                "sampradana": {"word": "teacher", "sanskrit": "acharyaya", "case": "dative", "vibhakti": "chaturthi"},
                "kriya": {"word": "asks", "root": "√prichchh", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The mother gives food to the child", "Mata balaya annam dadati", {
                "karta": {"word": "mother", "sanskrit": "Mata", "case": "nominative", "vibhakti": "prathama"},
                "karma": {"word": "food", "sanskrit": "annam", "case": "accusative", "vibhakti": "dvitiya"},
                "sampradana": {"word": "child", "sanskrit": "balaya", "case": "dative", "vibhakti": "chaturthi"},
                "kriya": {"word": "gives", "root": "√da", "tense": "present", "person": 3, "number": "singular"}
            }),
            
            # Sentences with source (Apadana)
            ("The student comes from the school", "Chhatrah vidyalayat gacchati", {
                "karta": {"word": "student", "sanskrit": "Chhatrah", "case": "nominative", "vibhakti": "prathama"},
                "apadana": {"word": "school", "sanskrit": "vidyalayat", "case": "ablative", "vibhakti": "panchami"},
                "kriya": {"word": "comes", "root": "√gam", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The water flows from the mountain", "Jalam parvvatat pravahati", {
                "karta": {"word": "water", "sanskrit": "Jalam", "case": "nominative", "vibhakti": "prathama"},
                "apadana": {"word": "mountain", "sanskrit": "parvvatat", "case": "ablative", "vibhakti": "panchami"},
                "kriya": {"word": "flows", "root": "√vah", "tense": "present", "person": 3, "number": "singular"}
            }),
            
            # More complex sentences
            ("The boy reads the book in the library", "Baalah pustakam pustakalaye pathati", {
                "karta": {"word": "boy", "sanskrit": "Baalah", "case": "nominative", "vibhakti": "prathama"},
                "karma": {"word": "book", "sanskrit": "pustakam", "case": "accusative", "vibhakti": "dvitiya"},
                "adhikarana": {"word": "library", "sanskrit": "pustakalaye", "case": "locative", "vibhakti": "saptami"},
                "kriya": {"word": "reads", "root": "√path", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The teacher teaches Sanskrit to the students", "Acharyah chhatrebhyah samskritam shikshayati", {
                "karta": {"word": "teacher", "sanskrit": "Acharyah", "case": "nominative", "vibhakti": "prathama"},
                "karma": {"word": "Sanskrit", "sanskrit": "samskritam", "case": "accusative", "vibhakti": "dvitiya"},
                "sampradana": {"word": "students", "sanskrit": "chhatrebhyah", "case": "dative", "vibhakti": "chaturthi"},
                "kriya": {"word": "teaches", "root": "√shiksh", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The king rules the kingdom with justice", "Raja dharmena rajyam shasati", {
                "karta": {"word": "king", "sanskrit": "Raja", "case": "nominative", "vibhakti": "prathama"},
                "karma": {"word": "kingdom", "sanskrit": "rajyam", "case": "accusative", "vibhakti": "dvitiya"},
                "karana": {"word": "justice", "sanskrit": "dharmena", "case": "instrumental", "vibhakti": "tritiya"},
                "kriya": {"word": "rules", "root": "√shas", "tense": "present", "person": 3, "number": "singular"}
            }),
            
            # Plural subjects
            ("The students read", "Chhatrah pathanti", {
                "karta": {"word": "students", "sanskrit": "Chhatrah", "case": "nominative", "vibhakti": "prathama", "number": "plural"},
                "kriya": {"word": "read", "root": "√path", "tense": "present", "person": 3, "number": "plural"}
            }),
            ("The students read books", "Chhatrah pustakani pathanti", {
                "karta": {"word": "students", "sanskrit": "Chhatrah", "case": "nominative", "vibhakti": "prathama", "number": "plural"},
                "karma": {"word": "books", "sanskrit": "pustakani", "case": "accusative", "vibhakti": "dvitiya", "number": "plural"},
                "kriya": {"word": "read", "root": "√path", "tense": "present", "person": 3, "number": "plural"}
            }),
            ("The teachers teach", "Acharyah shikshayanti", {
                "karta": {"word": "teachers", "sanskrit": "Acharyah", "case": "nominative", "vibhakti": "prathama", "number": "plural"},
                "kriya": {"word": "teach", "root": "√shiksh", "tense": "present", "person": 3, "number": "plural"}
            }),
            ("The boys play", "Balah kridanti", {
                "karta": {"word": "boys", "sanskrit": "Balah", "case": "nominative", "vibhakti": "prathama", "number": "plural"},
                "kriya": {"word": "play", "root": "√krid", "tense": "present", "person": 3, "number": "plural"}
            }),
            ("The girls write", "Balah likhanti", {
                "karta": {"word": "girls", "sanskrit": "Balah", "case": "nominative", "vibhakti": "prathama", "number": "plural"},
                "kriya": {"word": "write", "root": "√likh", "tense": "present", "person": 3, "number": "plural"}
            }),
            
            # More examples to reach 50
            ("The dog barks", "Shvah bhashati", {
                "karta": {"word": "dog", "sanskrit": "Shvah", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "barks", "root": "√bhash", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The cat sleeps", "Marjarah shayati", {
                "karta": {"word": "cat", "sanskrit": "Marjarah", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "sleeps", "root": "√shi", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The horse runs", "Ashvah dhavati", {
                "karta": {"word": "horse", "sanskrit": "Ashvah", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "runs", "root": "√dhav", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The cow gives milk", "Gauh dugdham dadati", {
                "karta": {"word": "cow", "sanskrit": "Gauh", "case": "nominative", "vibhakti": "prathama"},
                "karma": {"word": "milk", "sanskrit": "dugdham", "case": "accusative", "vibhakti": "dvitiya"},
                "kriya": {"word": "gives", "root": "√da", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The bird flies", "Pakshi patati", {
                "karta": {"word": "bird", "sanskrit": "Pakshi", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "flies", "root": "√pat", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The tree grows", "Vrkshah vardhate", {
                "karta": {"word": "tree", "sanskrit": "Vrkshah", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "grows", "root": "√vridh", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The flower blooms", "Pushpam vikasati", {
                "karta": {"word": "flower", "sanskrit": "Pushpam", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "blooms", "root": "√vikas", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The river flows", "Nadi pravahati", {
                "karta": {"word": "river", "sanskrit": "Nadi", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "flows", "root": "√vah", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The wind blows", "Vayuh vati", {
                "karta": {"word": "wind", "sanskrit": "Vayuh", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "blows", "root": "√va", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The fire burns", "Agnih dahati", {
                "karta": {"word": "fire", "sanskrit": "Agnih", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "burns", "root": "√dah", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The student learns", "Chhatrah shikshate", {
                "karta": {"word": "student", "sanskrit": "Chhatrah", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "learns", "root": "√shiksh", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The student learns Sanskrit", "Chhatrah samskritam shikshate", {
                "karta": {"word": "student", "sanskrit": "Chhatrah", "case": "nominative", "vibhakti": "prathama"},
                "karma": {"word": "Sanskrit", "sanskrit": "samskritam", "case": "accusative", "vibhakti": "dvitiya"},
                "kriya": {"word": "learns", "root": "√shiksh", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The man works", "Narah karmati", {
                "karta": {"word": "man", "sanskrit": "Narah", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "works", "root": "√kri", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The woman sings", "Stri gayati", {
                "karta": {"word": "woman", "sanskrit": "Stri", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "sings", "root": "√gai", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The child eats", "Balah khadati", {
                "karta": {"word": "child", "sanskrit": "Balah", "case": "nominative", "vibhakti": "prathama"},
                "kriya": {"word": "eats", "root": "√khad", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The child eats food", "Balah annam khadati", {
                "karta": {"word": "child", "sanskrit": "Balah", "case": "nominative", "vibhakti": "prathama"},
                "karma": {"word": "food", "sanskrit": "annam", "case": "accusative", "vibhakti": "dvitiya"},
                "kriya": {"word": "eats", "root": "√khad", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The mother loves the child", "Mata balam priyati", {
                "karta": {"word": "mother", "sanskrit": "Mata", "case": "nominative", "vibhakti": "prathama"},
                "karma": {"word": "child", "sanskrit": "balam", "case": "accusative", "vibhakti": "dvitiya"},
                "kriya": {"word": "loves", "root": "√pri", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The father protects the family", "Pita kutumbam rakshati", {
                "karta": {"word": "father", "sanskrit": "Pita", "case": "nominative", "vibhakti": "prathama"},
                "karma": {"word": "family", "sanskrit": "kutumbam", "case": "accusative", "vibhakti": "dvitiya"},
                "kriya": {"word": "protects", "root": "√raksh", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The sun sets in the west", "Suryah pashchimasyam dishi astameti", {
                "karta": {"word": "sun", "sanskrit": "Suryah", "case": "nominative", "vibhakti": "prathama"},
                "adhikarana": {"word": "west", "sanskrit": "pashchimasyam dishi", "case": "locative", "vibhakti": "saptami"},
                "kriya": {"word": "sets", "root": "√astam", "tense": "present", "person": 3, "number": "singular"}
            }),
            ("The stars shine in the night", "Tarah nishayam bhasanti", {
                "karta": {"word": "stars", "sanskrit": "Tarah", "case": "nominative", "vibhakti": "prathama", "number": "plural"},
                "adhikarana": {"word": "night", "sanskrit": "nishayam", "case": "locative", "vibhakti": "saptami"},
                "kriya": {"word": "shine", "root": "√bhas", "tense": "present", "person": 3, "number": "plural"}
            }),
        ]
    
    def generate_dataset(self, output_file: str = "datasets/toy_dataset.jsonl") -> List[Dict]:
        """
        Generate the toy dataset in JSONL format.
        
        Args:
            output_file: Path to output JSONL file
            
        Returns:
            List of training examples
        """
        examples = []
        
        for i, (english, sanskrit, karaka) in enumerate(self.sentence_templates, 1):
            example = {
                "id": i,
                "instruction": "Translate this English sentence to Sanskrit using correct case endings (Vibhakti) according to Panini's rules.",
                "input": english,
                "output": sanskrit,
                "output_devanagari": self._transliterate_to_devanagari(sanskrit),
                "karaka": karaka,
                "grammar_notes": self._generate_grammar_notes(karaka),
                "stage": "karaka",
                "complexity": self._assess_complexity(karaka)
            }
            examples.append(example)
        
        # Write to file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for example in examples:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        print(f"✓ Generated {len(examples)} examples")
        print(f"✓ Saved to: {output_path}")
        
        return examples
    
    def _transliterate_to_devanagari(self, transliterated: str) -> str:
        """
        Simple transliteration to Devanagari (basic mapping).
        For a full implementation, use a proper transliteration library.
        """
        # Basic IAST to Devanagari mapping (simplified)
        # In production, use a proper library like indic-transliteration
        mapping = {
            'a': 'अ', 'aa': 'आ', 'i': 'इ', 'ii': 'ई', 'u': 'उ', 'uu': 'ऊ',
            'e': 'ए', 'ai': 'ऐ', 'o': 'ओ', 'au': 'औ',
            'k': 'क', 'kh': 'ख', 'g': 'ग', 'gh': 'घ', 'ng': 'ङ',
            'ch': 'च', 'chh': 'छ', 'j': 'ज', 'jh': 'झ', 'ny': 'ञ',
            't': 'त', 'th': 'थ', 'd': 'द', 'dh': 'ध', 'n': 'न',
            'p': 'प', 'ph': 'फ', 'b': 'ब', 'bh': 'भ', 'm': 'म',
            'y': 'य', 'r': 'र', 'l': 'ल', 'v': 'व', 'sh': 'श',
            'sh': 'ष', 's': 'स', 'h': 'ह',
            'ah': 'ः', 'am': 'ं', 'ah': 'ः'
        }
        
        # For now, return placeholder - proper transliteration requires a library
        # This is a simplified version for the POC
        return f"[Devanagari: {transliterated}]"  # Placeholder
    
    def _generate_grammar_notes(self, karaka: Dict) -> str:
        """Generate grammar explanation notes."""
        notes = []
        
        if "karta" in karaka:
            karta = karaka["karta"]
            notes.append(f"Karta (Agent): '{karta['word']}' → {karta['sanskrit']} ({karta['case']} case, {karta['vibhakti']})")
        
        if "karma" in karaka:
            karma = karaka["karma"]
            notes.append(f"Karma (Object): '{karma['word']}' → {karma['sanskrit']} ({karma['case']} case, {karma['vibhakti']})")
        
        if "karana" in karaka:
            karana = karaka["karana"]
            notes.append(f"Karana (Instrument): '{karana['word']}' → {karana['sanskrit']} ({karana['case']} case, {karana['vibhakti']})")
        
        if "sampradana" in karaka:
            sampradana = karaka["sampradana"]
            notes.append(f"Sampradana (Recipient): '{sampradana['word']}' → {sampradana['sanskrit']} ({sampradana['case']} case, {sampradana['vibhakti']})")
        
        if "apadana" in karaka:
            apadana = karaka["apadana"]
            notes.append(f"Apadana (Source): '{apadana['word']}' → {apadana['sanskrit']} ({apadana['case']} case, {apadana['vibhakti']})")
        
        if "adhikarana" in karaka:
            adhikarana = karaka["adhikarana"]
            notes.append(f"Adhikarana (Location): '{adhikarana['word']}' → {adhikarana['sanskrit']} ({adhikarana['case']} case, {adhikarana['vibhakti']})")
        
        if "kriya" in karaka:
            kriya = karaka["kriya"]
            notes.append(f"Kriya (Verb): '{kriya['word']}' → {kriya['root']} → {kriya['tense']}, {kriya['person']}rd person, {kriya['number']}")
        
        return "; ".join(notes)
    
    def _assess_complexity(self, karaka: Dict) -> str:
        """Assess sentence complexity."""
        karaka_count = len([k for k in karaka.keys() if k != "kriya"])
        
        if karaka_count == 1:
            return "simple"
        elif karaka_count == 2:
            return "medium"
        else:
            return "complex"


def main():
    """Generate the toy dataset."""
    print("=" * 70)
    print("Paninian Engine - Toy Dataset Generator (POC)")
    print("=" * 70)
    print()
    print("Generating 50 English-to-Sanskrit sentence pairs...")
    print("Each sentence includes:")
    print("  - English input")
    print("  - Sanskrit output (transliterated)")
    print("  - Complete Karaka breakdown")
    print("  - Grammar notes")
    print()
    
    generator = ToyDatasetGenerator()
    examples = generator.generate_dataset()
    
    print()
    print("=" * 70)
    print("Dataset Summary")
    print("=" * 70)
    print(f"Total examples: {len(examples)}")
    
    # Count by complexity
    complexity_count = {}
    for ex in examples:
        comp = ex["complexity"]
        complexity_count[comp] = complexity_count.get(comp, 0) + 1
    
    print("\nComplexity distribution:")
    for comp, count in sorted(complexity_count.items()):
        print(f"  {comp}: {count} examples")
    
    # Show sample
    print("\n" + "=" * 70)
    print("Sample Example:")
    print("=" * 70)
    sample = examples[5]  # "The boy reads the book"
    print(json.dumps(sample, indent=2, ensure_ascii=False))
    
    print()
    print("=" * 70)
    print("✓ Toy dataset ready for training experiment!")
    print("=" * 70)


if __name__ == "__main__":
    main()
