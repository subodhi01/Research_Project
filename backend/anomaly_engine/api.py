from fastapi import APIRouter, Query
from datetime import datetime, timedelta

from ..database import SessionLocal
from ..models import CloudUsage, AnomalyModelRun
from .services_ml import detect_iforest, detect_autoencoder, evaluate_iforest_vs_threshold
from .services_cloud_dataset import detect_cloud_dataset_anomalies

router = APIRouter(prefix="/api/anomaly", tags=["anomaly"])


@router.get("/detect")
async def detect_simple():
    session = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=30)
        records = session.query(CloudUsage).filter(
            CloudUsage.provider == "vps",
            CloudUsage.metric == "daily_cost",
            CloudUsage.timestamp >= cutoff,
        ).order_by(CloudUsage.timestamp).all()
    finally:
        session.close()
    if len(records) < 10:
        return {
            "count": 0,
            "anomalies": [],
            "message": "Insufficient data for anomaly detection. Need at least 10 data points.",
        }
    data = []
    values = []
    for r in records:
        data.append(
            {
                "transaction_id": r.id,
                "resource_id": r.resource_id,
                "timestamp": r.timestamp.isoformat(),
                "cost": r.cost,
            }
        )
        values.append(r.cost)
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / len(values)
    std = var ** 0.5 if var > 0 else 1.0
    threshold = mean + 3 * std
    anomalies = [d for d in data if d["cost"] >= threshold]
    for a in anomalies:
        a["root_cause"] = f"Cost spike detected in {a['resource_id']} with value {a['cost']:.2f}"
    return {"count": len(anomalies), "anomalies": anomalies, "threshold": threshold}


@router.get("/detect/cloud-dataset")
async def detect_cloud_dataset(window_hours: int = Query(24, ge=1, le=168), contamination: float = Query(0.1, gt=0.0, lt=0.5), limit: int = Query(100, ge=1, le=1000)):
    return detect_cloud_dataset_anomalies(contamination=contamination, limit=limit)


@router.get("/detect/iforest")
async def detect_iforest_api(
    window_hours: int = Query(24, ge=1, le=168),
    contamination: float = Query(0.1, gt=0.0, lt=0.5),
    department: str | None = Query(None),
):
    return detect_iforest(window_hours=window_hours, contamination=contamination, department=department)


@router.get("/detect/autoencoder")
async def detect_autoencoder_api(window_hours: int = Query(24, ge=1, le=168), contamination: float = Query(0.1, gt=0.0, lt=0.5)):
    return detect_autoencoder(window_hours=window_hours, contamination=contamination)


@router.get("/evaluate/iforest")
async def evaluate_iforest_api(window_hours: int = Query(24, ge=1, le=168), z: float = Query(2.0, gt=0.5, lt=5.0)):
    return evaluate_iforest_vs_threshold(window_hours=window_hours, z=z)


@router.get("/metrics/model-runs")
async def anomaly_model_runs(limit: int = Query(50, ge=1, le=500), model_name: str | None = Query(None)):
    session = SessionLocal()
    try:
        q = session.query(AnomalyModelRun).order_by(AnomalyModelRun.created_at.desc())
        if model_name:
            q = q.filter(AnomalyModelRun.model_name == model_name)
        rows = q.limit(limit).all()
    finally:
        session.close()
    items = []
    for r in rows:
        items.append(
            {
                "id": r.id,
                "model_name": r.model_name,
                "window_hours": r.window_hours,
                "z_score": r.z_score,
                "tp": r.tp,
                "fp": r.fp,
                "fn": r.fn,
                "tn": r.tn if hasattr(r, 'tn') else None,
                "precision": r.precision,
                "recall": r.recall,
                "f1": r.f1,
                "accuracy": r.accuracy if hasattr(r, 'accuracy') else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )
    return {"items": items}
