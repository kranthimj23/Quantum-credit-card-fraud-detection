"""
Classical Monte Carlo Baseline for Fraud Probability Estimation
================================================================
Demonstrates how classical random sampling estimates fraud probability.
Shows the O(1/ε²) convergence rate — the fundamental limitation that
quantum methods overcome.

Fraud Model (matches the 6-qubit quantum circuit):
  - 4 features: amount (2 bits), time (1 bit), channel (1 bit)
  - 16 possible transaction states (2⁴)
  - Fraud rule: amount=HIGH (11) AND channel=INTERNATIONAL (1)
  - True P(fraud) = 2/16 = 0.125

Usage:
  python classical_baseline.py
"""

import numpy as np
import matplotlib.pyplot as plt
import time
import json
import os

# ============================================================
# CONSTANTS
# ============================================================
TRUE_FRAUD_PROB = 2 / 16  # = 0.125 (2 fraud states out of 16)


def is_fraud(amount_b1, amount_b0, time_bit, channel_bit):
    """
    Check if a transaction is fraudulent.

    Fraud rule: amount == HIGH (both bits = 1) AND channel == INTERNATIONAL (1)
    Time-of-day does NOT matter — fraud happens day or night.

    This is the SAME rule encoded in the quantum oracle (MCX gate on q0, q1, q3).
    """
    return (amount_b1 == 1) and (amount_b0 == 1) and (channel_bit == 1)


def classical_monte_carlo(n_samples, seed=None):
    """
    Run classical Monte Carlo estimation of fraud probability.

    Randomly generates transactions from a uniform distribution over
    the 4-bit feature space, and counts the fraction that are fraudulent.

    This is exactly what a bank does when it collects transaction data
    and counts how many are fraud — just at a much smaller scale.

    Args:
        n_samples: Number of random transactions to generate
        seed: Random seed for reproducibility

    Returns:
        dict with estimated probability, errors, and timing
    """
    rng = np.random.RandomState(seed)
    start_time = time.time()

    # Generate random 4-bit transactions (uniform distribution)
    # Each row = [amount_bit1, amount_bit0, time, channel]
    transactions = rng.randint(0, 2, size=(n_samples, 4))

    # Count fraudulent transactions
    fraud_count = np.sum([
        is_fraud(t[0], t[1], t[2], t[3]) for t in transactions
    ])

    elapsed = time.time() - start_time

    p_estimate = fraud_count / n_samples
    abs_error = abs(p_estimate - TRUE_FRAUD_PROB)
    rel_error = (abs_error / TRUE_FRAUD_PROB) * 100  # percentage

    return {
        "n_samples": int(n_samples),
        "fraud_count": int(fraud_count),
        "p_estimate": round(p_estimate, 6),
        "abs_error": round(abs_error, 6),
        "rel_error_pct": round(rel_error, 2),
        "time_seconds": round(elapsed, 4),
    }


def run_convergence_study(sample_sizes, n_trials=100):
    """
    Run Monte Carlo at multiple sample sizes to study convergence.

    For each sample size, runs many independent trials to compute
    mean and standard deviation of the estimate.

    This demonstrates the O(1/ε²) scaling:
      To halve the error, you need 4× more samples.
    """
    results = []

    for N in sample_sizes:
        trial_estimates = []
        trial_errors = []

        for trial in range(n_trials):
            r = classical_monte_carlo(N, seed=trial * 10000 + N)
            trial_estimates.append(r["p_estimate"])
            trial_errors.append(r["abs_error"])

        # Theoretical standard deviation: √(P(1-P)/N)
        theoretical_std = np.sqrt(TRUE_FRAUD_PROB * (1 - TRUE_FRAUD_PROB) / N)

        results.append({
            "n_samples": int(N),
            "mean_estimate": round(float(np.mean(trial_estimates)), 6),
            "std_estimate": round(float(np.std(trial_estimates)), 6),
            "mean_abs_error": round(float(np.mean(trial_errors)), 6),
            "mean_rel_error_pct": round(float(np.mean(trial_errors) / TRUE_FRAUD_PROB * 100), 2),
            "theoretical_std": round(float(theoretical_std), 6),
            "n_trials": n_trials,
        })

    return results


def plot_convergence(results, save_dir=None):
    """
    Create publication-quality convergence plots.

    Two panels:
      Left:  Estimate ± std vs sample size (log scale)
      Right: Error vs sample size, with theoretical 1/√N curve
    """
    # Dark theme for professional look
    plt.style.use("dark_background")
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    n_vals = [r["n_samples"] for r in results]
    means = [r["mean_estimate"] for r in results]
    stds = [r["std_estimate"] for r in results]
    errors = [r["mean_abs_error"] for r in results]
    theo_stds = [r["theoretical_std"] for r in results]

    # ---- Left Panel: Estimate Convergence ----
    ax1 = axes[0]
    ax1.fill_between(
        n_vals,
        [m - 2 * s for m, s in zip(means, stds)],
        [m + 2 * s for m, s in zip(means, stds)],
        alpha=0.25, color="#4FC3F7", label="±2σ range"
    )
    ax1.plot(n_vals, means, "o-", color="#29B6F6", linewidth=2,
             markersize=8, label="MC estimate", zorder=5)
    ax1.axhline(y=TRUE_FRAUD_PROB, color="#EF5350", linewidth=2,
                linestyle="--", label=f"True P = {TRUE_FRAUD_PROB}")
    ax1.set_xscale("log")
    ax1.set_xlabel("Number of Samples (N)", fontsize=13, fontweight="bold")
    ax1.set_ylabel("Estimated P(fraud)", fontsize=13, fontweight="bold")
    ax1.set_title("Classical Monte Carlo Convergence", fontsize=15, fontweight="bold")
    ax1.legend(fontsize=11, loc="upper right")
    ax1.grid(True, alpha=0.3)

    # ---- Right Panel: Error Scaling ----
    ax2 = axes[1]
    ax2.loglog(n_vals, errors, "s-", color="#FF7043", linewidth=2,
               markersize=8, label="Measured error", zorder=5)
    ax2.loglog(n_vals, theo_stds, "--", color="#66BB6A", linewidth=2,
               label=r"Theoretical: $\sigma / \sqrt{N}$")

    # Add annotation showing the O(1/ε²) scaling
    ax2.annotate(
        "To halve the error →\nneed 4× more samples\n(the ε² penalty)",
        xy=(n_vals[3], errors[3]),
        xytext=(n_vals[3] * 5, errors[3] * 4),
        fontsize=11, color="#FFD54F",
        arrowprops=dict(arrowstyle="->", color="#FFD54F", lw=2),
        bbox=dict(boxstyle="round,pad=0.3", fc="#333333", ec="#FFD54F"),
    )

    ax2.set_xlabel("Number of Samples (N)", fontsize=13, fontweight="bold")
    ax2.set_ylabel("Absolute Error |P̂ - P|", fontsize=13, fontweight="bold")
    ax2.set_title("Error Scaling: O(1/√N) = O(1/ε²) samples needed",
                  fontsize=15, fontweight="bold")
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout(pad=2.0)

    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, "classical_convergence.png")
        plt.savefig(path, dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        print(f"  ✓ Saved: {path}")

    plt.show()


def plot_single_run_animation(n_total=2000, save_dir=None):
    """
    Create a step-by-step convergence animation (saved as static plot).

    Shows how the classical estimate bounces around and slowly settles,
    demonstrating the random walk nature of MC estimation.
    """
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(14, 6))

    rng = np.random.RandomState(42)
    running_estimates = []
    fraud_so_far = 0

    # Generate transactions one at a time
    for i in range(1, n_total + 1):
        t = rng.randint(0, 2, size=4)
        if is_fraud(*t):
            fraud_so_far += 1
        running_estimates.append(fraud_so_far / i)

    x = np.arange(1, n_total + 1)

    ax.plot(x, running_estimates, color="#4FC3F7", linewidth=0.8, alpha=0.8)
    ax.axhline(y=TRUE_FRAUD_PROB, color="#EF5350", linewidth=2,
               linestyle="--", label=f"True P = {TRUE_FRAUD_PROB}")

    # Mark key milestones
    milestones = [10, 50, 100, 500, 1000, 2000]
    for m in milestones:
        if m <= n_total:
            est = running_estimates[m - 1]
            err = abs(est - TRUE_FRAUD_PROB)
            ax.plot(m, est, "o", color="#FFD54F", markersize=8, zorder=10)
            ax.annotate(
                f"N={m}\nP̂={est:.3f}\nerr={err:.3f}",
                xy=(m, est),
                xytext=(m * 1.3, est + 0.03 * (1 if m % 2 == 0 else -1)),
                fontsize=8, color="#FFD54F",
                arrowprops=dict(arrowstyle="->", color="#FFD54F", lw=1),
            )

    ax.set_xlabel("Number of Transactions Sampled", fontsize=13, fontweight="bold")
    ax.set_ylabel("Running Estimate of P(fraud)", fontsize=13, fontweight="bold")
    ax.set_title("Classical Monte Carlo: A Random Walk Toward the Answer",
                 fontsize=15, fontweight="bold")
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-0.05, 0.4)

    plt.tight_layout()

    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, "classical_random_walk.png")
        plt.savefig(path, dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        print(f"  ✓ Saved: {path}")

    plt.show()


# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    print("=" * 65)
    print("  CLASSICAL MONTE CARLO — FRAUD PROBABILITY ESTIMATION")
    print("=" * 65)
    print()
    print(f"  Fraud Model:")
    print(f"    Features: amount (2 bits) × time (1 bit) × channel (1 bit)")
    print(f"    Total states: 16")
    print(f"    Fraud rule: amount=HIGH AND channel=INTERNATIONAL")
    print(f"    True P(fraud) = {TRUE_FRAUD_PROB} (2/16)")
    print()

    # --- Single runs at different sample sizes ---
    print("─" * 65)
    print("  SINGLE RUNS")
    print("─" * 65)
    sample_sizes = [100, 500, 1_000, 5_000, 10_000, 50_000, 100_000, 1_000_000]

    for N in sample_sizes:
        result = classical_monte_carlo(N, seed=42)
        print(f"  N = {N:>10,d}  │  P̂ = {result['p_estimate']:.6f}  │  "
              f"Error = {result['abs_error']:.6f}  │  "
              f"Rel Error = {result['rel_error_pct']:>6.2f}%  │  "
              f"Time = {result['time_seconds']:.4f}s")

    # --- Convergence study (multiple trials per sample size) ---
    print()
    print("─" * 65)
    print("  CONVERGENCE STUDY (100 trials per sample size)")
    print("─" * 65)

    study_sizes = [50, 100, 200, 500, 1_000, 2_000, 5_000, 10_000, 50_000, 100_000]
    conv_results = run_convergence_study(study_sizes, n_trials=100)

    print(f"  {'N':>10s}  │  {'Mean P̂':>10s}  │  {'Std':>10s}  │  "
          f"{'Mean Error':>10s}  │  {'Theo Std':>10s}  │  {'Rel Err %':>10s}")
    print("  " + "─" * 75)
    for r in conv_results:
        print(f"  {r['n_samples']:>10,d}  │  {r['mean_estimate']:>10.6f}  │  "
              f"{r['std_estimate']:>10.6f}  │  {r['mean_abs_error']:>10.6f}  │  "
              f"{r['theoretical_std']:>10.6f}  │  {r['mean_rel_error_pct']:>10.2f}%")

    # --- Save results ---
    output_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(output_dir, exist_ok=True)

    results_path = os.path.join(output_dir, "classical_results.json")
    with open(results_path, "w") as f:
        json.dump({
            "method": "classical_monte_carlo",
            "true_probability": TRUE_FRAUD_PROB,
            "convergence_study": conv_results,
        }, f, indent=2)
    print(f"\n  ✓ Results saved: {results_path}")

    # --- Generate plots ---
    print("\n  Generating plots...")
    plot_dir = os.path.join(os.path.dirname(__file__), "plots")
    plot_convergence(conv_results, save_dir=plot_dir)
    plot_single_run_animation(n_total=2000, save_dir=plot_dir)

    print("\n  ✓ Classical baseline complete!")
    print("=" * 65)
