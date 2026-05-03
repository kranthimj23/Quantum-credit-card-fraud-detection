"""
Submit the trained VQC / QSVC inference circuits to a REAL IBM Quantum backend
via Qiskit IBM Runtime (SamplerV2 / EstimatorV2).

This script is meant to be run AFTER you've successfully demoed on the simulator
(scripts 04 + 05). It assumes:

    1. You have an IBM Quantum account at https://quantum.ibm.com
    2. You've set the env var `IBM_QUANTUM_TOKEN` (or saved credentials with
       `QiskitRuntimeService.save_account(...)`).
    3. You have access to a backend such as `ibm_brisbane`, `ibm_kyoto`, or any
       open-plan device with >= n_qubits available qubits.

What it does:
    - Loads the same preprocessed quantum test set as the simulator scripts.
    - Rebuilds the ZZFeatureMap + EfficientSU2 ansatz (you must pass the trained
      parameters via --weights-json from results/04_vqc_metrics.json or rerun
      training in this script with --train).
    - Transpiles the circuit for the chosen backend (ISA-aware for IBM Heron/Eagle).
    - Submits a small batch of test transactions (default 50) to the real device
      using SamplerV2.
    - Computes AUC-ROC on the device output and compares vs simulator.

Usage:
    # Set token (one-time)
    export IBM_QUANTUM_TOKEN="your_token_here"

    # Submit (the demo script -- limit to a small batch on real HW!)
    python src/06_ibm_runtime_real_hw.py --backend ibm_brisbane --batch 50

    # If you don't pass a backend it picks the least busy open-plan device:
    python src/06_ibm_runtime_real_hw.py --batch 30 --auto-backend

NOTE: Real HW queue times can be minutes to hours on the open plan. For senior-
mgmt demos schedule the queue submission BEFORE the meeting and use the cached
results during the live walkthrough.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import time
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--backend", default=None, help="IBM Quantum backend name (e.g. ibm_brisbane).")
    p.add_argument("--auto-backend", action="store_true", help="Auto-pick the least busy open-plan backend.")
    p.add_argument("--batch", type=int, default=50, help="Number of test rows to submit (default: 50)")
    p.add_argument("--shots", type=int, default=4096, help="Shots per circuit (default: 4096)")
    p.add_argument("--reps-fmap", type=int, default=2)
    p.add_argument("--reps-ansatz", type=int, default=3)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument(
        "--token-env",
        default="IBM_QUANTUM_TOKEN",
        help="Env var name holding the IBM Quantum API token (default: IBM_QUANTUM_TOKEN).",
    )
    p.add_argument(
        "--instance",
        default=None,
        help="IBM Quantum instance string, e.g. 'ibm-q/open/main'. Optional with newer accounts.",
    )
    p.add_argument(
        "--weights-npy",
        default=None,
        help="Path to a .npy of trained ansatz parameters. If omitted, uses random parameters "
        "(the run will produce a circuit but predictions will be untrained -- intended for "
        "validating the device pipeline, not a final demo).",
    )
    p.add_argument("--dry-run", action="store_true", help="Build & transpile but don't submit.")
    return p.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()

    # Lazy imports.
    from qiskit import QuantumCircuit, transpile
    from qiskit.circuit.library import EfficientSU2, ZZFeatureMap
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    # Load token.
    token = os.environ.get(args.token_env)
    if token is None:
        raise SystemExit(
            f"Set {args.token_env} env var with your IBM Quantum API token. "
            "Get one at https://quantum.ibm.com -> Account -> API token."
        )

    # Connect to runtime.
    service_kwargs = {"channel": "ibm_quantum", "token": token}
    if args.instance:
        service_kwargs["instance"] = args.instance
    service = QiskitRuntimeService(**service_kwargs)

    # Pick backend.
    if args.auto_backend or args.backend is None:
        backend = service.least_busy(operational=True, simulator=False)
        logger.info("Auto-selected backend: %s (queue=%d)", backend.name, backend.status().pending_jobs)
    else:
        backend = service.backend(args.backend)
        logger.info("Using backend: %s", backend.name)

    # Load test set.
    X_test = np.load(PROCESSED / "quantum_X_test.npy")
    y_test = np.load(PROCESSED / "quantum_y_test.npy")
    n_qubits = X_test.shape[1]
    if backend.num_qubits < n_qubits:
        raise SystemExit(f"Backend {backend.name} has only {backend.num_qubits} qubits; need >= {n_qubits}.")

    # Stratified subsample to the requested batch size.
    rng = np.random.default_rng(args.seed)
    idx_pos = np.where(y_test == 1)[0]
    idx_neg = np.where(y_test == 0)[0]
    n_pos = min(len(idx_pos), max(1, args.batch // 2))
    n_neg = args.batch - n_pos
    n_neg = min(n_neg, len(idx_neg))
    chosen = np.concatenate(
        [
            rng.choice(idx_pos, size=n_pos, replace=False),
            rng.choice(idx_neg, size=n_neg, replace=False),
        ]
    )
    rng.shuffle(chosen)
    X_batch = X_test[chosen]
    y_batch = y_test[chosen]
    logger.info("Submitting batch: %d rows (%d fraud, %d normal)", len(y_batch), int(y_batch.sum()), int((1 - y_batch).sum()))

    # Build the circuit (feature map -> trained ansatz -> measurements).
    fmap = ZZFeatureMap(feature_dimension=n_qubits, reps=args.reps_fmap, entanglement="linear")
    ansatz = EfficientSU2(num_qubits=n_qubits, reps=args.reps_ansatz, entanglement="linear")
    full_circuit = QuantumCircuit(n_qubits, n_qubits)
    full_circuit.compose(fmap, inplace=True)
    full_circuit.compose(ansatz, inplace=True)
    full_circuit.measure(range(n_qubits), range(n_qubits))

    # Bind ansatz weights.
    if args.weights_npy and Path(args.weights_npy).exists():
        weights = np.load(args.weights_npy)
        if len(weights) != ansatz.num_parameters:
            raise SystemExit(
                f"Weights file has {len(weights)} params but ansatz expects {ansatz.num_parameters}."
            )
        logger.info("Loaded trained weights from %s", args.weights_npy)
    else:
        logger.warning(
            "No --weights-npy supplied; using random weights. Use this run only to verify "
            "the device pipeline (transpilation + queue + result format). Re-run after copying "
            "trained ansatz params from the simulator."
        )
        weights = rng.uniform(-np.pi, np.pi, size=ansatz.num_parameters)

    # Build per-row bound circuits.
    fmap_params = list(fmap.parameters)
    ansatz_params = list(ansatz.parameters)
    bound_circuits = []
    for x in X_batch:
        bind = {}
        for p, val in zip(fmap_params, x):
            bind[p] = float(val)
        for p, val in zip(ansatz_params, weights):
            bind[p] = float(val)
        bound_circuits.append(full_circuit.assign_parameters(bind))

    # ISA-aware transpile for the target backend.
    logger.info("Transpiling %d circuits for backend %s ...", len(bound_circuits), backend.name)
    t0 = time.perf_counter()
    isa_circuits = transpile(bound_circuits, backend=backend, optimization_level=3, seed_transpiler=args.seed)
    logger.info("Transpiled in %.1f s. Sample depth=%d, gate count=%s",
                time.perf_counter() - t0, isa_circuits[0].depth(), dict(isa_circuits[0].count_ops()))

    if args.dry_run:
        logger.info("Dry run -- not submitting.")
        return

    # Submit.
    sampler = SamplerV2(mode=backend)
    sampler.options.default_shots = args.shots
    logger.info("Submitting job to %s (%d shots/circuit) ...", backend.name, args.shots)
    job = sampler.run(isa_circuits)
    logger.info("Job ID: %s -- waiting for result ...", job.job_id())
    result = job.result()
    logger.info("Job done.")

    # Decode: probability(class=1) = parity probability of measured bitstring.
    scores = []
    for pub_result in result:
        counts = pub_result.data.c.get_counts() if hasattr(pub_result.data, "c") else pub_result.data.meas.get_counts()
        total = sum(counts.values())
        # Use parity (sum of bits mod 2) as the binary classifier readout.
        odd = sum(c for bs, c in counts.items() if bin(int(bs.replace(" ", ""), 2)).count("1") % 2 == 1)
        scores.append(odd / max(1, total))
    scores = np.array(scores)

    # Metrics.
    from sklearn.metrics import average_precision_score, roc_auc_score

    metrics = {
        "model": "vqc_real_hw",
        "backend": backend.name,
        "shots": args.shots,
        "n_qubits": n_qubits,
        "n_test": int(len(y_batch)),
        "auc_roc": float(roc_auc_score(y_batch, scores)) if len(set(y_batch)) > 1 else None,
        "pr_auc": float(average_precision_score(y_batch, scores)) if len(set(y_batch)) > 1 else None,
        "weights_random": args.weights_npy is None,
        "transpiled_depth": int(isa_circuits[0].depth()),
        "gate_counts_first_circuit": dict(isa_circuits[0].count_ops()),
        "job_id": job.job_id(),
    }
    out = RESULTS / "06_ibm_runtime_metrics.json"
    out.write_text(json.dumps(metrics, indent=2))
    np.save(RESULTS / "06_ibm_runtime_test_scores.npy", scores)
    np.save(RESULTS / "06_ibm_runtime_test_labels.npy", y_batch)
    logger.info("Wrote %s", out)

    print("\n=== Real HW results ===")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
