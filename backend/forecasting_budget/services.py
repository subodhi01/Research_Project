"""
FORECAST BUDGET SERVICES
========================
This file contains the core business logic for forecast and budget calculations.

CONNECTION FLOW:
1. Called from: backend/routers/forecast.py (API endpoints)
2. Uses: database.py (SessionLocal), models.py (CloudUsage, ForecastRun, etc.)
3. Uses: aws_client.py (fetch_aws_costs), services_monitor.py (DEPARTMENTS)
4. Uses: pandas, numpy, statsmodels (ARIMA), sklearn (error metrics)

DATA FLOW:
API Endpoint → Service Function → Database/External API → Process Data → Return Results
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
import json
from urllib import request as urlrequest

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.arima.model import ARIMA

from ..database import SessionLocal
from ..models import CloudUsage, ForecastRun, Department, BudgetAlert
from ..aws_client import fetch_aws_costs
from ..services_monitor import DEPARTMENTS, DEPARTMENT_ALLOCATIONS


COST_RATE_PER_CPU_PCT_DAY = 0.05  # Cost per 1% CPU usage per day


def ingest_vps_daily_costs_to_db(days: int = 60, vms: List[str] | None = None) -> List[Dict]:
    """
    INGEST VPS DAILY COSTS TO DATABASE
    ===================================
    
    CALLED FROM:
    - backend/routers/forecast.py -> ingest_vps_costs() endpoint
    - Frontend: ForecastPanel.jsx (line 27) -> ingestVps() -> POST /api/forecast/ingest/vps
    
    WHAT IT DOES:
    1. Reads CPU usage data from CloudUsage table (metric="cpu_pct")
    2. Groups by date and calculates average CPU per day
    3. Converts CPU % to daily cost: Cost = Average CPU % × 0.05
    4. Stores daily costs in CloudUsage table (metric="daily_cost")
    
    CONNECTS TO:
    - Reads from: database.models.CloudUsage (cpu_pct metric)
    - Writes to: database.models.CloudUsage (daily_cost metric)
    - Uses: database.SessionLocal (database connection)
    
    MATH:
    - Daily Cost = max(Average CPU %, 0) × COST_RATE_PER_CPU_PCT_DAY
    - Example: 50% CPU = 50 × 0.05 = $2.50/day
    
    RETURNS: List of {"date": str, "avg_cpu_pct": float, "cost": float}
    """
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=days)
    session = SessionLocal()
    session.query(CloudUsage).filter(CloudUsage.provider == "vps", CloudUsage.metric == "daily_cost").delete()
    try:
        records = (
            session.query(CloudUsage)
            .filter(
                CloudUsage.provider == "vps",
                CloudUsage.metric == "cpu_pct",
                CloudUsage.timestamp >= start_dt,
            )
            .order_by(CloudUsage.timestamp)
            .all()
        )
        if not records:
            session.commit()
            return []
        rows = []
        for r in records:
            rows.append(
                {
                    "department": r.account_id,
                    "timestamp": r.timestamp,
                    "cpu_pct": r.value,
                }
            )
        df = pd.DataFrame(rows)
        df["date"] = df["timestamp"].dt.date
        daily_cpu = df.groupby("date")["cpu_pct"].mean()
        results: List[Dict] = []
        for day, avg_cpu in daily_cpu.items():
            total_cost = float(max(avg_cpu, 0.0) * COST_RATE_PER_CPU_PCT_DAY)
            usage = CloudUsage(
                provider="vps",
                account_id="global",
                resource_id="vps-cost",
                resource_type="vps",
                metric="daily_cost",
                timestamp=datetime.combine(day, datetime.min.time()),
                value=total_cost,
                cost=total_cost,
            )
            session.add(usage)
            results.append({"date": str(day), "avg_cpu_pct": float(avg_cpu), "cost": total_cost})
        session.commit()
        return results
    finally:
        session.close()


def ingest_aws_daily_costs_to_db(days: int = 60) -> List[Dict]:
    """
    INGEST AWS DAILY COSTS TO DATABASE
    ==================================
    
    CALLED FROM:
    - backend/routers/forecast.py -> ingest_aws_costs() endpoint
    - Frontend: ForecastPanel.jsx (line 28) -> ingestAws() -> POST /api/forecast/ingest/aws
    
    WHAT IT DOES:
    1. Fetches AWS costs from AWS Cost Explorer API
    2. Stores daily AWS costs per service in database
    
    CONNECTS TO:
    - Calls: aws_client.fetch_aws_costs() (AWS Cost Explorer API)
    - Writes to: database.models.CloudUsage (daily_cost metric, provider="aws")
    - Uses: database.SessionLocal (database connection)
    
    RETURNS: List of {"date": str, "service": str, "cost": float}
    """
    end_dt = datetime.utcnow().date()
    start_dt = end_dt - timedelta(days=days)
    rows = fetch_aws_costs(
        start_date=datetime.combine(start_dt, datetime.min.time()),
        end_date=datetime.combine(end_dt + timedelta(days=1), datetime.min.time()),
    )
    if not rows:
        return []
    session = SessionLocal()
    session.query(CloudUsage).filter(CloudUsage.provider == "aws", CloudUsage.metric == "daily_cost").delete()
    try:
        out: List[Dict] = []
        for r in rows:
            ts = datetime.strptime(r["date"], "%Y-%m-%d")
            usage = CloudUsage(
                provider="aws",
                account_id="aws",
                resource_id=r["service"],
                resource_type="service",
                metric="daily_cost",
                timestamp=ts,
                value=r["cost"],
                cost=r["cost"],
            )
            session.add(usage)
            out.append(
                {
                    "date": r["date"],
                    "service": r["service"],
                    "cost": float(r["cost"]),
                }
            )
        session.commit()
        return out
    finally:
        session.close()


def load_cost_series_from_db(provider: str = "vps", scope: Optional[str] = None) -> pd.Series:
    """
    LOAD COST SERIES FROM DATABASE
    ==============================
    
    CALLED FROM:
    - arima_forecast_cost() (line 136)
    - workload_aware_forecast() (line 320)
    - multi_cloud_cost_trends() (line 467)
    
    WHAT IT DOES:
    1. Queries database for daily costs (metric="daily_cost")
    2. Groups by date and sums costs (in case multiple records per day)
    3. Creates pandas Series with dates as index and costs as values
    4. Fills missing days with forward fill
    
    CONNECTS TO:
    - Reads from: database.models.CloudUsage (daily_cost metric)
    - Uses: database.SessionLocal (database connection)
    - Returns: pandas.Series (date-indexed cost values)
    
    RETURNS: pandas.Series with dates as index and costs as values
    """
    session = SessionLocal()
    try:
        q = (
            session.query(CloudUsage)
            .filter(CloudUsage.provider == provider, CloudUsage.metric == "daily_cost")
            .order_by(CloudUsage.timestamp)
        )
        records = q.all()
    finally:
        session.close()
    if not records:
        return pd.Series(dtype=float)
    dates = [r.timestamp for r in records]
    values = [r.value for r in records]
    df = pd.DataFrame({"timestamp": pd.to_datetime(dates), "value": values})
    daily = df.groupby(df["timestamp"].dt.date)["value"].sum()  # Sum costs per day
    s = daily.copy()
    s.index = pd.to_datetime(s.index)
    s = s.asfreq("D").ffill()  # Fill missing days with forward fill
    return s


def arima_forecast_cost(horizon_days: int = 30, provider: str = "vps"):
    """
    ARIMA FORECAST COST
    ===================
    
    CALLED FROM:
    - backend/routers/forecast.py -> usage_forecast() endpoint
    - compare_forecast_to_budget() (line 196)
    - department_cost_forecast() (line 477)
    - Frontend: ForecastPanel.jsx -> getUsageForecast() -> GET /api/forecast/usage
    
    WHAT IT DOES:
    1. Loads historical cost data from database
    2. Splits into training (all but last 7 days) and test (last 7 days)
    3. Fits ARIMA(1,1,1) model on training data
    4. Forecasts next N days
    5. Calculates accuracy metrics (MAE, RMSE, MAPE) using test data
    6. Saves forecast run to database
    
    CONNECTS TO:
    - Calls: load_cost_series_from_db() (loads cost data)
    - Uses: statsmodels.tsa.arima.model.ARIMA (time series model)
    - Uses: sklearn.metrics (error calculations)
    - Writes to: database.models.ForecastRun (saves forecast results)
    
    MATH:
    - ARIMA(1,1,1) model: y(t) = c + φ₁×y(t-1) + θ₁×ε(t-1) + ε(t)
    - MAE = mean(|actual - predicted|)
    - RMSE = sqrt(mean((actual - predicted)²))
    - MAPE = mean(|(actual - predicted) / actual|) × 100%
    
    RETURNS: {
        "run_id": int,
        "mae": float,
        "rmse": float,
        "mape": float,
        "history": [{"timestamp": str, "value": float}],  # Last 90 days
        "forecast": [{"timestamp": str, "value": float}]   # Next N days
    }
    """
    series = load_cost_series_from_db(provider=provider)  # Load cost data from database
    if len(series) < 10:
        return {
            "run_id": None,
            "mae": 0.0,
            "rmse": 0.0,
            "mape": 0.0,
            "history": [],
            "forecast": [],
            "message": "Insufficient cost history for forecasting.",
        }
    train = series.iloc[:-7]  # Training data (all but last 7 days)
    test = series.iloc[-7:]   # Test data (last 7 days for validation)
    model = ARIMA(train, order=(1, 1, 1))  # ARIMA model: AR(1), I(1), MA(1)
    fitted = model.fit()  # Fit model to training data
    forecast = fitted.forecast(steps=horizon_days)
    forecast_index = forecast.index
    if len(test) > 0:
        aligned_forecast = forecast.reindex(test.index, method="nearest")
        mae = float(mean_absolute_error(test.values, aligned_forecast.values))
        rmse = float(mean_squared_error(test.values, aligned_forecast.values) ** 0.5)
        mape = float(np.mean(np.abs((test.values - aligned_forecast.values) / np.maximum(test.values, 1e-6))) * 100.0)
    else:
        mae = 0.0
        rmse = 0.0
        mape = 0.0
    predictions = []
    for ts, val in zip(forecast_index, forecast.values):
        predictions.append({"timestamp": ts.isoformat(), "value": float(val)})
    session = SessionLocal()
    try:
        run = ForecastRun(
            provider=provider,
            scope="total_daily_cost",
            model_type="arima",
            mae=mae,
            rmse=rmse,
            mape=mape,
            horizon_hours=horizon_days * 24,
            input_points=len(series),
            predictions=predictions,
        )
        session.add(run)
        session.commit()
        run_id = run.id
    finally:
        session.close()
    return {
        "run_id": run_id,
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "history": [
            {"timestamp": ts.isoformat(), "value": float(v)} for ts, v in series.iloc[-90:].items()
        ],
        "forecast": predictions,
    }


def compare_forecast_to_budget(monthly_budget: float, forecast_days: int = 30, provider: str = "vps"):
    """
    COMPARE FORECAST TO BUDGET
    ===========================
    
    CALLED FROM:
    - backend/routers/forecast.py -> budget_vs_forecast() endpoint
    - compute_budget_allocation() (line 394)
    - scenario_planning() (line 453)
    - Frontend: ForecastPanel.jsx -> getBudgetVsForecast() -> GET /api/forecast/budget
    
    WHAT IT DOES:
    1. Gets forecast for next N days
    2. Sums forecasted costs to get projected total
    3. Calculates delta (projected - budget)
    4. Determines status based on delta threshold (5% of budget)
    
    CONNECTS TO:
    - Calls: arima_forecast_cost() (gets forecast)
    
    MATH:
    - Projected Total = sum(forecasted costs for next N days)
    - Delta = Projected Total - Monthly Budget
    - Status:
      - "over_budget_risk" if delta > 5% of budget
      - "under_budget" if delta < -5% of budget
      - "on_track" otherwise
    
    RETURNS: {
        "metrics": {"mae": float, "rmse": float, "mape": float},
        "budget": float,
        "projected_total": float,
        "delta": float,
        "status": str  # "on_track" | "over_budget_risk" | "under_budget"
    }
    """
    result = arima_forecast_cost(horizon_days=forecast_days, provider=provider)  # Get forecast
    if not result.get("forecast"):
        return {
            "metrics": {"mae": 0.0, "rmse": 0.0, "mape": 0.0},
            "budget": monthly_budget,
            "projected_total": 0.0,
            "delta": -monthly_budget,
            "status": "under_budget",
            "utilization_target": 0.75,
            "message": result.get("message", "No forecast available"),
        }
    forecast_values = [p["value"] for p in result["forecast"]]
    projected_total = float(np.sum(forecast_values))  # Sum all forecasted costs
    delta = projected_total - monthly_budget  # Calculate difference
    status = "on_track"
    if delta > 0.05 * monthly_budget:  # More than 5% over budget
        status = "over_budget_risk"
    elif delta < -0.05 * monthly_budget:  # More than 5% under budget
        status = "under_budget"
    utilization_target = 0.75
    return {
        "metrics": {
            "mae": result["mae"],
            "rmse": result["rmse"],
            "mape": result["mape"],
        },
        "budget": monthly_budget,
        "projected_total": projected_total,
        "delta": delta,
        "status": status,
        "utilization_target": utilization_target,
    }


def analyze_utilization(window_hours: int = 24, provider: str = "vps") -> List[Dict]:
    cutoff = datetime.utcnow() - timedelta(hours=window_hours)
    session = SessionLocal()
    try:
        records = (
            session.query(CloudUsage)
            .filter(
                CloudUsage.provider == provider,
                CloudUsage.metric.in_(["cpu_pct", "mem_pct"]),
                CloudUsage.timestamp >= cutoff,
            )
            .order_by(CloudUsage.timestamp)
            .all()
        )
    finally:
        session.close()
    if not records:
        return []
    rows = []
    for r in records:
        rows.append(
            {
                "resource_id": r.resource_id,
                "metric": r.metric,
                "timestamp": r.timestamp,
                "value": r.value,
            }
        )
    df = pd.DataFrame(rows)
    pivot = df.pivot_table(
        index=["resource_id"],
        columns="metric",
        values="value",
        aggfunc="mean",
    ).reset_index()
    out: List[Dict] = []
    for _, row in pivot.iterrows():
        cpu = float(row.get("cpu_pct", 0.0) or 0.0)
        mem = float(row.get("mem_pct", 0.0) or 0.0)
        score = (cpu + mem) / 2.0
        if score < 20:
            status = "idle"
        elif score < 50:
            status = "underutilized"
        elif score < 80:
            status = "balanced"
        else:
            status = "overutilized"
        out.append(
            {
                "resource_id": row["resource_id"],
                "avg_cpu": cpu,
                "avg_mem": mem,
                "utilization_score": score,
                "status": status,
            }
        )
    return out


def list_forecast_runs(limit: int = 20, provider: str = "vps") -> List[Dict]:
    session = SessionLocal()
    try:
        rows = (
            session.query(ForecastRun)
            .filter(ForecastRun.provider == provider)
            .order_by(ForecastRun.created_at.desc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()
    out: List[Dict] = []
    for r in rows:
        out.append(
            {
                "id": r.id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "model_type": r.model_type,
                "mae": r.mae,
                "rmse": r.rmse,
                "mape": r.mape,
                "horizon_hours": r.horizon_hours,
                "input_points": r.input_points,
            }
        )
    return out


def workload_aware_forecast(horizon_days: int = 30, provider: str = "vps"):
    series = load_cost_series_from_db(provider=provider)
    if len(series) < 10:
        return {
            "run_id": None,
            "mae": 0.0,
            "rmse": 0.0,
            "mape": 0.0,
            "history": [],
            "forecast": [],
            "message": "Insufficient cost history for workload-aware forecasting.",
        }
    df = series.to_frame(name="cost")
    df["dow"] = df.index.dayofweek
    df["day"] = df.index.day
    exog = pd.get_dummies(df[["dow"]], prefix="dow", drop_first=True)
    train = df.iloc[:-7]
    test = df.iloc[-7:]
    exog_train = exog.iloc[:-7]
    exog_test = exog.iloc[-7:]
    model = ARIMA(train["cost"], order=(1, 1, 1), exog=exog_train)
    fitted = model.fit()
    future_exog = exog.iloc[-1:]
    for _ in range(horizon_days - 1):
        future_exog = pd.concat([future_exog, future_exog.iloc[-1:]], ignore_index=True)
    forecast = fitted.forecast(steps=horizon_days, exog=future_exog)
    forecast_index = pd.date_range(
        start=series.index[-1] + timedelta(days=1),
        periods=horizon_days,
        freq="D",
    )
    forecast.index = forecast_index
    if len(test) > 0:
        aligned_forecast = forecast.reindex(test.index, method="nearest")
        mae = float(mean_absolute_error(test.values, aligned_forecast.values))
        rmse = float(mean_squared_error(test.values, aligned_forecast.values) ** 0.5)
        mape = float(np.mean(np.abs((test.values - aligned_forecast.values) / np.maximum(test.values, 1e-6))) * 100.0)
    else:
        mae = 0.0
        rmse = 0.0
        mape = 0.0
    predictions = []
    for ts, val in zip(forecast.index, forecast.values):
        predictions.append({"timestamp": ts.isoformat(), "value": float(val)})
    session = SessionLocal()
    try:
        run = ForecastRun(
            provider=provider,
            scope="total_daily_cost",
            model_type="arima_workload",
            mae=mae,
            rmse=rmse,
            mape=mape,
            horizon_hours=horizon_days * 24,
            input_points=len(series),
            predictions=predictions,
        )
        session.add(run)
        session.commit()
        run_id = run.id
    finally:
        session.close()
    return {
        "run_id": run_id,
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "history": [
            {"timestamp": ts.isoformat(), "value": float(v)} for ts, v in series.iloc[-90:].items()
        ],
        "forecast": predictions,
    }


def compute_budget_allocation(monthly_budget: float, forecast_days: int = 30) -> Dict:
    """
    COMPUTE BUDGET ALLOCATION
    =========================
    
    CALLED FROM:
    - backend/routers/forecast.py -> budget_allocation() endpoint
    - Frontend: ForecastPanel.jsx -> getBudgetAllocation() -> GET /api/forecast/budget/allocation
    
    WHAT IT DOES:
    1. Gets base forecast comparison
    2. Allocates budget across departments based on weights
    3. Calculates projected costs per department
    4. Creates budget alerts if departments are over/under budget
    5. Can send alerts via webhook if configured
    
    CONNECTS TO:
    - Calls: compare_forecast_to_budget() (gets base forecast)
    - Uses: services_monitor.DEPARTMENTS and DEPARTMENT_ALLOCATIONS (department weights)
    - Writes to: database.models.BudgetAlert (if over/under budget)
    - Uses: os.getenv("ALERT_WEBHOOK_URL") (optional webhook for alerts)
    
    MATH:
    - Total Weight = sum(all department weights)
    - Department Budget = Monthly Budget × (Department Weight / Total Weight)
    - Department Projected = Projected Total × (Department Weight / Total Weight)
    - Department Delta = Department Projected - Department Budget
    
    RETURNS: {
        "summary": {...},  # Base forecast comparison
        "allocations": [{  # Per department
            "department": str,
            "budget": float,
            "projected": float,
            "delta": float,
            "status": str
        }]
    }
    """
    base = compare_forecast_to_budget(monthly_budget=monthly_budget, forecast_days=forecast_days)  # Get base forecast
    if not DEPARTMENTS:
        return {"summary": base, "allocations": []}
    total_weight = sum(DEPARTMENT_ALLOCATIONS.get(d, 0.25) for d in DEPARTMENTS)  # Sum all weights
    allocations: List[Dict] = []
    alerts: List[BudgetAlert] = []
    webhook_url = os.getenv("ALERT_WEBHOOK_URL")
    session = SessionLocal()
    try:
        for dept in DEPARTMENTS:
            weight = DEPARTMENT_ALLOCATIONS.get(dept, 0.25)  # Get department weight
            # Allocate budget proportionally
            dept_budget = monthly_budget * weight / total_weight if total_weight > 0 else monthly_budget / len(DEPARTMENTS)
            # Allocate projected costs proportionally
            projected_share = base["projected_total"] * weight / total_weight if total_weight > 0 else base["projected_total"] / len(DEPARTMENTS)
            delta = projected_share - dept_budget  # Calculate department delta
            status = "on_track"
            if delta > 0.05 * dept_budget:  # More than 5% over budget
                status = "over_budget_risk"
            elif delta < -0.05 * dept_budget:  # More than 5% under budget
                status = "under_budget"
            payload = {
                "department": dept,
                "budget": dept_budget,
                "projected": projected_share,
                "delta": delta,
                "status": status,
            }
            allocations.append(payload)
            if status != "on_track":
                delivered_via = "none"
                if webhook_url:
                    data = json.dumps(payload).encode("utf-8")
                    req = urlrequest.Request(webhook_url, data=data, headers={"Content-Type": "application/json"})
                    try:
                        urlrequest.urlopen(req, timeout=5)
                        delivered_via = "webhook"
                    except Exception:
                        delivered_via = "none"
                alert = BudgetAlert(
                    department=dept,
                    provider="vps",
                    severity=status,
                    message="Budget status {}".format(status),
                    payload=payload,
                    delivered_via=delivered_via,
                    status="delivered" if delivered_via == "webhook" else "created",
                )
                alerts.append(alert)
        if alerts:
            for a in alerts:
                session.add(a)
            session.commit()
    finally:
        session.close()
    return {"summary": base, "allocations": allocations}


def scenario_planning(budgets: List[float], forecast_days: int = 30) -> List[Dict]:
    scenarios: List[Dict] = []
    for b in budgets:
        summary = compare_forecast_to_budget(monthly_budget=b, forecast_days=forecast_days)
        scenarios.append(
            {
                "budget": b,
                "projected_total": summary["projected_total"],
                "delta": summary["delta"],
                "status": summary["status"],
                "metrics": summary["metrics"],
            }
        )
    return scenarios


def multi_cloud_cost_trends(days: int = 60) -> Dict:
    vps_series = load_cost_series_from_db(provider="vps")
    aws_series = load_cost_series_from_db(provider="aws")
    vps_tail = vps_series.iloc[-days:] if len(vps_series) > days else vps_series
    aws_tail = aws_series.iloc[-days:] if len(aws_series) > days else aws_series
    vps = [{"timestamp": ts.isoformat(), "value": float(v)} for ts, v in vps_tail.items()]
    aws = [{"timestamp": ts.isoformat(), "value": float(v)} for ts, v in aws_tail.items()]
    return {"vps": vps, "aws": aws}


def department_cost_forecast(department: str, horizon_days: int = 30) -> Dict:
    base = arima_forecast_cost(horizon_days=horizon_days, provider="vps")
    if not base.get("forecast"):
        return base
    weight = DEPARTMENT_ALLOCATIONS.get(department, 0.25)
    scaled_forecast = []
    for p in base["forecast"]:
        scaled_forecast.append(
            {
                "timestamp": p["timestamp"],
                "value": p["value"] * weight,
            }
        )
    return {
        "run_id": base["run_id"],
        "mae": base["mae"],
        "rmse": base["rmse"],
        "mape": base["mape"],
        "history": base["history"],
        "forecast": scaled_forecast,
    }
