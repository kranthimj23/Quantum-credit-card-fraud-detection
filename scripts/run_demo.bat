@echo off
REM Quantum Credit-Card Fraud Detection -- one-shot Windows CMD demo runner.
REM
REM For PowerShell users, prefer scripts\run_demo.ps1 (more featureful).
REM This .bat is for users who can't / don't want to enable PowerShell scripts.
REM
REM Runs from anywhere -- auto-resolves to the repo root via %~dp0.

setlocal enableextensions

REM Switch to the repo root (parent of scripts\)
pushd "%~dp0.."
echo Repo root: %CD%

if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found at %CD%. Repo checkout looks incomplete.
    popd
    exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
    echo .venv not found. Creating...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create venv. Is Python on PATH?
        popd
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ERROR: Failed to activate .venv.
    popd
    exit /b 1
)

echo.
echo === Upgrading pip and installing dependencies ===
python -m pip install --upgrade pip
if errorlevel 1 (
    echo ERROR: pip upgrade failed.
    popd
    exit /b 1
)
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: pip install -r requirements.txt failed.
    popd
    exit /b 1
)

if not exist "data\creditcard.csv" if not exist "data\creditcard_2023.csv" if not exist "data\creditcard_synthetic.csv" (
    echo.
    echo No dataset found. Generating synthetic fallback...
    python "src\00_generate_synthetic.py" --rows 10000 --fraud-rate 0.0017
    if errorlevel 1 (
        echo ERROR: Synthetic data generation failed.
        popd
        exit /b 1
    )
)

echo.
echo === Step 1/5: EDA ===
python "src\01_eda.py"
if errorlevel 1 ( echo ERROR: EDA failed. & popd & exit /b 1 )

echo.
echo === Step 2/5: Preprocessing ===
python "src\02_preprocessing.py" --n-qubits 6 --train-size 1500 --test-size 800
if errorlevel 1 ( echo ERROR: Preprocessing failed. & popd & exit /b 1 )

echo.
echo === Step 3/5: Classical baselines ===
python "src\03_classical_baseline.py"
if errorlevel 1 ( echo ERROR: Classical baselines failed. & popd & exit /b 1 )

echo.
echo === Step 4/5: VQC simulator ===
python "src\04_quantum_vqc_simulator.py" --optimizer spsa --maxiter 80
if errorlevel 1 ( echo ERROR: VQC failed. & popd & exit /b 1 )

echo.
echo === Step 5/5: Quantum kernel SVM ===
python "src\05_quantum_kernel_qsvc.py" --reps 2 --C 1.0
if errorlevel 1 ( echo ERROR: QSVC failed. & popd & exit /b 1 )

echo.
echo ==============================================================
echo Pipeline complete!
echo ==============================================================
echo.
echo To launch the demo dashboard, run:
echo     streamlit run src\07_compare_dashboard.py
echo.
echo (Browser will open at http://localhost:8501)
echo.

popd
endlocal
