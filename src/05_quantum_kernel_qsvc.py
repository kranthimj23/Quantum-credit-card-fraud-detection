"""
Quantum-Kernel SVM (QSVC) and Pegasos QSVC for credit-card fraud detection.

Idea: encode classical data x -> |phi(x)> via a feature map circuit U_phi(x), then
the inner product |<phi(x_i)|phi(x_j)>|^2 is a quantum kernel matrix that we feed
to a standard SVM. This is the most studied "near-term advantage" candidate -- the
Hilbert-space kernel can capture correlations that no efficient classical kernel
can compute (Liu, Arunachalam & Temme, 2021).

Models:
    1. QSVC -- exact dual SVM with the FidelityQuantumKernel. Best AUC, but
       O(N^2) kernel evals, so we use the sub-sampled quantum train/test set.
    2. PegasosQSVC -- stochastic gradient SVM that needs O(N) kernel evals per
       epoch -- much faster training, slightly lower AUC.

Both produce probability-like decision scores that we benchmark against the
classical baselines.

Usage:
    python src/05_quantum_kernel_qsvc.py [--reps 2] [--C 1.0]
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reps", type=int, default=2, help="Feature map repetitions (default: 2)")
    p.add_argument("--C", type=float, default=1.0, help="SVC regularization C (default: 1.0)")
    p.add_argument(
        "--feature-map",
        choices=["zz", "pauli", "z"],
        default="zz",
        help="Feature map circuit (default: zz). 'zz' = ZZFeatureMap (best for non-trivial entanglement).",
    )
    p.add_argument("--pegasos-iters", type=int, default=1000, help="Pegasos QSVC iterations (default: 1000)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument(
        "--skip-pegasos",
        action="store_true",
        help="Skip the Pegasos variant (run only full QSVC).",
    )
    return p.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()

    from qiskit.circuit.library import PauliFeatureMap, ZFeatureMap, ZZFeatureMap
    from qiskit_algorithms.utils import algorithm_globals
    from qiskit_machine_learning.algorithms import PegasosQSVC, QSVC
    from qiskit_machine_learning.kernels import FidelityQuantumKernel
    from sklearn.metrics import (
        average_precision_score,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )

    algorithm_globals.random_seed = args.seed
    np.random.seed(args.seed)

    RESULTS.mkdir(parents=True, exist_ok=True)

    X_train = np.load(PROCESSED / "quantum_X_train.npy")
    y_train = np.load(PROCESSED / "quantum_y_train.npy")
    X_test = np.load(PROCESSED / "quantum_X_test.npy")
    y_test = np.load(PROCESSED / "quantum_y_test.npy")

    n_qubits = X_train.shape[1]
    logger.info(
        "Loaded quantum arrays: train=%s (fraud=%d), test=%s (fraud=%d), n_qubits=%d",
        X_train.shape,
        int(y_train.sum()),
        X_test.shape,
        int(y_test.sum()),
        n_qubits,
    )

    if args.feature_map == "zz":
        fmap = ZZFeatureMap(feature_dimension=n_qubits, reps=args.reps, entanglement="linear")
    elif args.feature_map == "pauli":
        fmap = PauliFeatureMap(feature_dimension=n_qubits, reps=args.reps, paulis=["Z", "ZZ"])
    else:
        fmap = ZFeatureMap(feature_dimension=n_qubits, reps=args.reps)

    qkernel = FidelityQuantumKernel(feature_map=fmap)

    all_metrics: list[dict] = []

    # ===== 1. Full QSVC (kernel SVM) =====
    qsvc = QSVC(quantum_kernel=qkernel, C=args.C, probability=True, random_state=args.seed)
    logger.info("Training QSVC (full kernel matrix) ...")
    t0 = time.perf_counter()
    qsvc.fit(X_train, y_train)
    train_seconds = time.perf_counter() - t0
    logger.info("QSVC trained in %.1f s", train_seconds)

    t0 = time.perf_counter()
    y_proba = qsvc.predict_proba(X_test)[:, 1]
    latency_ms = 1000 * (time.perf_counter() - t0) / max(1, len(y_test))
    y_pred = (y_proba >= 0.5).astype(int)

    qsvc_metrics = {
        "model": "qsvc_simulator",
        "n_qubits": n_qubits,
        "feature_map": fmap.__class__.__name__ + f"(reps={args.reps})",
        "C": args.C,
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "auc_roc": float(roc_auc_score(y_test, y_proba)),
        "pr_auc": float(average_precision_score(y_test, y_proba)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "train_seconds": float(train_seconds),
        "latency_ms_per_pred": float(latency_ms),
    }
    all_metrics.append(qsvc_metrics)
    np.save(RESULTS / "05_qsvc_test_scores.npy", y_proba)
    np.save(RESULTS / "05_qsvc_test_labels.npy", y_test)
    logger.info(
        "[QSVC] AUC=%.4f PR-AUC=%.4f F1=%.4f train=%.1fs lat=%.3f ms/pred",
        qsvc_metrics["auc_roc"],
        qsvc_metrics["pr_auc"],
        qsvc_metrics["f1"],
        train_seconds,
        latency_ms,
    )

    # ===== 2. Pegasos QSVC (stochastic, faster) =====
    if not args.skip_pegasos:
        pegasos = PegasosQSVC(quantum_kernel=qkernel, C=args.C, num_steps=args.pegasos_iters, seed=args.seed)
        # PegasosQSVC expects labels in {-1, +1} but it handles {0, 1} too via its
        # internal mapping in qiskit-machine-learning >= 0.7.
        logger.info("Training PegasosQSVC (%d iters) ...", args.pegasos_iters)
        t0 = time.perf_counter()
        pegasos.fit(X_train, y_train)
        train_seconds = time.perf_counter() - t0
        logger.info("PegasosQSVC trained in %.1f s", train_seconds)

        t0 = time.perf_counter()
        # PegasosQSVC has decision_function; map to a pseudo-prob via sigmoid for plotting.
        decision = pegasos.decision_function(X_test)
        latency_ms = 1000 * (time.perf_counter() - t0) / max(1, len(y_test))
        # Sigmoid to put scores in [0, 1] for ROC plotting consistency.
        peg_score = 1.0 / (1.0 + np.exp(-decision))
        y_pred_p = (peg_score >= 0.5).astype(int)

        peg_metrics = {
            "model": "pegasos_qsvc_simulator",
            "n_qubits": n_qubits,
            "feature_map": fmap.__class__.__name__ + f"(reps={args.reps})",
            "C": args.C,
            "num_steps": args.pegasos_iters,
            "n_train": int(len(y_train)),
            "n_test": int(len(y_test)),
            "auc_roc": float(roc_auc_score(y_test, peg_score)),
            "pr_auc": float(average_precision_score(y_test, peg_score)),
            "f1": float(f1_score(y_test, y_pred_p, zero_division=0)),
            "precision": float(precision_score(y_test, y_pred_p, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred_p, zero_division=0)),
            "train_seconds": float(train_seconds),
            "latency_ms_per_pred": float(latency_ms),
        }
        all_metrics.append(peg_metrics)
        np.save(RESULTS / "05_pegasos_qsvc_test_scores.npy", peg_score)
        logger.info(
            "[PegasosQSVC] AUC=%.4f PR-AUC=%.4f F1=%.4f train=%.1fs lat=%.3f ms/pred",
            peg_metrics["auc_roc"],
            peg_metrics["pr_auc"],
            peg_metrics["f1"],
            train_seconds,
            latency_ms,
        )

    # Save aggregate JSON.
    out_json = RESULTS / "05_qsvc_metrics.json"
    out_json.write_text(json.dumps(all_metrics, indent=2))
    logger.info("Wrote %s", out_json)

    print("\n=== Quantum kernel results ===")
    print(json.dumps(all_metrics, indent=2))


if __name__ == "__main__":
    main()
