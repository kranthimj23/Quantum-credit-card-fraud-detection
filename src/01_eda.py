"""
Exploratory data analysis for the credit-card-fraud dataset.

Prints summary statistics, class imbalance, per-feature stats, and writes a few
PNG plots to results/ for the management deck.

Usage:
    python src/01_eda.py [--prefer kaggle_2023_balanced|kaggle_ulb_original|synthetic_fallback]
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from data_loader import load

logger = logging.getLogger(__name__)
RESULTS = Path(__file__).resolve().parent.parent / "results"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefer", default=None, help="Preferred dataset name")
    parser.add_argument("--nrows", type=int, default=None, help="Optional row cap")
    args = parser.parse_args()

    ds = load(prefer=args.prefer, nrows=args.nrows)
    print("=" * 70)
    print(ds.summary())
    print("=" * 70)

    df = ds.df
    print("\nFirst 5 rows:")
    print(df.head().to_string())

    print("\nClass distribution:")
    print(df[ds.target_col].value_counts())

    print("\nAmount stats by class:")
    print(df.groupby(ds.target_col)["Amount"].describe().to_string())

    RESULTS.mkdir(parents=True, exist_ok=True)

    # 1. Class imbalance bar chart.
    fig, ax = plt.subplots(figsize=(6, 4))
    counts = df[ds.target_col].value_counts().sort_index()
    ax.bar(["Normal (0)", "Fraud (1)"], counts.values, color=["#2E86AB", "#E63946"])
    ax.set_title(f"Class distribution -- {ds.name}\n{ds.n_rows:,} rows, fraud rate {ds.fraud_rate * 100:.4f}%")
    ax.set_ylabel("count")
    ax.set_yscale("log" if not ds.is_balanced else "linear")
    for i, v in enumerate(counts.values):
        ax.text(i, v, f"{v:,}", ha="center", va="bottom")
    fig.tight_layout()
    out = RESULTS / f"01_class_distribution_{ds.name}.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    logger.info("Saved %s", out)

    # 2. Amount histogram by class.
    fig, ax = plt.subplots(figsize=(7, 4))
    for cls, color, label in [(0, "#2E86AB", "Normal"), (1, "#E63946", "Fraud")]:
        amounts = df.loc[df[ds.target_col] == cls, "Amount"].clip(upper=1500)
        ax.hist(amounts, bins=50, alpha=0.55, label=label, color=color, density=True)
    ax.set_title(f"Transaction amount density by class -- {ds.name}")
    ax.set_xlabel("Amount (clipped at 1500)")
    ax.set_ylabel("density")
    ax.legend()
    fig.tight_layout()
    out = RESULTS / f"01_amount_histogram_{ds.name}.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    logger.info("Saved %s", out)

    # 3. Top-15 most class-discriminative features (mean shift) -- guides which dims
    #    to keep when we PCA down to 4-8 qubits for the quantum models.
    feat_means = df.groupby(ds.target_col)[ds.feature_cols].mean()
    mean_diff = (feat_means.loc[1] - feat_means.loc[0]).abs().sort_values(ascending=False)
    top15 = mean_diff.head(15)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(top15.index[::-1], top15.values[::-1], color="#6A4C93")
    ax.set_title(f"Top 15 features by |mean(fraud) - mean(normal)| -- {ds.name}")
    ax.set_xlabel("|mean shift| (z-score units)")
    fig.tight_layout()
    out = RESULTS / f"01_top_features_{ds.name}.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    logger.info("Saved %s", out)

    # 4. Correlation heatmap on a sample (full matrix is 30x30 but with 568K rows
    #    correlation is fine; we just plot it).
    sample = df.sample(min(50_000, len(df)), random_state=0)
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        sample[ds.feature_cols + [ds.target_col]].corr(),
        cmap="coolwarm",
        center=0,
        vmin=-1,
        vmax=1,
        ax=ax,
        cbar_kws={"shrink": 0.7},
    )
    ax.set_title(f"Feature correlation heatmap -- {ds.name}")
    fig.tight_layout()
    out = RESULTS / f"01_correlation_{ds.name}.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    logger.info("Saved %s", out)

    print(f"\n[done] EDA artifacts in {RESULTS.resolve()}")


if __name__ == "__main__":
    main()
