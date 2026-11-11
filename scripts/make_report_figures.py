"""Generate the report's data figures (vector PDFs) from the saved experiment results.

Run: python scripts/make_report_figures.py   (needs matplotlib; not an application dependency)
"""

import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

BLUE, GREEN, RED, GREY = "#2457d6", "#1f9d63", "#d1433b", "#8590a0"
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.axisbelow": True,
        "figure.dpi": 150,
        "pdf.fonttype": 42,
    }
)

data = json.loads((ROOT / "results/experiments.json").read_text(encoding="utf-8"))
records = data["records"]
summary = data["summary"]
ps = [row["p"] for row in summary]
labels = [f"{p:g}" for p in ps]


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.pdf")
    plt.close(fig)
    print("wrote", OUT / f"{name}.pdf")


# 1. Fraction of strategyproof instances per attack probability
fig, ax = plt.subplots(figsize=(5.6, 3.2))
fractions = [row["fraction"] * 100 for row in summary]
bars = ax.bar(labels, fractions, color=BLUE, width=0.6)
for bar, row in zip(bars, summary):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 1.5,
        f"{row['fraction'] * 100:.1f}%\n({row['strategyproof']}/{row['instances']})",
        ha="center",
        va="bottom",
        fontsize=8.5,
    )
ax.set_ylim(0, 100)
ax.set_xlabel("Attack probability $p$")
ax.set_ylabel("Strategyproof instances (%)")
save(fig, "fig_strategyproof_fraction")

# 2. Outcome breakdown: how the sufficient condition relates to measured strategyproofness
fig, ax = plt.subplots(figsize=(5.6, 3.4))
holds = [row["condition_holds"] for row in summary]
converse = [row["sp_condition_fails"] for row in summary]
manip = [row["instances"] - row["strategyproof"] for row in summary]
ax.bar(labels, holds, color=GREEN, width=0.6, label="Condition holds (all strategyproof)")
ax.bar(
    labels,
    converse,
    bottom=holds,
    color=BLUE,
    width=0.6,
    label="Strategyproof, condition fails",
)
ax.bar(
    labels,
    manip,
    bottom=[h + c for h, c in zip(holds, converse)],
    color=RED,
    width=0.6,
    label="Manipulable",
)
ax.set_xlabel("Attack probability $p$")
ax.set_ylabel("Instances (out of 1000)")
ax.set_ylim(0, 1000)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1, frameon=False, fontsize=8.5)
save(fig, "fig_condition_breakdown")

# 3. Heatmap: strategyproof fraction by p and number of arguments
counts = defaultdict(lambda: [0, 0])
for r in records:
    cell = counts[(r["p"], r["n"])]
    cell[0] += r["strategyproof"]
    cell[1] += 1
ns = sorted({r["n"] for r in records})
grid = [[counts[(p, n)][0] / counts[(p, n)][1] * 100 for n in ns] for p in ps]
cmap = LinearSegmentedColormap.from_list("sp", ["#f3f5f9", BLUE])
fig, ax = plt.subplots(figsize=(4.6, 3.3))
ax.grid(False)
im = ax.imshow(grid, cmap=cmap, vmin=0, vmax=100, aspect="auto")
ax.set_xticks(range(len(ns)), [str(n) for n in ns])
ax.set_yticks(range(len(ps)), labels)
for i, row in enumerate(grid):
    for j, value in enumerate(row):
        ax.text(
            j, i, f"{value:.1f}", ha="center", va="center",
            color="white" if value > 55 else "#111827", fontsize=9,
        )
ax.set_xlabel("Number of arguments $n$")
ax.set_ylabel("Attack probability $p$")
fig.colorbar(im, ax=ax, label="Strategyproof (%)")
save(fig, "fig_heatmap_p_n")

# 4. Generator check: measured mean attacks vs. expectation p * E[n(n-1)]
expected_pairs = sum(n * (n - 1) for n in ns) / len(ns)
measured = []
for p in ps:
    group = [len(r["attacks"]) for r in records if r["p"] == p]
    measured.append(sum(group) / len(group))
fig, ax = plt.subplots(figsize=(5.0, 3.2))
ax.plot(ps, [p * expected_pairs for p in ps], color=GREY, linestyle="--", label="Expected $p\\,E[n(n-1)]$")
ax.plot(ps, measured, color=BLUE, marker="o", label="Measured (1000 instances per $p$)")
ax.set_xlabel("Attack probability $p$")
ax.set_ylabel("Mean number of attacks")
ax.legend(frameon=False)
save(fig, "fig_generator_check")

# 5. Cost of the exhaustive check: m * 2^n deviations, confirmed by every strategyproof instance
agents = data["config"]["agents"]
measured_cost = defaultdict(set)
for r in records:
    if r["strategyproof"]:
        measured_cost[r["n"]].add(r["comparisons"])
assert all(len(v) == 1 for v in measured_cost.values())
assert all(next(iter(v)) == agents * 2**n for n, v in measured_cost.items())
fig, ax = plt.subplots(figsize=(4.8, 3.2))
curve = range(4, 13)
ax.plot(list(curve), [agents * 2**n for n in curve], color=GREY, linestyle="--", label=f"$m\cdot 2^n$, $m={agents}$")
ax.plot(
    sorted(measured_cost),
    [next(iter(measured_cost[n])) for n in sorted(measured_cost)],
    color=BLUE, marker="o", linestyle="none", markersize=7,
    label="Measured (every strategyproof instance)",
)
ax.axvspan(5.5, 8.5, color="#e8efff", zorder=0)
ax.set_yscale("log")
ax.set_xlabel("Number of arguments $n$")
ax.set_ylabel("Deviations checked (log scale)")
ax.legend(frameon=False, fontsize=8.5, loc="upper left")
save(fig, "fig_comparisons_by_n")

# Numbers used in the text, for convenience
total = len(records)
print("total", total, "strategyproof", sum(r["strategyproof"] for r in records))
