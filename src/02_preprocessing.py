"""
Preprocessing pipeline for both classical and quantum tracks.

Steps:
1. Load dataset (auto-detects which Kaggle CSV is present).
2. Train/test split (stratified).
3. StandardScaler on features.
4. Class rebalancing:
     - If dataset is already balanced (2023): no rebalancing.
     - Else: SMOTE oversampling on the train set ONLY (never the test set).
5. PCA dimensionality reduction:
     - Classical track: keep all 29 features (V1..V28 + Amount).
     - Quantum track: reduce to `--n-qubits` features (default 6) so the circuit
       fits on NISQ simulators / hardware.
6. Save processed numpy arrays to data/processed/ for downstream scripts.

Usage:
    python src/02_preprocessing.py                  # default: 6 qubits, full classical features
    python src/02_preprocessing.py --n-qubits 4 --train-size 5000 --test-size 2000
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from data_loader import load

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prefer", default=None, help="Preferred dataset name (see data_loader.KNOWN_FILES)")
    p.add_argument("--n-qubits", type=int, default=6, help="Number of PCA components for quantum track (default: 6)")
    p.add_argument("--test-frac", type=float, default=0.2, help="Test split fraction (default: 0.2)")
    p.add_argument(
        "--train-size",
        type=int,
        default=2000,
        help="After rebalancing, cap the quantum train set to this many rows (default: 2000). "
        "Quantum kernels are O(N^2), so large N is impractical on simulators.",
    )
    p.add_argument(
        "--test-size",
        type=int,
        default=1000,
        help="Cap the test set used for the quantum track (default: 1000). The classical "
        "track always uses the full test set.",
    )
    p.add_argument("--seed", type=int, default=42)
    p.add_argument(
        "--rebalance",
        choices=["auto", "smote", "undersample", "none"],
        default="auto",
        help="Rebalancing strategy. 'auto' => SMOTE if imbalanced, else none.",
    )
    return p.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()
    rng = np.random.default_rng(args.seed)

    PROCESSED.mkdir(parents=True, exist_ok=True)

    # 1. Load.
    ds = load(prefer=args.prefer)
    logger.info("Loaded:\n%s", ds.summary())
    X = ds.features()
    y = ds.labels()

    # 2. Train/test split (stratified to preserve fraud rate).
    X_train_full, X_test_full, y_train_full, y_test_full = train_test_split(
        X, y, test_size=args.test_frac, random_state=args.seed, stratify=y
    )
    logger.info(
        "Initial split: train=%d (%d fraud), test=%d (%d fraud)",
        len(y_train_full),
        int(y_train_full.sum()),
        len(y_test_full),
        int(y_test_full.sum()),
    )

    # 3. Standard scale on train, transform test.
    scaler = StandardScaler()
    X_train_full = scaler.fit_transform(X_train_full)
    X_test_full = scaler.transform(X_test_full)

    # 4. Rebalance the TRAIN set only.
    rebalance = args.rebalance
    if rebalance == "auto":
        rebalance = "none" if ds.is_balanced else "smote"
    logger.info("Rebalancing strategy: %s", rebalance)

    if rebalance == "smote":
        sm = SMOTE(random_state=args.seed)
        X_train_bal, y_train_bal = sm.fit_resample(X_train_full, y_train_full)
    elif rebalance == "undersample":
        rus = RandomUnderSampler(random_state=args.seed)
        X_train_bal, y_train_bal = rus.fit_resample(X_train_full, y_train_full)
    else:
        X_train_bal, y_train_bal = X_train_full, y_train_full

    logger.info(
        "After rebalance: train=%d (fraud=%d, normal=%d)",
        len(y_train_bal),
        int((y_train_bal == 1).sum()),
        int((y_train_bal == 0).sum()),
    )

    # 5a. CLASSICAL TRACK -- keep all features, full train/test sets.
    np.save(PROCESSED / "classical_X_train.npy", X_train_bal)
    np.save(PROCESSED / "classical_y_train.npy", y_train_bal)
    np.save(PROCESSED / "classical_X_test.npy", X_test_full)
    np.save(PROCESSED / "classical_y_test.npy", y_test_full)
    logger.info(
        "Classical track saved: train=%d x %d, test=%d x %d",
        *X_train_bal.shape,
        *X_test_full.shape,
    )

    # 5b. QUANTUM TRACK -- PCA to n_qubits, then sub-sample.
    n_qubits = max(2, args.n_qubits)
    pca = PCA(n_components=n_qubits, random_state=args.seed)
    X_train_q = pca.fit_transform(X_train_bal)
    X_test_q = pca.transform(X_test_full)

    # Re-scale PCA outputs to roughly [-pi, pi] -- amplitude/angle encoding feature
    # maps assume bounded inputs.
    pca_scaler = StandardScaler()
    X_train_q = pca_scaler.fit_transform(X_train_q) * (np.pi / 3.0)
    X_test_q = pca_scaler.transform(X_test_q) * (np.pi / 3.0)
    X_train_q = np.clip(X_train_q, -np.pi, np.pi)
    X_test_q = np.clip(X_test_q, -np.pi, np.pi)

    # Sub-sample the train set (stratified) so quantum kernels finish in reasonable time.
    train_size = min(args.train_size, len(y_train_bal))
    if train_size < len(y_train_bal):
        # Stratified subsample.
        idx_pos = np.where(y_train_bal == 1)[0]
        idx_neg = np.where(y_train_bal == 0)[0]
        n_pos = min(len(idx_pos), train_size // 2)
        n_neg = train_size - n_pos
        n_neg = min(n_neg, len(idx_neg))
        chosen = np.concatenate(
            [
                rng.choice(idx_pos, size=n_pos, replace=False),
                rng.choice(idx_neg, size=n_neg, replace=False),
            ]
        )
        rng.shuffle(chosen)
        X_train_q = X_train_q[chosen]
        y_train_q = y_train_bal[chosen]
    else:
        y_train_q = y_train_bal

    test_size = min(args.test_size, len(y_test_full))
    if test_size < len(y_test_full):
        idx_pos = np.where(y_test_full == 1)[0]
        idx_neg = np.where(y_test_full == 0)[0]
        n_pos = min(len(idx_pos), max(1, test_size // 2))
        n_neg = test_size - n_pos
        n_neg = min(n_neg, len(idx_neg))
        chosen = np.concatenate(
            [
                rng.choice(idx_pos, size=n_pos, replace=False),
                rng.choice(idx_neg, size=n_neg, replace=False),
            ]
        )
        rng.shuffle(chosen)
        X_test_q = X_test_q[chosen]
        y_test_q = y_test_full[chosen]
    else:
        y_test_q = y_test_full

    np.save(PROCESSED / "quantum_X_train.npy", X_train_q)
    np.save(PROCESSED / "quantum_y_train.npy", y_train_q)
    np.save(PROCESSED / "quantum_X_test.npy", X_test_q)
    np.save(PROCESSED / "quantum_y_test.npy", y_test_q)

    logger.info(
        "Quantum track saved: train=%d x %d (%d fraud), test=%d x %d (%d fraud)",
        *X_train_q.shape,
        int((y_train_q == 1).sum()),
        *X_test_q.shape,
        int((y_test_q == 1).sum()),
    )

    # Save metadata for downstream scripts.
    meta = {
        "dataset_name": ds.name,
        "n_qubits": n_qubits,
        "rebalance": rebalance,
        "seed": args.seed,
        "pca_explained_variance": pca.explained_variance_ratio_.tolist(),
        "classical_train_shape": list(X_train_bal.shape),
        "classical_test_shape": list(X_test_full.shape),
        "quantum_train_shape": list(X_train_q.shape),
        "quantum_test_shape": list(X_test_q.shape),
    }
    import json

    (PROCESSED / "preprocessing_metadata.json").write_text(json.dumps(meta, indent=2))
    logger.info("PCA explained variance (%d comps): %s", n_qubits, [f"{v:.3f}" for v in pca.explained_variance_ratio_])
    logger.info("Total variance retained: %.3f", float(pca.explained_variance_ratio_.sum()))
    logger.info("Wrote metadata -> %s", PROCESSED / "preprocessing_metadata.json")
    print(f"\n[done] Processed arrays in {PROCESSED.resolve()}")


if __name__ == "__main__":
    main()
