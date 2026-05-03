# Architecture deep-dive

This document expands on `README.md` with the actual quantum-circuit topology,
the math behind quantum kernels, and a recommended hybrid serving architecture
HDFC Bank can deploy alongside its existing fraud stack.

---

## 1. End-to-end data flow (full ASCII diagram)

```
+============================================================================+
|                         DATA INGEST + PREP                                  |
+============================================================================+

      Kaggle CSV (V1..V28, Amount, Class)
                  |
                  v
         +------------------+
         |  StandardScaler  |   mean=0, var=1 per feature
         +--------+---------+
                  |
                  v
         +------------------+   only when imbalanced (ULB original)
         |  SMOTE on TRAIN  |   synthesises minority-class samples
         +--------+---------+
                  |
            +-----+-----+
            |           |
            v           v
   CLASSICAL TRACK   QUANTUM TRACK
   (29 features)     |
                     v
              +------+------+      reduces V1..V28 + Amount  ->  k principal
              |   PCA(k)    |      components (k = n_qubits, default 6)
              +------+------+
                     |
                     v
              +-------------+      rescales components to [-pi, pi] so they
              | angle scale |      are valid rotation arguments for the
              +------+------+      ZZFeatureMap encoding gates
                     |
                     v
                .npy arrays
                (data/processed/)


+============================================================================+
|                         CLASSICAL TRACK                                     |
+============================================================================+

   +------------------+    +------------------+    +------------------+
   |   LogisticReg    |    |   RandomForest   |    |     XGBoost      |
   |  class_weight=   |    |  class_weight=   |    | scale_pos_weight |
   |    balanced      |    |    balanced      |    |  = N_neg / N_pos |
   +--------+---------+    +--------+---------+    +--------+---------+
            |                       |                       |
            +-----------+-----------+-----------+-----------+
                                    |
                                    v
                  ROC, PR, F1, recall@1%FPR, latency_us


+============================================================================+
|                         QUANTUM TRACK -- VQC                                |
+============================================================================+

   x \in R^k (k=6 PCA components)
                  |
                  v
       +-----------------------+
       |   ZZFeatureMap U_phi  |   data encoding (depth = reps_fmap = 2)
       |   reps=2, linear ent  |
       +----------+------------+
                  |
                  v
       +-----------------------+
       |  EfficientSU2 ansatz  |   trainable variational block
       |  reps=3, theta in     |   ~ (2*reps + 1) * k params -> 42 params
       |  R^{n_params}         |   for k=6, reps=3
       +----------+------------+
                  |
                  v
       +-----------------------+
       | Z-measurement (all q) |   sampler returns counts -> parity decoder
       +----------+------------+   gives prob(class=1)
                  |
                  v
              cross-entropy loss
                  |
                  v
       +-----------------------+
       |   SPSA / COBYLA opt   |   gradient-free, robust to shot noise
       +----------+------------+
                  |
                  v
              theta_optimal


+============================================================================+
|                     QUANTUM TRACK -- QSVC (kernel SVM)                      |
+============================================================================+

   x_i, x_j -> |phi(x_i)>, |phi(x_j)>          ZZFeatureMap encoding
       |
       v
   K_ij = | <phi(x_i) | phi(x_j)> |^2         FidelityQuantumKernel
       |                                       (compute_swap_test or
       v                                        inverse_circuit)
   N x N kernel matrix
       |
       v
   Standard SVC (libsvm under the hood)
       |
       v
   Decision scores -> AUC-ROC, PR-AUC


+============================================================================+
|                     REAL HARDWARE (IBM QUANTUM)                             |
+============================================================================+

      Trained theta + test row x
                  |
                  v
       +-----------------------+
       | full_circuit.assign_  |
       | parameters({x, theta})|
       +----------+------------+
                  |
                  v
       +-----------------------+   transpile(circuit, backend, opt_level=3)
       | ISA-aware transpile   |   maps logical -> physical qubits, inserts
       | for ibm_brisbane /    |   SWAPs to satisfy device coupling map
       | ibm_kyoto             |
       +----------+------------+
                  |
                  v
       +-----------------------+   QiskitRuntimeService.run(job)
       |   SamplerV2 submit    |
       |   shots = 4096        |
       +----------+------------+
                  |
                  v
              counts dict per row
                  |
                  v
              parity decoder
                  |
                  v
              probabilities -> AUC-ROC on real HW
```

---

## 2. The actual VQC circuit (ASCII)

For `n_qubits = 4`, `reps_fmap = 2`, `reps_ansatz = 2`, the full circuit looks
like (left to right):

```
            +---+ +---------+ +-----+ +-----+ +-----+ +---+ +---------+ +-----+   . . .
q_0: ----- | H |-| RZ(2x_0)|-| ZZ  |-|     |-|     |-| H |-| RZ(2x_0)|-|     |--
            +---+ +---------+ +-----+ +-----+ +-----+ +---+ +---------+ +-----+
                              | x_0,|
                              | x_1 |
            +---+ +---------+ +-----+ +-----+ +-----+ +---+ +---------+ +-----+   . . .
q_1: ----- | H |-| RZ(2x_1)|-| ZZ  |-| ZZ  |-|     |-| H |-| RZ(2x_1)|-| ZZ  |--
            +---+ +---------+ +-----+ +-----+ +-----+ +---+ +---------+ +-----+
                              ^      | x_1,|
                              |      | x_2 |
            +---+ +---------+ +-----+ +-----+ +-----+ +---+ +---------+ +-----+   . . .
q_2: ----- | H |-| RZ(2x_2)|-|     |-| ZZ  |-| ZZ  |-| H |-| RZ(2x_2)|-|     |--
            +---+ +---------+ +-----+ +-----+ +-----+ +---+ +---------+ +-----+
                                            ^| x_2,|
                                             | x_3 |
            +---+ +---------+ +-----+ +-----+ +-----+ +---+ +---------+ +-----+   . . .
q_3: ----- | H |-| RZ(2x_3)|-|     |-|     |-| ZZ  |-| H |-| RZ(2x_3)|-|     |--
            +---+ +---------+ +-----+ +-----+ +-----+ +---+ +---------+ +-----+

         |<------------ ZZFeatureMap rep 1 ------------>|<-- ZZFeatureMap rep 2 ...
         |                                              |
         |                       U_phi(x)                                       |
         |---------------------- ENCODES DATA ----------|---- (continued) ------|
                                                        v
        ... continues through reps_fmap repetitions, then EfficientSU2 ansatz:

            +-----------+ +-----------+ +-----+ +-----------+ +-----------+
q_0: ----- | RY(theta_0)|-| RZ(theta_4)|-| CX  |-| RY(theta_8)|-| RZ(theta_12)|--   . . .
            +-----------+ +-----------+ +-----+ +-----------+ +-----------+
                                          |
            +-----------+ +-----------+ +-----+ +-----------+ +-----------+
q_1: ----- | RY(theta_1)|-| RZ(theta_5)|-| CX  |-| RY(theta_9)|-| RZ(theta_13)|--   . . .
            +-----------+ +-----------+ +-----+ +-----------+ +-----------+
                                                  |
            +-----------+ +-----------+         +-----+ +-----------+ +-----------+
q_2: ----- | RY(theta_2)|-| RZ(theta_6)|-------| CX  |-| RY(theta_10)|-| RZ(theta_14)|--
            +-----------+ +-----------+         +-----+ +-----------+ +-----------+
                                                          |
            +-----------+ +-----------+                  +-----+ +-----------+ +-----------+
q_3: ----- | RY(theta_3)|-| RZ(theta_7)|------------------| CX  |-| RY(theta_11)|-| RZ(theta_15)|--
            +-----------+ +-----------+                  +-----+ +-----------+ +-----------+

         |<--------------------------- EfficientSU2 rep 1 ------------------------------>|
                                                        ...
                                                        v
                                                  +---------+
                                                  | measure |  ----> classical bits c_0..c_3
                                                  +---------+
```

Counts:

- **ZZFeatureMap** with `reps=2`, `entanglement="linear"` → 2 H-layers + 2 RZ-encoding-layers + 2 ZZ-entangler-layers. Number of *encoding parameters* = `n_qubits` (each x_i is reused in every rep).
- **EfficientSU2** with `reps=3`, `entanglement="linear"` → for `n_qubits=6` produces `(2*3+1)*6 = 42` trainable parameters.
- **Total circuit depth** (after compose): `~30` for the simulator, `~80-150` after ISA transpilation on a real Heron / Eagle device.

---

## 3. Why a quantum kernel can be hard to simulate classically

The QSVC computes a kernel matrix:

```
K(x_i, x_j) = | <phi(x_i) | phi(x_j)> |^2
            = | <0| U_phi^dagger(x_j) U_phi(x_i) |0> |^2
```

For `U_phi` = ZZFeatureMap (or PauliFeatureMap with high-order Z terms), the
state `|phi(x)>` lives in a Hilbert space of dimension `2^n_qubits`. As `n_qubits`
grows past ~50 there is no known efficient classical algorithm to compute
this inner product — that's the formal "exponential separation" Liu, Arunachalam
& Temme (2021) proved for *some* feature maps. For `n_qubits = 6`, classical
simulation is trivial; the value of the demo is showing that the **architecture
is the same** at any qubit count, so adding qubits is a parameter sweep, not a
rewrite.

```
Hilbert space dimension grows as 2^n:

  n=2  ->  4-dim  (trivial)
  n=4  -> 16-dim
  n=6  -> 64-dim     <-- our default
  n=8  -> 256-dim
  n=12 -> 4,096-dim
  n=20 -> 1,048,576-dim
  n=30 -> 1.07 billion-dim    <-- where simulators start to struggle
  n=50 -> 1.13 quadrillion-dim   <-- formally beyond classical
```

The quantum kernel can detect non-linear correlations between *all subsets* of
features simultaneously, where a classical RBF or polynomial kernel only sees
pairwise distances. That's the "expressivity edge" in plain English.

---

## 4. Recommended hybrid serving architecture for HDFC

```
                        +-----------------------------+
                        |   Online transaction event  |
                        |   (POS / online / mobile)   |
                        +--------------+--------------+
                                       |
                                       v
                  +---------------------------------------+
                  |   Tier 1 -- Classical fraud model     |
                  |   (XGBoost on full 30+ features)      |
                  |   Latency: < 50 ms                    |
                  |   Throughput: 50K txn/sec             |
                  |                                       |
                  |   Output: risk score in [0, 1]        |
                  +---------------------+-----------------+
                                        |
                       +----------------+----------------+
                       |                                 |
                       v                                 v
              risk < 0.95: APPROVE                risk >= 0.95: ESCALATE
              (99% of transactions)               (top 1% suspicious tail)
                                                          |
                                                          v
                                  +----------------------------------------+
                                  |  Tier 2 -- Quantum kernel re-scorer    |
                                  |  (QSVC on PCA-reduced 6-dim features)  |
                                  |  Runs on Qiskit Aer simulator OR       |
                                  |  IBM Runtime (depending on SLA)        |
                                  |  Latency: 50-500 ms (sim), seconds (HW)|
                                  +-------------------+--------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |   Combined risk =                     |
                                  |     0.7 * classical + 0.3 * quantum   |
                                  |   Threshold -> approve / reject /     |
                                  |   step-up auth                        |
                                  +---------------------------------------+
```

Why this topology works:

1. **Classical handles 99% of throughput** — quantum never touches the hot path
   for the vast majority of transactions, so end-user latency is unchanged.
2. **Quantum handles the rare-event tail** where classical models are weakest
   and where an extra few percentage points of recall translate directly into
   crore-scale fraud savings.
3. **Graceful degradation** — if IBM Quantum is unavailable, Tier 2 falls back
   to the simulator (Aer or PennyLane lightning), which on 6-12 qubits still
   captures most of the kernel's expressivity at sub-second latency.
4. **Future-ready** — when fault-tolerant devices arrive (~2030), simply swap
   the simulator for `ibm_torino`-class hardware and increase `n_qubits` from 6
   to 30+. No application logic changes.

---

## 5. References

- Havlíček et al., *Supervised learning with quantum-enhanced feature spaces.* Nature 567 (2019).
- Liu, Arunachalam & Temme, *A rigorous and robust quantum speed-up in supervised machine learning.* Nat. Physics 17 (2021).
- Schuld & Killoran, *Quantum Machine Learning in Feature Hilbert Spaces.* PRL 122 (2019).
- IBM, *Variational quantum eigensolver and VQC tutorials.* <https://learning.quantum.ibm.com>
