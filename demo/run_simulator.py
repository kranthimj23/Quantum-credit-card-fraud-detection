"""
Quantum Fraud Estimation — Local Simulator
============================================
Runs the quantum amplitude estimation circuit on Qiskit Aer simulator.
No IBM Quantum account needed — runs entirely on your machine.

This script:
  1. Builds circuits at Grover powers m = 0, 1, 2, ..., 8
  2. Runs each on the Aer simulator with 4,000 shots
  3. Collects measurement statistics
  4. Estimates P(fraud) using Maximum Likelihood Estimation
  5. Compares against the true value P = 0.125
  6. Generates comparison plots

Usage:
  python run_simulator.py
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import os
import time
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))
from quantum_fraud_circuit import (
    build_ae_circuit,
    expected_probability,
    estimate_amplitude_mle,
    TRUE_FRAUD_PROB,
    TRUE_THETA,
    TOTAL_QUBITS,
)

from qiskit import transpile
from qiskit_aer import AerSimulator


# ============================================================
# CONFIGURATION
# ============================================================
GROVER_POWERS = [0, 1, 2, 3, 4, 5, 6, 7, 8]  # m values to test
SHOTS_PER_CIRCUIT = 4000                        # measurements per circuit
N_TRIALS = 10                                   # independent trials for statistics


def run_single_grover_power(simulator, m, shots=SHOTS_PER_CIRCUIT):
    """
    Run amplitude estimation circuit at a single Grover power m.

    Args:
        simulator: Qiskit Aer simulator backend
        m: Number of Grover iterations
        shots: Number of measurement shots

    Returns:
        dict with measurement results
    """
    # Build circuit
    qc = build_ae_circuit(m)

    # Transpile for the simulator
    t_qc = transpile(qc, simulator)

    # Execute
    result = simulator.run(t_qc, shots=shots).result()
    counts = result.get_counts()

    # Extract probability of measuring |1⟩ on ancilla
    ones_count = counts.get("1", 0)
    zeros_count = counts.get("0", 0)
    total = ones_count + zeros_count

    p_measured = ones_count / total if total > 0 else 0.0
    p_expected = expected_probability(m)

    return {
        "m": m,
        "ones": ones_count,
        "zeros": zeros_count,
        "total": total,
        "p_measured": round(p_measured, 6),
        "p_expected": round(p_expected, 6),
        "deviation": round(abs(p_measured - p_expected), 6),
        "circuit_depth": qc.depth(),
    }


def run_full_estimation(simulator, grover_powers=GROVER_POWERS,
                        shots=SHOTS_PER_CIRCUIT):
    """
    Run amplitude estimation at multiple Grover powers and combine results.

    This is the core of the demo:
      1. Measure at each Grover power
      2. Use MLE to find the best-fit θ
      3. Compute estimated fraud probability

    Args:
        simulator: Qiskit Aer simulator backend
        grover_powers: List of Grover iteration counts to use
        shots: Shots per circuit

    Returns:
        dict with all results and the final amplitude estimate
    """
    start_time = time.time()

    # Run each Grover power
    measurements = []
    for m in grover_powers:
        result = run_single_grover_power(simulator, m, shots)
        measurements.append(result)

    # Estimate amplitude using MLE
    mle_result = estimate_amplitude_mle(measurements)

    # Calculate total oracle calls
    # For Grover power m: (2m + 1) queries to the oracle per shot
    # Plus shots for each power
    total_oracle_calls = sum((2 * m + 1) * shots for m in grover_powers)

    elapsed = time.time() - start_time

    return {
        "method": "quantum_simulator",
        "simulator": "qiskit_aer",
        "grover_powers": grover_powers,
        "shots_per_circuit": shots,
        "measurements": measurements,
        "mle_estimate": mle_result,
        "total_oracle_calls": total_oracle_calls,
        "total_circuits": len(grover_powers),
        "time_seconds": round(elapsed, 4),
    }


def run_multiple_trials(n_trials=N_TRIALS):
    """
    Run the full estimation multiple times to get error statistics.
    """
    simulator = AerSimulator()
    all_estimates = []

    print(f"\n  Running {n_trials} independent trials...")
    for trial in range(n_trials):
        result = run_full_estimation(simulator)
        estimate = result["mle_estimate"]["amplitude_hat"]
        all_estimates.append(estimate)
        print(f"    Trial {trial + 1:>2d}: P̂ = {estimate:.6f}  "
              f"(error = {abs(estimate - TRUE_FRAUD_PROB):.6f})")

    mean_est = np.mean(all_estimates)
    std_est = np.std(all_estimates)
    mean_err = np.mean([abs(e - TRUE_FRAUD_PROB) for e in all_estimates])

    return {
        "n_trials": n_trials,
        "estimates": [round(e, 6) for e in all_estimates],
        "mean_estimate": round(mean_est, 6),
        "std_estimate": round(std_est, 6),
        "mean_abs_error": round(mean_err, 6),
        "mean_rel_error_pct": round((mean_err / TRUE_FRAUD_PROB) * 100, 2),
    }


def plot_grover_oscillations(measurements, save_dir=None):
    """
    Plot measured vs expected probabilities at each Grover power.

    This is a key explanatory plot:
      Shows how the quantum state "oscillates" through different
      probabilities as Grover iterations increase.
    """
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(12, 7))

    m_vals = [r["m"] for r in measurements]
    p_meas = [r["p_measured"] for r in measurements]
    p_exp = [r["p_expected"] for r in measurements]

    # Smooth theoretical curve
    m_smooth = np.linspace(0, max(m_vals), 200)
    p_smooth = [expected_probability(m) for m in m_smooth]

    # Plot
    ax.plot(m_smooth, p_smooth, "-", color="#66BB6A", linewidth=2,
            alpha=0.6, label="Theory: sin²((2m+1)θ)")
    ax.plot(m_vals, p_meas, "o", color="#29B6F6", markersize=12,
            markeredgecolor="white", markeredgewidth=1.5,
            label="Simulator measurement", zorder=10)
    ax.plot(m_vals, p_exp, "x", color="#EF5350", markersize=10,
            markeredgewidth=2.5, label="Expected (exact)")

    # Reference line for true fraud probability
    ax.axhline(y=TRUE_FRAUD_PROB, color="#FFD54F", linewidth=1.5,
               linestyle=":", alpha=0.7, label=f"True P = {TRUE_FRAUD_PROB}")

    # Annotations
    ax.annotate(
        "m=0: Just state prep\nP = 0.125 (true value)",
        xy=(0, p_meas[0]),
        xytext=(0.8, p_meas[0] - 0.15),
        fontsize=10, color="#FFD54F",
        arrowprops=dict(arrowstyle="->", color="#FFD54F", lw=1.5),
    )
    ax.annotate(
        "m=2: Peak amplification\nP ≈ 0.94 (fraud signal boosted!)",
        xy=(2, p_meas[2]),
        xytext=(3.5, 1.05),
        fontsize=10, color="#FFD54F",
        arrowprops=dict(arrowstyle="->", color="#FFD54F", lw=1.5),
    )

    ax.set_xlabel("Grover Iterations (m)", fontsize=14, fontweight="bold")
    ax.set_ylabel("P(ancilla = |1⟩)", fontsize=14, fontweight="bold")
    ax.set_title("Quantum Amplitude Oscillation — Fraud Signal Amplification",
                 fontsize=16, fontweight="bold")
    ax.legend(fontsize=11, loc="center right")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-0.05, 1.15)
    ax.set_xticks(m_vals)

    plt.tight_layout()

    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, "grover_oscillations.png")
        plt.savefig(path, dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        print(f"  ✓ Saved: {path}")

    plt.show()


def plot_estimation_result(mle_result, save_dir=None):
    """
    Plot the amplitude estimation result as a clear visual comparison.
    """
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(8, 6))

    methods = ["True Value", "Quantum\nEstimate"]
    values = [mle_result["amplitude_true"], mle_result["amplitude_hat"]]
    colors = ["#EF5350", "#29B6F6"]

    bars = ax.bar(methods, values, color=colors, width=0.5,
                  edgecolor="white", linewidth=1.5)

    # Add value labels
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.003,
                f"{val:.6f}", ha="center", va="bottom",
                fontsize=14, fontweight="bold", color="white")

    # Add error annotation
    err = mle_result["relative_error_pct"]
    ax.text(0.5, max(values) * 0.6,
            f"Relative Error: {err:.2f}%",
            ha="center", fontsize=16, fontweight="bold",
            color="#FFD54F",
            transform=ax.transAxes)

    ax.set_ylabel("P(fraud)", fontsize=14, fontweight="bold")
    ax.set_title("Quantum Amplitude Estimation Result (Simulator)",
                 fontsize=15, fontweight="bold")
    ax.set_ylim(0, max(values) * 1.25)
    ax.grid(True, alpha=0.2, axis="y")

    plt.tight_layout()

    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, "quantum_estimate_result.png")
        plt.savefig(path, dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        print(f"  ✓ Saved: {path}")

    plt.show()


def save_circuit_diagram(save_dir=None):
    """Save the quantum circuit diagram as an image."""
    from quantum_fraud_circuit import build_visualization_circuit

    qc = build_visualization_circuit(1)

    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, "quantum_circuit_m1.png")
        try:
            fig = qc.draw(output="mpl", style="iqp", fold=60)
            fig.savefig(path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            print(f"  ✓ Saved circuit diagram: {path}")
        except Exception as e:
            # Fallback: save text diagram
            text_path = os.path.join(save_dir, "quantum_circuit_m1.txt")
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(str(qc.draw(output="text", fold=120)))
            print(f"  ✓ Saved text circuit: {text_path}")
            print(f"    (matplotlib circuit drawing failed: {e})")


# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    print("=" * 65)
    print("  QUANTUM AMPLITUDE ESTIMATION — AER SIMULATOR")
    print("=" * 65)
    print()

    simulator = AerSimulator()
    plot_dir = os.path.join(os.path.dirname(__file__), "plots")
    results_dir = os.path.join(os.path.dirname(__file__), "results")

    # --- Run single full estimation ---
    print("─" * 65)
    print("  SINGLE ESTIMATION RUN")
    print("─" * 65)

    result = run_full_estimation(simulator)

    print(f"\n  Grover Power Measurements:")
    print(f"  {'m':>3s}  │  {'P(1) measured':>14s}  │  {'P(1) expected':>14s}  │  "
          f"{'Deviation':>10s}  │  {'Depth':>6s}")
    print("  " + "─" * 60)
    for m_result in result["measurements"]:
        print(f"  {m_result['m']:>3d}  │  {m_result['p_measured']:>14.6f}  │  "
              f"{m_result['p_expected']:>14.6f}  │  "
              f"{m_result['deviation']:>10.6f}  │  {m_result['circuit_depth']:>6d}")

    print(f"\n  ┌──────────────────────────────────────────────┐")
    print(f"  │  MLE RESULT                                  │")
    print(f"  │  Estimated P(fraud) = {result['mle_estimate']['amplitude_hat']:.6f}             │")
    print(f"  │  True P(fraud)      = {TRUE_FRAUD_PROB:.6f}             │")
    print(f"  │  Relative Error     = {result['mle_estimate']['relative_error_pct']:.2f}%               │")
    print(f"  │  Total Oracle Calls = {result['total_oracle_calls']:,d}               │")
    print(f"  │  Time               = {result['time_seconds']:.4f}s               │")
    print(f"  └──────────────────────────────────────────────┘")

    # --- Multiple trials for statistics ---
    print()
    print("─" * 65)
    print("  STATISTICAL ANALYSIS (multiple trials)")
    print("─" * 65)

    trial_results = run_multiple_trials(n_trials=N_TRIALS)

    print(f"\n  Summary over {trial_results['n_trials']} trials:")
    print(f"    Mean estimate:     {trial_results['mean_estimate']:.6f}")
    print(f"    Std deviation:     {trial_results['std_estimate']:.6f}")
    print(f"    Mean abs error:    {trial_results['mean_abs_error']:.6f}")
    print(f"    Mean rel error:    {trial_results['mean_rel_error_pct']:.2f}%")

    # --- Save results ---
    os.makedirs(results_dir, exist_ok=True)
    results_path = os.path.join(results_dir, "simulator_results.json")
    with open(results_path, "w") as f:
        json.dump({
            "single_run": result,
            "statistical_analysis": trial_results,
        }, f, indent=2)
    print(f"\n  ✓ Results saved: {results_path}")

    # --- Generate plots ---
    print("\n  Generating plots...")
    plot_grover_oscillations(result["measurements"], save_dir=plot_dir)
    plot_estimation_result(result["mle_estimate"], save_dir=plot_dir)
    save_circuit_diagram(save_dir=plot_dir)

    print("\n  ✓ Simulator run complete!")
    print("=" * 65)
