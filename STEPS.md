# Step-by-step execution guide

Every script in `src/` documented in the order you run them, with the
**why**, the **what** (params / output), and the **expected runtime** on a
modest laptop (Intel i7, 16 GB RAM, no GPU).

```
+---------------------+   +---------------------+   +---------------------+
| 00_generate_synth.. |   | data_loader.py      |   | 01_eda.py           |
+---------------------+   +---------------------+   +---------------------+
            |                       ^                          |
            |                       |                          v
            v                       |              +---------------------+
   data/creditcard_synthetic.csv    |              | results/01_*.png    |
                                    |              | (class dist, top    |
            (or)                    |              |  feats, corr map)   |
                                    |              +---------------------+
   data/creditcard.csv      <-------+
   data/creditcard_2023.csv <-------+
                                    |
                                    v
                      +---------------------+
                      | 02_preprocessing.py |
                      +---------------------+
                                    |
                                    v
                      data/processed/*.npy
                                    |
            +-----------+-----------+-----------+
            |                       |
            v                       v
   +-------------------+   +---------------------+
   | 03_classical_     |   | 04_quantum_vqc_     |
   |   baseline.py     |   |   simulator.py      |
   +-------------------+   +---------------------+
            |                       |
            |                       v
            |              +---------------------+
            |              | 05_quantum_kernel_  |
            |              |   qsvc.py           |
            |              +---------------------+
            |                       |
            |                       v
            |              +---------------------+
            |              | 06_ibm_runtime_     |
            |              |   real_hw.py (opt.) |
            |              +---------------------+
            |                       |
            +-----------+-----------+
                        |
                        v
              +---------------------+
              | 07_compare_         |
              | dashboard.py        |
              | (Streamlit demo)    |
              +---------------------+
```

---

## Step 0 -- (optional) generate synthetic data

**Script:** `src/00_generate_synthetic.py`

**Why:** lets you smoke-test the entire pipeline without a Kaggle account.
Writes a deterministic CSV with the same schema as the Kaggle datasets.

```bash
python src/00_generate_synthetic.py --rows 20000 --fraud-rate 0.0017
```

**Output:** `data/creditcard_synthetic.csv` (~3 MB)

**Runtime:** < 1 second.

**Skip if:** you've already downloaded a Kaggle dataset. The loader auto-detects
which CSV is present and prefers the real Kaggle ones.

---

## Step 1 -- Exploratory data analysis

**Script:** `src/01_eda.py`

**What it does:**

1. Auto-loads whichever CSV exists in `data/`.
2. Prints class distribution, schema, per-class amount stats.
3. Writes 4 PNGs to `results/`:
   - class distribution bar chart (log scale on imbalanced data)
   - amount histogram by class (clipped at 1500)
   - top-15 features by `|mean(fraud) - mean(normal)|` (guides which dims matter)
   - 30x30 correlation heatmap

**Why this matters for the demo:** the class-distribution plot is the *first
slide* you'll show senior management — "out of 568K transactions, only 0.17%
are fraud" is the entire reason fraud detection is hard.

```bash
python src/01_eda.py
```

**Runtime:** ~10 s on the 2023 dataset.

---

## Step 2 -- Preprocessing

**Script:** `src/02_preprocessing.py`

**Pipeline:**

```
raw_csv
   |
   v
[stratified train/test split]   80 / 20
   |
   v
[StandardScaler]                fit on train, transform test
   |
   v
[SMOTE on train ONLY]           skip if dataset is already balanced
   |
   +-----> classical_*.npy      keeps all 29 features
   |
   v
[PCA(n_qubits)]                 default 6 components
   |
   v
[rescale to [-pi, pi]]          for ZZFeatureMap angle encoding
   |
   v
[stratified subsample]          quantum kernel is O(N^2), cap train at 2K rows
   |
   v
quantum_*.npy
```

**Why we sub-sample for the quantum track:** computing the full
`FidelityQuantumKernel` matrix is O(N^2) circuit evaluations. For a 2,000-row
training set that's 4 million circuit runs — about 30-90 minutes on a laptop
simulator, hours on real hardware. Sub-sampling makes the demo finish in a
sensible time without losing the architectural story.

```bash
python src/02_preprocessing.py --n-qubits 6 --train-size 2000 --test-size 1000
```

**Output:**
- `data/processed/classical_X_train.npy`, `..._y_train.npy`, `..._X_test.npy`, `..._y_test.npy`
- `data/processed/quantum_*.npy` (PCA-reduced + sub-sampled)
- `data/processed/preprocessing_metadata.json` (PCA explained variance, dataset name, etc.)

**Runtime:** ~5 s on the 2023 dataset; ~30 s on the original ULB with SMOTE.

---

## Step 3 -- Classical baselines

**Script:** `src/03_classical_baseline.py`

**Models trained on the FULL preprocessed train set (no PCA reduction):**

| Model | Why it's the right baseline |
|---|---|
| LogisticRegression(class_weight=balanced) | Simplest interpretable model; banks know it; great sanity check. |
| RandomForest(class_weight=balanced) | Captures non-linear interactions cheaply; common production model. |
| XGBoost(scale_pos_weight=N_neg/N_pos) | Industry-standard gradient-boosting for fraud — what every fintech runs in prod. |
| LightGBM(class_weight=balanced) | Faster, similar quality; good GPU story. |

**Metrics computed:**
- AUC-ROC (primary)
- PR-AUC (Average Precision) — much more meaningful on imbalanced data
- F1, precision, recall (at 0.5 threshold)
- **Recall @ 1% FPR** — the operationally relevant fraud-detection metric
- Per-prediction latency (ms)

```bash
python src/03_classical_baseline.py
```

**Output:**
- `results/03_classical_metrics.json`
- `results/03_classical_roc.png`, `03_classical_pr.png`

**Runtime:** ~30 s on a laptop for the original ULB dataset; ~3-4 min on the
2023 dataset (more rows).

**Expected AUC-ROC** (rough, depends on seed):

| Model | ULB original (imbalanced) | 2023 balanced |
|---|---|---|
| LogReg | 0.97 | 0.96 |
| RandomForest | 0.95 | 0.99 |
| XGBoost | 0.98 | 0.999 |
| LightGBM | 0.98 | 0.999 |

---

## Step 4 -- Variational Quantum Classifier (VQC) on simulator

**Script:** `src/04_quantum_vqc_simulator.py`

**Architecture:**

```
x \in R^6  -->  ZZFeatureMap(reps=2)  -->  EfficientSU2(reps=3, 42 params)
                                                  ^
                                                  |
                                          theta optimized via SPSA / COBYLA
                                                  |
                                                  v
                                            measurement
                                                  |
                                                  v
                                         softmax via parity readout
                                                  |
                                                  v
                                         cross-entropy loss
```

**Hyper-parameters (defaults):**

| Param | Default | Notes |
|---|---|---|
| `--optimizer` | `spsa` | SPSA is the standard NISQ optimizer (gradient-free, robust to shot noise). Try `cobyla` for noiseless simulators. |
| `--maxiter` | `80` | 60-100 is a sweet spot for SPSA at 6 qubits. |
| `--reps-fmap` | `2` | More reps -> more entanglement but harder to train. |
| `--reps-ansatz` | `3` | More reps -> more expressivity but more parameters. |

```bash
python src/04_quantum_vqc_simulator.py --optimizer spsa --maxiter 80
```

**Output:**
- `results/04_vqc_metrics.json`
- `results/04_vqc_loss.png` (loss curve)
- `results/04_vqc_test_scores.npy` (for the dashboard ROC overlay)

**Runtime:** 3-10 min depending on `train_size` and `maxiter`.

**Expected AUC-ROC:** 0.92 - 0.97 on the 6-qubit PCA-reduced features (i.e. the
VQC, working with only 6 features, comes within 1-3 points of XGBoost which has
all 29 features). This is the headline number for the demo.

---

## Step 5 -- Quantum Kernel SVM (QSVC + PegasosQSVC)

**Script:** `src/05_quantum_kernel_qsvc.py`

**Two variants:**

1. **QSVC** — full SVM dual problem with FidelityQuantumKernel. Best AUC-ROC.
2. **PegasosQSVC** — stochastic gradient SVM with O(N) kernel evals per epoch
   instead of O(N^2). 10-100x faster training; small AUC drop.

```bash
python src/05_quantum_kernel_qsvc.py --reps 2 --C 1.0
```

**Output:**
- `results/05_qsvc_metrics.json`
- `results/05_qsvc_test_scores.npy`, `05_pegasos_qsvc_test_scores.npy`

**Runtime:** QSVC takes 5-20 min for 2K x 2K kernel matrix on a laptop.
PegasosQSVC takes 1-3 min.

**Why both:** QSVC shows the *upper bound* of quantum-kernel quality;
PegasosQSVC shows the *production-realistic* version that scales to bigger N.

---

## Step 6 -- Real IBM Quantum hardware (optional)

**Script:** `src/06_ibm_runtime_real_hw.py`

**Pre-requisites:**
- IBM Quantum account: <https://quantum.ibm.com>
- API token in `IBM_QUANTUM_TOKEN` env var.
- Open-plan access to a backend with >= 6 qubits (any IBM Heron / Eagle device).

**What it does:**
1. Connects to `QiskitRuntimeService`.
2. Picks a backend (auto-least-busy or user-specified).
3. Builds the same `ZZFeatureMap + EfficientSU2` circuit.
4. **ISA-aware transpilation** for the device coupling map (level 3).
5. Submits a small batch (default 30) of test transactions via `SamplerV2`.
6. Decodes counts via parity readout and computes AUC-ROC.

```bash
export IBM_QUANTUM_TOKEN=<your-token>
python src/06_ibm_runtime_real_hw.py --auto-backend --batch 30 --shots 4096
```

**Output:**
- `results/06_ibm_runtime_metrics.json` (includes `job_id`, `backend`, `transpiled_depth`)
- `results/06_ibm_runtime_test_scores.npy`

**Runtime:** queue + execution can be **15 min to 4 hours** on the open plan.
**Schedule the run before the demo and play back the cached results live.**

---

## Step 7 -- Streamlit dashboard for the demo

**Script:** `src/07_compare_dashboard.py`

**Panels:**

```
+---------------------------------------------------------------+
|  1. Side-by-side metrics table                                 |
|     model | AUC | PR-AUC | F1 | precision | recall | train_s   |
+---------------------------------------------------------------+
|  2. ROC + PR curves (interactive plotly)                       |
+---------------------------------------------------------------+
|  3. Reality check narrative                                    |
|     - what classical wins today (training speed, latency)      |
|     - what quantum wins (Hilbert-space expressivity)           |
|     - hybrid serving recommendation                            |
+---------------------------------------------------------------+
|  4. Pipeline metadata                                          |
|     dataset, n_qubits, PCA explained variance, rebalancing     |
+---------------------------------------------------------------+
```

```bash
streamlit run src/07_compare_dashboard.py
```

Opens at `http://localhost:8501`.

**Tip for the live demo:** open the dashboard *before* the meeting so it's
already rendered. During the talk, walk through the four panels in order — the
narrative builds naturally from "here's how rare fraud is" -> "here's our
classical baseline" -> "here's what quantum adds" -> "here's the operational
reality".

---

## Putting it all together (one-shot script)

For the standard demo run on the 2023 balanced dataset:

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Get data (one of):
#   kaggle datasets download -d nelgiriyewithana/credit-card-fraud-detection-dataset-2023 -p data/ --unzip
# OR
#   python src/00_generate_synthetic.py

# Pipeline
python src/01_eda.py
python src/02_preprocessing.py --n-qubits 6 --train-size 1500 --test-size 800
python src/03_classical_baseline.py
python src/04_quantum_vqc_simulator.py --optimizer spsa --maxiter 80
python src/05_quantum_kernel_qsvc.py --reps 2 --C 1.0

# (optional, ahead of demo)
python src/06_ibm_runtime_real_hw.py --auto-backend --batch 30

# Demo time
streamlit run src/07_compare_dashboard.py
```

**Total runtime end-to-end (simulator-only, default params):** ~30-45 min on a
laptop. Add 1-4 hrs of queue time if you include real HW.
