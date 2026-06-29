"""
Quantum Fraud Detection Circuit Builder
========================================
Builds the 6-qubit quantum circuit for fraud probability estimation
using Amplitude Estimation (Grover-based).

Circuit Architecture:
  q0: amount bit 1  ─── H ─────●───────
  q1: amount bit 0  ─── H ─────●───────
  q2: time          ─── H ─────|───────
  q3: channel       ─── H ─────●───────
  q4: ancilla       ──────── MCX ───── ← measures fraud

Fraud Oracle:
  Flips ancilla q4 when: q0=1 AND q1=1 AND q3=1
  (amount=HIGH AND channel=INTERNATIONAL)

True fraud probability: P = 2/16 = 0.125
  θ = arcsin(√0.125) ≈ 0.3614 radians

After m Grover iterations:
  P(ancilla=1) = sin²((2m+1)θ)

Usage:
  from quantum_fraud_circuit import build_ae_circuit, estimate_amplitude
"""

import numpy as np
from qiskit import QuantumCircuit


# ============================================================
# CONSTANTS
# ============================================================
TRUE_FRAUD_PROB = 2 / 16  # = 0.125
TRUE_THETA = np.arcsin(np.sqrt(TRUE_FRAUD_PROB))  # ≈ 0.3614 rad
N_DATA_QUBITS = 4
ANCILLA_QUBIT = 4
TOTAL_QUBITS = 5


def build_state_preparation():
    """
    Build the state preparation operator A.

    A|0⟩ = (1/4) Σ_x |x⟩|f(x)⟩

    where f(x) = 1 for fraud states, 0 otherwise.

    After applying A:
      - The 4 data qubits are in uniform superposition over 16 states
      - The ancilla is |1⟩ for the 2 fraud states, |0⟩ for the 14 normal states
      - Amplitude of ancilla=1: √(2/16) = √(0.125) ≈ 0.354

    Returns:
        QuantumCircuit: The state preparation circuit (5 qubits, no measurements)
    """
    qc = QuantumCircuit(TOTAL_QUBITS, name="A")

    # Step 1: Uniform superposition on all data qubits
    # This creates: (1/4)(|0000⟩ + |0001⟩ + ... + |1111⟩) ⊗ |0⟩
    qc.h([0, 1, 2, 3])

    # Step 2: Fraud oracle — mark fraud states on ancilla
    # Fraud rule: q0=1 AND q1=1 AND q3=1 (amount=HIGH AND channel=INTL)
    # MCX (multi-controlled X) flips ancilla when all 3 controls are 1
    qc.mcx([0, 1, 3], ANCILLA_QUBIT)

    return qc


def build_grover_operator(state_prep):
    """
    Build one Grover operator Q for amplitude estimation.

    Q rotates the quantum state by angle 2θ in the
    {|good⟩, |bad⟩} subspace, where sin(θ) = √(P_fraud).

    Q = A · S₀ · A† · Sχ

    where:
      Sχ = phase flip of "good" states (ancilla = |1⟩)
      S₀ = phase flip of |0...0⟩ state
      A  = state preparation
      A† = inverse of state preparation

    Args:
        state_prep: The state preparation circuit A

    Returns:
        QuantumCircuit: One Grover iteration (5 qubits)
    """
    qc = QuantumCircuit(TOTAL_QUBITS, name="Q")

    # ---- Step 1: Sχ — Oracle phase flip ----
    # Flip the phase of states where ancilla = |1⟩
    # Z|0⟩ = |0⟩, Z|1⟩ = -|1⟩  →  flips phase of fraud states
    qc.z(ANCILLA_QUBIT)

    # ---- Step 2: A† — Inverse state preparation ----
    # Since H and MCX are both self-inverse:
    #   A  = MCX · H⊗4  (circuit order: H first, then MCX)
    #   A† = H⊗4 · MCX  (circuit order: MCX first, then H)
    qc.mcx([0, 1, 3], ANCILLA_QUBIT)   # MCX is self-inverse
    qc.h([0, 1, 2, 3])                  # H is self-inverse

    # ---- Step 3: S₀ — Zero-state reflection ----
    # Flips the phase of |00000⟩ only.
    # Implementation: X on all → multi-controlled Z → X on all
    #   X maps |0...0⟩ to |1...1⟩
    #   MCZ flips phase of |1...1⟩
    #   X maps back
    qc.x(range(TOTAL_QUBITS))
    # MCZ = H on target, MCX(controls→target), H on target
    qc.h(ANCILLA_QUBIT)
    qc.mcx([0, 1, 2, 3], ANCILLA_QUBIT)
    qc.h(ANCILLA_QUBIT)
    qc.x(range(TOTAL_QUBITS))

    # ---- Step 4: A — Reapply state preparation ----
    qc.h([0, 1, 2, 3])
    qc.mcx([0, 1, 3], ANCILLA_QUBIT)

    return qc


def build_ae_circuit(n_grover_iterations):
    """
    Build the complete amplitude estimation circuit.

    Applies the state preparation A, then m Grover iterations Q^m,
    then measures the ancilla qubit.

    After m iterations, P(ancilla=1) = sin²((2m+1)θ)
    where θ = arcsin(√P_fraud) ≈ 0.3614 rad

    Expected probabilities for each m:
      m=0: sin²(1·θ)  = 0.125  (just state prep, no amplification)
      m=1: sin²(3·θ)  = 0.781  (amplified!)
      m=2: sin²(5·θ)  = 0.944  (nearly certain)
      m=3: sin²(7·θ)  = 0.314  (oscillates back)
      m=4: sin²(9·θ)  = 0.012  (nearly zero)
      ...pattern continues oscillating

    The key insight: by measuring at MULTIPLE m values and fitting θ,
    we can determine P_fraud much more precisely than random sampling.

    Args:
        n_grover_iterations: Number of Grover iterations (m)

    Returns:
        QuantumCircuit: Complete circuit with measurement on ancilla
    """
    state_prep = build_state_preparation()
    grover_op = build_grover_operator(state_prep)

    # Build the full circuit
    qc = QuantumCircuit(TOTAL_QUBITS, 1, name=f"AE_m={n_grover_iterations}")

    # Apply state preparation A
    qc.compose(state_prep, inplace=True)

    # Apply Q^m (Grover operator m times)
    if n_grover_iterations > 0:
        qc.barrier(label=f"Q^{n_grover_iterations}")
        for i in range(n_grover_iterations):
            qc.compose(grover_op, inplace=True)
            if i < n_grover_iterations - 1:
                qc.barrier()

    # Measure the ancilla qubit
    qc.barrier(label="Measure")
    qc.measure(ANCILLA_QUBIT, 0)

    return qc


def build_visualization_circuit(n_grover_iterations):
    """
    Build a cleaner circuit for presentation visualization.

    Same logic as build_ae_circuit but with labels and barriers
    optimized for visual clarity.
    """
    qc = QuantumCircuit(TOTAL_QUBITS, 1)

    # Label the qubits for clarity
    # (Qiskit doesn't natively support qubit labels in all drawers,
    #  so we add them as comments)

    # ---- State Preparation ----
    qc.h([0, 1, 2, 3])
    qc.barrier(label="State Prep")
    qc.mcx([0, 1, 3], 4)
    qc.barrier(label="Oracle")

    # ---- Grover Iterations ----
    for i in range(n_grover_iterations):
        # Oracle reflection
        qc.z(4)
        # Inverse state prep
        qc.mcx([0, 1, 3], 4)
        qc.h([0, 1, 2, 3])
        # Zero-state reflection
        qc.x(range(5))
        qc.h(4)
        qc.mcx([0, 1, 2, 3], 4)
        qc.h(4)
        qc.x(range(5))
        # Re-apply state prep
        qc.h([0, 1, 2, 3])
        qc.mcx([0, 1, 3], 4)
        qc.barrier(label=f"Grover #{i + 1}")

    # Measure
    qc.measure(4, 0)

    return qc


def expected_probability(m, theta=TRUE_THETA):
    """
    Calculate the expected measurement probability after m Grover iterations.

    P(ancilla=1 | m iterations) = sin²((2m+1)·θ)

    Args:
        m: Number of Grover iterations
        theta: The angle (default: arcsin(√0.125) for our fraud problem)

    Returns:
        float: Expected probability of measuring |1⟩ on the ancilla
    """
    return np.sin((2 * m + 1) * theta) ** 2


def estimate_amplitude_mle(grover_measurements):
    """
    Maximum Likelihood Estimation of the fraud amplitude θ.

    Given measurement results at multiple Grover powers m,
    find θ that maximizes the likelihood of the observed data.

    Theoretical model: P(1|m) = sin²((2m+1)·θ)
    Observation: at power m, we saw k "ones" out of N total shots.

    Likelihood: L(θ) = Π_m  C(N,k) · p(m,θ)^k · (1-p(m,θ))^(N-k)
    We maximize log L(θ) = Σ_m  k·log(p) + (N-k)·log(1-p)

    Args:
        grover_measurements: list of dicts with keys:
            'm': Grover power
            'ones': count of |1⟩ outcomes
            'total': total shots

    Returns:
        dict with:
            'theta_hat': estimated angle
            'amplitude_hat': estimated fraud probability (sin²(θ))
            'relative_error_pct': relative error vs true value
    """
    from scipy.optimize import minimize_scalar

    def neg_log_likelihood(theta):
        nll = 0.0
        for meas in grover_measurements:
            m = meas["m"]
            k = meas["ones"]
            N = meas["total"]

            p = np.sin((2 * m + 1) * theta) ** 2
            # Clip to avoid log(0)
            p = np.clip(p, 1e-12, 1 - 1e-12)

            nll -= k * np.log(p) + (N - k) * np.log(1 - p)
        return nll

    # Search θ in (0, π/2)
    result = minimize_scalar(
        neg_log_likelihood,
        bounds=(0.001, np.pi / 2 - 0.001),
        method="bounded",
    )

    theta_hat = result.x
    amp_hat = np.sin(theta_hat) ** 2

    abs_err = abs(amp_hat - TRUE_FRAUD_PROB)
    rel_err = (abs_err / TRUE_FRAUD_PROB) * 100

    return {
        "theta_hat": round(theta_hat, 6),
        "theta_true": round(TRUE_THETA, 6),
        "amplitude_hat": round(amp_hat, 6),
        "amplitude_true": TRUE_FRAUD_PROB,
        "abs_error": round(abs_err, 6),
        "relative_error_pct": round(rel_err, 2),
    }


def get_circuit_stats(n_grover):
    """Get circuit statistics for a given number of Grover iterations."""
    qc = build_ae_circuit(n_grover)
    return {
        "n_grover": n_grover,
        "total_qubits": qc.num_qubits,
        "depth": qc.depth(),
        "gate_count": sum(qc.count_ops().values()),
        "ops_breakdown": dict(qc.count_ops()),
    }


# ============================================================
# MAIN — Demo of circuit building and theoretical predictions
# ============================================================
if __name__ == "__main__":
    print("=" * 65)
    print("  QUANTUM FRAUD CIRCUIT BUILDER")
    print("=" * 65)
    print()
    print(f"  True P(fraud) = {TRUE_FRAUD_PROB}")
    print(f"  True θ = {TRUE_THETA:.6f} rad ({np.degrees(TRUE_THETA):.2f}°)")
    print()

    # Show expected probabilities at each Grover power
    print("─" * 65)
    print("  EXPECTED MEASUREMENT PROBABILITIES (theory)")
    print("─" * 65)
    print(f"  {'m':>3s}  │  {'sin²((2m+1)θ)':>15s}  │  {'Interpretation':>30s}")
    print("  " + "─" * 55)
    for m in range(9):
        p = expected_probability(m)
        if m == 0:
            interp = "baseline (no amplification)"
        elif p > 0.9:
            interp = "strongly amplified"
        elif p > 0.5:
            interp = "moderately amplified"
        else:
            interp = "oscillated past peak"
        print(f"  {m:>3d}  │  {p:>15.6f}  │  {interp:>30s}")

    # Show circuit statistics
    print()
    print("─" * 65)
    print("  CIRCUIT STATISTICS")
    print("─" * 65)
    for m in [0, 1, 2, 4, 8]:
        stats = get_circuit_stats(m)
        print(f"  m={m}: depth={stats['depth']}, "
              f"gates={stats['gate_count']}, "
              f"qubits={stats['total_qubits']}")

    # Draw the circuit for m=1
    print()
    print("─" * 65)
    print("  CIRCUIT DIAGRAM (m=1, one Grover iteration)")
    print("─" * 65)
    qc = build_visualization_circuit(1)
    print(qc.draw(output="text", fold=120))

    print()
    print("  ✓ Circuit builder ready!")
    print("=" * 65)
