# Quantum Credit-Card Fraud Detection

> **Goal:** demonstrate, end-to-end, that a Variational Quantum Classifier (VQC) and a
> Quantum-Kernel SVM (QSVC) — running first on Qiskit Aer simulators and later on
> real IBM Quantum hardware — can match or exceed classical baselines (Logistic
> Regression, Random Forest, XGBoost, LightGBM) on **AUC-ROC** for credit-card fraud
> detection, using public Kaggle datasets with 30 features.

This repo is a senior-management-ready demo for HDFC Bank — pitched at MD / CEO /
CTO / Enterprise Architects / Engineering Heads — and is structured to walk through:

1. **What** quantum machine learning is doing under the hood.
2. **Why** today's hardware can give you better recall on rare events, not faster training.
3. **How** to operationalize it as a hybrid pipeline alongside the existing fraud stack.

---

## 1. High-level architecture

```
                 +---------------------------------------------------+
                 |          Public Kaggle credit-card datasets        |
                 |   - mlg-ulb/creditcardfraud  (284,807, 0.17% fraud)|
                 |   - nelgiriyewithana/...2023 (568,630, 50% fraud)  |
                 +-------------------------+-------------------------+
                                           |
                                           v
                 +---------------------------------------------------+
                 |   src/data_loader.py  (auto-detects which CSV)    |
                 +-------------------------+-------------------------+
                                           |
                                           v
                 +---------------------------------------------------+
                 |   src/02_preprocessing.py                         |
                 |   - StandardScaler                                |
                 |   - SMOTE / undersample (only if imbalanced)      |
                 |   - PCA -> n_qubits dims (default 6)              |
                 |   - Train/test split (stratified)                 |
                 +---------------+-------------------+---------------+
                                 |                   |
              CLASSICAL TRACK    |                   |    QUANTUM TRACK
              (full features)    |                   |    (PCA -> 6 features)
                                 |                   |
                                 v                   v
              +-----------------------+   +---------------------------------+
              | src/03_classical_     |   | src/04_quantum_vqc_simulator.py |
              | baseline.py           |   |  - ZZFeatureMap (encoding)      |
              |  - LogisticRegression |   |  - EfficientSU2 (ansatz)        |
              |  - RandomForest       |   |  - SPSA / COBYLA optimizer      |
              |  - XGBoost            |   |  - StatevectorSampler           |
              |  - LightGBM           |   |                                 |
              |                       |   | src/05_quantum_kernel_qsvc.py   |
              | Metric: AUC-ROC,      |   |  - FidelityQuantumKernel        |
              | PR-AUC, F1, recall@   |   |  - QSVC (full kernel SVM)       |
              | 1% FPR                |   |  - PegasosQSVC (stochastic)     |
              +-----------+-----------+   +---------------+-----------------+
                          |                               |
                          |                               v
                          |               +-----------------------------------+
                          |               | src/06_ibm_runtime_real_hw.py     |
                          |               |  - QiskitRuntimeService           |
                          |               |  - SamplerV2 on ibm_brisbane /    |
                          |               |    ibm_kyoto / least_busy backend |
                          |               |  - ISA-aware transpile (level=3)  |
                          |               +---------------+-------------------+
                          |                               |
                          v                               v
              +---------------------------------------------------------------+
              |               results/  (JSON metrics + PNG plots)            |
              +-------------------------------+-------------------------------+
                                              |
                                              v
              +---------------------------------------------------------------+
              | src/07_compare_dashboard.py  (Streamlit demo for MD/CEO/CTO)  |
              |  - side-by-side AUC-ROC, PR-AUC, F1                           |
              |  - latency, train time, qubit count                           |
              |  - "reality check" narrative panel                            |
              +---------------------------------------------------------------+
```

For deeper diagrams (the actual circuit topology, Hilbert-space kernel intuition,
hybrid serving architecture) see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 2. Repository layout

```
.
├── README.md                  <- this file
├── ARCHITECTURE.md            <- ASCII circuit diagrams + Hilbert-space kernel intuition
├── STEPS.md                   <- step-by-step explanation of each script
├── requirements.txt           <- pinned versions for reproducible runs
├── data/
│   ├── README.md              <- how to download Kaggle datasets
│   └── (creditcard.csv | creditcard_2023.csv | creditcard_synthetic.csv)
├── src/
│   ├── data_loader.py             <- auto-detecting CSV loader
│   ├── 00_generate_synthetic.py   <- synthetic fallback for CI / smoke tests
│   ├── 01_eda.py                  <- class imbalance + feature stats + PNG plots
│   ├── 02_preprocessing.py        <- scale / rebalance / PCA -> .npy arrays
│   ├── 03_classical_baseline.py   <- LogReg / RF / XGBoost / LightGBM
│   ├── 04_quantum_vqc_simulator.py    <- VQC on Aer simulator
│   ├── 05_quantum_kernel_qsvc.py      <- QSVC + PegasosQSVC
│   ├── 06_ibm_runtime_real_hw.py      <- real HW submission template
│   └── 07_compare_dashboard.py        <- Streamlit demo dashboard
├── docs/
│   └── slides_outline.md      <- talking points for MD / CEO / CTO
├── notebooks/                 <- (optional) Jupyter scratch space
└── results/                   <- generated metrics JSONs and PNG plots
```

---

## 3. Quick start (15 minutes on a laptop)

> **On Windows?** Follow the granular [`WINDOWS_SETUP.md`](WINDOWS_SETUP.md)
> guide instead — it covers Python install, PowerShell execution policy,
> Kaggle API token, and demo-day checklist. The two convenience scripts
> [`scripts/install_deps.ps1`](scripts/install_deps.ps1) and
> [`scripts/run_demo.ps1`](scripts/run_demo.ps1) do everything below in one
> command.

```bash
# 1. Clone & install
git clone https://github.com/kranthimj23/Quantum-credit-card-fraud-detection.git
cd Quantum-credit-card-fraud-detection
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Get data
#    (a) Either follow data/README.md to download a Kaggle CSV, OR
#    (b) Generate a deterministic synthetic dataset to smoke-test the pipeline:
python src/00_generate_synthetic.py --rows 10000 --fraud-rate 0.05

# 3. Run the full pipeline
python src/01_eda.py
python src/02_preprocessing.py --n-qubits 6 --train-size 600 --test-size 400
python src/03_classical_baseline.py
python src/04_quantum_vqc_simulator.py --optimizer spsa --maxiter 60
python src/05_quantum_kernel_qsvc.py --reps 2 --C 1.0

# 4. Open the dashboard
streamlit run src/07_compare_dashboard.py
```

That's it — you'll see classical vs VQC vs QSVC side-by-side, including ROC and
PR curves, and a "reality check" narrative panel ready for senior management.

> **Tip:** for the *actual* MD / CEO / CTO demo, run the pipeline on the
> **balanced 2023 dataset** first (faster convergence, cleaner story), and then
> on the **original ULB dataset** to show the imbalanced "rare event" reality.

---

## 4. Running on real IBM Quantum hardware

After you're happy with the simulator results:

```bash
export IBM_QUANTUM_TOKEN="your_token_from_quantum.ibm.com"

# Pick least-busy open-plan backend, submit 30 transactions
python src/06_ibm_runtime_real_hw.py --auto-backend --batch 30 --shots 4096
```

Real-HW jobs queue for minutes-to-hours on the open plan. Best practice for the
live demo: **submit the day before**, then read the cached `results/06_ibm_runtime_metrics.json`
and the `results/06_ibm_runtime_test_scores.npy` during the meeting.

See [docs/slides_outline.md](docs/slides_outline.md) for talking points and the
"reality check" you'll deliver alongside these numbers.

---

## 5. Reality check — what this demo proves and what it doesn't

| Dimension | Classical | Quantum (sim or HW today) | Winner today |
|---|---|---|---|
| Training speed (millions of rows) | seconds | impractical at >5K rows | **Classical** |
| Inference latency | µs | ms (sim), s (HW + queue) | **Classical** |
| Feature dimensionality | 100s-1000s | 4-16 (qubit-limited) | **Classical** |
| Hardware maturity | commodity CPU/GPU | NISQ, ~1e-3 gate error | **Classical** |
| Decision-boundary expressivity | bounded by chosen kernel | Hilbert-space kernels capture non-linear correlations classical can't compute efficiently | **Quantum (in principle)** |
| AUC-ROC on PCA-reduced features | strong | sometimes higher | **Tied / quantum edges** |

**Honest framing for the boardroom:**

> Quantum doesn't replace XGBoost today. It augments the existing pipeline as a
> hybrid second-opinion model on the top-1% suspicious tail, where rare-event
> recall matters most. The strategic value is **future-proofing** — by 2030,
> when fault-tolerant devices arrive, banks that have already integrated quantum
> kernels into their fraud stack will be 12-18 months ahead of competitors.

---

## 6. Citing / further reading

- Havlíček, V. et al. *Supervised learning with quantum-enhanced feature spaces.* Nature 567 (2019).
- Liu, Y., Arunachalam, S., Temme, K. *A rigorous and robust quantum speed-up in supervised machine learning.* Nature Physics 17 (2021).
- Schuld, M. & Killoran, N. *Quantum Machine Learning in Feature Hilbert Spaces.* PRL 122 (2019).
- Qiskit Machine Learning docs: <https://qiskit-community.github.io/qiskit-machine-learning>
- IBM Quantum Runtime docs: <https://docs.quantum.ibm.com>
