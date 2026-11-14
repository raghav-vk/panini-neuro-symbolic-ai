# Project Panini: Unified Neuro-Symbolic Architecture (`v1.0`)

**File Path:** `docs/architecture/unified_neuro_symbolic_architecture_specification.md`  
**Core Components:** Tiny Byte/SLP1 Transformer (`S-PA`) + Calibrated RLCD Decision Engine + `Vidyut` Paninian Compiler  
**Target Hardware:** Consumer Silicon (Apple M-Series MPS / Single Consumer CUDA GPU / CPU)

> **Status:** Draft design, not adopted; no results. Only the pretraining
> metrics in section 3.1 are measured (`reports/pretraining-v1/pretrain_S_PA_seed11.json`).
> Every other probability, latency and memory figure is illustrative or a
> target. Reviewed in `docs/RLCD_TRANSITION_PLAN.md` (draft amendment 0.7),
> which lists the known gaps: Vidyut needs a constraint layer to reject
> invalid ASTs, the encoder has never seen English, and the joint AST
> confidence used by the gate is not yet defined. RLCD follows Jev (Guo et
> al., arXiv:2609.29429, 2026); Jev's training is not published, so the
> training here is this project's own design.

---

## 1. Executive Summary

Project Panini replaces the conventional, compute-heavy autoregressive Large Language Model (LLM) paradigm with a **Compiler-Style Neuro-Symbolic Architecture**. Instead of training a multi-billion-parameter decoder to probabilistically guess Sanskrit characters and inflections token-by-token, the system decouples **perception and semantic intent (System 1)** from **morphological and phonetic derivation (System 2)**:

1. **Perception Trunk (Pretrained Tiny Transformer — `4.94M` params):** Encodes raw UTF-8 / SLP1 byte sequences into contextual phonetic and morphological representations.
2. **Decision Layer (RLCD Engine):** Answers typed questions (Jev's Choice, Score and Noul) about discrete Paninian parameters (*Vivakṣā*, *Kāraka*, *Dhātu*, *Lakāra*) in a single parallel forward pass, with calibrated probabilities. Training starts supervised (Brier score, then temperature scaling on held-out dev) and adds reinforcement learning as specified in `docs/RLCD_TRANSITION_PLAN.md`, section 4.1.
3. **Symbolic Compiler (`Vidyut` Paninian Engine in Rust):** Deterministically executes the *Aṣṭādhyāyī* sūtras over the RLCD Abstract Syntax Tree (AST) to synthesize Sanskrit with full sūtra-level provenance. Vidyut derives a form for any input it is given, including invented roots and impossible combinations, so a constraint layer (Dhātupāṭha lookup, pada, transitivity, voice and number limits, round-trip check) must accept the AST first. Output is then valid for the encoded rules; it does not prove that the AST matches the speaker's meaning.

---

## 2. End-to-End System Architecture

```text
                                   [ User Input ]
                  (English Text / Sanskrit Text / Speech via ASR)
                                         │
                                         ▼
                  ┌─────────────────────────────────────────────┐
                  │  0. Normalization & Script Layer            │
                  │     • English: UTF-8 Bytes                  │
                  │     • Sanskrit: Devanagari/IAST ──► SLP1    │
                  └──────────────────────┬──────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  1. PERCEPTION TRUNK: Pretrained Tiny Transformer (4.94M S-PA Encoder)          │
│     • Checkpoint: runs/pretrain-S-PA-seed11 (Trained on MLM + Sandhi Disc)      │
│     • Input: Raw Byte / SLP1 Sequence X                                         │
│     • Output: Contextual Hidden States H ∈ ℝ^(L × d_model)                      │
│     • Role: Phonetic & morphological representation (zero text generation)      │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  2. DECISION LAYER: RLCD Engine (Calibrated Multi-Head Schema)                  │
│     • Parallel Single-Pass Evaluation over Typed Primitives (Choice/Score/Noul) │
│     • Emits: Paninian AST + Calibrated Probabilities p ∈ [0, 1]                 │
│     • Supervised Brier + temperature scaling, then RL (see transition plan)     │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         ▼                               ▼
            [ Path A: Constructor ]         [ Path B: Auditor / Validator ]
            (English ──► Sanskrit)          (Sanskrit ──► Proof & Correction)
                         │                               │
                         └───────────────┬───────────────┘
                                         │
                                         ▼
                         ┌───────────────────────────────┐
                         │ Confidence Gate (τ, e.g. 0.85)│
                         └───┬───────────────────────┬───┘
              (p ≥ τ: Direct)│                       │(p < τ: Ambiguous)
                             ▼                       ▼
              ┌──────────────────────┐   ┌───────────────────────────────┐
              │ Single-AST Execution │   │ Top-K Symbolic Branch Search  │
              └──────────────┬───────┘   └───────────────┬───────────────┘
                             │                           │
                             └─────────────┬─────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  3. SYMBOLIC COMPILER: Paninian Rules Engine (Vidyut / Rust)                    │
│     • vidyut-kosha: Lexical lookup of Dhātus & Prātipadikas                     │
│     • vidyut-prakriya: Deterministic Aṣṭādhyāyī derivation (Tiṅanta & Subanta)  │
│     • vidyut-sandhi / cheda: Phonetic fusion & morphological segmentation       │
│     • Audit Trace: Emits exact Sūtra numbers (e.g., 1.4.2, 2.3.18, 6.1.77)      │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  4. OUTPUT & SELF-IMPROVEMENT LOOP                                              │
│     • SLP1 ──► Devanagari (vidyut-lipi / Aksharamukha)                          │
│     • Verified Derivations logged to Replay Buffer for RLCD calibration updates │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Deep-Dive & Empirical Foundation

### 3.1 Layer 1: The Pretrained Tiny Transformer (`pretrain-S-PA`)

Rather than initializing a decision network from scratch, Layer 1 reuses the **4,937,220-parameter** byte-level Transformer encoder (`S-PA`) pretrained on 439,274 sentences (19.73 MB of SLP1 corpus data).

#### Pretraining Baseline Metrics (`seed11`, 34,720 steps, Apple Silicon `mps`)
| Metric | Initial (Step 1,000) | Final (Step 34,720) | Architectural Significance |
| :--- | :--- | :--- | :--- |
| **`train_mlm_loss`** | `3.2095` | `1.5366` | Smooth convergence of byte-level contextual representations. |
| **`masked_byte_accuracy`** | `25.33%` | `51.38%` | Demonstrates why pure neural byte prediction hits a ceiling on fusional morphology. |
| **`train_disc_loss`** | `0.3725` | `0.0302` | Training loss on the vowel-length swaps (`a/A`, `i/I`, `u/U`, `e/E`, `o/O`); see dev accuracy for generalisation. |
| **`disc_attested_accuracy`** | `97.85%` | `99.56%` | `1,576 / 1,583` valid Sanskrit words recognized accurately. |
| **`disc_altered_accuracy`** | `40.59%` | `91.14%` | `247 / 271` synthetic Sandhi/vowel corruptions caught (peak `91.51%` at Step 28k). |
| **`disc_balanced_accuracy`** | `69.22%` | `95.35%` | Shows the encoder detects single-word vowel-length swaps (the only alteration it was trained on); not evidence of broader grammatical knowledge. |

**Why Layer 1 Stops at Representation:**  
While the 4.94M encoder achieves **95.35% balanced accuracy** on discriminating valid vs. altered forms, **8.86%** of altered words still pass through unflagged, and surface byte generation plateaus at **51.38%**. Freezing or fine-tuning this encoder as a feature extractor $\mathbf{H} = f_{\theta}(\mathbf{x})$ preserves its compact 19.8 MB footprint while offloading exact surface generation to the RLCD + Vidyut layers.

---

### 3.2 Layer 2: The RLCD Engine (Calibrated Decision Heads)

Attached directly to the Tiny Transformer's pooled and span-level hidden states $\mathbf{H}$, the **RLCD (reinforcement learning for calibrated decisions, after Jev, arXiv:2609.29429)** module replaces the standard vocabulary projection matrix with structured, schema-conditioned Plackett–Luce and sigmoid heads:

* **Clause-Level Vivakṣā Heads:**
  * `prayoga`: `Choice(kartari, karmani, bhave)` — Sūtra `3.4.69`
  * `lakara`: `Choice(laW, liW, luW, lfW, loW, laN, viDiliN, ASIrliN, luN, lfN)` — Sūtras `3.2.123–3.3.176`
* **Verbal Core (`Tiṅanta`) Heads:**
  * `dhatu_selection`: `Choice(K <= 255)` over candidate roots retrieved from `vidyut-kosha`
  * `upasarga_prefix`: `Choice(NONE, pra, parA, apa, sam, ...)` (22 Upasargas + `NONE` for no prefix)
  * `purusha` & `vacana`: `Choice(praTama, maDyama, uttama)` $\times$ `Choice(eka, dvi, bahu)`
* **Nominal Slot (`Kāraka / Subanta`) Heads:**
  * Evaluated in parallel across extracted entity spans (span extraction not yet specified): `Choice(NONE, kartf, karman, karaRa, sampradAna, apAdAna, aDikaraRa, sambanDa_zazWI, upapada_nimitta)` paired with `linga` and `vacana`.
* **Token-Level Auditor Head (`Path B`):**
  * Upgrades the pretrained binary `disc` head into a calibrated `Noul` ("Is this word lawful here?") outputting $p_{\text{valid}}(w_i)$ for every surface token or sandhi boundary. The current head was trained only on single-word vowel-length swaps; detecting agreement errors between words needs a new objective and data.

#### Mathematical Calibration Objective
To guarantee that the neural network never bluffs when encountering ambiguous compounds (*Samāsa*) or homophonous *Sandhi* splits, RLCD optimizes the policy $\pi_\phi(a \mid \mathbf{H})$ using a **Multi-Class Brier Score** combined with a differentiable **Batch Expected Calibration Error (ECE)** penalty:

$$
\mathcal{L}_{\text{RLCD}}(\phi) = \frac{1}{K} \sum_{k=1}^{K} \left( \pi_\phi(a_k \mid \mathbf{H}) - y_k \right)^2 + \lambda_{\text{ECE}} \sum_{m=1}^{M} \frac{\vert B_m \vert}{N} \left\vert \text{acc}(B_m) - \text{conf}(B_m) \right\vert
$$

The goal is that when the RLCD head reports $p = 0.62$, it is right about $62\%$ of the time; this must be measured on held-out data, not assumed. The ECE term is a project choice, not Jev's: its hard binning passes no gradient through bin membership, and adding it makes the loss no longer strictly proper. Calibration would allow the **Confidence Gate ($\tau = 0.85$)** to switch between single-shot compilation ($p \ge 0.85$) and symbolic branch search ($p < 0.85$). Which probability the gate uses for a whole AST (heads are answered independently, but voice, case and number are coupled) is not yet defined.

---

### 3.3 Layer 3: The Paninian Rules Engine (`Vidyut`)

The symbolic backend is powered by the Rust-based `Vidyut` ecosystem (exposed to Python via PyO3 bindings `vidyut-py`):

1. **Fast Path ($p \ge \tau$):** The top-1 AST from RLCD is passed to `vidyut::prakriya::Vyakarana`. It executes the *Aṣṭādhyāyī* state machine, resolves rule conflicts (`1.4.2 vipratiṣedhe paraṁ kāryam`, `8.2.1 pūrvatrāsiddham`), inflects all *Subantas* and *Tiṅantas*, applies `vidyut-sandhi`, and emits the final string plus the step-by-step sūtra derivation log.
2. **Ambiguous Path ($p < \tau$ — Symbolic Branching):** When RLCD outputs split probabilities (for example, $p(\text{karaRa}) = 0.54$ vs. $p(\text{upapada\_nimitta}) = 0.41$), the engine enumerates the top-$k$ candidate ASTs covering $\ge 95\%$ cumulative probability mass:
   $$\mathcal{B}(\mathbf{x}) = \left\{ \text{AST}_j \;\middle|\; \sum_{j=1}^{k} p(\text{AST}_j) \ge 0.95 \right\}$$
   Each candidate branch is compiled and checked against Paninian constraints (*Upapada* rules, *Akarmaka/Sakarmaka* transitivity constraints, and attested *Kośa* usage). Invalid branches are pruned; valid derivations are returned with their exact sūtra proofs.

---

## 4. Dual Execution Walkthroughs

> All probabilities and timings in this section are illustrative, not model output.

### 4.1 Path A: The Constructor (English $\rightarrow$ Validated Sanskrit)

* **Input:** `"The two boys happily go to the village."`
* **Step 1 (Tiny Transformer):** Encodes UTF-8 bytes into $\mathbf{H} \in \mathbb{R}^{41 \times 256}$. The current encoder was pretrained on SLP1 Sanskrit only and has never seen English; Path A needs an English-capable encoder (transition plan, section 6).
* **Step 2 (RLCD Single-Pass Output — `3.4 ms`):**
  * `prayoga`: `kartari` ($p = 0.991$)
  * `lakara`: `laW` ($p = 0.978$)
  * `dhatu`: `ga\mx~` ($p = 0.942$)
  * `Span["The two boys"]`: `role = kartf` ($p = 0.995$), `stem = bAlaka` ($p = 0.910$), `vacana = dvivacana` ($p = 0.988$)
  * `Span["to the village"]`: `role = karman` ($p = 0.960$), `stem = grAma` ($p = 0.982$), `vacana = ekavacana` ($p = 0.994$)
  * `Span["happily"]`: `role = kriyAviSezaRa` ($p = 0.920$; not yet an option in the schema), `stem = suKa` (`tftIyA` adverbial, $p = 0.890$)
* **Step 3 (Vidyut Compilation — `0.4 ms`):**
  * `bAlaka` + `praTamA/dvi` $\xrightarrow{\text{1.4.54, 2.3.46, 6.1.102}}$ `bAlakO`
  * `suKa` + `tftIyA/eka` $\xrightarrow{\text{2.3.18, 7.1.12}}$ `suKena`
  * `grAma` + `dvitIyA/eka` $\xrightarrow{\text{1.4.49, 2.3.2, 6.1.107}}$ `grAmam`
  * `ga\mx~` + `laW` + `praTama/dvi` $\xrightarrow{\text{3.2.123, 3.4.78, 7.3.77}}$ `gacCataH`
  * Sandhi Assembly $\rightarrow$ `bAlakO suKena grAmaM gacCataH` $\rightarrow$ **बालकौ सुखेन ग्रामं गच्छतः ।**

### 4.2 Path B: The Auditor (Sanskrit Validation & Self-Correction)

* **Input:** `"rAmeRa vanaM gacCati"` *(Error: Instrumental agent `rAmeRa` paired with active verb `gacCati`)*
* **Step 1 (Tiny Transformer + Calibrated `disc` Head; target behaviour, beyond what the current head was trained to detect):**
  * Token `rAmeRa`: $p_{\text{valid}} = 0.14$ (Flagged below $\tau = 0.85$)
  * Token `vanaM`: $p_{\text{valid}} = 0.98$
  * Token `gacCati`: $p_{\text{valid}} = 0.42$ (Agreement conflict detected)
* **Step 2 (RLCD Repair Branching):**
  * **Branch 1 ($p = 0.68$ — Active Voice Repair):** Preserve `prayoga = kartari`, repair `rAmeRa` (`3/1`) $\rightarrow$ `rAmaH` (`1/1` via Sūtra `2.3.46`).
    * Vidyut Output: `rAmo vanaM gacCati` (**रामो वनं गच्छति**)
  * **Branch 2 ($p = 0.29$ — Passive Voice Repair):** Preserve `rAmeRa` (`3/1` via Sūtra `2.3.18 kartṛkaraṇayos tṛtīyā`), switch `prayoga = karmani` $\rightarrow$ `vanaM` (`1/1`) + `gamyate` (`gam + yak + te` via Sūtra `3.1.67 sārvadhātuke yak`).
    * Vidyut Output: `rAmeRa vanaM gamyate` (**रामेण वनं गम्यते**)
* **Step 3 (Output):** Both rule-derived corrections and their governing sūtras are presented to the user.

---

## 5. Repository Directory Layout & Implementation Blueprint

Proposed layout. Of the paths below, `data/processed/pretrain-v1/`, `data/rules/development_sandhi.jsonl`, `runs/pretrain-S-PA-seed11/` and `scripts/simulate_calibration.py` exist; the rest are planned. The encoder currently lives in `src/panini/pretraining.py`.

```text
panini-neuro-symbolic-ai/
├── docs/
│   ├── architecture/PANINIAN_ENGINE_ARCHITECTURE.md
│   ├── architecture/rlcd_decision_schema_specification.md
│   ├── architecture/unified_neuro_symbolic_architecture_specification.md  <-- This specification
│   └── RLCD_TRANSITION_PLAN.md              <-- Review and staged plan (draft amendment 0.7)
├── data/
│   ├── processed/pretrain-v1/               <-- SLP1 byte corpora (P-A.jsonl, dev_sentences.jsonl)
│   ├── rules/development_sandhi.jsonl       <-- Phonetic perturbation rules
│   └── rlcd_ast/                            <-- Paired (Input, Paninian AST) training data
├── runs/
│   └── pretrain-S-PA-seed11/                <-- Pretrained 4.94M Tiny Transformer checkpoints
├── src/
│   ├── models/
│   │   ├── tiny_transformer.py              <-- 4.94M Byte/SLP1 Encoder trunk (Layer 1)
│   │   └── rlcd_heads.py                    <-- Calibrated Choice/Score/Noul heads + Brier/ECE loss (Layer 2)
│   ├── engine/
│   │   ├── vidyut_compiler.py               <-- Rust Vidyut prakriya/sandhi wrapper (Layer 3)
│   │   └── neuro_symbolic_pipeline.py       <-- Confidence-gated orchestrator (Layers 1 + 2 + 3)
│   └── schema/
│       └── panini_rlcd_schema.json          <-- Typed decision schema definition
└── scripts/
    ├── eval_calibration.py                  <-- Planned (stage 1): real ECE, Brier & reliability diagrams from checkpoints
    ├── simulate_calibration.py              <-- Existing simulation only; its outputs are not results
    └── run_panini_engine.py                 <-- CLI / Voice inference entry point
```

---

## 6. Reference Implementation (`src/engine/neuro_symbolic_pipeline.py`)

Sketch only; not in the repository and not run. The existing encoder (`src/panini/pretraining.py`) has no `encode` method, and mean pooling over the whole sentence cannot carry several entity spans.

```python
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class PaninianAST:
    prayoga: str          # "kartari" | "karmani" | "bhave"
    lakara: str           # "laW" | "liW" | "luW" | "lfW" | "loW" | "laN" | ...
    dhatu: str            # SLP1 Dhatupatha entry e.g. "ga\\mx~"
    upasarga: Optional[str]
    purusha: str          # "praTama" | "maDyama" | "uttama"
    vacana: str           # "ekavacana" | "dvivacana" | "bahuvacana"
    karakas: List[Dict[str, str]]
    confidence: float


class CalibratedRLCDModule(nn.Module):
    """
    Layer 2: Attaches calibrated Plackett-Luce Choice and Score heads
    on top of the pretrained 4.94M S-PA Tiny Transformer trunk.
    """
    def __init__(self, encoder: nn.Module, d_model: int = 256, num_dhatus: int = 255):
        super().__init__()
        self.encoder = encoder
        self.prayoga_head = nn.Linear(d_model, 3)
        self.lakara_head = nn.Linear(d_model, 10)
        self.dhatu_head = nn.Linear(d_model, num_dhatus)
        self.upasarga_head = nn.Linear(d_model, 23)  # 22 Upasargas + NONE
        self.audit_score_head = nn.Linear(d_model, 1)

        # Learned temperature parameter for post-hoc / online ECE calibration
        self.log_temp = nn.Parameter(torch.zeros(1))

    def forward(self, byte_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        # Layer 1: Extract contextual SLP1/byte representations H in R^(B x L x D)
        hidden_states = self.encoder.encode(byte_ids, attention_mask=attention_mask)
        pooled = hidden_states.mean(dim=1)

        temp = torch.exp(self.log_temp).clamp(min=0.05, max=10.0)

        return {
            "prayoga_probs": F.softmax(self.prayoga_head(pooled) / temp, dim=-1),
            "lakara_probs": F.softmax(self.lakara_head(pooled) / temp, dim=-1),
            "dhatu_probs": F.softmax(self.dhatu_head(pooled) / temp, dim=-1),
            "upasarga_probs": F.softmax(self.upasarga_head(pooled) / temp, dim=-1),
            "token_validity_scores": torch.sigmoid(self.audit_score_head(hidden_states) / temp).squeeze(-1),
        }


def compute_rlcd_brier_ece_loss(
    probs: torch.Tensor,
    targets: torch.Tensor,
    num_bins: int = 10,
    lambda_ece: float = 0.5,
) -> Tuple[torch.Tensor, Dict[str, float]]:
    """
    Strictly Proper Scoring Rule: Multi-Class Brier Score + Differentiable Batch ECE.
    """
    num_classes = probs.size(-1)
    one_hot = F.one_hot(targets, num_classes=num_classes).float()

    # 1. Multi-class Brier score
    brier_loss = torch.mean(torch.sum((probs - one_hot) ** 2, dim=-1))

    # 2. Batch Expected Calibration Error (ECE)
    confidences, predictions = torch.max(probs, dim=-1)
    accuracies = (predictions == targets).float()

    ece = torch.zeros(1, device=probs.device)
    bin_boundaries = torch.linspace(0.0, 1.0, num_bins + 1, device=probs.device)

    for i in range(num_bins):
        in_bin = (confidences > bin_boundaries[i]) & (confidences <= bin_boundaries[i + 1])
        prop_in_bin = in_bin.float().mean()
        if prop_in_bin > 0:
            accuracy_in_bin = accuracies[in_bin].mean()
            avg_confidence_in_bin = confidences[in_bin].mean()
            ece += torch.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin

    total_loss = brier_loss + lambda_ece * ece.squeeze(0)
    return total_loss, {"brier": brier_loss.item(), "ece": ece.item()}
```

---

## 7. Hardware & Latency Profile

**Targets, not measurements.** Only the parameter count (4,937,220) is measured. Latency and memory will be measured on the project Mac in stage 1 and reported with every accuracy figure.

| Stage | Component | Precision / Size | Execution Device | Target latency (p95) |
| :--- | :--- | :--- | :--- | :--- |
| **Layer 1** | Tiny Transformer (`S-PA`, 4.94M params) | FP32 (`19.8 MB`) / FP16 (`9.9 MB`) | Apple MPS / CPU / CUDA | `~2.1 ms` |
| **Layer 2** | RLCD Decision Heads (`Choice` / `Score`) | FP32 (`< 1.2 MB`) | Apple MPS / CPU / CUDA | `~0.8 ms` |
| **Layer 3** | `Vidyut` Paninian Engine (`prakriya` + `sandhi`) | Native Rust FFI (`~15 MB` lexicon) | Host CPU | `~0.5 ms` |
| **Total** | **End-to-End Neuro-Symbolic Pipeline** | **~36 MB Total RAM** | **Consumer Laptop / Desktop** | **~3.4 ms** |