"""
Variational Quantum Classifier (VQC) for credit-card fraud, on a Qiskit Aer simulator.

Architecture:
    [PCA-reduced features in [-pi, pi]]
            |
            v
    +-----------------------+        ZZFeatureMap (depth=2)  -- data encoding
    | Feature map U_phi(x)  |        Hadamards + ZZ entanglers parameterized by x
    +-----------------------+
            |
            v
    +-----------------------+        EfficientSU2 (reps=3)   -- trainable ansatz
    | Variational ansatz    |        single-qubit RY/RZ + CNOT entanglers
    | U_theta               |        ~ (2*reps + 1) * n_qubits trainable params
    +-----------------------+
            |
            v
    +-----------------------+        Z-basis measurement on all qubits
    | Measure -> bitstring  |        parity decoder gives prob(class=1)
    +-----------------------+

Loss: cross-entropy. Optimizer: SPSA (default; robust on noisy simulators) or COBYLA.
We use Qiskit Aer with statevector for fast, exact gradient evaluation in simulation
(no shot noise) -- on real hardware swap to SamplerV2 with shots=4096.

Usage:
    python src/04_quantum_vqc_simulator.py [--optimizer spsa|cobyla] [--maxiter 100]
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--optimizer", choices=["spsa", "cobyla", "adam"], default="spsa")
    p.add_argument("--maxiter", type=int, default=80, help="Optimizer iterations (default: 80)")
    p.add_argument("--reps-fmap", type=int, default=2, help="Feature map repetitions (default: 2)")
    p.add_argument("--reps-ansatz", type=int, default=3, help="Ansatz repetitions (default: 3)")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()

    # Lazy import so the rest of the project still imports if Qiskit isn't installed.
    import warnings

    from qiskit.circuit.library import EfficientSU2, ZZFeatureMap

    # qiskit-machine-learning 0.7.2 currently uses the V1 primitive API. The V1
    # `Sampler` is deprecated in qiskit 1.2 but still functional and is the
    # simplest path until qiskit-machine-learning ships full V2 support.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from qiskit.primitives import Sampler  # V1 primitive

    from qiskit_algorithms.optimizers import ADAM, COBYLA, SPSA
    from qiskit_algorithms.utils import algorithm_globals
    from qiskit_machine_learning.algorithms import VQC
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

    # ===== Build the quantum classifier =====
    feature_map = ZZFeatureMap(feature_dimension=n_qubits, reps=args.reps_fmap, entanglement="linear")
    ansatz = EfficientSU2(num_qubits=n_qubits, reps=args.reps_ansatz, entanglement="linear")

    logger.info(
        "Circuit: feature_map=%d params (ZZFeatureMap reps=%d), ansatz=%d params (EfficientSU2 reps=%d), depth=%d",
        feature_map.num_parameters,
        args.reps_fmap,
        ansatz.num_parameters,
        args.reps_ansatz,
        feature_map.compose(ansatz).decompose().depth(),
    )

    # Optimizer.
    if args.optimizer == "spsa":
        optimizer = SPSA(maxiter=args.maxiter)
    elif args.optimizer == "cobyla":
        optimizer = COBYLA(maxiter=args.maxiter)
    else:
        optimizer = ADAM(maxiter=args.maxiter, lr=0.05)

    # V1 Sampler -- statevector-based, exact, fast on a laptop.
    sampler = Sampler()

    # Track loss curve.
    loss_history: list[float] = []

    def callback(weights: np.ndarray, loss: float) -> None:  # noqa: ARG001
        loss_history.append(float(loss))
        if len(loss_history) % 10 == 0:
            logger.info("iter %3d  loss=%.4f", len(loss_history), loss)

    vqc = VQC(
        sampler=sampler,
        feature_map=feature_map,
        ansatz=ansatz,
        optimizer=optimizer,
        callback=callback,
    )

    # ===== Train =====
    logger.info("Training VQC (%s, maxiter=%d) ...", args.optimizer, args.maxiter)
    t0 = time.perf_counter()
    vqc.fit(X_train, y_train)
    train_seconds = time.perf_counter() - t0
    logger.info("VQC trained in %.1f s", train_seconds)

    # ===== Evaluate =====
    # qiskit-machine-learning 0.7.x VQC has no predict_proba; we go through the
    # underlying neural network forward pass to get class probabilities.
    t0 = time.perf_counter()
    probs = vqc.neural_network.forward(X_test, vqc.weights)
    latency_ms = 1000 * (time.perf_counter() - t0) / max(1, len(y_test))
    # probs shape is (N, num_classes) for SamplerQNN with binary parity readout.
    if probs.ndim == 1:
        # Some versions return shape (N,) -- treat as P(class=1).
        y_score = probs
    else:
        y_score = probs[:, 1]
    y_pred = (y_score >= 0.5).astype(int)

    metrics = {
        "model": "vqc_simulator",
        "n_qubits": n_qubits,
        "feature_map": f"ZZFeatureMap(reps={args.reps_fmap})",
        "ansatz": f"EfficientSU2(reps={args.reps_ansatz})",
        "optimizer": args.optimizer,
        "maxiter": args.maxiter,
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "auc_roc": float(roc_auc_score(y_test, y_score)),
        "pr_auc": float(average_precision_score(y_test, y_score)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "train_seconds": float(train_seconds),
        "latency_ms_per_pred": float(latency_ms),
        "final_loss": float(loss_history[-1]) if loss_history else None,
        "n_trainable_params": int(ansatz.num_parameters),
    }

    out_json = RESULTS / "04_vqc_metrics.json"
    out_json.write_text(json.dumps(metrics, indent=2))
    logger.info("Wrote %s", out_json)

    # Loss curve.
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(loss_history, color="#6A4C93")
    ax.set_xlabel("iteration")
    ax.set_ylabel("loss")
    ax.set_title(f"VQC training loss ({args.optimizer.upper()}, {args.maxiter} iters)")
    fig.tight_layout()
    out = RESULTS / "04_vqc_loss.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)

    # Save raw scores so 07_compare_dashboard can plot ROC alongside classical models.
    np.save(RESULTS / "04_vqc_test_scores.npy", y_score)
    np.save(RESULTS / "04_vqc_test_labels.npy", y_test)
    # Save trained ansatz weights so 06_ibm_runtime_real_hw can load them via --weights-npy.
    np.save(RESULTS / "04_vqc_weights.npy", np.asarray(vqc.weights, dtype=np.float64))

    print("\n=== VQC simulator results ===")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
