# Quantum Credit-Card Fraud Detection -- one-shot Windows pipeline runner.
#
# Runs from anywhere -- the script auto-detects its own location and
# operates against the repo root (its parent folder).
#
# Usage:
#     # From repo root:
#     .\scripts\run_demo.ps1
#     # From inside scripts\:
#     .\run_demo.ps1
#
# Optional parameters:
#     -NQubits <int>      number of qubits / PCA components (default 6)
#     -TrainSize <int>    train set size after rebalancing (default 1500)
#     -TestSize <int>     test set size (default 800)
#     -MaxIter <int>      VQC optimizer iterations (default 80)
#     -SkipQuantum        only run preprocessing + classical baselines
#     -SkipPegasos        skip the slower PegasosQSVC variant
#     -Optimizer <str>    VQC optimizer: spsa | cobyla | adam (default spsa)
#
# Example -- fast smoke test:
#     .\scripts\run_demo.ps1 -NQubits 4 -TrainSize 300 -TestSize 200 -MaxIter 20 -SkipPegasos
#
# Example -- full demo run on a beefy laptop:
#     .\scripts\run_demo.ps1 -NQubits 8 -TrainSize 2000 -TestSize 1000 -MaxIter 100

param(
    [int]$NQubits = 6,
    [int]$TrainSize = 1500,
    [int]$TestSize = 800,
    [int]$MaxIter = 80,
    [string]$Optimizer = "spsa",
    [switch]$SkipQuantum,
    [switch]$SkipPegasos
)

$ErrorActionPreference = "Stop"

function Write-Section($message) {
    Write-Host ""
    Write-Host "==================================================================" -ForegroundColor Cyan
    Write-Host $message -ForegroundColor Cyan
    Write-Host "==================================================================" -ForegroundColor Cyan
}

function Time-Step($label, $scriptBlock) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    & $scriptBlock
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Step '$label' failed with exit code $LASTEXITCODE"
        exit 1
    }
    $sw.Stop()
    Write-Host ("[{0}] completed in {1:N1} sec" -f $label, $sw.Elapsed.TotalSeconds) -ForegroundColor Green
}

# ----- Resolve repo root (parent of scripts\) and switch to it -----
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot
Write-Host "Repo root: $RepoRoot" -ForegroundColor DarkGray

# ----- Pre-flight -----
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Error ".venv not found at $RepoRoot. Run .\scripts\install_deps.ps1 first."
    exit 1
}
foreach ($f in @("requirements.txt", "src\01_eda.py", "src\02_preprocessing.py")) {
    if (-not (Test-Path $f)) {
        Write-Error "$f not found at $RepoRoot. The repo checkout looks incomplete."
        exit 1
    }
}

Write-Section "Activating .venv"
& ".\.venv\Scripts\Activate.ps1"

# Verify at least one dataset is present.
$dataPresent = (Test-Path "data\creditcard.csv") -or
               (Test-Path "data\creditcard_2023.csv") -or
               (Test-Path "data\creditcard_synthetic.csv")
if (-not $dataPresent) {
    Write-Warning "No dataset CSV found in data\\. Generating synthetic fallback..."
    python "src\00_generate_synthetic.py" --rows 10000 --fraud-rate 0.0017
    if ($LASTEXITCODE -ne 0) { Write-Error "Synthetic data generation failed."; exit 1 }
}

# ----- Pipeline -----
Write-Section "Step 1/5 -- Exploratory data analysis (01_eda.py)"
Time-Step "EDA" { python "src\01_eda.py" }

Write-Section "Step 2/5 -- Preprocessing (02_preprocessing.py) -- n_qubits=$NQubits"
Time-Step "Preprocess" {
    python "src\02_preprocessing.py" `
        --n-qubits $NQubits `
        --train-size $TrainSize `
        --test-size $TestSize
}

Write-Section "Step 3/5 -- Classical baselines (03_classical_baseline.py)"
Time-Step "Classical" { python "src\03_classical_baseline.py" }

if ($SkipQuantum) {
    Write-Host ""
    Write-Host "Skipping quantum steps because -SkipQuantum was passed." -ForegroundColor Yellow
}
else {
    Write-Section "Step 4/5 -- VQC simulator (04_quantum_vqc_simulator.py) -- optimizer=$Optimizer maxiter=$MaxIter"
    Time-Step "VQC" {
        python "src\04_quantum_vqc_simulator.py" `
            --optimizer $Optimizer `
            --maxiter $MaxIter
    }

    Write-Section "Step 5/5 -- Quantum kernel SVM (05_quantum_kernel_qsvc.py)"
    if ($SkipPegasos) {
        Time-Step "QSVC" { python "src\05_quantum_kernel_qsvc.py" --reps 2 --C 1.0 --skip-pegasos }
    }
    else {
        Time-Step "QSVC + Pegasos" { python "src\05_quantum_kernel_qsvc.py" --reps 2 --C 1.0 }
    }
}

# ----- Summary -----
Write-Section "Pipeline complete!"
Write-Host ""
Write-Host "Generated artifacts in results\\ :" -ForegroundColor Green
Get-ChildItem -Path "results" -File | Select-Object Name, Length, LastWriteTime | Format-Table

Write-Host ""
Write-Host "Now launch the demo dashboard:" -ForegroundColor Yellow
Write-Host "    streamlit run src\07_compare_dashboard.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "(Browser opens at http://localhost:8501)" -ForegroundColor Yellow
