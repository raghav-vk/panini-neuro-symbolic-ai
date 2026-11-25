# Neuro-Symbolic Architecture: From System 1 to System 2

**Version:** 1.0  
**Last Updated:** January 16, 2026  
**Core Vision:** Evolution from Data-Driven Training to Thinking-Based Inference

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [The System 1 vs System 2 Framework](#the-system-1-vs-system-2-framework)
3. [Current Architecture: System 1 Critique](#current-architecture-system-1-critique)
4. [Evolution Roadmap: System 1 → System 2](#evolution-roadmap-system-1--system-2)
5. [Stage A: Constraint-Based Decoding (The "Shim")](#stage-a-constraint-based-decoding-the-shim)
6. [Stage B: Tree of Thoughts (Iterative Refinement)](#stage-b-tree-of-thoughts-iterative-refinement)
7. [Stage C: Knowledge Graph Integration (Semantics)](#stage-c-knowledge-graph-integration-semantics)
8. [System 2 Architecture Overview](#system-2-architecture-overview)
9. [Implementation Strategy](#implementation-strategy)
10. [Comparison: System 1 vs System 2](#comparison-system-1-vs-system-2)

---

## 🎯 Executive Summary

The Paninian Engine currently operates in **System 1** mode: fast, intuitive, data-driven training that teaches the neural network through examples. While effective for fluency, this approach is insufficient for "mathematical perfection" required by Sanskrit grammar.

This document outlines the evolution to **System 2**: a thinking-based architecture where the Panini Engine operates **during inference**, not just training, enabling:

1. **Constraint-Based Decoding**: Real-time grammar validation prevents invalid outputs
2. **Tree of Thoughts**: Iterative refinement generates multiple drafts, selects best
3. **Knowledge Graph Integration**: Semantic understanding via Amarakosha thesaurus

**Architecture Evolution:**
- **v0.1 (Current):** Training-time data generation (System 1)
- **v0.5 (Next):** Inference-time shim with constraint decoding (System 2 start)
- **v1.0 (Final):** Full System 2 with Tree of Thoughts + Knowledge Graph (System 2 complete)

---

## 🧠 The System 1 vs System 2 Framework

### System 1: Fast, Intuitive, Pattern-Based

**Characteristics:**
- Fast: Generates output in single forward pass
- Intuitive: Learns patterns from data
- Pattern-Based: Statistical next-token prediction
- Fallible: Can hallucinate or violate rules

**Current Paninian Engine:**
- Panini Engine generates training data
- Neural network learns from examples
- Inference is purely neural (no Panini Engine)
- **Verdict:** System 1 architecture

### System 2: Slow, Deliberate, Rule-Based

**Characteristics:**
- Slow: Takes time to reason and validate
- Deliberate: Explicit rule checking and refinement
- Rule-Based: Follows deterministic logic
- Reliable: Mathematically guaranteed correctness

**Target Paninian Engine:**
- Panini Engine operates during inference
- Real-time constraint checking
- Multiple draft generation and selection
- **Verdict:** System 2 architecture

---

## ⚠️ Current Architecture: System 1 Critique

### The Current "System 1" Approach

**Architecture Flow:**
```
Training Phase:
  Panini Engine → Synthetic Data → Neural Network Training → Model Weights

Inference Phase:
  User Input → Neural Network → Output (No Panini Engine)
```

**How It Works:**
1. **Training:** Panini Engine generates grammatically perfect synthetic data
2. **Learning:** Neural network learns patterns from this data
3. **Inference:** Neural network generates output based on learned patterns

### The Flaw: Statistical Memorization vs Deterministic Rules

**Problem Statement:**
The current design is **Data-Driven**. You are using the Panini Engine to generate training data to "teach" the neural network rules.

**The Flaw:**
This relies on the model **memorizing the rules**. But neural networks are **probabilistic**, not **deterministic**. Even with 99% accuracy, the model will eventually hallucinate a grammatically incorrect sentence because it is "guessing" the next token based on **probability**, not **logic**.

**Example Failure:**
```
Input: "The boy goes"
Neural Network (System 1): "Baalah gacchati" (Correct 99% of the time)

But occasionally:
Neural Network (System 1): "Baalah gacchanti" (Wrong: plural verb with singular noun)
```

**Why This Happens:**
- Neural network learned pattern: "gacchati" usually follows "Baalah"
- But it's probabilistic: sometimes samples "gacchanti" (plural) by chance
- No deterministic rule enforcement during generation

### The Verdict: System 1 Limitations

**Strengths:**
- ✅ Fast generation
- ✅ Good fluency
- ✅ Natural-sounding output
- ✅ Efficient training

**Weaknesses:**
- ❌ Can violate grammar rules (probabilistic)
- ❌ No guarantee of correctness
- ❌ Hallucinations on edge cases
- ❌ Insufficient for "mathematical perfection"

**Conclusion:**
This is a **System 1 approach** (Fast, Intuitive, but Fallible). It is great for fluency but insufficient for the "mathematical perfection" required by Sanskrit.

---

## 🚀 Evolution Roadmap: System 1 → System 2

### Architecture Evolution Summary

| Phase | Architecture | Role of Panini Engine | System Type |
|-------|-------------|----------------------|-------------|
| **v0.1 (Current)** | Training-Time | Generates synthetic data to train weights | System 1 |
| **v0.5 (Next)** | Inference-Time Shim | Filters "bad tokens" in real-time (Constraint Decoding) | System 2 Start |
| **v1.0 (Final)** | System 2 Search | Generates multiple drafts, grades them, outputs best | System 2 Complete |

### Migration Path

```
┌─────────────────────────────────────────────────────────────────┐
│                    EVOLUTION TIMELINE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  v0.1 (Current)                    v0.5 (6 months)              │
│  ┌─────────────────────┐          ┌─────────────────────┐     │
│  │  Training-Time      │   ───→   │  Inference Shim     │     │
│  │  Data Generation    │          │  Constraint Decode  │     │
│  └─────────────────────┘          └─────────────────────┘     │
│         System 1                      System 2 (Partial)        │
│         │                                                       │
│         │                                                       │
│         └───────────────────┬───────────────────┐              │
│                             │                   │              │
│                             ▼                   ▼              │
│                    ┌─────────────────────────────────────┐    │
│                    │      v1.0 (12 months)               │    │
│                    │  ┌───────────────────────────┐      │    │
│                    │  │  Full System 2:           │      │    │
│                    │  │  • Tree of Thoughts       │      │    │
│                    │  │  • Knowledge Graph        │      │    │
│                    │  │  • Iterative Refinement   │      │    │
│                    │  └───────────────────────────┘      │    │
│                    └─────────────────────────────────────┘    │
│                           System 2 (Complete)                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Stage A: Constraint-Based Decoding (The "Shim")

### Concept: Real-Time Grammar Validation

Instead of letting the LLM output whatever token it wants, you place a **Panini Shim** between the model and the user.

**Key Innovation:** Panini Engine operates **during inference**, not just training.

### Architecture: The Panini Shim

```
┌─────────────────────────────────────────────────────────────────┐
│              CONSTRAINT-BASED DECODING ARCHITECTURE              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User Input: "Translate 'The boy goes'"                         │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  STEP 1: Neural Network Predicts Next Token              │  │
│  │  Output: "Baalah" (Boy)                                  │  │
│  │         │                                                 │  │
│  │         ▼                                                 │  │
│  │  ┌───────────────────────────────────────────────────┐   │  │
│  │  │  STEP 2: Panini Shim Intervenes                    │   │  │
│  │  │  ├─ Check Panini Engine State                       │   │  │
│  │  │  ├─ Question: "Active verb expected next? Yes."     │   │  │
│  │  │  └─ Token Approved ✓                                │   │  │
│  │  └───────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  STEP 3: Neural Network Predicts Next Token              │  │
│  │  Output: "gacchati" (Goes)                               │  │
│  │         │                                                 │  │
│  │         ▼                                                 │  │
│  │  ┌───────────────────────────────────────────────────┐   │  │
│  │  │  STEP 4: Panini Shim Intervenes                    │   │  │
│  │  │  ├─ Check: "Baalah" is singular                     │   │  │
│  │  │  ├─ Check: "gacchati" is singular (3rd person)      │   │  │
│  │  │  ├─ Agreement: ✓ Singular matches                    │   │  │
│  │  │  └─ Token Approved ✓                                │   │  │
│  │  └───────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│  Output: "Baalah gacchati" (Grammatically Perfect)              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### How It Works: Token-by-Token Validation

**Step-by-Step Process:**

1. **Neural Network Predicts:** LLM generates probability distribution over next tokens
   ```
   P(token | context) = [0.4: "gacchati", 0.3: "gacchanti", 0.3: others]
   ```

2. **Panini Shim Intervenes:** Checks which tokens are grammatically valid
   ```
   Context: "Baalah" (singular subject)
   Panini Check: "Next token must be singular 3rd person verb"
   Valid Tokens: ["gacchati", "pathati", "likhati", ...]
   Invalid Tokens: ["gacchanti" (plural), "gacchasi" (2nd person), ...]
   ```

3. **Token Masking:** Set invalid token probabilities to zero
   ```
   Masked P(token | context) = [0.4: "gacchati", 0.0: "gacchanti", ...]
   ```

4. **Re-normalize and Sample:** Sample only from valid tokens
   ```
   Final P(token | context) = [1.0: "gacchati", 0.0: others]
   ```

### Constraint Example: Preventing Errors

**Scenario:** Model tries to generate incorrect grammar

```
Neural Network Wants: "Baalah gacchanti" (Wrong: plural verb)
Panini Shim Checks: 
  - "Baalah" is singular (Nominative, Ekavacanam)
  - "gacchanti" is plural (3rd person, Bahuvacanam)
  - Rule: Singular subject requires singular verb
  - Result: ❌ Agreement violation
  - Action: Mask "gacchanti" probability to 0
  - Model Forced: Generate "gacchati" instead
```

**Result:** Mathematically guaranteed grammatical correctness.

### Implementation: The Panini Shim Module

```python
class PaniniShim:
    """Real-time grammar constraint decoder."""
    
    def __init__(self, panini_engine, neural_model):
        self.panini_engine = panini_engine
        self.neural_model = neural_model
        self.symbolic_state = None
    
    def decode_with_constraints(self, input_text, max_length=128):
        """Generate tokens with Panini constraints."""
        tokens = []
        self.symbolic_state = self.panini_engine.initialize_state()
        
        for step in range(max_length):
            # 1. Neural network predicts next tokens
            logits = self.neural_model.predict_next(input_text, tokens)
            token_probs = torch.softmax(logits, dim=-1)
            
            # 2. Panini Engine checks valid tokens
            valid_tokens = self.panini_engine.get_valid_tokens(
                current_tokens=tokens,
                symbolic_state=self.symbolic_state
            )
            
            # 3. Mask invalid tokens
            masked_probs = self.mask_invalid_tokens(
                token_probs, valid_tokens
            )
            
            # 4. Sample from valid tokens
            next_token = self.sample_token(masked_probs)
            
            # 5. Update symbolic state
            self.symbolic_state = self.panini_engine.update_state(
                self.symbolic_state, next_token
            )
            
            tokens.append(next_token)
            
            # 6. Check for completion
            if self.panini_engine.is_complete(self.symbolic_state):
                break
        
        return tokens
    
    def mask_invalid_tokens(self, probs, valid_tokens):
        """Set probability of invalid tokens to zero."""
        masked_probs = probs.clone()
        for token_id, prob in enumerate(probs):
            if token_id not in valid_tokens:
                masked_probs[token_id] = 0.0
        # Renormalize
        return masked_probs / masked_probs.sum()
```

### Benefits of Constraint-Based Decoding

**Advantages:**
- ✅ **Guaranteed Correctness:** Cannot generate invalid grammar
- ✅ **Real-Time Validation:** Immediate feedback on token validity
- ✅ **No Post-Processing:** Grammar correct during generation
- ✅ **Transparent:** Clear why tokens were selected

**Challenges:**
- ⚠️ **Slower Inference:** Requires symbolic rule checking per token
- ⚠️ **Complex State Management:** Track grammatical state across tokens
- ⚠️ **Rule Coverage:** Must handle all Paninian rules in real-time

**Mitigation:**
- Cache frequently-used rule checks
- Optimize symbolic state updates
- Parallel rule evaluation where possible

---

## 🌳 Stage B: Tree of Thoughts (Iterative Refinement)

### Concept: Multiple Drafts, Best Selection

This is how you handle complex essays or novels. The system generates **multiple versions**, **grades** them, and **selects** the best.

**Key Innovation:** Allows model to be "creative" (Neural) but "correct" (Symbolic).

### Architecture: Tree of Thoughts Process

```
┌─────────────────────────────────────────────────────────────────┐
│              TREE OF THOUGHTS: ITERATIVE REFINEMENT             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User Prompt: "Write a paragraph about truth"                   │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  DRAFTING PHASE: Generate Multiple Versions               │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │  Draft 1     │  │  Draft 2     │  │  Draft 3     │   │  │
│  │  │  (Creative)  │  │  (Formal)    │  │  (Poetic)    │   │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │  │
│  │         │                  │                  │          │  │
│  └─────────┼──────────────────┼──────────────────┼──────────┘  │
│            │                  │                  │              │
│            ▼                  ▼                  ▼              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SCORING PHASE: Panini Engine "Grades" Each Draft        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │  Draft 1     │  │  Draft 2     │  │  Draft 3     │   │  │
│  │  │  Score: 85%  │  │  Score: 95%  │  │  Score: 90%  │   │  │
│  │  │  Errors: 3   │  │  Errors: 0   │  │  Errors: 1   │   │  │
│  │  │  • Wrong     │  │  • Perfect   │  │  • Minor     │   │  │
│  │  │    Vibhakti  │  │    Grammar   │  │    Sandhi    │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│            │                  │                  │              │
│            └──────────────────┼──────────────────┘              │
│                               │                                 │
│                               ▼                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SELECTION PHASE: Choose Best Version                     │  │
│  │  Winner: Draft 2 (Score: 95%, Errors: 0)                  │  │
│  │  Reason: Perfect grammar, formal style matches context    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                               │                                 │
│                               ▼                                 │
│  Output: Draft 2 (Grammatically Perfect + Contextually Appropriate) │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### The Process: Draft → Score → Select

**Phase 1: Drafting**
- Neural network generates N different versions (diversity via temperature/sampling)
- Each draft explores different stylistic paths:
  - **Draft 1:** Creative/experimental (high temperature)
  - **Draft 2:** Formal/standard (medium temperature)
  - **Draft 3:** Poetic/stylistic (low temperature, style-aware)

**Phase 2: Scoring**
- Panini Engine evaluates each draft:
  - **Grammar Score:** Count of rule violations (0 = perfect)
  - **Vibhakti Score:** Correctness of case endings
  - **Sandhi Score:** Proper word combination
  - **Semantic Score:** Meaning preservation (from Knowledge Graph)

**Phase 3: Selection**
- Rank drafts by combined score:
  - **Primary:** Grammar correctness (must be 0 errors)
  - **Secondary:** Semantic appropriateness
  - **Tertiary:** Stylistic quality

### Implementation: Tree of Thoughts Module

```python
class TreeOfThoughts:
    """Generate multiple drafts, score them, select best."""
    
    def __init__(self, neural_model, panini_engine, knowledge_graph):
        self.neural_model = neural_model
        self.panini_engine = panini_engine
        self.knowledge_graph = knowledge_graph
    
    def generate_with_refinement(self, prompt, num_drafts=3):
        """Generate refined output via Tree of Thoughts."""
        
        # Phase 1: Drafting
        drafts = self.generate_drafts(prompt, num_drafts)
        
        # Phase 2: Scoring
        scored_drafts = self.score_drafts(drafts, prompt)
        
        # Phase 3: Selection
        best_draft = self.select_best(scored_drafts)
        
        return best_draft
    
    def generate_drafts(self, prompt, num_drafts):
        """Generate multiple diverse drafts."""
        drafts = []
        temperatures = [0.9, 0.7, 0.5]  # Creative, Standard, Formal
        
        for i in range(num_drafts):
            draft = self.neural_model.generate(
                prompt, 
                temperature=temperatures[i % len(temperatures)],
                do_sample=True
            )
            drafts.append(draft)
        
        return drafts
    
    def score_drafts(self, drafts, prompt):
        """Score each draft using Panini Engine."""
        scored = []
        
        for draft in drafts:
            # Grammar scoring
            grammar_score = self.panini_engine.evaluate_grammar(draft)
            
            # Semantic scoring
            semantic_score = self.knowledge_graph.evaluate_semantics(
                draft, prompt
            )
            
            # Combined score
            total_score = (
                0.7 * grammar_score +  # Grammar is primary
                0.3 * semantic_score   # Semantics is secondary
            )
            
            scored.append({
                'draft': draft,
                'grammar_score': grammar_score,
                'semantic_score': semantic_score,
                'total_score': total_score
            })
        
        return scored
    
    def select_best(self, scored_drafts):
        """Select draft with highest score and 0 grammar errors."""
        # Filter: Only consider drafts with 0 grammar errors
        valid_drafts = [
            d for d in scored_drafts 
            if d['grammar_score'] == 1.0  # Perfect grammar
        ]
        
        if not valid_drafts:
            # If no perfect drafts, pick best grammar score
            valid_drafts = sorted(
                scored_drafts, 
                key=lambda x: x['grammar_score'], 
                reverse=True
            )[:1]
        
        # Among valid drafts, pick highest total score
        best = max(valid_drafts, key=lambda x: x['total_score'])
        return best['draft']
```

### Benefits of Tree of Thoughts

**Advantages:**
- ✅ **Creativity + Correctness:** Neural creativity, symbolic validation
- ✅ **Best of Both Worlds:** Multiple creative options, pick best grammatically
- ✅ **Robustness:** Handles complex, long-form generation
- ✅ **Transparency:** Shows why draft was selected

**Challenges:**
- ⚠️ **Computational Cost:** Generate N drafts, score all
- ⚠️ **Latency:** Slower than single-pass generation
- ⚠️ **Quality vs Quantity:** More drafts don't always mean better quality

**Mitigation:**
- Limit to 3-5 drafts (diminishing returns)
- Parallel draft generation and scoring
- Early stopping if perfect draft found

---

## 🗺️ Stage C: Knowledge Graph Integration (Semantics)

### Concept: Beyond Syntax to Semantics

Currently, your model knows **Syntax** (Grammar), but it doesn't necessarily know **Semantics** (Meaning).

**The Upgrade:** Integrate the **Amarakosha** (Ancient Sanskrit Thesaurus) as a Knowledge Graph.

### Architecture: Knowledge Graph Integration

```
┌─────────────────────────────────────────────────────────────────┐
│              KNOWLEDGE GRAPH: SEMANTIC UNDERSTANDING            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input: "The King goes"                                         │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  NEURAL MODEL: Generates Candidates                       │  │
│  │  Primary: "Rajah gacchati"                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  KNOWLEDGE GRAPH: Amarakosha Lookup                         │  │
│  │  Query: "King"                                               │  │
│  │  Results:                                                    │  │
│  │    ├─ "Rajah" (राजः) - Common, standard                     │  │
│  │    ├─ "Nrupah" (नृपः) - Poetic, meter-friendly              │  │
│  │    ├─ "Bhupalah" (भूपालः) - Formal, elegant                 │  │
│  │    └─ "Parthivah" (पार्थिवः) - Literary, classical          │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CONTEXTUAL SELECTION: Choose Best Synonym                 │  │
│  │  Context: Previous sentence uses Chanda (Meter)            │  │
│  │  Decision: "Nrupah" fits meter better                      │  │
│  │  Output: "Nrupah gacchati" (Not "Rajah gacchati")         │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                        │
│         ▼                                                        │
│  Advanced Use: Poetry Generation with Meter                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Input: "Write a Shloka about truth"                      │  │
│  │  Process:                                                  │  │
│  │    1. Generate meaning structure (Neural)                  │  │
│  │    2. Find synonyms from Amarakosha (Knowledge Graph)      │  │
│  │    3. Select synonyms that fit Chanda (Meter)              │  │
│  │    4. Apply Paninian grammar (Symbolic)                    │  │
│  │  Output: Grammatically correct + Metrically perfect Shloka │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Scenario: Semantic Synonym Selection

**Standard LLM Approach:**
```
Input: "The King goes"
Output: "Rajah gacchati" (Default translation)
```

**Knowledge Graph LLM Approach:**
```
Input: "The King goes"
Knowledge Graph Lookup: "King" → {Rajah, Nrupah, Bhupalah, Parthivah}
Context Analysis: Previous sentence uses Anustubh Chanda (8 syllables)
Meter Check: "Nrupah" fits meter better than "Rajah"
Decision: "Nrupah gacchati" (Contextually better choice)
```

### The Amarakosha Knowledge Graph

**Structure:**
```python
knowledge_graph = {
    "King": {
        "synonyms": [
            {"word": "Rajah", "usage": "common", "meter": "any"},
            {"word": "Nrupah", "usage": "poetic", "meter": "short"},
            {"word": "Bhupalah", "usage": "formal", "meter": "medium"},
            {"word": "Parthivah", "usage": "literary", "meter": "long"}
        ],
        "semantic_relations": {
            "hypernym": "Ruler",
            "hyponyms": ["Emperor", "Prince", "Chief"],
            "meronyms": ["Crown", "Scepter", "Throne"]
        }
    }
}
```

### Implementation: Knowledge Graph Module

```python
class AmarakoshaKnowledgeGraph:
    """Sanskrit thesaurus as Knowledge Graph."""
    
    def __init__(self, amarakosha_data):
        self.graph = self.build_graph(amarakosha_data)
        self.meter_analyzer = ChandaAnalyzer()
    
    def get_synonyms(self, word, context=None):
        """Get synonyms for word, optionally filtered by context."""
        synonyms = self.graph.get(word, {}).get("synonyms", [])
        
        if context:
            # Filter by meter if context has meter requirements
            if context.get("meter"):
                synonyms = [
                    s for s in synonyms 
                    if self.meter_analyzer.fits_meter(
                        s["word"], context["meter"]
                    )
                ]
            
            # Filter by style if context has style requirements
            if context.get("style"):
                synonyms = [
                    s for s in synonyms 
                    if s["usage"] == context["style"]
                ]
        
        return synonyms
    
    def select_best_synonym(self, word, candidates, context):
        """Select best synonym based on context."""
        synonyms = self.get_synonyms(word, context)
        
        # Score each synonym
        scores = []
        for synonym in synonyms:
            score = 0.0
            
            # Meter fit (if applicable)
            if context.get("meter"):
                meter_score = self.meter_analyzer.score_meter(
                    synonym["word"], context["meter"]
                )
                score += 0.4 * meter_score
            
            # Style match (if applicable)
            if context.get("style"):
                if synonym["usage"] == context["style"]:
                    score += 0.3
            
            # Frequency/preference
            if synonym["word"] in candidates:
                score += 0.3
            
            scores.append((synonym, score))
        
        # Return highest scoring synonym
        best = max(scores, key=lambda x: x[1])
        return best[0]["word"]
```

### End State: Poetry Generation

**Capability:**
A model that writes poetry (Shlokas) that are:
- ✅ **Grammatically correct** (Panini Engine)
- ✅ **Metrically perfect** (Chanda rules via Knowledge Graph)
- ✅ **Semantically appropriate** (Amarakosha synonyms)
- ✅ **Stylistically beautiful** (Neural model)

**Example:**
```
Input: "Write a Shloka about truth using Anustubh meter"

Process:
  1. Neural Model: Generate meaning structure
  2. Knowledge Graph: Find synonyms fitting meter
  3. Panini Engine: Apply grammar rules
  4. Meter Check: Validate Chanda compliance

Output: 
  "सत्यं श्रेष्ठतमं वचः सुखदं मोक्षप्रदं तत्त्वतः। 
   अनृतं दुःखदं पापं व्यर्थं नाशप्रदं भवेत्॥"
  
  (Grammatically correct + Metrically perfect + Semantically rich)
```

---

## 🏛️ System 2 Architecture Overview

### Complete System 2 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  SYSTEM 2: COMPLETE ARCHITECTURE                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              INPUT PROCESSING                              │  │
│  │  User: "Translate 'The King goes' into Sanskrit poetry"   │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PHASE 1: DRAFTING (Neural + Knowledge Graph)            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │  Draft 1     │  │  Draft 2     │  │  Draft 3     │   │  │
│  │  │  "Rajah..."  │  │  "Nrupah..." │  │  "Bhupalah..."│   │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │  │
│  └─────────┼──────────────────┼──────────────────┼──────────┘  │
│            │                  │                  │              │
│            ▼                  ▼                  ▼              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PHASE 2: CONSTRAINT VALIDATION (Panini Shim)            │  │
│  │  Each draft validated token-by-token during generation    │  │
│  │  Invalid tokens masked, grammar enforced in real-time     │  │
│  └──────────────────────────────────────────────────────────┘  │
│            │                  │                  │              │
│            ▼                  ▼                  ▼              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PHASE 3: SCORING (Panini Engine + Knowledge Graph)      │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │  Grammar: ✓  │  │  Grammar: ✓  │  │  Grammar: ✓  │   │  │
│  │  │  Meter: ✗     │  │  Meter: ✓    │  │  Meter: ✗    │   │  │
│  │  │  Score: 70%  │  │  Score: 95%  │  │  Score: 75%  │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│            │                  │                  │              │
│            └──────────────────┼──────────────────┘              │
│                               │                                 │
│                               ▼                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PHASE 4: SELECTION (Best Draft)                          │  │
│  │  Winner: Draft 2 ("Nrupah gacchati")                      │  │
│  │  Reason: Perfect grammar + Perfect meter + Context fit    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                               │                                 │
│                               ▼                                 │
│  Output: "Nrupah gacchati" (Grammatically Perfect + Metrically Perfect) │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### System 2 Components

**1. Neural Model (Creativity)**
- Generates diverse drafts
- Provides semantic understanding
- Handles context and style

**2. Panini Shim (Grammar)**
- Real-time token validation
- Constraint-based decoding
- Guarantees grammatical correctness

**3. Panini Engine (Validation)**
- Scores draft quality
- Evaluates grammar compliance
- Identifies rule violations

**4. Knowledge Graph (Semantics)**
- Synonym selection
- Meter matching
- Semantic relationships

---

## 🛠️ Implementation Strategy

### Phase 1: v0.5 - Constraint Decoding Shim (6 months)

**Goal:** Move Panini Engine from training to inference

**Tasks:**
1. ✅ Implement Panini Shim module
2. ✅ Real-time token validation
3. ✅ Token masking during generation
4. ✅ State management for grammar rules
5. ✅ Performance optimization (caching, parallelization)

**Success Criteria:**
- Zero grammar errors in output
- < 2x latency increase vs System 1
- 100% backward compatibility with existing model

### Phase 2: v0.7 - Tree of Thoughts (9 months)

**Goal:** Add iterative refinement capability

**Tasks:**
1. ✅ Implement draft generation
2. ✅ Implement scoring system
3. ✅ Implement selection logic
4. ✅ Parallel draft generation
5. ✅ Performance optimization

**Success Criteria:**
- 3-5 drafts generated in < 5 seconds
- Selection matches human preference > 80% of time
- Quality improvement measurable on long-form tasks

### Phase 3: v1.0 - Knowledge Graph Integration (12 months)

**Goal:** Add semantic understanding via Amarakosha

**Tasks:**
1. ✅ Integrate Amarakosha thesaurus
2. ✅ Build Knowledge Graph structure
3. ✅ Implement synonym selection
4. ✅ Meter analysis and matching
5. ✅ Poetry generation capability

**Success Criteria:**
- Semantic appropriateness improved > 30%
- Meter-perfect poetry generation
- Synonym selection matches context > 85% of time

---

## 📊 Comparison: System 1 vs System 2

| Aspect | System 1 (v0.1) | System 2 (v1.0) |
|--------|-----------------|-----------------|
| **Panini Engine Role** | Training-time data generation | Inference-time validation + guidance |
| **Generation Speed** | Fast (single pass) | Slower (multi-draft + validation) |
| **Grammar Correctness** | ~99% (probabilistic) | 100% (guaranteed) |
| **Creativity** | High (unconstrained) | High (constrained but diverse) |
| **Semantic Understanding** | Limited | High (Knowledge Graph) |
| **Meter/Chanda Support** | None | Full support |
| **Poetry Generation** | Basic | Advanced (meter-perfect) |
| **Hallucination Risk** | Medium-High | Low (symbolic validation) |
| **Edge Case Handling** | Weak | Strong (multiple drafts) |
| **Transparency** | Low | High (shows reasoning) |

---

## ✅ Conclusion

The evolution from **System 1** (fast, intuitive, fallible) to **System 2** (deliberate, rule-based, reliable) transforms the Paninian Engine from a training tool into a **thinking partner** during inference.

**Key Innovations:**
1. **Constraint-Based Decoding:** Real-time grammar enforcement
2. **Tree of Thoughts:** Iterative refinement for quality
3. **Knowledge Graph:** Semantic understanding via Amarakosha

**End State:**
A model that writes Sanskrit poetry that is:
- ✅ Grammatically perfect (Panini Engine)
- ✅ Metrically perfect (Chanda rules)
- ✅ Semantically rich (Amarakosha)
- ✅ Stylistically beautiful (Neural model)

**Migration Path:**
- **v0.1 → v0.5:** Add Panini Shim (6 months)
- **v0.5 → v0.7:** Add Tree of Thoughts (3 months)
- **v0.7 → v1.0:** Add Knowledge Graph (3 months)

**Total Timeline:** 12 months to full System 2 architecture

---

*Neuro-Symbolic Architecture: From System 1 to System 2*  
*Last Updated: January 16, 2026*  
*Project Panini Architecture Evolution*
