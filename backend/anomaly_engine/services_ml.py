from datetime import datetime, timedelta
from typing import Dict, List
import os
import json
from urllib import request as urlrequest

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neural_network import MLPRegressor

from ..database import SessionLocal
from ..models import CloudUsage, AnomalyAlert, AnomalyThresholdConfig, AnomalyModelRun


def _load_anomaly_dataset(window_hours: int = 24) -> pd.DataFrame:
    session = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        records = session.query(CloudUsage).filter(
            CloudUsage.provider == "vps",
            CloudUsage.metric.in_(["cpu_pct", "mem_pct", "load_avg", "daily_cost"]),
            CloudUsage.timestamp >= cutoff,
        ).order_by(CloudUsage.timestamp).all()
    finally:
        session.close()
    rows: List[Dict] = []
    for r in records:
        rows.append(
            {
                "department": r.account_id,
                "resource_id": r.resource_id,
                "metric": r.metric,
                "timestamp": r.timestamp,
                "value": r.value if r.metric != "daily_cost" else r.cost,
            }
        )
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    pivot = df.pivot_table(
        index=["department", "resource_id", "timestamp"],
        columns="metric",
        values="value",
        aggfunc="mean",
    ).reset_index()
    for col in ["cpu_pct", "mem_pct", "load_avg", "daily_cost"]:
        if col not in pivot.columns:
            pivot[col] = 0.0
    return pivot


def _load_threshold_configs(session) -> Dict[str, AnomalyThresholdConfig]:
    configs = session.query(AnomalyThresholdConfig).all()
    result: Dict[str, AnomalyThresholdConfig] = {}
    for c in configs:
        key = c.department if c.department is not None else "__global__"
        result[key] = c
    return result


def _send_alert_notification(payload: Dict) -> bool:
    url = os.getenv("ALERT_WEBHOOK_URL")
    if not url:
        return False
    data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urlrequest.urlopen(req, timeout=5)
        return True
    except Exception:
        return False


def _build_iforest_explanation(row: pd.Series, top_features: List[str], contributions: Dict[str, float], severity: str) -> str:
    parts: List[str] = []
    cost_delta = contributions.get("daily_cost")
    if cost_delta is not None:
        parts.append("Cost deviation {:.2f} from baseline".format(cost_delta))
    if top_features:
        parts.append("Primary driver {}".format(top_features[0]))
        if len(top_features) > 1:
            parts.append("Additional drivers {}".format(", ".join(top_features[1:])))
    parts.append("Severity {}".format(severity))
    return ". ".join(parts)


def detect_iforest(window_hours: int = 24, contamination: float = 0.1, department: str | None = None) -> Dict:
    pivot = _load_anomaly_dataset(window_hours)
    if pivot.empty or len(pivot) < 10:
        return {"count": 0, "anomalies": [], "message": "Insufficient data"}
    features = pivot[["cpu_pct", "mem_pct", "load_avg", "daily_cost"]].fillna(0.0)
    model = IsolationForest(contamination=contamination, random_state=42)
    model.fit(features)
    scores = model.decision_function(features)
    labels = model.predict(features)
    pivot["anomaly_score"] = scores
    pivot["is_anomaly"] = labels
    anomalies = pivot[pivot["is_anomaly"] == -1]
    records: List[Dict] = []
    baseline = features.mean()
    base_q_critical, base_q_warning = np.quantile(scores, [0.05, 0.15])
    session = SessionLocal()
    try:
        threshold_configs = _load_threshold_configs(session)
        alerts: List[AnomalyAlert] = []
        for _, row in anomalies.iterrows():
            if department and row["department"] != department:
                continue
            diffs = row[["cpu_pct", "mem_pct", "load_avg", "daily_cost"]] - baseline
            ordered = diffs.abs().sort_values(ascending=False)
            top_features = list(ordered.index[:3])
            contributions = {}
            for name in ordered.index:
                v = float(diffs[name])
                if np.isnan(v):
                    v = 0.0
                contributions[name] = v
            dept = row["department"]
            config_key = dept if dept in threshold_configs else "__global__"
            config = threshold_configs.get(config_key)
            q_critical = base_q_critical
            q_warning = base_q_warning
            if config and config.method == "quantile":
                q_critical = np.quantile(scores, max(0.0, min(config.value, 0.5)))
                q_warning = np.quantile(scores, min(0.9, q_critical + 0.1))
            score = float(row["anomaly_score"])
            severity = "low"
            if score <= q_critical:
                severity = "high"
            elif score <= q_warning:
                severity = "moderate"
            explanation = _build_iforest_explanation(row, top_features, contributions, severity)
            cpu = 0.0 if pd.isna(row["cpu_pct"]) else float(row["cpu_pct"])
            mem = 0.0 if pd.isna(row["mem_pct"]) else float(row["mem_pct"])
            load = 0.0 if pd.isna(row["load_avg"]) else float(row["load_avg"])
            cost = 0.0 if pd.isna(row["daily_cost"]) else float(row["daily_cost"])
            score_safe = 0.0 if np.isnan(score) else float(score)
            record = {
                "department": row["department"],
                "resource_id": row["resource_id"],
                "timestamp": row["timestamp"].isoformat(),
                "cpu_pct": cpu,
                "mem_pct": mem,
                "load_avg": load,
                "daily_cost": cost,
                "anomaly_score": score_safe,
                "severity": severity,
                "top_features": top_features,
                "feature_contributions": contributions,
                "explanation": explanation,
            }
            records.append(record)
            if severity in ["high", "moderate"]:
                alert_payload = {
                    "department": record["department"],
                    "resource_id": record["resource_id"],
                    "metric": "daily_cost",
                    "severity": severity,
                    "message": explanation,
                    "timestamp": record["timestamp"],
                    "daily_cost": record["daily_cost"],
                }
                delivered = _send_alert_notification(alert_payload)
                delivered_via = "webhook" if delivered else "none"
                alert = AnomalyAlert(
                    department=record["department"],
                    resource_id=record["resource_id"],
                    metric="daily_cost",
                    severity=severity,
                    message=explanation,
                    payload=record,
                    delivered_via=delivered_via,
                    status="delivered" if delivered else "created",
                )
                alerts.append(alert)
        if alerts:
            for a in alerts:
                session.add(a)
            session.commit()
    finally:
        session.close()
    return {"count": len(records), "anomalies": records}


def detect_autoencoder(window_hours: int = 24, contamination: float = 0.1) -> Dict:
    pivot = _load_anomaly_dataset(window_hours)
    if pivot.empty or len(pivot) < 10:
        return {"count": 0, "anomalies": [], "message": "Insufficient data"}
    features = pivot[["cpu_pct", "mem_pct", "load_avg", "daily_cost"]].fillna(0.0)
    model = MLPRegressor(hidden_layer_sizes=(8, 4, 8), activation="relu", max_iter=500, random_state=42)
    model.fit(features, features)
    recon = model.predict(features)
    recon_error = np.mean((features.values - recon) ** 2, axis=1)
    threshold = np.quantile(recon_error, 1 - contamination)
    pivot["recon_error"] = recon_error
    anomalies = pivot[pivot["recon_error"] >= threshold]
    records: List[Dict] = []
    for _, row in anomalies.iterrows():
        records.append(
            {
                "department": row["department"],
                "resource_id": row["resource_id"],
                "timestamp": row["timestamp"].isoformat(),
                "cpu_pct": float(row["cpu_pct"]),
                "mem_pct": float(row["mem_pct"]),
                "load_avg": float(row["load_avg"]),
                "daily_cost": float(row["daily_cost"]),
                "reconstruction_error": float(row["recon_error"]),
            }
        )
    return {"count": len(records), "anomalies": records}


def evaluate_iforest_vs_threshold(window_hours: int = 24, z: float = 2.0) -> Dict:
    pivot = _load_anomaly_dataset(window_hours)
    if pivot.empty or len(pivot) < 10:
        return {"message": "Insufficient data", "precision": 0.0, "recall": 0.0, "f1": 0.0}
    features = pivot[["cpu_pct", "mem_pct", "load_avg", "daily_cost"]].fillna(0.0)
    cost = features["daily_cost"]
    mean = cost.mean()
    std = cost.std() or 1.0
    threshold = mean + z * std
    true_labels = (cost >= threshold).astype(int)
    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(features)
    preds = (model.predict(features) == -1).astype(int)
    tp = int(((preds == 1) & (true_labels == 1)).sum())
    fp = int(((preds == 1) & (true_labels == 0)).sum())
    fn = int(((preds == 0) & (true_labels == 1)).sum())
    tn = int(((preds == 0) & (true_labels == 0)).sum())
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
    result = {
        "window_hours": window_hours,
        "z_score_threshold": float(threshold),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "accuracy": round(accuracy, 3),
    }
    session = SessionLocal()
    try:
        run = AnomalyModelRun(
            model_name="iforest_vs_z",
            window_hours=window_hours,
            z_score=float(z),
            tp=tp,
            fp=fp,
            fn=fn,
            tn=tn,
            precision=result["precision"],
            recall=result["recall"],
            f1=result["f1"],
            accuracy=result["accuracy"],
        )
        session.add(run)
        session.commit()
    finally:
        session.close()
    return result


def detect_iforest_seasonal(window_days: int = 60, contamination: float = 0.1) -> Dict:
    window_hours = window_days * 24
    pivot = _load_anomaly_dataset(window_hours)
    if pivot.empty or len(pivot) < 10:
        return {"count": 0, "anomalies": [], "message": "Insufficient data"}
    df = pivot.copy()
    df["hour"] = df["timestamp"].dt.hour
    df["dow"] = df["timestamp"].dt.dayofweek
    metrics = ["cpu_pct", "mem_pct", "load_avg", "daily_cost"]
    for m in metrics:
        key = m + "_baseline"
        baseline = df.groupby(["dow", "hour"])[m].transform("mean")
        df[key] = baseline
        df[m + "_residual"] = df[m] - baseline
    feature_cols = [m + "_residual" for m in metrics]
    features = df[feature_cols].fillna(0.0)
    model = IsolationForest(contamination=contamination, random_state=42)
    model.fit(features)
    scores = model.decision_function(features)
    labels = model.predict(features)
    df["anomaly_score"] = scores
    df["is_anomaly"] = labels
    anomalies = df[df["is_anomaly"] == -1]
    records: List[Dict] = []
    base_q_critical, base_q_warning = np.quantile(scores, [0.05, 0.15])
    for _, row in anomalies.iterrows():
        diffs = {m: float(row[m + "_residual"]) for m in metrics}
        ordered = sorted(diffs.items(), key=lambda x: abs(x[1]), reverse=True)
        top_features = [name for name, _ in ordered[:3]]
        score = float(row["anomaly_score"])
        severity = "low"
        if score <= base_q_critical:
            severity = "high"
        elif score <= base_q_warning:
            severity = "moderate"
        explanation = _build_iforest_explanation(row, top_features, diffs, severity)
        baseline_values = {m: float(row[m + "_baseline"]) for m in metrics}
        record = {
            "department": row["department"],
            "resource_id": row["resource_id"],
            "timestamp": row["timestamp"].isoformat(),
            "cpu_pct": float(row["cpu_pct"]),
            "mem_pct": float(row["mem_pct"]),
            "load_avg": float(row["load_avg"]),
            "daily_cost": float(row["daily_cost"]),
            "anomaly_score": score,
            "severity": severity,
            "top_features": top_features,
            "feature_contributions": diffs,
            "seasonal_baseline": baseline_values,
            "explanation": explanation,
        }
        records.append(record)
    return {"count": len(records), "anomalies": records}
