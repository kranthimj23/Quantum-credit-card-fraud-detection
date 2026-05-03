# Windows setup — granular step-by-step demo guide

This document walks you through running the full **Quantum Credit-Card Fraud
Detection demo** on a Windows 10 / 11 laptop, from a clean machine to the
live Streamlit dashboard you'll show to MD / CEO / CTO.

> **Audience:** an SVP / engineering head who is comfortable with PowerShell
> but has never installed Python or Qiskit before.
>
> **Total time investment:**
> - First-time setup: ~30-45 min (Python install + dependencies + Kaggle download).
> - Each subsequent run: ~10-15 min (with `--prefer kaggle_2023_balanced --maxiter 60`).
> - Live demo: 10 min walkthrough + Q&A.

---

## TL;DR — the 5 commands you actually run on demo day

After first-time setup is complete:

```powershell
# 1. Open PowerShell, go to the repo
cd C:\Users\<you>\Quantum-credit-card-fraud-detection

# 2. Activate the virtual env
.\.venv\Scripts\Activate.ps1

# 3. Run the full pipeline (about 10-15 min)
.\scripts\run_demo.ps1

# 4. Launch the Streamlit dashboard
streamlit run src\07_compare_dashboard.py

# 5. (browser opens at http://localhost:8501 — that's your demo screen)
```

The rest of this document is the **first-time setup** that gets you to step 1.

---

## Section 1 — Pre-flight checks (5 min)

Before installing anything, verify your machine:

| Requirement | Minimum | How to check |
|---|---|---|
| Windows version | 10 (build 1903+) or 11 | `winver` in Start menu |
| RAM | 8 GB (16 GB recommended for VQC) | Task Manager → Performance |
| Free disk space | 5 GB | `Get-PSDrive C` in PowerShell |
| Admin rights | Required to install Python | Right-click PowerShell → "Run as administrator" |
| Internet | Required for downloads | — |
| Antivirus exclusion | Add `.venv` and `data` folders to exclusions to avoid 10x slowdown | Windows Security → Virus & threat protection → Manage settings → Exclusions |

> **Corporate laptop note:** If you're on a locked-down HDFC corporate device, you may need IT to (a) allow PowerShell script execution, (b) whitelist `pypi.org` and `pythonhosted.org`, and (c) add the project folder to antivirus exclusions. Get this approved BEFORE the day of the demo.

---

## Section 2 — Install Python 3.12 (5-10 min)

We pin to **Python 3.12.x** because that's what we tested all the Qiskit pins against.

1. Go to <https://www.python.org/downloads/windows/>.
2. Download **"Windows installer (64-bit)" for Python 3.12.x** (latest 3.12.* — at time of writing, 3.12.7).
3. Run the installer. **Critical:** on the first screen, tick **"Add python.exe to PATH"** (bottom checkbox). Then click **"Install Now"**.
4. After install completes, close any open PowerShell windows and open a fresh one.
5. Verify:

```powershell
python --version
# Expected: Python 3.12.x

pip --version
# Expected: pip 24.x or higher
```

> **If `python` is not found:** the PATH checkbox was missed. Re-run the installer → "Modify" → tick "Add to PATH" → "Install".

---

## Section 3 — Install Git for Windows (3-5 min)

You need Git to clone the repo (and to use Git Bash if PowerShell gives you trouble).

1. Go to <https://git-scm.com/download/win>.
2. Download the 64-bit installer.
3. Run installer with **all defaults** — just keep clicking "Next". The defaults install Git Bash and put `git` on PATH.
4. Verify:

```powershell
git --version
# Expected: git version 2.4x.x
```

---

## Section 4 — Allow PowerShell scripts to run (1 min)

Windows blocks PowerShell scripts by default. Run this **once** as admin to allow signed-or-local scripts:

1. Right-click **PowerShell** in the Start menu → **"Run as administrator"**.
2. Run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
# Press Y when prompted
```

3. Close the admin PowerShell window. From here on, use a **regular** (non-admin) PowerShell window.

> **Don't want to change the policy?** Use Git Bash instead — it ships with Git for Windows and runs `.sh` scripts unrestricted. Every command in this guide also works in Git Bash; just replace `.\.venv\Scripts\Activate.ps1` with `source .venv/Scripts/activate`.

---

## Section 5 — Clone the repo (1 min)

Pick a folder with a short path (avoid `OneDrive` and `Documents` — long paths can break some Windows tools).

```powershell
cd C:\Users\<your-username>
git clone https://github.com/kranthimj23/Quantum-credit-card-fraud-detection.git
cd Quantum-credit-card-fraud-detection
```

Verify:

```powershell
ls
# Expected to see: README.md, ARCHITECTURE.md, src, requirements.txt, etc.
```

---

## Section 6 — Create and activate the virtual environment (2 min)

A virtual environment isolates the project's Python packages from your system.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

After activation, your prompt will show `(.venv)` at the start:

```
(.venv) PS C:\Users\you\Quantum-credit-card-fraud-detection>
```

> **Always activate the venv BEFORE running any python or pip command.** Every PowerShell window starts fresh — re-activate each time you open a new one.

Upgrade pip (avoids old-pip warnings):

```powershell
python -m pip install --upgrade pip
```

---

## Section 7 — Install dependencies (10-15 min on first run)

This installs Qiskit, scikit-learn, XGBoost, LightGBM, Streamlit, and ~60 transitive dependencies. About 700 MB of downloads.

```powershell
pip install -r requirements.txt
```

You'll see a long stream of "Collecting..." and "Installing..." messages. **Be patient** — `qiskit-aer` and `qiskit-machine-learning` are the slowest because they include compiled extensions.

When it finishes, verify all the key libraries import:

```powershell
python -c "import qiskit, qiskit_aer, qiskit_machine_learning, qiskit_ibm_runtime, sklearn, xgboost, lightgbm, streamlit; print('all OK')"
# Expected: all OK
```

> **If `pip install` fails on `qiskit-aer` with a "Microsoft Visual C++ 14.0 or greater is required" error:**
> Install **Microsoft C++ Build Tools** from <https://visualstudio.microsoft.com/visual-cpp-build-tools/> → run installer → tick **"Desktop development with C++"** → install. Then re-run `pip install -r requirements.txt`.

---

## Section 8 — Get the data (10-15 min)

You have **three** options; pick the one that fits your situation.

### Option A: Quickest — synthetic fallback (no Kaggle needed)

Good for verifying the pipeline works before you invest time in Kaggle setup.

```powershell
python src\00_generate_synthetic.py --rows 20000 --fraud-rate 0.0017
```

This writes `data\creditcard_synthetic.csv`. Pipeline will use it automatically if no real Kaggle data is present. **Use this for the first dry-run.**

### Option B: Real Kaggle data via Kaggle CLI (recommended for the actual demo)

1. Sign in at <https://www.kaggle.com> (create a free account if you don't have one — use your `@hdfcbank.com` email if you want it as a corporate account).
2. Go to <https://www.kaggle.com/settings>.
3. Scroll to **API** → click **"Create New API Token"**. A `kaggle.json` file downloads to your `Downloads` folder.
4. Move it to the right location:

```powershell
# Create the .kaggle folder in your home directory
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.kaggle"

# Move the downloaded kaggle.json there
Move-Item -Path "$env:USERPROFILE\Downloads\kaggle.json" -Destination "$env:USERPROFILE\.kaggle\kaggle.json" -Force
```

5. Download the datasets:

```powershell
# 2023 balanced dataset (568K rows, 50/50 fraud) -- recommended for the first demo run
kaggle datasets download -d nelgiriyewithana/credit-card-fraud-detection-dataset-2023 -p data\ --unzip

# Original ULB dataset (284K rows, 0.17% fraud) -- recommended for the "reality check" slide
kaggle datasets download -d mlg-ulb/creditcardfraud -p data\ --unzip
```

6. Verify:

```powershell
ls data\*.csv
# Expected:
#   data\creditcard.csv          (~144 MB)
#   data\creditcard_2023.csv     (~144 MB)
```

### Option C: Manual download (if Kaggle CLI is blocked by IT)

1. Open <https://www.kaggle.com/datasets/nelgiriyewithana/credit-card-fraud-detection-dataset-2023> in your browser.
2. Click **"Download"** (top-right). You'll get `archive.zip`.
3. Extract the zip into the `data\` folder so that `data\creditcard_2023.csv` exists.
4. Repeat for <https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud> if you want the ULB dataset too.

---

## Section 9 — Run the pipeline (10-30 min depending on dataset and params)

Run scripts **in order**. Each one prints a summary at the end.

### 9.1 — Exploratory data analysis

```powershell
python src\01_eda.py
```

**What it does:** prints class distribution, transaction-amount stats, and writes 4 PNG plots to `results\` (class distribution, amount histogram, top-15 features, correlation heatmap).

**Expected output (on the 2023 balanced dataset):**

```
======================================================================
Dataset: kaggle_2023_balanced
  rows         : 568,630
  fraud rows   : 284,315 (50.0000%)
  features     : 29 (V1..Amount)
  is_balanced  : True
======================================================================
...
[done] EDA artifacts in C:\Users\you\Quantum-credit-card-fraud-detection\results
```

Open `results\01_class_distribution_kaggle_2023_balanced.png` to see the bar chart you'll show in the demo.

### 9.2 — Preprocessing (StandardScaler + SMOTE + PCA)

```powershell
python src\02_preprocessing.py --n-qubits 6 --train-size 1500 --test-size 800
```

**Recommended params for the live demo:**

| Param | Value | Why |
|---|---|---|
| `--n-qubits` | `6` | 2^6 = 64-dim Hilbert space; works on every IBM Quantum backend; trains in reasonable time. |
| `--train-size` | `1500` | QSVC is O(N²) — 1500 keeps it under 5 min on a laptop. |
| `--test-size` | `800` | Enough for stable AUC numbers, fast to evaluate. |

**Expected output:**

```
PCA explained variance (6 comps): ['0.121', '0.084', ...]
Total variance retained: 0.387
Quantum track saved: train=1500 x 6 (750 fraud), test=800 x 6 (400 fraud)
```

### 9.3 — Classical baselines

```powershell
python src\03_classical_baseline.py
```

**Runtime:** 1-4 min depending on dataset size.

**Expected output (2023 balanced dataset):**

```
=== Classical results ===
  logreg          AUC=0.9636  PR-AUC=0.9701  ...
  random_forest   AUC=0.9999  PR-AUC=0.9999  ...
  xgboost         AUC=0.9999  PR-AUC=0.9999  ...
  lightgbm        AUC=0.9998  PR-AUC=0.9998  ...
```

> **Note:** the 2023 dataset is unusually clean and balanced — XGBoost gets close to perfect AUC. Run on the original ULB dataset (`data\creditcard.csv`) to show the more challenging real-world imbalanced scenario.

### 9.4 — Variational Quantum Classifier (VQC)

```powershell
python src\04_quantum_vqc_simulator.py --optimizer spsa --maxiter 80
```

**Runtime:** 5-10 min. You'll see the loss decrease every 10 iterations.

**Expected output:**

```
2026-XX-XX iter  10  loss=0.6831
2026-XX-XX iter  20  loss=0.5124
...
2026-XX-XX iter  80  loss=0.3211
=== VQC simulator results ===
{
  "auc_roc": 0.9421,
  "pr_auc": 0.9355,
  ...
}
```

**Trained ansatz weights** are saved to `results\04_vqc_weights.npy` for use in the real-HW step.

### 9.5 — Quantum-Kernel SVM (QSVC)

```powershell
python src\05_quantum_kernel_qsvc.py --reps 2 --C 1.0
```

**Runtime:** 5-15 min for QSVC + Pegasos. You can pass `--skip-pegasos` if you're short on time.

**Expected output:**

```
[QSVC] AUC=0.9485 PR-AUC=0.9412 F1=0.8763 train=8.4 min
[PegasosQSVC] AUC=0.9351 ...
```

### 9.6 — Launch the live demo dashboard

```powershell
streamlit run src\07_compare_dashboard.py
```

A browser tab opens automatically at <http://localhost:8501> showing:

- Side-by-side metrics table (classical vs VQC vs QSVC vs PegasosQSVC).
- Interactive Plotly ROC and PR curves.
- The "Reality Check" narrative panel.
- Pipeline metadata (which dataset, n_qubits, PCA explained variance).

**Keep this browser tab open during the demo** — alt-tab to it from your slides.

---

## Section 10 — (Optional) Real IBM Quantum hardware run

Do this **24 hours before** the demo (queue times are unpredictable on the open plan).

1. Go to <https://quantum.ibm.com> → sign in (free open plan is fine).
2. Click your avatar → **Account settings** → copy the **API token**.
3. In PowerShell:

```powershell
$env:IBM_QUANTUM_TOKEN = "paste_your_token_here"

python src\06_ibm_runtime_real_hw.py --auto-backend --batch 30 --shots 4096 `
    --weights-npy results\04_vqc_weights.npy
```

You'll see queue progress messages. When done, results land in `results\06_ibm_runtime_metrics.json` and the Streamlit dashboard automatically picks them up on its next reload.

> **For a permanent setup:** instead of `$env:` (which only lasts the session), set the token globally via **Start menu → "Edit the system environment variables" → Environment Variables → New (User variables)** with name `IBM_QUANTUM_TOKEN` and your token as value. Restart PowerShell after.

---

## Section 11 — One-shot runner script

If you want to run the entire pipeline with one command, the repo provides:

```powershell
.\scripts\run_demo.ps1
```

This activates the venv (if not already), runs steps 8 (synthetic data check), 9.1 - 9.5, and prints the final command to launch the Streamlit dashboard. Useful for the dress rehearsal.

For just dependency setup (steps 6 + 7) on a fresh machine:

```powershell
.\scripts\install_deps.ps1
```

---

## Section 12 — Demo-day checklist

Run through this **30 minutes before** the meeting:

- [ ] Laptop on AC power (VQC is CPU-heavy and may throttle on battery).
- [ ] Close Slack / Teams / Outlook to free RAM.
- [ ] Plug in a wired ethernet cable if possible (don't risk WiFi during the demo).
- [ ] Pre-run the full pipeline once so all `results\*.json` files are fresh.
- [ ] Open the Streamlit dashboard in your browser and **leave it open** on a second monitor or alt-tab slot.
- [ ] Open `docs\slides_outline.md` in a markdown viewer (or copy it into PowerPoint).
- [ ] Print or save the **reality check table** (`README.md` Section 5) on a sticky note — you'll reference it during Q&A.
- [ ] Verify your IBM Quantum job (if you ran step 10) has actually completed.
- [ ] Have a backup screenshot of `results\01_*.png` and the dashboard in case something hangs live.

---

## Section 13 — Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `python: command not found` | Python not on PATH | Re-run installer with "Add to PATH" ticked. |
| `pip install` hangs / 0% progress | Corporate proxy | Set `pip` to use the proxy: `pip config set global.proxy http://your.proxy:port`. Get URL from your IT team. |
| `error: Microsoft Visual C++ 14.0 required` | Missing MSVC compiler | Install [MSVC Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/). |
| `Activate.ps1 cannot be loaded` | PowerShell ExecutionPolicy | Re-run Section 4 (`Set-ExecutionPolicy RemoteSigned`). |
| `kaggle: command not found` | venv not activated | Run `.\.venv\Scripts\Activate.ps1`. |
| `kaggle.json not found` | wrong path | Should be at `%USERPROFILE%\.kaggle\kaggle.json`. Check with `Get-Item $env:USERPROFILE\.kaggle\kaggle.json`. |
| `kaggle: 403 Forbidden` | Haven't accepted the dataset's terms | Open the dataset URL in a browser, click "I Understand and Accept" once. |
| `MemoryError` during VQC | Too few RAM, too large train_size | Re-run preprocessing with smaller `--train-size 800`. |
| Streamlit shows blank page | Result files missing | Run scripts 02 → 03 → 04 → 05 first, then refresh. |
| `Job failed: backend not available` | All open-plan IBM backends busy | Wait an hour, or switch to `--backend ibmq_qasm_simulator` (cloud simulator, faster than real HW for this demo). |
| `OSError: [WinError 10013]` on Streamlit | Port 8501 blocked by another process / firewall | `streamlit run src\07_compare_dashboard.py --server.port 8502`. |
| Long path errors (`filename or extension is too long`) | Project folder too deep on disk | Move repo to `C:\Quantum-credit-card-fraud-detection\` (root drive). |

---

## Section 14 — Cleanup / re-run

To start fresh without re-downloading the data:

```powershell
# Remove processed arrays + result artifacts (keeps the venv and CSVs)
Remove-Item -Recurse -Force data\processed, results\*.png, results\*.json, results\*.npy
```

To completely uninstall:

```powershell
deactivate                          # if venv is still active
Remove-Item -Recurse -Force .venv   # delete the virtual env
# (CSVs in data\ are large — keep them or delete with Remove-Item -Path data\creditcard*.csv)
```

---

## Section 15 — Suggested demo flow (timing)

| Time | Activity | Slide / Action |
|---|---|---|
| 0:00 | Open with the problem | Slide 1 (the problem) |
| 1:30 | Why classical hits a ceiling | Slide 2 |
| 3:00 | Hilbert-space pitch | Slide 3 |
| 4:30 | Reality check (be honest about NISQ) | Slide 4 |
| 6:00 | What this PoC delivered | Slide 5 |
| 7:30 | **Live: Streamlit dashboard** | Alt-tab to <http://localhost:8501> |
| 12:00 | Numbers that matter | Slide 7 |
| 13:30 | Hybrid serving architecture | Slide 8 |
| 15:00 | Roadmap | Slide 9 |
| 17:00 | Investment ask | Slide 10 |
| 18:30 | Risks + mitigations | Slide 11 |
| 19:30 | Why HDFC, why now | Slide 12 |
| 20:30 | Decision asks | Slide 13 |
| 22:00 | Q&A | Slide 14 anticipated answers |
| ~25:00 | Close | Slide 15 |

---

## Reference: full PowerShell session (copy-paste-able from a fresh terminal)

For convenience, here is the **entire** sequence from a fresh PowerShell window on a machine where Python and Git are already installed:

```powershell
# Navigate to home
cd $env:USERPROFILE

# Clone (skip if already cloned)
git clone https://github.com/kranthimj23/Quantum-credit-card-fraud-detection.git
cd Quantum-credit-card-fraud-detection

# Set up venv (skip if already created)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# Get data (Option A: synthetic, fastest)
python src\00_generate_synthetic.py --rows 20000 --fraud-rate 0.0017

# Run full pipeline
python src\01_eda.py
python src\02_preprocessing.py --n-qubits 6 --train-size 1500 --test-size 800
python src\03_classical_baseline.py
python src\04_quantum_vqc_simulator.py --optimizer spsa --maxiter 80
python src\05_quantum_kernel_qsvc.py --reps 2 --C 1.0

# Launch demo dashboard
streamlit run src\07_compare_dashboard.py
# -> Browser opens at http://localhost:8501
```

Total: ~25-40 min on first run, ~15-20 min on subsequent runs.

---

## Need help during the demo?

Keep these references open in a second tab:

- `STEPS.md` — what each script does
- `ARCHITECTURE.md` — circuit diagrams + Hilbert-space math
- `docs\slides_outline.md` — the deck talking points
- This file — for live Windows-specific recovery
