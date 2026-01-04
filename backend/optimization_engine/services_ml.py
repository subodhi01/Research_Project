from datetime import datetime, timedelta
from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from ..database import SessionLocal
from ..models import CloudUsage, OptimizationModelRun
from ..services_monitor import DEPARTMENTS


def compute_ml_scores_for_departments(window_minutes: int = 60) -> Dict[str, Dict]:
    session = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        records = session.query(CloudUsage).filter(
            CloudUsage.provider == "vps",
            CloudUsage.metric.in_(["cpu_pct", "mem_pct", "load_avg"]),
            CloudUsage.timestamp >= cutoff,
        ).order_by(CloudUsage.timestamp).all()
    finally:
        session.close()

    if not records:
        return {d: {"score": 0.0, "risk": "unknown"} for d in DEPARTMENTS}

    rows = []
    for r in records:
        rows.append(
            {
                "department": r.account_id,
                "resource_id": r.resource_id,
                "metric": r.metric,
                "timestamp": r.timestamp,
                "value": r.value,
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return {d: {"score": 0.0, "risk": "unknown"} for d in DEPARTMENTS}
    pivot = df.pivot_table(
        index=["department", "timestamp"],
        columns="metric",
        values="value",
        aggfunc="mean",
    ).reset_index()
    features = pivot[["cpu_pct", "mem_pct", "load_avg"]].fillna(0.0)
    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(features)
    scores = model.decision_function(features)
    pivot["anomaly_score"] = scores
    result: Dict[str, Dict] = {}
    for dept in DEPARTMENTS:
        dept_rows = pivot[pivot["department"] == dept]
        if dept_rows.empty:
            result[dept] = {"score": 0.0, "risk": "unknown"}
        else:
            mean_score = float(dept_rows["anomaly_score"].mean())
            if mean_score < -0.1:
                risk = "high"
            elif mean_score < 0.0:
                risk = "moderate"
            else:
                risk = "low"
            result[dept] = {"score": mean_score, "risk": risk}
    return result


def retrain_department_scores(window_minutes: int = 60) -> Dict:
    scores = compute_ml_scores_for_departments(window_minutes=window_minutes)
    session = SessionLocal()
    try:
        run = OptimizationModelRun(
            model_name="department_iforest",
            window_minutes=window_minutes,
            provider="vps",
        )
        session.add(run)
        session.commit()
    finally:
        session.close()
    return {"window_minutes": window_minutes, "scores": scores}


def rank_recommendations_with_ml(
    ml_scores: Dict[str, Dict],
    department_recommendations: Dict[str, List[Dict]],
    department_monitors: Dict[str, Dict],
) -> Dict[str, Dict]:
    out: Dict[str, Dict] = {}
    for dept, recs in department_recommendations.items():
        score_info = ml_scores.get(dept, {"score": 0.0, "risk": "unknown"})
        base_score = score_info["score"]
        scored_recs = []
        for r in recs:
            if isinstance(r, dict):
                data = r
            else:
                saving = float(getattr(r, "estimated_monthly_saving", 0.0) or 0.0)
                action = getattr(r, "action", "")
                if action in ["Downsize", "Upsize"]:
                    rec_type = "rightsizing"
                else:
                    rec_type = "other"
                if saving < 0:
                    risk = "high"
                elif saving > 50:
                    risk = "medium"
                else:
                    risk = "low"
                data = {
                    "id": getattr(r, "id", None),
                    "provider": getattr(r, "provider", None),
                    "account_id": getattr(r, "account_id", None),
                    "resource_id": getattr(r, "resource_id", None),
                    "current_type": getattr(r, "current_type", None),
                    "recommended_type": getattr(r, "recommended_type", None),
                    "action": action,
                    "reason": getattr(r, "reason", None),
                    "estimated_monthly_saving": saving,
                    "status": getattr(r, "status", None),
                    "type": rec_type,
                    "risk": risk,
                }
            priority = 0.0
            if data.get("type") == "rightsizing":
                priority += 0.3
            if data.get("type") == "shutdown":
                priority += 0.4
            if data.get("risk") == "high":
                priority += 0.3
            elif data.get("risk") == "medium":
                priority += 0.15
            combined = float(base_score) - priority
            scored_recs.append({**data, "ml_score": combined})
        scored_recs.sort(key=lambda x: x["ml_score"])
        out[dept] = {
            "ml_risk": score_info,
            "recommendations": scored_recs,
            "monitor": department_monitors.get(dept, {}),
        }
    return out
