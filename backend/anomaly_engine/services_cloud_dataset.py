from typing import Dict, List
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


DATA_PATH = os.path.join(os.path.dirname(__file__), "anomaly_cloud_dataset.csv")


def _load_cloud_dataset() -> pd.DataFrame:
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame()
    df = pd.read_csv(DATA_PATH)
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df = df.dropna(subset=["Timestamp"])
    return df


def _build_cloud_explanation(row: pd.Series, top_features: List[str], severity: str) -> str:
    metric_texts: List[str] = []
    for feature in top_features:
        value = float(row[feature])
        label = feature.replace("_", " ")
        metric_texts.append(f"{label} {value:.2f}")
    metrics_part = ", ".join(metric_texts)
    label_value = int(row["Anomaly_Label"]) if "Anomaly_Label" in row else 0
    nature = "labelled anomaly" if label_value == 1 else "model flagged event"
    return f"{row['Workload_Type']} activity {nature} with {severity} deviation in {metrics_part}"


def detect_cloud_dataset_anomalies(contamination: float = 0.1, limit: int = 100) -> Dict:
    df = _load_cloud_dataset()
    if df.empty:
        return {"count": 0, "anomalies": [], "message": "Dataset is empty or missing"}
    required_cols = [
        "Timestamp",
        "CPU_Usage",
        "Memory_Usage",
        "Disk_IO",
        "Network_IO",
        "Workload_Type",
        "Anomaly_Label",
    ]
    for col in required_cols:
        if col not in df.columns:
            return {"count": 0, "anomalies": [], "message": "Dataset schema is invalid"}
    feature_cols = ["CPU_Usage", "Memory_Usage", "Disk_IO", "Network_IO"]
    features = df[feature_cols].astype(float).fillna(0.0)
    model = IsolationForest(contamination=contamination, random_state=42)
    model.fit(features)
    scores = model.decision_function(features)
    labels = model.predict(features)
    df["anomaly_score"] = scores
    df["is_anomaly"] = labels
    anomalies = df[df["is_anomaly"] == -1].copy()
    if anomalies.empty:
        return {"count": 0, "anomalies": [], "message": "No anomalies detected"}
    baseline = features.mean()
    base_q_critical, base_q_warning = np.quantile(scores, [0.05, 0.15])
    records: List[Dict] = []
    for _, row in anomalies.iterrows():
        diffs = row[feature_cols] - baseline
        ordered = diffs.abs().sort_values(ascending=False)
        top_features = list(ordered.index[:3])
        score = float(row["anomaly_score"])
        severity = "low"
        if score <= base_q_critical:
            severity = "high"
        elif score <= base_q_warning:
            severity = "moderate"
        explanation = _build_cloud_explanation(row, top_features, severity)
        record = {
            "timestamp": row["Timestamp"].isoformat() if pd.notna(row["Timestamp"]) else None,
            "workload_type": row["Workload_Type"],
            "cpu_usage": float(row["CPU_Usage"]),
            "memory_usage": float(row["Memory_Usage"]),
            "disk_io": float(row["Disk_IO"]),
            "network_io": float(row["Network_IO"]),
            "severity": severity,
            "top_features": top_features,
            "anomaly_score": score,
            "anomaly_label": int(row["Anomaly_Label"]),
            "explanation": explanation,
        }
        records.append(record)
    severity_rank = {"high": 2, "moderate": 1, "low": 0}
    records.sort(key=lambda r: (r["timestamp"] or "", severity_rank.get(r["severity"], 0)), reverse=True)
    if limit and len(records) > limit:
        records = records[:limit]
    return {"count": len(records), "anomalies": records}