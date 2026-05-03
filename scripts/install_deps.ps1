# Quantum Credit-Card Fraud Detection -- one-shot Windows dependency installer.
#
# Runs from anywhere -- the script auto-detects its own location and
# operates against the repo root (its parent folder).
#
# Usage (any of these work):
#     # From repo root:
#     .\scripts\install_deps.ps1
#     # From inside scripts\:
#     .\install_deps.ps1
#     # By absolute path:
#     C:\path\to\repo\scripts\install_deps.ps1
#
# What it does:
#   1. Verifies Python 3.11 / 3.12 is on PATH.
#   2. Creates .venv in the repo root if it does not exist.
#   3. Activates the venv.
#   4. Upgrades pip.
#   5. Installs requirements.txt.
#   6. Generates synthetic data (only if no real Kaggle CSV is present).
#
# Re-runnable: skips steps that are already done. Aborts on any error.

$ErrorActionPreference = "Stop"

function Write-Section($message) {
    Write-Host ""
    Write-Host "==================================================================" -ForegroundColor Cyan
    Write-Host $message -ForegroundColor Cyan
    Write-Host "==================================================================" -ForegroundColor Cyan
}

# ----- Resolve repo root (parent of scripts\) and switch to it -----
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot
Write-Host "Repo root: $RepoRoot" -ForegroundColor DarkGray

# Sanity: confirm we're in a real checkout.
if (-not (Test-Path "requirements.txt")) {
    Write-Error "requirements.txt not found at $RepoRoot. Are you running this from a clone of the Quantum-credit-card-fraud-detection repo?"
    exit 1
}
if (-not (Test-Path "src\00_generate_synthetic.py")) {
    Write-Error "src\00_generate_synthetic.py not found at $RepoRoot. The repo checkout looks incomplete."
    exit 1
}

# ----- Step 1: Python check -----
Write-Section "Step 1/6 -- Verifying Python is installed"
try {
    $pyVersion = & python --version 2>&1
    Write-Host "Found: $pyVersion"
    if ($pyVersion -notmatch "Python 3\.(1[0-3])") {
        Write-Warning "Python 3.10-3.13 is supported. You have $pyVersion. Pipeline may still work but is unverified."
    }
}
catch {
    Write-Error "Python not found on PATH. Install from https://www.python.org/downloads/windows/ and re-run."
    exit 1
}

# ----- Step 2: venv -----
Write-Section "Step 2/6 -- Creating virtual environment (.venv) in $RepoRoot"
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    if (Test-Path ".venv") {
        Write-Warning ".venv folder exists but Activate.ps1 is missing. Removing and recreating."
        Remove-Item -Recurse -Force .venv
    }
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { Write-Error "python -m venv .venv failed."; exit 1 }
    Write-Host ".venv created."
}
else {
    Write-Host ".venv already exists -- skipping."
}

# ----- Step 3: activate -----
Write-Section "Step 3/6 -- Activating .venv"
& ".\.venv\Scripts\Activate.ps1"
Write-Host "venv activated. Prompt should now show (.venv)."

# ----- Step 4: pip upgrade -----
Write-Section "Step 4/6 -- Upgrading pip"
python -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -ne 0) { Write-Error "pip upgrade failed."; exit 1 }
Write-Host "pip upgraded."

# ----- Step 5: install requirements -----
Write-Section "Step 5/6 -- Installing project dependencies (this may take 10-15 min)"
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install -r requirements.txt failed. See errors above. Common fixes: install MSVC C++ Build Tools, or check your corporate proxy settings."
    exit 1
}
Write-Host "Dependencies installed."

# ----- Step 6: synthetic data fallback -----
Write-Section "Step 6/6 -- Ensuring at least one dataset is available"
$dataPresent = (Test-Path "data\creditcard.csv") -or
               (Test-Path "data\creditcard_2023.csv") -or
               (Test-Path "data\creditcard_synthetic.csv")
if (-not $dataPresent) {
    Write-Host "No dataset found. Generating synthetic fallback (5000 rows, 0.17% fraud)..."
    python "src\00_generate_synthetic.py" --rows 5000 --fraud-rate 0.0017
    if ($LASTEXITCODE -ne 0) { Write-Error "Synthetic data generation failed."; exit 1 }
}
else {
    Write-Host "Dataset already present -- skipping synthetic generation."
}

Write-Section "All set!"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "  1. (Optional) Download real Kaggle data into data\\ -- see WINDOWS_SETUP.md Section 8."
Write-Host "  2. Run the demo pipeline:    .\scripts\run_demo.ps1"
Write-Host "  3. Launch dashboard:         streamlit run src\07_compare_dashboard.py"
Write-Host ""
