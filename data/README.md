# Data folder

The raw Kaggle CSVs are **not committed** to the repo — they're large (44 MB and 144 MB) and Kaggle-licensed. Download them locally before running the pipeline.

## Supported datasets

This project supports **both** of the public Kaggle credit-card-fraud datasets, and the loader (`src/data_loader.py`) auto-detects which one is present:

| Dataset | Slug | Rows | Schema | Class balance |
|---|---|---|---|---|
| **2023 balanced** | `nelgiriyewithana/credit-card-fraud-detection-dataset-2023` | 568,630 | `id, V1..V28, Amount, Class` | 50.0% fraud (balanced) |
| **Original ULB** | `mlg-ulb/creditcardfraud` | 284,807 | `Time, V1..V28, Amount, Class` | 0.172% fraud (severely imbalanced) |

Both have 28 PCA-anonymized features (`V1..V28`) plus `Amount`, so the same model architecture works on both — only the rebalancing step changes.

## Download instructions

### Option 1: Kaggle CLI (recommended)

```bash
# 1. Install the kaggle CLI (already in requirements.txt)
pip install kaggle

# 2. Place your kaggle.json API token at ~/.kaggle/kaggle.json
#    (Generate one at https://www.kaggle.com/settings -> "Create New API Token")
chmod 600 ~/.kaggle/kaggle.json

# 3. Download whichever dataset(s) you want
cd data

# 2023 balanced (recommended for first demo run -- larger, balanced, faster to converge)
kaggle datasets download -d nelgiriyewithana/credit-card-fraud-detection-dataset-2023
unzip credit-card-fraud-detection-dataset-2023.zip
# -> creditcard_2023.csv

# Original ULB (recommended for the "reality check" -- shows quantum advantage on rare events)
kaggle datasets download -d mlg-ulb/creditcardfraud
unzip creditcardfraud.zip
# -> creditcard.csv
```

### Option 2: Manual download

1. Visit either dataset page on Kaggle (links above) and click "Download" (Kaggle sign-in required).
2. Unzip into this folder so that `data/creditcard_2023.csv` and/or `data/creditcard.csv` exist.

### Option 3: Synthetic fallback (for smoke tests / CI)

If you don't have a Kaggle account handy and just want to verify the pipeline runs end-to-end, use:

```bash
python src/00_generate_synthetic.py
```

This creates `data/creditcard_synthetic.csv` with the same schema (28 PCA-like features + `Amount` + `Class`) and roughly the same class imbalance (~0.17% fraud). The synthetic data is deterministic (seeded) and is enough to smoke-test the VQC and QSVC pipelines without touching Kaggle.

## Schema reference

### Original ULB (`creditcard.csv`)

| Column | Type | Notes |
|---|---|---|
| `Time` | float | seconds elapsed between this and first transaction |
| `V1`..`V28` | float | 28 PCA-anonymized features (already preprocessed by Kaggle) |
| `Amount` | float | transaction amount (USD) |
| `Class` | int | 0 = normal, 1 = fraud (target) |

Total: 284,807 rows. Fraud: 492 (0.172%).

### 2023 balanced (`creditcard_2023.csv`)

| Column | Type | Notes |
|---|---|---|
| `id` | int | row identifier (no semantic meaning) |
| `V1`..`V28` | float | 28 anonymized features |
| `Amount` | float | transaction amount |
| `Class` | int | 0 = normal, 1 = fraud |

Total: 568,630 rows. Fraud: ~284,315 (50.0%).

The loader drops `id` / `Time` and keeps `V1..V28 + Amount + Class` for both, so downstream code is identical.
