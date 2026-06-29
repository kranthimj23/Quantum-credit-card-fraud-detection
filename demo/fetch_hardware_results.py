"""
Fetch Results from IBM Quantum Hardware
=========================================
Retrieves and processes results from a previously submitted hardware job.

Run this DURING YOUR DEMO to pull live results from the quantum computer.

Usage:
  python fetch_hardware_results.py

  # Or specify a job ID directly:
  python fetch_hardware_results.py --job-id JOB_ID_HERE
"""

import sys
import os
import json
import argparse
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from quantum_fraud_circuit import (
    expected_probability,
    estimate_amplitude_mle,
    TRUE_FRAUD_PROB,
    TRUE_THETA,
)


# ============================================================
# CONFIGURATION
# ============================================================
JOB_FILE = os.path.join(os.path.dirname(__file__), "results", "hardware_job.json")
RESULTS_FILE = os.path.join(os.path.dirname(__file__), "results", "hardware_results.json")


def fetch_results(job_id=None):
    """
    Fetch and process results from IBM Quantum hardware.

    Tries multiple methods to extract counts from the job result,
    handling API differences across qiskit-ibm-runtime versions.
    """
    from qiskit_ibm_runtime import QiskitRuntimeService

    # Load job info
    if job_id is None:
        if not os.path.exists(JOB_FILE):
            print("  ✗ No job file found. Run submit_to_hardware.py first.")
            print("    Or provide --job-id JOB_ID")
            sys.exit(1)

        with open(JOB_FILE, "r") as f:
            job_data = json.load(f)
        job_id = job_data["job_id"]
        grover_powers = job_data["grover_powers"]
        shots = job_data["shots"]
    else:
        # Default values if job file not available
        grover_powers = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        shots = 4000

    print(f"  Job ID: {job_id}")

    # Connect and fetch
    try:
        service = QiskitRuntimeService(channel="ibm_quantum_platform")
    except ValueError:
        service = QiskitRuntimeService(channel="ibm_quantum")
    job = service.job(job_id)

    status = job.status()
    print(f"  Status: {status}")

    if str(status) != "DONE":
        print(f"\n  ⚠ Job is not complete yet (status: {status})")
        print("    Please wait and try again.")
        sys.exit(1)

    print("  Fetching results...")
    result = job.result()

    # Process results for each circuit
    measurements = []

    for i, m in enumerate(grover_powers):
        # Try different methods to get counts (API varies by version)
        counts = None

        try:
            # Method 1: SamplerV2 result format
            pub_result = result[i]
            if hasattr(pub_result, "data"):
                # Try to get the classical register counts
                for attr_name in ["c", "meas", "cr"]:
                    if hasattr(pub_result.data, attr_name):
                        data_obj = getattr(pub_result.data, attr_name)
                        if hasattr(data_obj, "get_counts"):
                            counts = data_obj.get_counts()
                            break

                if counts is None:
                    # Try iterating over data attributes
                    for key in dir(pub_result.data):
                        if not key.startswith("_"):
                            data_obj = getattr(pub_result.data, key)
                            if hasattr(data_obj, "get_counts"):
                                counts = data_obj.get_counts()
                                break
        except (IndexError, AttributeError):
            pass

        if counts is None:
            try:
                # Method 2: Legacy format
                counts = result.get_counts(i)
            except (AttributeError, IndexError):
                pass

        if counts is None:
            try:
                # Method 3: Quasi-distributions
                quasi_dist = result.quasi_dists[i]
                total = shots
                counts = {}
                for bitstring, prob in quasi_dist.items():
                    counts[format(bitstring, "01")] = int(prob * total)
            except (AttributeError, IndexError):
                pass

        if counts is None:
            print(f"  ⚠ Could not extract counts for circuit m={m}")
            print(f"    Result type: {type(result)}")
            if hasattr(result, "__len__"):
                print(f"    Result length: {len(result)}")
            continue

        # Count ones and zeros
        ones_count = 0
        zeros_count = 0
        for bitstring, count in counts.items():
            # The measurement bit is the last character (or only character)
            bit = bitstring.strip()[-1] if len(bitstring.strip()) > 0 else "0"
            if bit == "1":
                ones_count += count
            else:
                zeros_count += count

        total = ones_count + zeros_count
        p_measured = ones_count / total if total > 0 else 0.0
        p_expected = expected_probability(m)

        measurements.append({
            "m": m,
            "ones": ones_count,
            "zeros": zeros_count,
            "total": total,
            "p_measured": round(p_measured, 6),
            "p_expected": round(p_expected, 6),
            "deviation": round(abs(p_measured - p_expected), 6),
            "raw_counts": counts,
        })

    if not measurements:
        print("  ✗ Could not extract any measurement results!")
        sys.exit(1)

    # MLE estimation
    mle_result = estimate_amplitude_mle(measurements)

    # Total oracle calls
    total_oracle_calls = sum(
        (2 * meas["m"] + 1) * meas["total"] for meas in measurements
    )

    hardware_results = {
        "method": "quantum_hardware",
        "job_id": job_id,
        "backend": job_data.get("backend", "unknown") if job_id is None or os.path.exists(JOB_FILE) else "unknown",
        "measurements": measurements,
        "mle_estimate": mle_result,
        "total_oracle_calls": total_oracle_calls,
    }

    return hardware_results


def plot_hardware_results(hw_results, save_dir=None):
    """Plot hardware measurement results vs expected values."""
    plt.style.use("dark_background")
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    measurements = hw_results["measurements"]
    m_vals = [r["m"] for r in measurements]
    p_meas = [r["p_measured"] for r in measurements]
    p_exp = [r["p_expected"] for r in measurements]

    # ---- Left: Oscillation comparison ----
    ax1 = axes[0]
    m_smooth = np.linspace(0, max(m_vals), 200)
    p_smooth = [expected_probability(m) for m in m_smooth]

    ax1.plot(m_smooth, p_smooth, "-", color="#66BB6A", linewidth=2,
             alpha=0.5, label="Theory")
    ax1.plot(m_vals, p_exp, "x", color="#66BB6A", markersize=10,
             markeredgewidth=2.5, label="Expected (exact)")
    ax1.plot(m_vals, p_meas, "o", color="#FF7043", markersize=12,
             markeredgecolor="white", markeredgewidth=1.5,
             label="IBM Quantum (measured)", zorder=10)

    # Draw error bars (deviation from expected)
    for m, pm, pe in zip(m_vals, p_meas, p_exp):
        ax1.plot([m, m], [pm, pe], "-", color="#FF7043", alpha=0.5, linewidth=1)

    ax1.axhline(y=TRUE_FRAUD_PROB, color="#FFD54F", linewidth=1.5,
                linestyle=":", alpha=0.7)
    ax1.set_xlabel("Grover Iterations (m)", fontsize=13, fontweight="bold")
    ax1.set_ylabel("P(ancilla = |1⟩)", fontsize=13, fontweight="bold")
    ax1.set_title("Real Quantum Hardware Results", fontsize=15, fontweight="bold")
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(-0.05, 1.15)
    ax1.set_xticks(m_vals)

    # ---- Right: Estimation result ----
    ax2 = axes[1]
    mle = hw_results["mle_estimate"]

    methods = ["True\nValue", "Quantum HW\n(raw MLE)"]
    values = [mle["amplitude_true"], mle["amplitude_hat"]]
    colors = ["#EF5350", "#FF7043"]

    bars = ax2.bar(methods, values, color=colors, width=0.4,
                   edgecolor="white", linewidth=1.5)

    for bar, val in zip(bars, values):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.003,
                 f"{val:.6f}", ha="center", va="bottom",
                 fontsize=14, fontweight="bold", color="white")

    err = mle["relative_error_pct"]
    ax2.set_title(f"Hardware Estimate (Error: {err:.1f}%)",
                  fontsize=15, fontweight="bold")
    ax2.set_ylabel("P(fraud)", fontsize=13, fontweight="bold")
    ax2.set_ylim(0, max(values) * 1.4)
    ax2.grid(True, alpha=0.2, axis="y")

    plt.tight_layout(pad=2.0)

    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, "hardware_results.png")
        plt.savefig(path, dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        print(f"  ✓ Saved: {path}")

    plt.show()


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch quantum fraud estimation results from IBM Quantum"
    )
    parser.add_argument("--job-id", type=str, help="IBM Quantum job ID")
    args = parser.parse_args()

    print("=" * 65)
    print("  FETCHING RESULTS FROM IBM QUANTUM HARDWARE")
    print("=" * 65)
    print()

    hw_results = fetch_results(job_id=args.job_id)

    # Display results
    print()
    print("─" * 65)
    print("  HARDWARE MEASUREMENT RESULTS")
    print("─" * 65)
    print(f"  {'m':>3s}  │  {'P(1) HW':>12s}  │  {'P(1) expected':>14s}  │  "
          f"{'Deviation':>10s}")
    print("  " + "─" * 50)
    for r in hw_results["measurements"]:
        print(f"  {r['m']:>3d}  │  {r['p_measured']:>12.6f}  │  "
              f"{r['p_expected']:>14.6f}  │  {r['deviation']:>10.6f}")

    mle = hw_results["mle_estimate"]
    print(f"\n  ┌──────────────────────────────────────────────────┐")
    print(f"  │  QUANTUM HARDWARE RESULT                         │")
    print(f"  │                                                   │")
    print(f"  │  Estimated P(fraud) = {mle['amplitude_hat']:.6f}             │")
    print(f"  │  True P(fraud)      = {TRUE_FRAUD_PROB:.6f}             │")
    print(f"  │  Relative Error     = {mle['relative_error_pct']:.2f}%               │")
    print(f"  │  Total Oracle Calls = {hw_results['total_oracle_calls']:,d}               │")
    print(f"  └──────────────────────────────────────────────────┘")

    # Save results
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        # Convert counts dicts for JSON serialization
        serializable = hw_results.copy()
        for m in serializable["measurements"]:
            if "raw_counts" in m:
                m["raw_counts"] = {str(k): v for k, v in m["raw_counts"].items()}
        json.dump(serializable, f, indent=2)
    print(f"\n  ✓ Results saved: {RESULTS_FILE}")

    # Generate plots
    print("\n  Generating plots...")
    plot_dir = os.path.join(os.path.dirname(__file__), "plots")
    plot_hardware_results(hw_results, save_dir=plot_dir)

    print("\n  ✓ Hardware results fetched and processed!")
    print("=" * 65)
