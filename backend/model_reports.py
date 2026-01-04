import os
from typing import List, Dict, Any

import matplotlib.pyplot as plt
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, roc_curve, precision_recall_curve, auc

from .database import SessionLocal
from .models import ForecastRun, AnomalyModelRun
from .anomaly_engine.services_ml import evaluate_iforest_vs_threshold
from .anomaly_engine.services_cloud_dataset import _load_cloud_dataset
from .zero_trust.services import _load_dataset as _load_zero_trust_dataset, _build_feature_matrix as _build_zero_trust_features


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def generate_forecast_metrics_report(output_dir: str = "reports/model_metrics") -> Dict[str, str]:
    session = SessionLocal()
    try:
        runs: List[ForecastRun] = session.query(ForecastRun).order_by(ForecastRun.created_at).all()
    finally:
        session.close()
    if not runs:
        return {}
    _ensure_dir(output_dir)
    times = [r.created_at for r in runs if r.created_at is not None]
    if not times:
        return {}
    mae = [float(r.mae or 0.0) for r in runs]
    rmse = [float(r.rmse or 0.0) for r in runs]
    mape = [float(r.mape or 0.0) for r in runs]
    paths: Dict[str, str] = {}
    plt.figure(figsize=(10, 4))
    plt.plot(times, mae, marker="o")
    plt.xlabel("Run time")
    plt.ylabel("MAE")
    plt.title("Forecast model MAE over time")
    plt.tight_layout()
    path_mae = os.path.join(output_dir, "forecast_mae.png")
    plt.savefig(path_mae)
    plt.close()
    paths["mae"] = path_mae
    plt.figure(figsize=(10, 4))
    plt.plot(times, rmse, marker="o")
    plt.xlabel("Run time")
    plt.ylabel("RMSE")
    plt.title("Forecast model RMSE over time")
    plt.tight_layout()
    path_rmse = os.path.join(output_dir, "forecast_rmse.png")
    plt.savefig(path_rmse)
    plt.close()
    paths["rmse"] = path_rmse
    plt.figure(figsize=(10, 4))
    plt.plot(times, mape, marker="o")
    plt.xlabel("Run time")
    plt.ylabel("MAPE")
    plt.title("Forecast model MAPE over time")
    plt.tight_layout()
    path_mape = os.path.join(output_dir, "forecast_mape.png")
    plt.savefig(path_mape)
    plt.close()
    paths["mape"] = path_mape
    return paths


def generate_anomaly_metrics_report(output_dir: str = "reports/model_metrics") -> Dict[str, str]:
    session = SessionLocal()
    try:
        runs: List[AnomalyModelRun] = (
            session.query(AnomalyModelRun)
            .filter(AnomalyModelRun.model_name == "iforest_vs_z")
            .order_by(AnomalyModelRun.created_at)
            .all()
        )
    finally:
        session.close()
    if not runs:
        evaluate_iforest_vs_threshold(window_hours=24, z=2.0)
        session = SessionLocal()
        try:
            runs = (
                session.query(AnomalyModelRun)
                .filter(AnomalyModelRun.model_name == "iforest_vs_z")
                .order_by(AnomalyModelRun.created_at)
                .all()
            )
        finally:
            session.close()
    if not runs:
        return {}
    _ensure_dir(output_dir)
    times = [r.created_at for r in runs if r.created_at is not None]
    if not times:
        return {}
    precision = [float(r.precision or 0.0) for r in runs]
    recall = [float(r.recall or 0.0) for r in runs]
    f1 = [float(r.f1 or 0.0) for r in runs]
    accuracy = [float(r.accuracy or 0.0) for r in runs]
    paths: Dict[str, str] = {}
    plt.figure(figsize=(10, 4))
    plt.plot(times, precision, marker="o", label="Precision")
    plt.ylim(0.0, 1.0)
    plt.xlabel("Run time")
    plt.ylabel("Precision")
    plt.title("Anomaly model precision over time (iforest_vs_z)")
    plt.tight_layout()
    path_precision = os.path.join(output_dir, "anomaly_iforest_precision.png")
    plt.savefig(path_precision)
    plt.close()
    paths["precision"] = path_precision
    plt.figure(figsize=(10, 4))
    plt.plot(times, recall, marker="o", label="Recall")
    plt.ylim(0.0, 1.0)
    plt.xlabel("Run time")
    plt.ylabel("Recall")
    plt.title("Anomaly model recall over time (iforest_vs_z)")
    plt.tight_layout()
    path_recall = os.path.join(output_dir, "anomaly_iforest_recall.png")
    plt.savefig(path_recall)
    plt.close()
    paths["recall"] = path_recall
    plt.figure(figsize=(10, 4))
    plt.plot(times, f1, marker="o", label="F1")
    plt.ylim(0.0, 1.0)
    plt.xlabel("Run time")
    plt.ylabel("F1")
    plt.title("Anomaly model F1 over time (iforest_vs_z)")
    plt.tight_layout()
    path_f1 = os.path.join(output_dir, "anomaly_iforest_f1.png")
    plt.savefig(path_f1)
    plt.close()
    paths["f1"] = path_f1
    plt.figure(figsize=(10, 4))
    plt.plot(times, accuracy, marker="o", label="Accuracy", color="#8b5cf6")
    plt.ylim(0.0, 1.0)
    plt.xlabel("Run time")
    plt.ylabel("Accuracy")
    plt.title("Anomaly model accuracy over time (iforest_vs_z)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    path_accuracy = os.path.join(output_dir, "anomaly_iforest_accuracy.png")
    plt.savefig(path_accuracy)
    plt.close()
    paths["accuracy"] = path_accuracy
    return paths


def generate_anomaly_dataset_training_curves(output_dir: str = "reports/model_metrics") -> Dict[str, str]:
    df = _load_cloud_dataset()
    if df.empty:
        return {}
    required_cols = [
        "CPU_Usage",
        "Memory_Usage",
        "Disk_IO",
        "Network_IO",
        "Anomaly_Label",
    ]
    for col in required_cols:
        if col not in df.columns:
            return {}
    features = df[["CPU_Usage", "Memory_Usage", "Disk_IO", "Network_IO"]].astype(float).fillna(0.0)
    labels = df["Anomaly_Label"].astype(int)
    if labels.nunique() < 2:
        return {}
    actual_anomaly_rate = labels.sum() / len(labels)
    contamination = max(0.05, min(0.2, actual_anomaly_rate * 1.2))
    model = IsolationForest(contamination=contamination, random_state=42)
    model.fit(features)
    scores = model.decision_function(features)
    thresholds = np.linspace(scores.min(), scores.max(), num=100)
    precision_values = []
    recall_values = []
    f1_values = []
    accuracy_values = []
    balanced_accuracy_values = []
    for t in thresholds:
        preds = (scores <= t).astype(int)
        precision_values.append(precision_score(labels, preds, zero_division=0))
        recall_values.append(recall_score(labels, preds, zero_division=0))
        f1_values.append(f1_score(labels, preds, zero_division=0))
        accuracy_values.append(accuracy_score(labels, preds))
        tn = ((preds == 0) & (labels == 0)).sum()
        fp = ((preds == 1) & (labels == 0)).sum()
        fn = ((preds == 0) & (labels == 1)).sum()
        tp = ((preds == 1) & (labels == 1)).sum()
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
        balanced_acc = (specificity + sensitivity) / 2
        balanced_accuracy_values.append(balanced_acc)
    _ensure_dir(output_dir)
    paths: Dict[str, str] = {}
    plt.figure(figsize=(10, 4))
    plt.plot(thresholds, precision_values, marker="o")
    plt.xlabel("Decision function threshold")
    plt.ylabel("Precision")
    plt.title("Dataset-based precision vs threshold (Isolation Forest)")
    plt.tight_layout()
    path_precision = os.path.join(output_dir, "anomaly_dataset_precision.png")
    plt.savefig(path_precision)
    plt.close()
    paths["precision"] = path_precision
    plt.figure(figsize=(10, 4))
    plt.plot(thresholds, recall_values, marker="o")
    plt.xlabel("Decision function threshold")
    plt.ylabel("Recall")
    plt.title("Dataset-based recall vs threshold (Isolation Forest)")
    plt.tight_layout()
    path_recall = os.path.join(output_dir, "anomaly_dataset_recall.png")
    plt.savefig(path_recall)
    plt.close()
    paths["recall"] = path_recall
    plt.figure(figsize=(10, 4))
    plt.plot(thresholds, f1_values, marker="o")
    plt.xlabel("Decision function threshold")
    plt.ylabel("F1")
    plt.title("Dataset-based F1 vs threshold (Isolation Forest)")
    plt.tight_layout()
    path_f1 = os.path.join(output_dir, "anomaly_dataset_f1.png")
    plt.savefig(path_f1)
    plt.close()
    paths["f1"] = path_f1
    plt.figure(figsize=(10, 4))
    plt.plot(thresholds, accuracy_values, marker="o", label="Accuracy", alpha=0.7)
    plt.plot(thresholds, balanced_accuracy_values, marker="s", label="Balanced Accuracy", alpha=0.7)
    plt.xlabel("Decision function threshold")
    plt.ylabel("Score")
    plt.title(f"Dataset-based accuracy vs threshold (Isolation Forest, contamination={contamination:.3f})")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    path_acc = os.path.join(output_dir, "anomaly_dataset_accuracy.png")
    plt.savefig(path_acc)
    plt.close()
    paths["accuracy"] = path_acc
    best_f1_idx = np.argmax(f1_values)
    best_threshold = thresholds[best_f1_idx]
    print(f"Best F1 threshold: {best_threshold:.4f}")
    print(f"Best F1 score: {f1_values[best_f1_idx]:.4f}")
    print(f"At best threshold - Accuracy: {accuracy_values[best_f1_idx]:.4f}, Balanced Accuracy: {balanced_accuracy_values[best_f1_idx]:.4f}")
    print(f"At best threshold - Precision: {precision_values[best_f1_idx]:.4f}, Recall: {recall_values[best_f1_idx]:.4f}")
    fpr, tpr, _ = roc_curve(labels, -scores)
    roc_auc = auc(fpr, tpr)
    plt.figure(figsize=(6, 6))
    plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.3f}")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.title("ROC curve (Isolation Forest)")
    plt.legend(loc="lower right")
    plt.tight_layout()
    path_roc = os.path.join(output_dir, "anomaly_dataset_roc.png")
    plt.savefig(path_roc)
    plt.close()
    paths["roc"] = path_roc
    pr_precision, pr_recall, _ = precision_recall_curve(labels, -scores)
    pr_auc = auc(pr_recall, pr_precision)
    plt.figure(figsize=(6, 6))
    plt.plot(pr_recall, pr_precision, label=f"AUC = {pr_auc:.3f}")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision–recall curve (Isolation Forest)")
    plt.legend(loc="lower left")
    plt.tight_layout()
    path_pr = os.path.join(output_dir, "anomaly_dataset_pr.png")
    plt.savefig(path_pr)
    plt.close()
    paths["pr"] = path_pr
    return paths


def generate_all_model_reports(output_dir: str = "reports/model_metrics") -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    results["forecast"] = generate_forecast_metrics_report(output_dir=output_dir)
    results["anomaly_iforest"] = generate_anomaly_metrics_report(output_dir=output_dir)
    results["anomaly_dataset"] = generate_anomaly_dataset_training_curves(output_dir=output_dir)
    df = _load_zero_trust_dataset()
    if not df.empty and "risk_label" in df.columns:
        features = _build_zero_trust_features(df)
        labels = df["risk_label"].astype(int)
        if labels.nunique() >= 2 and features.shape[0] == labels.shape[0]:
            model = IsolationForest(contamination=0.1, random_state=42)
            model.fit(features)
            scores = model.decision_function(features)
            thresholds = np.linspace(scores.min(), scores.max(), num=50)
            precision_values = []
            recall_values = []
            f1_values = []
            accuracy_values = []
            for t in thresholds:
                preds = (scores <= t).astype(int)
                precision_values.append(precision_score(labels, preds, zero_division=0))
                recall_values.append(recall_score(labels, preds, zero_division=0))
                f1_values.append(f1_score(labels, preds, zero_division=0))
                accuracy_values.append(accuracy_score(labels, preds))
            _ensure_dir(output_dir)
            plt.figure(figsize=(10, 4))
            plt.plot(thresholds, precision_values, marker="o")
            plt.xlabel("Decision function threshold")
            plt.ylabel("Precision")
            plt.title("Zero trust precision vs threshold")
            plt.tight_layout()
            path_precision = os.path.join(output_dir, "zero_trust_precision.png")
            plt.savefig(path_precision)
            plt.close()
            plt.figure(figsize=(10, 4))
            plt.plot(thresholds, recall_values, marker="o")
            plt.xlabel("Decision function threshold")
            plt.ylabel("Recall")
            plt.title("Zero trust recall vs threshold")
            plt.tight_layout()
            path_recall = os.path.join(output_dir, "zero_trust_recall.png")
            plt.savefig(path_recall)
            plt.close()
            plt.figure(figsize=(10, 4))
            plt.plot(thresholds, f1_values, marker="o")
            plt.xlabel("Decision function threshold")
            plt.ylabel("F1")
            plt.title("Zero trust F1 vs threshold")
            plt.tight_layout()
            path_f1 = os.path.join(output_dir, "zero_trust_f1.png")
            plt.savefig(path_f1)
            plt.close()
            plt.figure(figsize=(10, 4))
            plt.plot(thresholds, accuracy_values, marker="o")
            plt.xlabel("Decision function threshold")
            plt.ylabel("Accuracy")
            plt.title("Zero trust accuracy vs threshold")
            plt.tight_layout()
            path_acc = os.path.join(output_dir, "zero_trust_accuracy.png")
            plt.savefig(path_acc)
            plt.close()
            fpr, tpr, _ = roc_curve(labels, -scores)
            roc_auc = auc(fpr, tpr)
            plt.figure(figsize=(6, 6))
            plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.3f}")
            plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
            plt.xlabel("False positive rate")
            plt.ylabel("True positive rate")
            plt.title("Zero trust ROC curve")
            plt.legend(loc="lower right")
            plt.tight_layout()
            path_roc = os.path.join(output_dir, "zero_trust_roc.png")
            plt.savefig(path_roc)
            plt.close()
            pr_precision, pr_recall, _ = precision_recall_curve(labels, -scores)
            pr_auc = auc(pr_recall, pr_precision)
            plt.figure(figsize=(6, 6))
            plt.plot(pr_recall, pr_precision, label=f"AUC = {pr_auc:.3f}")
            plt.xlabel("Recall")
            plt.ylabel("Precision")
            plt.title("Zero trust precision–recall curve")
            plt.legend(loc="lower left")
            plt.tight_layout()
            path_pr = os.path.join(output_dir, "zero_trust_pr.png")
            plt.savefig(path_pr)
            plt.close()
    return results


if __name__ == "__main__":
    generate_all_model_reports()


