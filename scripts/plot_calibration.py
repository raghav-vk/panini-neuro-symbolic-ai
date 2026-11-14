#!/usr/bin/env python3
"""Paper figure for RLCD stage 1, from reports/rlcd-stage1/calibration.json (observed dev results).

Three panels, raw confidence, P-A seeds 7, 11 and 19:
  (a) reliability of the H-P2 ranker (equal-mass bins)
  (b) reliability of the discriminator asked as a Noul (equal-mass bins)
  (c) accuracy of accepted items against coverage, with the pre-registered thresholds marked

Raw confidence is shown because temperature scaling changed nothing (DEV_RESULTS.md). Seeds
differ by colour, marker and line style, so identity never rests on colour alone.
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Reference palette (dataviz skill), validated on white: slots 1-3 pass the lightness, chroma,
# CVD and normal-vision checks; aqua is under 3:1 contrast, so markers, line styles and the
# tables in SUMMARY.md carry identity too.
SERIES = {"7": ("#2a78d6", "o", "-"), "11": ("#eb6834", "s", "--"), "19": ("#1baf7a", "^", ":")}
INK, SECONDARY, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"


def style(ax, title, xlabel, ylabel):
    ax.set_title(title, loc="left", color=INK, fontsize=10)
    ax.set_xlabel(xlabel, color=SECONDARY)
    ax.set_ylabel(ylabel, color=SECONDARY)
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelcolor=SECONDARY, labelsize=8)


def reliability(ax, seeds, title):
    low = min(b["confidence"] for s in seeds.values() for b in s["raw"]["bins_equal_mass"])
    low = min(low, min(b["accuracy"] for s in seeds.values() for b in s["raw"]["bins_equal_mass"]))
    low = max(0.0, (int(low * 20) - 1) / 20)
    ax.plot([low, 1], [low, 1], color=MUTED, linewidth=1, linestyle=(0, (4, 3)), label="Perfect calibration")
    for seed, block in seeds.items():
        color, marker, line = SERIES[seed]
        b = block["raw"]["bins_equal_mass"]
        ece = block["raw"]["ece_equal_mass"]["value"]
        ax.plot([x["confidence"] for x in b], [x["accuracy"] for x in b], color=color, marker=marker,
                linestyle=line, linewidth=1.5, markersize=5, markeredgecolor="white", markeredgewidth=0.8,
                label=f"Seed {seed} (ECE {ece:.3f})")
    ax.set_xlim(low, 1.005)
    ax.set_ylim(low, 1.005)
    ax.set_aspect("equal")
    style(ax, title, "Confidence (raw)", "Accuracy")
    ax.legend(loc="upper left", fontsize=7.5, frameon=False, labelcolor=SECONDARY)


def coverage(ax, seeds, taus):
    floor = 1.0
    for seed, block in seeds.items():
        color, marker, line = SERIES[seed]
        curve = block["abstention"]["risk_coverage"]
        n = len(curve)
        start = n // 10  # below 10% coverage the curve is a handful of items
        xs = [(k + 1) / n for k in range(start, n)]
        ax.plot(xs, curve[start:], color=color, linestyle=line, linewidth=1.5, label=f"Seed {seed}")
        floor = min(floor, min(curve[start:]))
        for point in block["abstention"]["thresholds"]:
            ax.plot(point["coverage"], point["accepted_accuracy"], marker=marker, color=color, markersize=6,
                    markeredgecolor="white", markeredgewidth=0.8, linestyle="none")
    for tau, (x, y) in taus.items():
        ax.annotate(f"τ = {tau}", (x, y), xytext=(-7, -11), textcoords="offset points", fontsize=7.5,
                    color=SECONDARY, ha="right")
    ax.set_xlim(0.1, 1.0)
    ax.set_ylim(max(0.9, floor - 0.01), 1.003)
    style(ax, "(c) Abstention: accuracy of accepted items", "Coverage", "Accuracy of accepted items")
    ax.legend(loc="lower left", fontsize=7.5, frameon=False, labelcolor=SECONDARY)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=ROOT / "reports/rlcd-stage1/calibration.json")
    p.add_argument("--output", type=Path, nargs="+", default=[ROOT / "reports/rlcd-stage1/calibration_figure",
                                                             ROOT / "docs/paper/artifacts/rlcd_stage1_calibration"])
    args = p.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    result = json.loads(args.input.read_text())
    ranker = result["ranker"]["seeds"]
    noul = {s: b for s, b in result["noul"]["seeds"].items() if b["reproduction"]["passed"]}
    # Label each threshold once, at the seed-7 point.
    taus = {t["tau"]: (t["coverage"], t["accepted_accuracy"]) for t in ranker["7"]["abstention"]["thresholds"]}
    plt.rcParams.update({"font.size": 9, "font.family": "sans-serif", "pdf.fonttype": 42})
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.0))
    reliability(axes[0], ranker, "(a) Sandhi ranker (H-P2), 988 dev items")
    reliability(axes[1], noul, "(b) Discriminator as a Noul, 1,854 dev words")
    coverage(axes[2], ranker, taus)
    fig.text(0.01, 0.005, "Dev only. Observed outputs of the 4.94M-parameter encoder; out-of-fold, equal-mass bins. "
             "Source: reports/rlcd-stage1/calibration.json.", fontsize=7, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    for out in args.output:
        out.parent.mkdir(parents=True, exist_ok=True)
        for ext in ("pdf", "png"):
            fig.savefig(out.with_suffix(f".{ext}"), dpi=200, facecolor="white")
            print(out.with_suffix(f".{ext}"))
    plt.close(fig)


if __name__ == "__main__":
    main()
