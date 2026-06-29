"""
Submit Quantum Fraud Estimation to IBM Quantum Hardware
========================================================
Submits the amplitude estimation circuits to a real IBM quantum processor.

IMPORTANT: Run this 2-3 HOURS before your demo.
           IBM Quantum free-tier jobs can take 10-120 minutes in queue.

Prerequisites:
  1. Create a free account at https://quantum.ibm.com
  2. Get your API token from Settings > API Token
  3. Run this script with your token (first time only saves credentials)

Usage:
  # First time — save credentials:
  python submit_to_hardware.py --token YOUR_API_TOKEN

  # Subsequent runs:
  python submit_to_hardware.py

  # Check job status:
  python submit_to_hardware.py --status
"""

import sys
import os
import json
import argparse
import time

sys.path.insert(0, os.path.dirname(__file__))
from quantum_fraud_circuit import build_ae_circuit, TOTAL_QUBITS


# ============================================================
# CONFIGURATION
# ============================================================
GROVER_POWERS = [0, 1, 2, 3, 4, 5, 6, 7, 8]  # Same as simulator
SHOTS = 4000                                     # Shots per circuit
JOB_FILE = os.path.join(os.path.dirname(__file__), "results", "hardware_job.json")


def save_credentials(token):
    """Save IBM Quantum credentials (one-time setup)."""
    # pyrefly: ignore [missing-import]
    from qiskit_ibm_runtime import QiskitRuntimeService

    print("  Saving IBM Quantum credentials...")
    try:
        QiskitRuntimeService.save_account(
            channel="ibm_quantum_platform",
            token=token,
            overwrite=True
        )
    except ValueError:
        # Fallback for older qiskit-ibm-runtime versions
        QiskitRuntimeService.save_account(
            channel="ibm_quantum",
            token=token,
            url="https://quantum.cloud.ibm.com",
            overwrite=True
        )
    print("  ✓ Credentials saved successfully!")
    print("    You won't need to provide the token again.")


def get_best_backend(service):
    """Find the least-busy backend with enough qubits."""
    print("  Finding least-busy backend with ≥ 6 qubits...")

    backends = service.backends(
        min_num_qubits=TOTAL_QUBITS,
        simulator=False,
    )

    if not backends:
        print("  ✗ No suitable backends found!")
        print("    Make sure your IBM Quantum account has access to hardware.")
        sys.exit(1)

    # Sort by queue length (least busy first)
    backend_info = []
    for b in backends:
        try:
            status = b.status()
            queue_len = status.pending_jobs if hasattr(status, "pending_jobs") else 999
            backend_info.append((b, queue_len))
        except Exception:
            backend_info.append((b, 999))

    backend_info.sort(key=lambda x: x[1])

    best = backend_info[0][0]
    queue = backend_info[0][1]

    print(f"  ✓ Selected: {best.name}")
    print(f"    Qubits: {best.num_qubits}")
    print(f"    Queue: ~{queue} pending jobs")

    return best


def submit_job():
    """Build circuits and submit to IBM Quantum hardware."""
    # pyrefly: ignore [missing-import]
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    from qiskit import transpile

    print("─" * 65)
    print("  CONNECTING TO IBM QUANTUM")
    print("─" * 65)

    try:
        service = QiskitRuntimeService(channel="ibm_quantum_platform")
    except ValueError:
        service = QiskitRuntimeService(channel="ibm_quantum")
    backend = get_best_backend(service)

    print()
    print("─" * 65)
    print("  BUILDING & TRANSPILING CIRCUITS")
    print("─" * 65)

    circuits = []
    circuit_info = []

    for m in GROVER_POWERS:
        qc = build_ae_circuit(m)
        circuits.append(qc)
        circuit_info.append({
            "grover_power": m,
            "original_depth": qc.depth(),
        })
        print(f"  Built circuit m={m}: depth={qc.depth()}")

    # Transpile all circuits for the hardware backend
    print(f"\n  Transpiling for {backend.name}...")
    transpiled = transpile(
        circuits,
        backend=backend,
        optimization_level=3,  # Maximum optimization
    )

    for i, (tc, info) in enumerate(zip(transpiled, circuit_info)):
        info["transpiled_depth"] = tc.depth()
        info["transpiled_gates"] = sum(tc.count_ops().values())
        print(f"  m={info['grover_power']}: "
              f"depth {info['original_depth']} → {info['transpiled_depth']} "
              f"({info['transpiled_gates']} gates)")

    # Submit the job
    print()
    print("─" * 65)
    print("  SUBMITTING TO HARDWARE")
    print("─" * 65)

    sampler = SamplerV2(backend)

    print(f"  Submitting {len(transpiled)} circuits × {SHOTS} shots...")
    print(f"  Backend: {backend.name}")

    # Submit all circuits as a single job
    # SamplerV2 expects a list of PUBs (primitive unified blocs)
    job = sampler.run(transpiled, shots=SHOTS)

    job_id = job.job_id()
    submit_time = time.strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n  ┌──────────────────────────────────────────────────┐")
    print(f"  │  ✓ JOB SUBMITTED SUCCESSFULLY!                   │")
    print(f"  │                                                   │")
    print(f"  │  Job ID:  {job_id:<38s}  │")
    print(f"  │  Backend: {backend.name:<38s}  │")
    print(f"  │  Time:    {submit_time:<38s}  │")
    print(f"  │                                                   │")
    print(f"  │  The job is now in queue.                         │")
    print(f"  │  Estimated wait: 10-120 minutes (free tier)       │")
    print(f"  │                                                   │")
    print(f"  │  To check status:                                 │")
    print(f"  │    python submit_to_hardware.py --status           │")
    print(f"  │                                                   │")
    print(f"  │  To fetch results (after completion):             │")
    print(f"  │    python fetch_hardware_results.py                │")
    print(f"  └──────────────────────────────────────────────────┘")

    # Save job info for later retrieval
    os.makedirs(os.path.dirname(JOB_FILE), exist_ok=True)
    job_data = {
        "job_id": job_id,
        "backend": backend.name,
        "submit_time": submit_time,
        "grover_powers": GROVER_POWERS,
        "shots": SHOTS,
        "circuit_info": circuit_info,
    }
    with open(JOB_FILE, "w") as f:
        json.dump(job_data, f, indent=2)
    print(f"\n  ✓ Job info saved: {JOB_FILE}")


def check_status():
    """Check the status of a previously submitted job."""
    # pyrefly: ignore [missing-import]
    from qiskit_ibm_runtime import QiskitRuntimeService

    if not os.path.exists(JOB_FILE):
        print("  ✗ No submitted job found. Run without --status first.")
        return

    with open(JOB_FILE, "r") as f:
        job_data = json.load(f)

    job_id = job_data["job_id"]
    print(f"  Job ID:  {job_id}")
    print(f"  Backend: {job_data['backend']}")
    print(f"  Submitted: {job_data['submit_time']}")

    try:
        service = QiskitRuntimeService(channel="ibm_quantum_platform")
    except ValueError:
        service = QiskitRuntimeService(channel="ibm_quantum")
    job = service.job(job_id)
    status = job.status()

    print(f"\n  Status: {status}")

    if str(status) == "DONE":
        print("\n  ✓ Job is COMPLETE! Run fetch_hardware_results.py to get results.")
    elif str(status) in ("QUEUED", "RUNNING"):
        print("\n  ⏳ Job is still running. Check back later.")
    else:
        print(f"\n  ⚠ Unexpected status: {status}")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Submit quantum fraud estimation to IBM Quantum hardware"
    )
    parser.add_argument("--token", type=str, help="IBM Quantum API token (first time setup)")
    parser.add_argument("--status", action="store_true", help="Check job status")
    args = parser.parse_args()

    print("=" * 65)
    print("  QUANTUM FRAUD ESTIMATION — IBM QUANTUM HARDWARE")
    print("=" * 65)
    print()

    if args.token:
        save_credentials(args.token)
        print()

    if args.status:
        check_status()
    else:
        submit_job()

    print()
    print("=" * 65)
