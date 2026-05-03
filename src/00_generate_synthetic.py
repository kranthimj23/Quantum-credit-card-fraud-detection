"""
Generate a synthetic credit-card-fraud CSV with the same schema as the Kaggle datasets.

This is a smoke-test fallback so the rest of the pipeline can run end-to-end without
requiring a Kaggle account. Output has 28 PCA-like features + Amount + Class with a
realistic class imbalance (~0.17% fraud, similar to the original ULB dataset).

Usage:
    python src/00_generate_synthetic.py [--rows N] [--fraud-rate 0.0017] [--output data/creditcard_synthetic.csv]
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "data" / "creditcard_synthetic.csv"


def generate(rows: int = 20_000, fraud_rate: float = 0.0017, seed: int = 42) -> pd.DataFrame:
    """
    Build a synthetic dataset whose two classes have *separable* mean shifts on a few
    features but heavy noise -- realistic for tabular fraud detection.
    """
    rng = np.random.default_rng(seed)

    n_fraud = max(1, int(round(rows * fraud_rate)))
    n_normal = rows - n_fraud

    # Normal class: 28 standardized PCA-like features ~ N(0, 1)
    X_normal = rng.standard_normal(size=(n_normal, 28))
    amount_normal = np.abs(rng.normal(loc=88.0, scale=250.0, size=n_normal))

    # Fraud class: shift several features to make the problem learnable but non-trivial.
    # We pick 6 features and add modest mean shifts; the rest stay at the same Gaussian.
    X_fraud = rng.standard_normal(size=(n_fraud, 28))
    shift_features = [0, 2, 4, 9, 13, 16]  # arbitrary, fixed
    shift_magnitudes = [+1.8, -1.5, +2.2, -1.7, +1.4, -2.0]
    for f, m in zip(shift_features, shift_magnitudes):
        X_fraud[:, f] += m
    # Fraud transactions tend to be larger / more skewed.
    amount_fraud = np.abs(rng.normal(loc=420.0, scale=900.0, size=n_fraud))

    X = np.vstack([X_normal, X_fraud])
    amount = np.concatenate([amount_normal, amount_fraud])
    y = np.concatenate([np.zeros(n_normal, dtype=int), np.ones(n_fraud, dtype=int)])

    # Shuffle rows so fraud isn't all at the bottom.
    perm = rng.permutation(len(y))
    X, amount, y = X[perm], amount[perm], y[perm]

    cols = [f"V{i}" for i in range(1, 29)]
    df = pd.DataFrame(X, columns=cols)
    df["Amount"] = amount
    df["Class"] = y
    return df


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=20_000, help="Total rows (default: 20000)")
    parser.add_argument(
        "--fraud-rate",
        type=float,
        default=0.0017,
        help="Fraction of fraud rows (default: 0.0017, matches original ULB dataset)",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output CSV path")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    df = generate(rows=args.rows, fraud_rate=args.fraud_rate, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    n_fraud = int(df["Class"].sum())
    logger.info(
        "Wrote %s rows (%s fraud, %.4f%%) -> %s",
        f"{len(df):,}",
        f"{n_fraud:,}",
        100 * n_fraud / len(df),
        args.output,
    )


if __name__ == "__main__":
    main()
