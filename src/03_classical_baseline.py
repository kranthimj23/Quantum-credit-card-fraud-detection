"""
Classical baselines for credit-card fraud detection.

Trains LogisticRegression, RandomForest, and XGBoost on the FULL preprocessed
classical training set, then evaluates on the held-out test set with:
    - AUC-ROC (primary)
    - PR-AUC (Average Precision -- more meaningful on imbalanced data)
    - F1, Precision, Recall, Recall@1%FPR
    - Latency (avg ms per prediction)

Writes results to results/03_classical_metrics.json and ROC/PR curve PNGs.

Usage:
    python src/03_classical_baseline.py
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"


def recall_at_fpr(y_true: np.ndarray, y_score: np.ndarray, fpr_target: float = 0.01) -> float:
    """Recall at the threshold that achieves <= fpr_target false positive rate."""
    fpr, tpr, _ = roc_curve(y_true, y_score)
    mask = fpr <= fpr_target
    return float(tpr[mask].max()) if mask.any() else 0.0


def evaluate(name: str, model, X_test: np.ndarray, y_test: np.ndarray) -> dict:
    """Score a fitted classifier on the test set; return a metrics dict."""
    t0 = time.perf_counter()
    if hasattr(model, "predict_proba"):
        y_score = model.predict_proba(X_test)[:, 1]
    else:
        y_score = model.decision_function(X_test)
    latency_ms = 1000 * (time.perf_counter() - t0) / max(1, len(y_test))

    y_pred = (y_score >= 0.5).astype(int)
    metrics = {
        "model": name,
        "auc_roc": float(roc_auc_score(y_test, y_score)),
        "pr_auc": float(average_precision_score(y_test, y_score)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "recall_at_1pct_fpr": recall_at_fpr(y_test, y_score, 0.01),
        "latency_ms_per_pred": float(latency_ms),
    }
    logger.info(
        "[%s] AUC=%.4f PR-AUC=%.4f F1=%.4f recall@1%%FPR=%.4f lat=%.3f ms/pred",
        name,
        metrics["auc_roc"],
        metrics["pr_auc"],
        metrics["f1"],
        metrics["recall_at_1pct_fpr"],
        metrics["latency_ms_per_pred"],
    )
    return metrics, y_score


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    RESULTS.mkdir(parents=True, exist_ok=True)

    X_train = np.load(PROCESSED / "classical_X_train.npy")
    y_train = np.load(PROCESSED / "classical_y_train.npy")
    X_test = np.load(PROCESSED / "classical_X_test.npy")
    y_test = np.load(PROCESSED / "classical_y_test.npy")

    logger.info(
        "Loaded classical arrays: train=%s, test=%s, train_fraud=%d, test_fraud=%d",
        X_train.shape,
        X_test.shape,
        int(y_train.sum()),
        int(y_test.sum()),
    )

    models = {
        "logreg": LogisticRegression(max_iter=2000, n_jobs=-1, class_weight="balanced"),
        "random_forest": RandomForestClassifier(
            n_estimators=200, n_jobs=-1, class_weight="balanced", random_state=42
        ),
    }

    # XGBoost is optional (heavier dep) -- include if importable.
    try:
        from xgboost import XGBClassifier

        # scale_pos_weight = (#neg / #pos) helps a lot on imbalanced data.
        n_pos = max(1, int(y_train.sum()))
        n_neg = max(1, int((1 - y_train).sum()))
        models["xgboost"] = XGBClassifier(
            n_estimators=400,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.9,
            colsample_bytree=0.9,
            tree_method="hist",
            n_jobs=-1,
            scale_pos_weight=n_neg / n_pos,
            eval_metric="aucpr",
            random_state=42,
        )
    except ImportError:
        logger.warning("xgboost not installed; skipping that baseline.")

    # LightGBM is also optional.
    try:
        from lightgbm import LGBMClassifier

        models["lightgbm"] = LGBMClassifier(
            n_estimators=400,
            learning_rate=0.05,
            class_weight="balanced",
            n_jobs=-1,
            random_state=42,
            verbose=-1,
        )
    except ImportError:
        logger.warning("lightgbm not installed; skipping that baseline.")

    all_metrics: list[dict] = []
    scores_by_model: dict[str, np.ndarray] = {}
    train_times: dict[str, float] = {}

    for name, model in models.items():
        logger.info("Training %s ...", name)
        t0 = time.perf_counter()
        model.fit(X_train, y_train)
        train_times[name] = time.perf_counter() - t0
        logger.info("  trained in %.2f s", train_times[name])

        metrics, y_score = evaluate(name, model, X_test, y_test)
        metrics["train_seconds"] = train_times[name]
        all_metrics.append(metrics)
        scores_by_model[name] = y_score

    # Save metrics JSON.
    out_json = RESULTS / "03_classical_metrics.json"
    out_json.write_text(json.dumps(all_metrics, indent=2))
    logger.info("Wrote %s", out_json)

    # ROC curves.
    fig, ax = plt.subplots(figsize=(6, 5))
    for name, scores in scores_by_model.items():
        fpr, tpr, _ = roc_curve(y_test, scores)
        auc = roc_auc_score(y_test, scores)
        ax.plot(fpr, tpr, label=f"{name} (AUC={auc:.4f})")
    ax.plot([0, 1], [0, 1], "k--", alpha=0.4)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("Classical baselines -- ROC")
    ax.legend(loc="lower right")
    fig.tight_layout()
    out = RESULTS / "03_classical_roc.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    logger.info("Wrote %s", out)

    # PR curves.
    fig, ax = plt.subplots(figsize=(6, 5))
    for name, scores in scores_by_model.items():
        prec, rec, _ = precision_recall_curve(y_test, scores)
        ap = average_precision_score(y_test, scores)
        ax.plot(rec, prec, label=f"{name} (AP={ap:.4f})")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Classical baselines -- Precision/Recall")
    ax.legend(loc="lower left")
    fig.tight_layout()
    out = RESULTS / "03_classical_pr.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    logger.info("Wrote %s", out)

    print("\n=== Classical results ===")
    for m in all_metrics:
        print(
            f"  {m['model']:<15} AUC={m['auc_roc']:.4f}  PR-AUC={m['pr_auc']:.4f}  "
            f"F1={m['f1']:.4f}  Recall@1%FPR={m['recall_at_1pct_fpr']:.4f}  "
            f"train={m['train_seconds']:.1f}s  lat={m['latency_ms_per_pred']:.3f} ms/pred"
        )


if __name__ == "__main__":
    main()
