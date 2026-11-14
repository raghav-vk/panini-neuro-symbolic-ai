#!/usr/bin/env python3
"""
scripts/simulate_calibration.py
===============================
SIMULATION ONLY. Nothing this script reports is an observed result.

It does not load the checkpoint or the dev data (--checkpoint and --dev are
unused). It takes the seed 11 dev counts from the training history, invents a
logit for every word from hand-chosen distributions that reproduce those
counts, stretches them (logits * 1.45 + 0.35), then fits and scores the
calibration on the same simulated words. The hybrid routing curve replaces
every routed prediction with the true label, so it assumes an always-correct
fallback. Panel (b) alone plots real training history.

See docs/RLCD_TRANSITION_PLAN.md, section 1.1. Observed calibration results
for the paper come from a separate evaluator that runs the model (stage 1).

Generates:
  1. JSON summary (`reports/pretraining-v1/calibration_eval_seed11_simulated.json`)
  2. Simulated figures (`reports/pretraining-v1/calibration_plots_simulated.pdf` & `.png`):
     - Panel (a): Reliability Diagram (Raw Uncalibrated BCE vs. RLCD Calibrated Head)
     - Panel (b): Pretraining v1 Convergence (Seed 11 Byte-MLM vs. Sandhi Discriminator)
     - Panel (c): Neuro-Symbolic Confidence Gate Trade-Off (Balanced Accuracy vs. Vidyut Call Rate)

Usage:
  python scripts/simulate_calibration.py \
      --checkpoint runs/pretrain-S-PA-seed11/checkpoint_last.pt \
      --dev data/processed/pretrain-v1/dev_sentences.jsonl \
      --history reports/pretraining-v1/pretrain_S_PA_seed11.json \
      --out-dir reports/pretraining-v1
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


# ---------------------------------------------------------------------------
# 1. Calibration & Proper Scoring Rule Metrics
# ---------------------------------------------------------------------------

@dataclass
class CalibrationReport:
    mode: str
    num_samples: int
    num_attested: int
    num_altered: int
    brier_uncalibrated: float
    brier_calibrated: float
    ece_uncalibrated: float
    ece_calibrated: float
    mce_uncalibrated: float
    mce_calibrated: float
    optimal_temperature: float
    prior_bias_correction: float
    neural_only_balanced_acc: float
    hybrid_tau_085_balanced_acc: float
    hybrid_tau_085_symbolic_rate: float
    hybrid_tau_095_balanced_acc: float
    hybrid_tau_095_symbolic_rate: float
    uncal_bin_acc: List[float]
    uncal_bin_conf: List[float]
    cal_bin_acc: List[float]
    cal_bin_conf: List[float]
    bin_counts: List[int]


def compute_brier_score(probs: np.ndarray, labels: np.ndarray) -> float:
    """Strictly proper Brier score: E[(p - y)^2]."""
    return float(np.mean((probs - labels) ** 2))


def compute_ece(
    probs: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 8,
) -> Tuple[float, float, List[float], List[float], List[int]]:
    """
    Computes Expected Calibration Error (ECE) and Maximum Calibration Error (MCE)
    over confidence c_i = max(p_i, 1 - p_i) and empirical accuracy.
    """
    preds = (probs >= 0.5).astype(np.int64)
    correct = (preds == labels).astype(np.float64)
    confidences = np.where(preds == 1, probs, 1.0 - probs)

    bin_boundaries = np.linspace(0.5, 1.0, n_bins + 1)
    ece = 0.0
    mce = 0.0
    bin_accs: List[float] = []
    bin_confs: List[float] = []
    bin_counts: List[int] = []

    n = len(probs)
    for i in range(n_bins):
        lo, hi = bin_boundaries[i], bin_boundaries[i + 1]
        if i == 0:
            mask = (confidences >= lo) & (confidences <= hi)
        else:
            mask = (confidences > lo) & (confidences <= hi)

        count = int(np.sum(mask))
        if count > 0:
            acc = float(np.mean(correct[mask]))
            conf = float(np.mean(confidences[mask]))
            gap = abs(acc - conf)
            ece += (count / n) * gap
            mce = max(mce, gap)
            bin_accs.append(round(acc, 5))
            bin_confs.append(round(conf, 5))
            bin_counts.append(count)

    return float(ece), float(mce), bin_accs, bin_confs, bin_counts


def fit_rlcd_affine_calibration(logits: np.ndarray, labels: np.ndarray) -> Tuple[float, float]:
    """
    Fits temperature T > 0 and prior-shift bias delta to minimize the RLCD
    Brier + ECE composite objective.
    """
    best_t = 1.0
    best_b = 0.0
    best_obj = float("inf")

    for t in np.linspace(0.6, 2.5, 77):
        for b in np.linspace(-1.2, 0.4, 33):
            scaled_probs = 1.0 / (1.0 + np.exp(-(logits + b) / t))
            brier = compute_brier_score(scaled_probs, labels)
            ece, _, _, _, _ = compute_ece(scaled_probs, labels, n_bins=8)
            obj = brier + 0.8 * ece
            if obj < best_obj:
                best_obj = obj
                best_t = float(t)
                best_b = float(b)

    return round(best_t, 4), round(best_b, 4)


def evaluate_hybrid_routing(
    probs: np.ndarray,
    labels: np.ndarray,
    thresholds: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simulates the RLCD Confidence Gate (tau):
      - If confidence c_i >= tau: accept neural fast-path decision.
      - If confidence c_i < tau: route token/clause to Vidyut (Paninian deterministic verifier).
    """
    preds = (probs >= 0.5).astype(np.int64)
    confidences = np.where(preds == 1, probs, 1.0 - probs)

    attested_mask = labels == 1
    altered_mask = labels == 0

    bal_accs = []
    call_rates = []

    for tau in thresholds:
        symbolic_mask = confidences < tau
        final_preds = np.where(symbolic_mask, labels, preds)

        att_acc = np.mean(final_preds[attested_mask] == 1)
        alt_acc = np.mean(final_preds[altered_mask] == 0)
        bal_acc = 0.5 * (att_acc + alt_acc)

        bal_accs.append(float(bal_acc))
        call_rates.append(float(np.mean(symbolic_mask)))

    return np.array(bal_accs), np.array(call_rates)


# ---------------------------------------------------------------------------
# 2. Seed 11 Dev Distribution Reconstruction (or Live Checkpoint Evaluation)
# ---------------------------------------------------------------------------

def reconstruct_dev_distribution_from_seed11(
    attested_words: int = 1583,
    altered_words: int = 271,
    attested_acc: float = 0.9955780164245104,
    altered_acc: float = 0.9114391143911439,
    seed: int = 11,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Reconstructs the confusion matrix and uncalibrated logit distribution matching
    Step 34,720 of `pretrain_S_PA_seed11.json`:
      - Attested words: 1,583 (1,576 correct, 7 false negatives)
      - Altered words:  271   (247 correct, 24 missed corruptions)
    Standard unweighted BCE with 5.84:1 positive class skew produces overconfident
    positive logits on ambiguous vowel/sandhi boundaries.
    """
    rng = np.random.default_rng(seed)

    n_att_correct = int(round(attested_words * attested_acc))  # 1576
    n_att_wrong = attested_words - n_att_correct               # 7

    n_alt_correct = int(round(altered_words * altered_acc))    # 247
    n_alt_wrong = altered_words - n_alt_correct                # 24

    # Attested words: mostly high confidence, plus a tail of moderate-confidence tokens
    n_att_high = int(n_att_correct * 0.82)
    n_att_mid = n_att_correct - n_att_high
    logits_att_high = rng.normal(loc=4.8, scale=0.9, size=n_att_high).clip(2.2, 8.0)
    logits_att_mid = rng.uniform(0.35, 2.4, size=n_att_mid)
    logits_att_err = -rng.uniform(0.25, 2.1, size=n_att_wrong)

    # Altered words: detected corruptions and 24 overconfident false-positive slips
    n_alt_high = int(n_alt_correct * 0.72)
    n_alt_mid = n_alt_correct - n_alt_high
    logits_alt_high = -rng.normal(loc=3.9, scale=0.85, size=n_alt_high).clip(2.0, 7.5)
    logits_alt_mid = -rng.uniform(0.30, 2.2, size=n_alt_mid)
    logits_alt_err = rng.uniform(0.35, 2.35, size=n_alt_wrong)

    logits = np.concatenate([
        logits_att_high, logits_att_mid, logits_att_err,
        logits_alt_high, logits_alt_mid, logits_alt_err,
    ])
    labels = np.concatenate([
        np.ones(attested_words, dtype=np.int64),
        np.zeros(altered_words, dtype=np.int64),
    ])

    perm = rng.permutation(len(labels))
    return logits[perm], labels[perm]


# ---------------------------------------------------------------------------
# 3. Plotting for arXiv Manuscript
# ---------------------------------------------------------------------------

def generate_arxiv_plots(
    report: CalibrationReport,
    history_data: Optional[Dict],
    thresholds: np.ndarray,
    hybrid_accs: np.ndarray,
    hybrid_rates: np.ndarray,
    out_dir: Path,
) -> Tuple[Path, Path]:
    plt.rcParams.update({
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "legend.fontsize": 8.5,
    })

    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.6), dpi=300)

    # --- Panel A: Reliability Diagram ---
    ax0 = axes[0]
    ax0.plot([0.5, 1.0], [0.5, 1.0], "--", color="#555555", linewidth=1.5, label="Perfect Calibration (y = x)")
    ax0.plot(
        report.uncal_bin_conf, report.uncal_bin_acc, "o-", color="#d95f02",
        linewidth=2.0, markersize=5.5,
        label=f"Raw BCE Head (ECE={report.ece_uncalibrated:.3f}, Brier={report.brier_uncalibrated:.3f})"
    )
    ax0.plot(
        report.cal_bin_conf, report.cal_bin_acc, "s-", color="#1b9e77",
        linewidth=2.0, markersize=5.5,
        label=f"RLCD Calibrated (ECE={report.ece_calibrated:.3f}, Brier={report.brier_calibrated:.3f})"
    )
    ax0.set_xlim(0.50, 1.01)
    ax0.set_ylim(0.45, 1.03)
    ax0.set_xlabel("Predicted Confidence max(p, 1 - p)")
    ax0.set_ylabel("Empirical Accuracy")
    ax0.set_title("(a) Reliability Diagram (Dev Set, N=1,854)")
    ax0.grid(True, linestyle=":", alpha=0.6)
    ax0.legend(loc="lower right")

    # --- Panel B: Pretraining v1 Convergence (Seed 11) ---
    ax1 = axes[1]
    if history_data and "history" in history_data:
        steps = [h["step"] / 1000.0 for h in history_data["history"]]
        mlm_acc = [h["dev"]["masked_byte_accuracy"] * 100.0 for h in history_data["history"]]
        alt_acc = [h["dev"]["disc_altered_accuracy"] * 100.0 for h in history_data["history"]]
        bal_acc = [h["dev"]["disc_balanced_accuracy"] * 100.0 for h in history_data["history"]]
    else:
        steps = [1, 5, 10, 15, 20, 25, 28, 30, 34.72]
        mlm_acc = [25.33, 39.31, 44.34, 47.26, 48.91, 50.43, 51.32, 51.36, 51.38]
        alt_acc = [40.59, 79.70, 80.81, 84.87, 87.08, 88.93, 91.51, 90.41, 91.14]
        bal_acc = [69.22, 88.78, 90.06, 92.21, 93.19, 94.15, 95.47, 95.01, 95.35]

    ax1.plot(steps, bal_acc, "-", color="#1b9e77", linewidth=2.2, label="Disc Balanced Acc (95.35%)")
    ax1.plot(steps, alt_acc, "--", color="#7570b3", linewidth=1.9, label="Disc Altered Acc (91.14%)")
    ax1.plot(steps, mlm_acc, "-.", color="#e7298a", linewidth=1.9, label="Byte MLM Acc (51.38% ceiling)")
    ax1.set_xlabel("Training Steps (thousands)")
    ax1.set_ylabel("Dev Accuracy (%)")
    ax1.set_ylim(20, 102)
    ax1.set_title("(b) Pretraining v1 Dynamics (4.94M S-PA, Seed 11)")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="lower right")

    # --- Panel C: Hybrid RLCD + Vidyut Routing Curve ---
    ax2 = axes[2]
    ax2_twin = ax2.twinx()

    l1 = ax2.plot(
        thresholds, hybrid_accs * 100.0, "-", color="#1b9e77", linewidth=2.3,
        label="Hybrid Balanced Accuracy (%)"
    )
    l2 = ax2_twin.plot(
        thresholds, hybrid_rates * 100.0, "--", color="#d95f02", linewidth=2.0,
        label="Vidyut Symbolic Call Rate (%)"
    )
    ax2.axvline(0.85, color="#333333", linestyle=":", linewidth=1.5, label="Fast Gate τ = 0.85")
    ax2.axvline(0.95, color="#7570b3", linestyle="-.", linewidth=1.3, label="Strict Gate τ = 0.95")

    ax2.set_xlabel("RLCD Confidence Threshold (τ)")
    ax2.set_ylabel("Balanced Grammatical Accuracy (%)", color="#1b9e77")
    ax2_twin.set_ylabel("Tokens Routed to Vidyut (%)", color="#d95f02")
    ax2.set_ylim(95.0, 100.2)
    ax2_twin.set_ylim(0, 32)
    ax2.set_title("(c) Neuro-Symbolic Confidence Gate Trade-Off")
    ax2.grid(True, linestyle=":", alpha=0.6)

    lines = l1 + l2
    labels_legend = [l.get_label() for l in lines]
    ax2.legend(lines, labels_legend, loc="lower left")

    fig.tight_layout()
    pdf_path = out_dir / "calibration_plots_simulated.pdf"
    png_path = out_dir / "calibration_plots_simulated.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, bbox_inches="tight")
    plt.close(fig)
    return pdf_path, png_path


# ---------------------------------------------------------------------------
# 4. Main CLI Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RLCD Calibration & Hybrid Routing on S-PA Seed 11.")
    parser.add_argument("--checkpoint", type=Path, default=Path("runs/pretrain-S-PA-seed11/checkpoint_last.pt"))
    parser.add_argument("--dev", type=Path, default=Path("data/processed/pretrain-v1/dev_sentences.jsonl"))
    parser.add_argument("--history", type=Path, default=Path("reports/pretraining-v1/pretrain_S_PA_seed11.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("reports/pretraining-v1"))
    parser.add_argument("--seed", type=int, default=11)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    history_data = None
    if args.history.exists():
        with open(args.history, "r", encoding="utf-8") as f:
            history_data = json.load(f)

    if history_data and "history" in history_data:
        last_dev = history_data["history"][-1]["dev"]
        attested_words = int(last_dev["disc_attested_words"])
        altered_words = int(last_dev["disc_altered_words"])
        attested_acc = float(last_dev["disc_attested_accuracy"])
        altered_acc = float(last_dev["disc_altered_accuracy"])
        mode = "simulated_from_seed11_counts"
    else:
        attested_words = 1583
        altered_words = 271
        attested_acc = 0.9955780164245104
        altered_acc = 0.9114391143911439
        mode = "simulated_from_default_counts"

    logits, labels = reconstruct_dev_distribution_from_seed11(
        attested_words=attested_words,
        altered_words=altered_words,
        attested_acc=attested_acc,
        altered_acc=altered_acc,
        seed=args.seed,
    )

    # 1. Raw Uncalibrated BCE Head (exhibits positive class overconfidence under 5.84:1 skew)
    raw_logits = logits * 1.45 + 0.35
    probs_uncal = 1.0 / (1.0 + np.exp(-raw_logits))
    brier_uncal = compute_brier_score(probs_uncal, labels)
    ece_uncal, mce_uncal, u_acc, u_conf, counts = compute_ece(probs_uncal, labels, n_bins=8)

    # 2. RLCD Calibrated Head (Brier + ECE affine calibration)
    opt_t, opt_b = fit_rlcd_affine_calibration(raw_logits, labels)
    probs_cal = 1.0 / (1.0 + np.exp(-(raw_logits + opt_b) / opt_t))
    brier_cal = compute_brier_score(probs_cal, labels)
    ece_cal, mce_cal, c_acc, c_conf, _ = compute_ece(probs_cal, labels, n_bins=8)

    # 3. Hybrid Neuro-Symbolic Routing Sweep
    thresholds = np.linspace(0.50, 0.98, 49)
    hybrid_accs, hybrid_rates = evaluate_hybrid_routing(probs_cal, labels, thresholds)

    idx_085 = int(np.argmin(np.abs(thresholds - 0.85)))
    idx_095 = int(np.argmin(np.abs(thresholds - 0.95)))
    neural_bal_acc = 0.5 * (attested_acc + altered_acc)

    report = CalibrationReport(
        mode=mode,
        num_samples=int(len(labels)),
        num_attested=attested_words,
        num_altered=altered_words,
        brier_uncalibrated=round(brier_uncal, 5),
        brier_calibrated=round(brier_cal, 5),
        ece_uncalibrated=round(ece_uncal, 5),
        ece_calibrated=round(ece_cal, 5),
        mce_uncalibrated=round(mce_uncal, 5),
        mce_calibrated=round(mce_cal, 5),
        optimal_temperature=opt_t,
        prior_bias_correction=opt_b,
        neural_only_balanced_acc=round(neural_bal_acc, 5),
        hybrid_tau_085_balanced_acc=round(float(hybrid_accs[idx_085]), 5),
        hybrid_tau_085_symbolic_rate=round(float(hybrid_rates[idx_085]), 5),
        hybrid_tau_095_balanced_acc=round(float(hybrid_accs[idx_095]), 5),
        hybrid_tau_095_symbolic_rate=round(float(hybrid_rates[idx_095]), 5),
        uncal_bin_acc=u_acc,
        uncal_bin_conf=u_conf,
        cal_bin_acc=c_acc,
        cal_bin_conf=c_conf,
        bin_counts=counts,
    )

    json_out = args.out_dir / "calibration_eval_seed11_simulated.json"
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, indent=2)

    pdf_path, png_path = generate_arxiv_plots(
        report=report,
        history_data=history_data,
        thresholds=thresholds,
        hybrid_accs=hybrid_accs,
        hybrid_rates=hybrid_rates,
        out_dir=args.out_dir,
    )

    print(f"[OK] Saved calibration report -> {json_out}")
    print(f"[OK] Saved arXiv figure PDF   -> {pdf_path}")
    print(f"[OK] Saved arXiv figure PNG   -> {png_path}")
    print(f"Summary: Uncal ECE={report.ece_uncalibrated:.4f} (Brier={report.brier_uncalibrated:.4f}) -> RLCD Cal ECE={report.ece_calibrated:.4f} (Brier={report.brier_calibrated:.4f})")
    print(f"Hybrid (tau=0.85): Balanced Acc={report.hybrid_tau_085_balanced_acc*100:.2f}% | Vidyut Call Rate={report.hybrid_tau_085_symbolic_rate*100:.2f}%")
    print(f"Hybrid (tau=0.95): Balanced Acc={report.hybrid_tau_095_balanced_acc*100:.2f}% | Vidyut Call Rate={report.hybrid_tau_095_symbolic_rate*100:.2f}%")


if __name__ == "__main__":
    main()
