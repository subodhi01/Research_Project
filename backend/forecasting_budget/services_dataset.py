from datetime import datetime, timedelta
from typing import Dict, Optional
import os

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA


# ============================================================
# 📊 CSV DATASET LOCATION
# ============================================================
# Dataset file: backend/forecasting_budget/Cloud Budget Dataset/cloud_budget_2023_dataset.csv
# This CSV contains historical cost data used for forecasting
# Columns: date, net_cost, department, account_id, environment
# ============================================================
DATA_PATH = os.path.join(
    os.path.dirname(__file__),
    "Cloud Budget Dataset",
    "cloud_budget_2023_dataset.csv",
)


def _load_budget_dataframe() -> pd.DataFrame:
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame()
    df = pd.read_csv(DATA_PATH)
    if "date" not in df.columns or "net_cost" not in df.columns:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    return df


def load_budget_series(
    department: Optional[str] = None,
    account_id: Optional[str] = None,
    environment: Optional[str] = None,
) -> pd.Series:
    df = _load_budget_dataframe()
    if df.empty:
        return pd.Series(dtype=float)
    if department is not None:
        df = df[df["department"] == department]
    if account_id is not None:
        df = df[df["account_id"] == account_id]
    if environment is not None:
        df = df[df["environment"] == environment]
    if df.empty:
        return pd.Series(dtype=float)
    df = df.copy()
    df["net_cost"] = pd.to_numeric(df["net_cost"], errors="coerce").fillna(0.0)
    daily = df.groupby("date")["net_cost"].sum().sort_index()
    series = daily.copy()
    series.index = pd.to_datetime(series.index)
    series = series.asfreq("D").fillna(0.0)
    return series


def arima_forecast_cost_dataset(
    horizon_days: int = 30,
    department: Optional[str] = None,
    account_id: Optional[str] = None,
    environment: Optional[str] = None,
) -> Dict:
    series = load_budget_series(
        department=department,
        account_id=account_id,
        environment=environment,
    )
    if len(series) < 10:
        return {
            "run_id": None,
            "mae": 0.0,
            "rmse": 0.0,
            "mape": 0.0,
            "history": [],
            "forecast": [],
            "message": "Insufficient budget cost history for forecasting.",
        }
    
    # ============================================================
    # ⭐ ARIMA MODEL TRAINING (CSV DATASET) ⭐
    # ============================================================
    # This function trains ARIMA on CSV dataset instead of database
    # Dataset location: backend/forecasting_budget/Cloud Budget Dataset/cloud_budget_2023_dataset.csv
    
    # Step 1: Split data into training and test sets
    train = series.iloc[:-7]  # Training data (all but last 7 days)
    test = series.iloc[-7:]   # Test data (last 7 days for validation)
    
    # Step 2: Create ARIMA(1,1,1) model
    model = ARIMA(train, order=(1, 1, 1))
    
    # Step 3: ⭐ TRAIN THE MODEL ⭐
    # Trains on CSV dataset data (historical costs from CSV file)
    fitted = model.fit()  # ⭐ TRAINING HAPPENS HERE
    forecast = fitted.forecast(steps=horizon_days)
    forecast_index = forecast.index
    if len(test) > 0:
        aligned = forecast.reindex(test.index, method="nearest")
        y_true = test.values.astype(float)
        y_pred = aligned.values.astype(float)
        mae = float(np.mean(np.abs(y_true - y_pred)))
        rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
        denom = np.maximum(np.abs(y_true), 1e-6)
        mape = float(np.mean(np.abs((y_true - y_pred) / denom)) * 100.0)
    else:
        mae = 0.0
        rmse = 0.0
        mape = 0.0
    history = [
        {"timestamp": ts.isoformat(), "value": float(v)}
        for ts, v in series.iloc[-90:].items()
    ]
    predictions = [
        {"timestamp": ts.isoformat(), "value": float(v)}
        for ts, v in zip(forecast_index, forecast.values)
    ]
    return {
        "run_id": None,
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "history": history,
        "forecast": predictions,
    }


def compare_forecast_to_budget_dataset(
    monthly_budget: float,
    forecast_days: int = 30,
    department: Optional[str] = None,
    account_id: Optional[str] = None,
    environment: Optional[str] = None,
) -> Dict:
    result = arima_forecast_cost_dataset(
        horizon_days=forecast_days,
        department=department,
        account_id=account_id,
        environment=environment,
    )
    if not result.get("forecast"):
        return {
            "metrics": {"mae": 0.0, "rmse": 0.0, "mape": 0.0},
            "budget": monthly_budget,
            "projected_total": 0.0,
            "delta": -monthly_budget,
            "status": "under_budget",
            "message": result.get("message", "No forecast available"),
        }
    values = [p["value"] for p in result["forecast"]]
    projected_total = float(np.sum(values))
    delta = projected_total - monthly_budget
    status = "on_track"
    if delta > 0.05 * monthly_budget:
        status = "over_budget_risk"
    elif delta < -0.05 * monthly_budget:
        status = "under_budget"
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
    }


def estimate_company_budget_profile(
    num_departments: int,
    num_users: int,
    environment: Optional[str] = "prod",
) -> Dict:
    df = _load_budget_dataframe()
    if df.empty:
        return {
            "recommended_monthly_budget": 0.0,
            "baseline_monthly_budget": 0.0,
            "scale_factor_departments": 0.0,
            "num_departments": num_departments,
            "num_users": num_users,
            "per_department": [],
        }
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["net_cost"] = pd.to_numeric(df["net_cost"], errors="coerce").fillna(0.0)
    if environment is not None:
        df_env = df[df["environment"] == environment]
        if df_env.empty:
            df_env = df
    else:
        df_env = df
    if df_env.empty:
        return {
            "recommended_monthly_budget": 0.0,
            "baseline_monthly_budget": 0.0,
            "scale_factor_departments": 0.0,
            "num_departments": num_departments,
            "num_users": num_users,
            "per_department": [],
        }
    df_env["month"] = df_env["date"].dt.to_period("M")
    monthly_total = df_env.groupby("month")["net_cost"].sum()
    if monthly_total.empty:
        return {
            "recommended_monthly_budget": 0.0,
            "baseline_monthly_budget": 0.0,
            "scale_factor_departments": 0.0,
            "num_departments": num_departments,
            "num_users": num_users,
            "per_department": [],
        }
    baseline_monthly = float(monthly_total.mean())
    baseline_departments = df_env["department"].nunique()
    if baseline_departments <= 0:
        scale_departments = 0.0
    else:
        scale_departments = float(num_departments) / float(baseline_departments)
    if scale_departments < 0.0:
        scale_departments = 0.0
    recommended_monthly = baseline_monthly * scale_departments
    dept_monthly = (
        df_env.groupby(["month", "department"])["net_cost"].sum().reset_index()
    )
    dept_avg = dept_monthly.groupby("department")["net_cost"].mean()
    total_dept_avg = float(dept_avg.sum()) if not dept_avg.empty else 0.0
    per_department: List[Dict] = []
    if total_dept_avg > 0.0:
        for dept, value in dept_avg.items():
            share = float(value) / total_dept_avg
            per_department.append(
                {
                    "department": str(dept),
                    "recommended_monthly_budget": recommended_monthly * share,
                    "baseline_monthly_budget": baseline_monthly * share,
                    "share": share,
                }
            )
    return {
        "recommended_monthly_budget": recommended_monthly,
        "baseline_monthly_budget": baseline_monthly,
        "scale_factor_departments": scale_departments,
        "num_departments": num_departments,
        "num_users": num_users,
        "environment": environment,
        "per_department": per_department,
    }
