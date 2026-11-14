# RLCD Decision Schema Specification (`v0.2`)

**Module:** `src/schema/panini_rlcd_schema.json`  
**Architecture:** Neuro-Symbolic Decision Compiler (Jev / Laya RLCD Pattern)  
**Encoding Standard:** SLP1 (`Sanskrit Library Phonetic Basic`)

> **Status:** Draft design, not adopted; no results. All probabilities,
> latencies and ECE values below are illustrative, not measured. Reviewed in
> `docs/RLCD_TRANSITION_PLAN.md` (draft amendment 0.7), which lists the known
> gaps. RLCD and the Choice, Score and Noul primitives come from Jev (Guo et
> al., *Just Ask Jev: Reinforcement Learning for Calibrated Decisions as a
> Zero-Shot Detector of AI Alignment Failures*, arXiv:2609.29429, 2026).
> Jev's training is not published; the training described in section 4 is
> this project's own design.
>
> **Schema v0.3** (stage 2) is the machine-checked contract:
> `data/schemas/rlcd-clause.schema.json`, with fixtures and the constraint
> layer described in `docs/RLCD_CONSTRAINTS.md`. Where this document and v0.3
> differ, v0.3 holds. For example, v0.3 has no `upapada_nimitta` or
> `sambanDa_zazWI` role.

---

## 1. Architectural Overview

Instead of using a large autoregressive language model to predict Sanskrit surface tokens one by one—which leads to subword fragmentation and morphological hallucinations—Project Panini uses **reinforcement learning for calibrated decisions (RLCD)**, the approach introduced with Jev (arXiv:2609.29429), on a compact transformer encoder. The acronym also stands for reinforcement learning from contrastive distillation (Yang et al., 2024); here it always means the Jev sense.

In a single forward pass (target latency, not yet measured), the tiny transformer reads the input sentence (English or Sanskrit) alongside a fixed schema of grammatical questions. It outputs **calibrated probability distributions** over discrete Paninian parameters (*Vivakṣā*). The deterministic Rust engine (`Vidyut`) then compiles these parameters into mathematically guaranteed Sanskrit forms.

### RLCD Primitive Types Used
The three primitives follow Jev's definitions:

1. **`Choice`:** a probability distribution over a listed set of options, with the most probable option and a confidence (e.g., selecting the *Lakāra*, *Prayoga*, or *Kāraka* role). An absent slot is the option `NONE`. *Project choices, not from Jev:* a cap of 255 options and a Plackett–Luce head when options must be ranked.
2. **`Score`:** a probability distribution over ordered levels $0, \dots, K-1$, with the expected level (e.g., a graded naturalness or grammaticality rubric).
3. **`Noul`:** a yes/no question; returns $P(\text{yes})$ (e.g., "Is this split licensed by 6.1.101?", "Is this surface form lawful?").

---

## 2. Core JSON Decision Schema (Request Template)

When querying the RLCD encoder during **Path A (Constructor: English $\rightarrow$ Sanskrit)** or **Path B (Auditor: Sanskrit $\rightarrow$ Validation)**, the middleware passes the following schema structure alongside the candidate lexical pool retrieved from the *Dhātupāṭha* and *Amarakosha*.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "schema_version": "0.2.0",
  "task_routing": {
    "input_mode": {
      "type": "Choice",
      "options": [
        "CONSTRUCT_FROM_ENGLISH",
        "VALIDATE_SANSKRIT_SURFACE",
        "DISAMBIGUATE_SAMASA_SANDHI"
      ],
      "description": "Determines cognitive pipeline routing."
    },
    "surface_grammaticality": {
      "type": "Noul",
      "description": "Is the raw input already Paninian-compliant? Returns calibrated P(yes) (used in Auditor mode)."
    }
  },
  "vivaksha_clause_frame": {
    "prayoga": {
      "type": "Choice",
      "sutra_ref": "3.4.69 (laH karmaNi ca bhAve cAkarmakebhyaH)",
      "options": [
        "kartari",
        "karmani",
        "bhave"
      ],
      "description": "Voice selection: Active (Kartari), Passive (Karmani), or Impersonal (Bhāve)."
    },
    "lakara": {
      "type": "Choice",
      "sutra_ref": "3.2.123 - 3.3.176",
      "options": [
        "laW",
        "liW",
        "luW",
        "lfW",
        "loW",
        "laN",
        "viDiliN",
        "ASIrliN",
        "luN",
        "lfN"
      ],
      "description": "SLP1 encoded tense/mood markers (e.g., laW = Present/Laṭ, lfW = Future/Lṛṭ, laN = Imperfect Past/Laṅ)."
    }
  },
  "tinanta_verbal_core": {
    "dhatu_selection": {
      "type": "Choice",
      "max_candidates": 255,
      "allow_none": false,
      "candidates_source": "dynamic_lexical_lookup",
      "options_example": [
        "ga\\mx~ (01.1137 - gatO)",
        "i\\R (02.0040 - gatO)",
        "yA\\ (02.0044 - prApaRe)",
        "paWa~ (01.0381 - vyaktAyAM vAci)"
      ],
      "description": "Selects the exact Paninian verbal root, written as its Dhatupatha entry in SLP1 with anubandha and accent markers (Vidyut 0.4.0 needs `ga\\mx~`; `gam\\l~` is rejected and `gamx~` derives the wrong form `gamataH`)."
    },
    "upasarga_prefix": {
      "type": "Choice",
      "allow_none": true,
      "options": [
        "NONE",
        "pra", "parA", "apa", "sam", "anu", "ava", "nis", "nir",
        "dus", "dur", "vi", "AN", "ni", "aDi", "api", "ati",
        "su", "ut", "aBi", "prati", "pari", "upa"
      ],
      "description": "Selects the verbal prefix, or NONE if the root is unprefixed."
    },
    "pada_override": {
      "type": "Choice",
      "allow_none": true,
      "options": [
        "NONE",
        "parasmEpada",
        "Atmanepada"
      ],
      "description": "For Ubhayapada roots, decides whether the speaker intends fruit-for-self (Ātmanepada) or fruit-for-other (Parasmaipada)."
    },
    "purusha": {
      "type": "Choice",
      "sutra_ref": "1.4.101 (tiNas trIRi trIRi praTama-maDyama-uttamAH)",
      "options": ["praTama", "maDyama", "uttama"]
    },
    "vacana": {
      "type": "Choice",
      "sutra_ref": "1.4.102 (tAny ekavacana-dvivacana-bahuvacanAny ekaSaH)",
      "options": ["ekavacana", "dvivacana", "bahuvacana"]
    }
  },
  "karaka_subanta_slots": {
    "description": "Evaluated in parallel for each extracted noun phrase / entity in the input clause.",
    "slot_template": {
      "karaka_role": {
        "type": "Choice",
        "allow_none": true,
        "sutra_ref": "1.4.23 (kArake) - 1.4.55",
        "options": [
          "NONE",
          "kartf (1.4.54 - svatantraH kartA)",
          "karman (1.4.49 - kartur IpsitatamaM karma)",
          "karaRa (1.4.42 - sADakatamaM karaRam)",
          "sampradAna (1.4.32 - karmaRA yam aBiprEti sa sampradAnam)",
          "apAdAna (1.4.24 - Druvam apAye 'pAdAnam)",
          "aDikaraRa (1.4.45 - ADAro 'DikaraRam)",
          "sambanDa_zazWI (2.3.50 - zazWI Seze)",
          "upapada_nimitta (2.3.19 - सहयुक्तेऽप्रधाने etc.)"
        ]
      },
      "pratipadika_stem": {
        "type": "Choice",
        "max_candidates": 255,
        "candidates_source": "amarakosha_synonym_pool",
        "options_example": ["rAma", "vaMSa", "grAma", "vana", "pustaka"]
      },
      "linga": {
        "type": "Choice",
        "options": ["puMliNga", "strIliNga", "napuMsakaliNga"]
      },
      "vacana": {
        "type": "Choice",
        "options": ["ekavacana", "dvivacana", "bahuvacana"]
      }
    }
  }
}
```

---

## 3. Concrete Execution Trace (Single Forward Pass)

### Input State ($s$)
```text
User Input: "The boy happily goes to the village with his friend."
Mode: English-to-Sanskrit Construction
```

### RLCD Model Output (Calibrated Decisions)
The RLCD transformer evaluates the input state against the schema and returns the following probability distributions in a single pass:

```json
{
  "_note": "Illustrative values only; nothing here is measured.",
  "inference_time_ms": 18.4,
  "calibration_ece_estimate": 0.014,
  "decisions": {
    "vivaksha_clause_frame": {
      "prayoga": { "choice": "kartari", "prob": 0.982 },
      "lakara": { "choice": "laW", "prob": 0.965, "runner_up": { "choice": "loW", "prob": 0.021 } }
    },
    "tinanta_verbal_core": {
      "dhatu_selection": {
        "choice": "ga\\mx~",
        "prob": 0.910,
        "runner_up": { "choice": "i\\R", "prob": 0.075 }
      },
      "upasarga_prefix": { "choice": "NONE", "prob": 0.991 },
      "purusha": { "choice": "praTama", "prob": 0.998 },
      "vacana": { "choice": "ekavacana", "prob": 0.995 }
    },
    "entities": [
      {
        "source_span": "The boy",
        "karaka_role": { "choice": "kartf", "prob": 0.994 },
        "pratipadika_stem": { "choice": "bAlaka", "prob": 0.880, "runner_up": { "choice": "SiSu", "prob": 0.090 } },
        "linga": { "choice": "puMliNga", "prob": 0.999 },
        "vacana": { "choice": "ekavacana", "prob": 0.992 }
      },
      {
        "source_span": "to the village",
        "karaka_role": { "choice": "karman", "prob": 0.945 },
        "pratipadika_stem": { "choice": "grAma", "prob": 0.970 },
        "linga": { "choice": "puMliNga", "prob": 0.990 },
        "vacana": { "choice": "ekavacana", "prob": 0.996 }
      },
      {
        "source_span": "with his friend",
        "karaka_role": {
          "choice": "upapada_nimitta",
          "prob": 0.610,
          "runner_up": { "choice": "karaRa", "prob": 0.365 },
          "uncertainty_flag": "BRANCH_SYMBOLIC_ENGINE"
        },
        "upapada_particle": { "choice": "saha", "prob": 0.940 },
        "pratipadika_stem": { "choice": "mitra", "prob": 0.955 },
        "linga": { "choice": "napuMsakaliNga", "prob": 0.985 },
        "vacana": { "choice": "ekavacana", "prob": 0.991 }
      }
    ]
  }
}
```

### How the Symbolic Engine (`Vidyut`) Consumes This Output

1. **Deterministic Vibhakti Mapping:** Because `prayoga = kartari` ($0.982$), the Paninian state machine applies Sutra `2.3.46 (prAtipadikArtha-liNga-parimANa-vacana-mAtre praTamA)` to the *Kartṛ* (`bAlaka`), assigning **Prathamā Vibhakti** (`bAlakaH`). It applies `2.3.2 (karmaNi dvitIyA)` to the *Karman* (`grAma`), assigning **Dvitīyā Vibhakti** (`grAmam`).
2. **Handling Calibrated Uncertainty (`0.610` vs `0.365`):** Notice that for *"with his friend"*, the RLCD model splits its probability between `upapada_nimitta` ($61\%$) and `karaRa` ($36.5\%$). Because the model is Brier-calibrated, the Rust engine detects that confidence is below the $\tau = 0.85$ threshold and checks both rules:
   * Sutra `2.3.19 (sahayukte 'praDAne)` dictates **Tṛtīyā Vibhakti** when paired with `saha`.
   * Sutra `2.3.18 (kartfkaraRayos tftIyA)` also dictates **Tṛtīyā Vibhakti**.
   * Both branches converge on `mitreRa saha`!
3. **Final Symbolic Compilation (`SLP1` $\rightarrow$ `Devanagari`):**
   * **SLP1 Derived:** `bAlakaH mitreRa saha suKena grAmaM gacCati .`
   * **Aksharamukha Output:** `बालकः मित्रेण सह सुखेन ग्रामं गच्छति ।`

---

## 4. Training Objective: Brier Score + Batch ECE

> **Project design, not Jev's.** Jev measures calibration with ECE and
> reliability curves and does not publish its training objective. The loss
> below is supervised. The reinforcement-learning stages (a cost-aware
> confidence gate, and policy-gradient fine-tuning with a Vidyut-verified
> reward and a proper-scoring calibration reward) are specified in
> `docs/RLCD_TRANSITION_PLAN.md`, section 4.1. Two cautions: the hard ECE
> binning passes no gradient through bin membership, and adding ECE makes the
> loss no longer strictly proper.

To train the tiny encoder on consumer GPUs (e.g., single RTX 3090/4090) without reward hacking or overconfident hallucinations, the policy $\pi_\theta(a \mid s)$ is optimized using a strictly proper scoring rule over synthetic `Vidyut` derivations:

$$\mathcal{L}_{\text{RLCD}}(\theta) = \underbrace{\frac{1}{K} \sum_{k=1}^{K} \left( \pi_\theta(a_k \mid s) - y_k \right)^2}_{\text{Multi-Class Brier Score}} + \lambda_{\text{ECE}} \cdot \underbrace{\sum_{m=1}^{M} \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|}_{\text{Batch Expected Calibration Error}}$$

Where:
* $y_k \in \{0, 1\}$ is the ground-truth Paninian derivation label generated by `Vidyut`.
* $B_m$ represents confidence bin $m$ across the training mini-batch of size $N$.
* $\lambda_{\text{ECE}}$ (typically $0.5$) penalizes any divergence between the model's predicted probability and its empirical accuracy on Sanskrit morphological tags.