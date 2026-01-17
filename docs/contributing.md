# Contributing to Neuro Symbolic Sanskrit SLM 🤝

We specifically need help from Computer Science and Linguistics students for:

- **Data Engineering**: Writing Python wrappers for Sanskrit grammar rules.
- **Corpus Cleaning**: Parsing texts from Kalidasa and the Mahabharata.
- **Evaluation**: Creating "Gold Standard" test sets to verify grammatical accuracy.

---

## Training Guide & Technical References 🧠

This document outlines the step-by-step process for data generation, environment setup, and fine-tuning for Project Panini.

## Phase 1: The "Neuro-Symbolic" Data Strategy

We do not rely solely on scraped web data. We manufacture "Synthetic Data" to teach the model grammar.

### 1.1 Synthetic Generation (The Panini Engine)

- **Concept:** Use deterministic rules to generate correct input/output pairs.
- **Tool:** We use [Vidyut](https://github.com/ambuda-org/vidyut) (Rust) for high-speed word derivation.
- **Task:** Generate 100k pairs of *Sandhi* (Euphonic combination) and *Subanta* (Noun declensions).
- **Data Format (JSONL):**
    ```json
    {
      "instruction": "Apply Sandhi rules to combine these words.",
      "input": "Deva + Alaya",
      "output": "Devalaya"
    }
    ```

### 1.2 The "Style" Corpus (Kalidasa & Beyond)

- **Source:** [GRETIL](http://gretil.sub.uni-goettingen.de/gretil.html) or [Ambuda](https://ambuda.org/).
- **Preprocessing:**
    * Remove verse numbers.
    * Strip non-Devanagari metadata.
    * Chunk text into context windows of 2048 tokens.

---

## Phase 2: Training Environment (Minimal GPU)

We use **Unsloth** because it allows us to fine-tune Llama-3/Mistral on a single GPU without crashing.

### 2.1 Hardware Requirements

- **Minimum:** NVIDIA GPU with 16GB VRAM (e.g., RTX 4080, Tesla T4 on Colab).
- **Recommended:** NVIDIA RTX 3090/4090 (24GB VRAM).
- **RAM:** 32GB System RAM.

### 2.2 Setup (Colab/Local)

We use the Unsloth library for optimized training.

```python
# Install Unsloth & PyTorch
!pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
!pip install --no-deps xformers "trl<0.9.0" peft accelerate bitsandbytes
```

---

## Phase 3: Fine-Tuning Process

### 3.1 Model Configuration

We load the model in 4-bit quantization to save memory.

```python
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/mistral-7b-instruct-v0.3-bnb-4bit",
    max_seq_length = 2048,
    load_in_4bit = True,
)
```

### 3.2 LoRA (Low-Rank Adaptation) Settings

We update only specific modules to keep the model "smart" while teaching it Sanskrit.

- **Rank (r):** 16 (Higher = more capacity to learn new info, but slower).
- **Target Modules:** `["q_proj", "k_proj", "v_proj", "o_proj"]` (Attention mechanisms).
- **Alpha:** 16.

### 3.3 The Training Loop

- **Epochs:** 1-3 (Do not overtrain; LLMs memorize quickly).
- **Learning Rate:** 2e-4.
- **Batch Size:** 2 (Keep small for consumer GPUs) with Gradient Accumulation = 4.

---

## Phase 4: References & Learning Material

### 📚 Essential Reading

- **LoRA Paper:** [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)
- **Unsloth Blog:** [How to make LLM fine-tuning 2x faster](https://github.com/unslothai/unsloth)
- **Panini's Grammar:** [Ashtadhyayi Structure & Algorithms](https://en.wikipedia.org/wiki/A%E1%B9%A3%E1%B9%AD%C4%81dhy%C4%81y%C4%AB)
- **Panini's Grammar:** [Ashtadhyayi website data](https://github.com/ashtadhyayi-com/data)

### 📺 Video Tutorials (For Students)

- **Andrej Karpathy - Intro to LLMs:** The best non-technical intro. ([YouTube](https://www.youtube.com/watch?v=zjkBMFhNj_g))
- **Neuro-Symbolic AI Explained:** Why rules + neural nets is the future. ([YouTube](https://www.youtube.com/results?search_query=neuro-symbolic+AI))
- **Fine-Tuning Mistral on Custom Data:** Step-by-step code walkthrough. ([YouTube](https://www.youtube.com/results?search_query=fine+tuning+mistral))

### 🧰 Tools

- **Vidyut:** High-performance Sanskrit parser. ([GitHub](https://github.com/ambuda-org/vidyut))
- **Sanskrit Heritage Engine:** For verifying grammatical correctness. ([Website](https://sanskrit.inria.fr/))

---

## Phase 5: Inference (Running the Model)

Once trained, we export the model to GGUF format for easy distribution.

```python
# Save to GGUF
model.save_pretrained_gguf("panini-v1", tokenizer, quantization_method = "q4_k_m")
```

Users can then load `panini-v1.gguf` into LM Studio or Ollama to chat with the model locally.

---

## How to Contribute

### Getting Started

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Areas Where We Need Help

We are seeking contributors for the following initial phases:

- **Phase 1 (Data Engineering):** Building the Python wrappers for Paninian rule engines to generate the "Golden Dataset."
- **Phase 2 (Scraping & Cleaning):** Processing raw text files of Meghaduta and Raghuvamsha, cleaning XML tags, and formatting for tokenization.
- **Phase 3 (Model Training):** Running initial LoRA experiments on Google Colab (Free Tier) or local GPUs.

### Detailed Contribution Areas

1. **Data Engineering**
   - Write Python wrappers for Paninian rule engines
   - Generate synthetic grammar datasets
   - Clean and preprocess classical texts

2. **Model Training**
   - Experiment with different LoRA configurations
   - Optimize training hyperparameters
   - Create evaluation metrics

3. **Testing & Validation**
   - Create "Gold Standard" test sets
   - Evaluate grammatical accuracy
   - Test on various Sanskrit texts

4. **Documentation**
   - Improve code documentation
   - Write tutorials and guides
   - Translate documentation

---

## Code Style

- Follow PEP 8 for Python code
- Use type hints where possible
- Write docstrings for functions and classes
- Keep functions focused and small

---

## Questions?

If you have questions about contributing, please:

- Open an issue on GitHub
- Check the existing documentation
- Reach out to the project maintainers

---

*Contributing Guide - Project Panini*  
*Last Updated: January 16, 2026*
