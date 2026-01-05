"""
FORECAST BUDGET API ROUTER
==========================
This file defines all FastAPI endpoints for the forecast budget system.

CONNECTION FLOW:
1. Registered in: backend/main.py (line 6, 33)
   - main.py imports: from .forecasting_budget import router as forecast
   - main.py registers: app.include_router(forecast)
   
2. Called from: Frontend API client (frontend/src/api/forecast.js)
   - Frontend makes HTTP requests to these endpoints
   
3. Calls: Service functions from forecasting_budget/services.py and services_dataset.py
   - These services contain the business logic (ARIMA forecasting, budget calculations)
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List

# Import service functions from main services module
# These functions contain the core business logic for forecasting
from ..forecasting_budget.services import (
    ingest_vps_daily_costs_to_db,      # Converts CPU usage to daily costs
    ingest_aws_daily_costs_to_db,       # Fetches AWS costs from API
    arima_forecast_cost,                # Main ARIMA forecasting function
    compare_forecast_to_budget,         # Compares forecast to budget
    analyze_utilization,                # Analyzes resource utilization
    list_forecast_runs,                 # Lists historical forecast runs
    workload_aware_forecast,            # Enhanced forecast with day-of-week patterns
    compute_budget_allocation,           # Allocates budget across departments
    scenario_planning,                  # Tests multiple budget scenarios
    multi_cloud_cost_trends,            # Multi-cloud cost trends
    department_cost_forecast,           # Department-specific forecasts
)
# Import dataset-based services (uses CSV files instead of database)
from ..forecasting_budget.services_dataset import (
    arima_forecast_cost_dataset,        # ARIMA forecast using CSV dataset
    compare_forecast_to_budget_dataset, # Budget comparison using CSV dataset
    estimate_company_budget_profile,     # Budget recommendation based on company size
)

# Create FastAPI router with prefix /api/forecast
# All endpoints will be accessible at /api/forecast/*
router = APIRouter(prefix="/api/forecast", tags=["forecast"])


class CompanyBudgetProfile(BaseModel):
    """Pydantic model for budget recommendation request body"""
    num_departments: int
    num_users: int
    environment: str | None = "prod"


@router.post("/ingest/vps")
async def ingest_vps_costs(days: int = Query(60, ge=1, le=365)):
    """
    ENDPOINT: POST /api/forecast/ingest/vps
    
    CALLED FROM:
    - Frontend: frontend/src/api/forecast.js -> ingestVps()
    - Frontend: frontend/src/components/forecasting-budget/ForecastPanel.jsx (line 27)
    
    WHAT IT DOES:
    - Converts VPS CPU usage percentages to daily costs
    - Reads CPU usage from CloudUsage table (metric="cpu_pct")
    - Calculates: Daily Cost = Average CPU % × 0.05
    - Stores daily costs in CloudUsage table (metric="daily_cost")
    
    CONNECTS TO:
    - Calls: services.ingest_vps_daily_costs_to_db()
    - Reads from: database.models.CloudUsage (cpu_pct metric)
    - Writes to: database.models.CloudUsage (daily_cost metric)
    
    RETURNS: {"rows": number_of_rows_ingested}
    """
    rows = ingest_vps_daily_costs_to_db(days=days)
    return {"rows": len(rows)}


@router.post("/ingest/aws")
async def ingest_aws_costs(days: int = Query(60, ge=1, le=365)):
    """
    ENDPOINT: POST /api/forecast/ingest/aws
    
    CALLED FROM:
    - Frontend: frontend/src/api/forecast.js -> ingestAws()
    - Frontend: frontend/src/components/forecasting-budget/ForecastPanel.jsx (line 28)
    
    WHAT IT DOES:
    - Fetches AWS costs from AWS Cost Explorer API
    - Stores daily AWS costs per service in database
    
    CONNECTS TO:
    - Calls: services.ingest_aws_daily_costs_to_db()
    - Which calls: aws_client.fetch_aws_costs() (AWS API)
    - Writes to: database.models.CloudUsage (daily_cost metric, provider="aws")
    
    RETURNS: {"rows": number_of_rows_ingested}
    """
    rows = ingest_aws_daily_costs_to_db(days=days)
    return {"rows": len(rows)}


@router.get("/usage")
async def usage_forecast(horizon_days: int = Query(30, ge=7, le=365), provider: str = Query("vps")):
    """
    ENDPOINT: GET /api/forecast/usage?horizon_days=30&provider=vps
    
    CALLED FROM:
    - Frontend: frontend/src/api/forecast.js -> getUsageForecast()
    - Frontend: frontend/src/components/forecasting-budget/ForecastPanel.jsx (line 30)
    
    WHAT IT DOES:
    - Generates ARIMA forecast for future costs
    - Uses historical cost data to predict next N days
    - Calculates forecast accuracy metrics (MAE, RMSE, MAPE)
    
    CONNECTS TO:
    - Calls: services.arima_forecast_cost()
    - Which calls: services.load_cost_series_from_db() (reads from database)
    - Uses: statsmodels.tsa.arima.model.ARIMA (time series model)
    - Writes to: database.models.ForecastRun (saves forecast results)
    
    RETURNS: {
        "run_id": int,
        "mae": float,           # Mean Absolute Error
        "rmse": float,          # Root Mean Squared Error
        "mape": float,          # Mean Absolute Percentage Error
        "history": [{"timestamp": str, "value": float}],  # Last 90 days
        "forecast": [{"timestamp": str, "value": float}]   # Next N days
    }
    """
    result = arima_forecast_cost(horizon_days=horizon_days, provider=provider)
    return result


@router.get("/usage/dataset")
async def usage_forecast_dataset(
    horizon_days: int = Query(30, ge=7, le=365),
    department: str | None = Query(None),
    account_id: str | None = Query(None),
    environment: str | None = Query(None),
):
    """
    ENDPOINT: GET /api/forecast/usage/dataset
    
    CALLED FROM: External API clients (not currently used by frontend)
    
    WHAT IT DOES:
    - Same as /usage but uses CSV dataset instead of database
    - Can filter by department, account_id, or environment
    
    CONNECTS TO:
    - Calls: services_dataset.arima_forecast_cost_dataset()
    - Reads from: CSV file (Cloud Budget Dataset/cloud_budget_2023_dataset.csv)
    
    RETURNS: Same format as /usage endpoint
    """
    return arima_forecast_cost_dataset(
        horizon_days=horizon_days,
        department=department,
        account_id=account_id,
        environment=environment,
    )


@router.get("/usage/workload")
async def usage_forecast_workload(horizon_days: int = Query(30, ge=7, le=365), provider: str = Query("vps")):
    """
    ENDPOINT: GET /api/forecast/usage/workload
    
    CALLED FROM: External API clients (not currently used by frontend)
    
    WHAT IT DOES:
    - Enhanced ARIMA forecast that considers day-of-week patterns
    - Uses external variables (day-of-week) to improve accuracy
    
    CONNECTS TO:
    - Calls: services.workload_aware_forecast()
    - Uses: ARIMA with exogenous variables (ARIMAX model)
    
    RETURNS: Same format as /usage endpoint
    """
    result = workload_aware_forecast(horizon_days=horizon_days, provider=provider)
    return result


@router.get("/budget")
async def budget_vs_forecast(
    monthly_budget: float = Query(..., gt=0),
    horizon_days: int = Query(30, ge=7, le=365),
    provider: str = Query("vps"),
):
    """
    ENDPOINT: GET /api/forecast/budget?monthly_budget=3000&horizon_days=30
    
    CALLED FROM:
    - Frontend: frontend/src/api/forecast.js -> getBudgetVsForecast()
    - Frontend: frontend/src/components/forecasting-budget/ForecastPanel.jsx
      - Line 31: Initial load
      - Line 113: When user clicks "Recalculate" button
    
    WHAT IT DOES:
    - Gets forecast for next N days
    - Sums forecasted costs to get projected total
    - Compares projected total to monthly budget
    - Determines status: "on_track", "over_budget_risk", or "under_budget"
    
    CONNECTS TO:
    - Calls: services.compare_forecast_to_budget()
    - Which calls: services.arima_forecast_cost() (gets forecast)
    - Math: Delta = Projected Total - Monthly Budget
    - Status: "over_budget_risk" if delta > 5% of budget
    
    RETURNS: {
        "metrics": {"mae": float, "rmse": float, "mape": float},
        "budget": float,              # Monthly budget
        "projected_total": float,    # Sum of forecasted costs
        "delta": float,              # projected_total - budget
        "status": str                # "on_track" | "over_budget_risk" | "under_budget"
    }
    """
    result = compare_forecast_to_budget(monthly_budget=monthly_budget, forecast_days=horizon_days, provider=provider)
    return result


@router.get("/budget/dataset")
async def budget_vs_forecast_dataset(
    monthly_budget: float = Query(..., gt=0),
    horizon_days: int = Query(30, ge=7, le=365),
    department: str | None = Query(None),
    account_id: str | None = Query(None),
    environment: str | None = Query(None),
):
    """
    ENDPOINT: GET /api/forecast/budget/dataset
    
    CALLED FROM: External API clients (not currently used by frontend)
    
    WHAT IT DOES:
    - Same as /budget but uses CSV dataset instead of database
    - Can filter by department, account_id, or environment
    
    CONNECTS TO:
    - Calls: services_dataset.compare_forecast_to_budget_dataset()
    
    RETURNS: Same format as /budget endpoint
    """
    return compare_forecast_to_budget_dataset(
        monthly_budget=monthly_budget,
        forecast_days=horizon_days,
        department=department,
        account_id=account_id,
        environment=environment,
    )


@router.post("/budget/recommendation")
async def budget_recommendation(profile: CompanyBudgetProfile):
    """
    ENDPOINT: POST /api/forecast/budget/recommendation
    
    CALLED FROM:
    - Frontend: frontend/src/api/forecast.js -> getBudgetRecommendation()
    - Frontend: frontend/src/components/forecasting-budget/ForecastPanel.jsx (line 152)
      - When user clicks "Budget calculator" button
    
    WHAT IT DOES:
    - Estimates recommended monthly budget based on company size
    - Uses historical dataset to calculate baseline budget
    - Scales budget by number of departments
    - Allocates budget per department based on historical patterns
    
    CONNECTS TO:
    - Calls: services_dataset.estimate_company_budget_profile()
    - Reads from: CSV file (Cloud Budget Dataset/cloud_budget_2023_dataset.csv)
    - Math: Recommended = Baseline × (New Departments / Baseline Departments)
    
    REQUEST BODY: {
        "num_departments": int,
        "num_users": int,
        "environment": str (optional, default="prod")
    }
    
    RETURNS: {
        "recommended_monthly_budget": float,
        "baseline_monthly_budget": float,
        "scale_factor_departments": float,
        "per_department": [{"department": str, "recommended_monthly_budget": float, ...}]
    }
    """
    return estimate_company_budget_profile(
        num_departments=profile.num_departments,
        num_users=profile.num_users,
        environment=profile.environment,
    )


@router.get("/utilization")
async def utilization(window_hours: int = Query(24, ge=1, le=168), provider: str = Query("vps")):
    """
    ENDPOINT: GET /api/forecast/utilization
    
    CALLED FROM: External API clients (not currently used by frontend)
    
    WHAT IT DOES:
    - Analyzes resource utilization (CPU, memory) for last N hours
    - Categorizes resources as: "idle", "underutilized", "balanced", "overutilized"
    
    CONNECTS TO:
    - Calls: services.analyze_utilization()
    - Reads from: database.models.CloudUsage (cpu_pct, mem_pct metrics)
    
    RETURNS: {"items": [{"resource_id": str, "avg_cpu": float, "avg_mem": float, "status": str}]}
    """
    return {"items": analyze_utilization(window_hours=window_hours, provider=provider)}


@router.get("/runs")
async def forecast_runs(limit: int = Query(20, ge=1, le=100), provider: str = Query("vps")):
    """
    ENDPOINT: GET /api/forecast/runs?limit=20
    
    CALLED FROM:
    - Frontend: frontend/src/api/forecast.js -> getForecastRuns()
    - Frontend: frontend/src/components/forecasting-budget/ForecastPanel.jsx (line 32)
    
    WHAT IT DOES:
    - Lists historical forecast runs with their accuracy metrics
    - Used to track forecast accuracy over time
    
    CONNECTS TO:
    - Calls: services.list_forecast_runs()
    - Reads from: database.models.ForecastRun
    
    RETURNS: {
        "items": [{
            "id": int,
            "created_at": str,
            "model_type": str,
            "mae": float,
            "rmse": float,
            "mape": float,
            "horizon_hours": int,
            "input_points": int
        }]
    }
    """
    return {"items": list_forecast_runs(limit=limit, provider=provider)}


@router.get("/budget/allocation")
async def budget_allocation(monthly_budget: float = Query(..., gt=0), horizon_days: int = Query(30, ge=7, le=365)):
    """
    ENDPOINT: GET /api/forecast/budget/allocation?monthly_budget=3000&horizon_days=30
    
    CALLED FROM:
    - Frontend: frontend/src/api/forecast.js -> getBudgetAllocation()
    - Frontend: frontend/src/components/forecasting-budget/ForecastPanel.jsx (line 33)
    
    WHAT IT DOES:
    - Allocates monthly budget across departments based on weights
    - Calculates projected costs per department
    - Creates budget alerts if departments are over/under budget
    - Can send alerts via webhook if configured
    
    CONNECTS TO:
    - Calls: services.compute_budget_allocation()
    - Which calls: services.compare_forecast_to_budget() (gets base forecast)
    - Uses: services_monitor.DEPARTMENTS and DEPARTMENT_ALLOCATIONS (department weights)
    - Writes to: database.models.BudgetAlert (if over/under budget)
    - Math: Dept Budget = Total Budget × (Dept Weight / Total Weight)
    
    RETURNS: {
        "summary": {
            "metrics": {...},
            "budget": float,
            "projected_total": float,
            "delta": float,
            "status": str
        },
        "allocations": [{
            "department": str,
            "budget": float,
            "projected": float,
            "delta": float,
            "status": str
        }]
    }
    """
    return compute_budget_allocation(monthly_budget=monthly_budget, forecast_days=horizon_days)


@router.get("/scenarios")
async def forecast_scenarios(
    budgets: List[float] = Query(..., description="Multiple monthly budget values"),
    horizon_days: int = Query(30, ge=7, le=365),
):
    """
    ENDPOINT: GET /api/forecast/scenarios?budgets=2400&budgets=3000&budgets=3600&horizon_days=30
    
    CALLED FROM:
    - Frontend: frontend/src/api/forecast.js -> getForecastScenarios()
    - Frontend: frontend/src/components/forecasting-budget/ForecastPanel.jsx (line 34)
      - Tests 3 scenarios: 80%, 100%, 120% of current budget
    
    WHAT IT DOES:
    - Tests multiple budget scenarios (e.g., what if budget is 20% lower/higher?)
    - For each budget, calculates projected costs and status
    - Used for "what-if" analysis and planning
    
    CONNECTS TO:
    - Calls: services.scenario_planning()
    - Which calls: services.compare_forecast_to_budget() for each budget
    
    RETURNS: {
        "items": [{
            "budget": float,
            "projected_total": float,
            "delta": float,
            "status": str,
            "metrics": {...}
        }]
    }
    """
    return {"items": scenario_planning(budgets=budgets, forecast_days=horizon_days)}


@router.get("/history")
async def forecast_history(days: int = Query(60, ge=7, le=365)):
    """
    ENDPOINT: GET /api/forecast/history?days=60
    
    CALLED FROM:
    - Frontend: frontend/src/api/forecast.js -> getForecastHistory()
    - Currently not used by ForecastPanel.jsx
    
    WHAT IT DOES:
    - Returns historical cost trends for multiple cloud providers (VPS, AWS)
    - Shows cost data for last N days
    
    CONNECTS TO:
    - Calls: services.multi_cloud_cost_trends()
    - Reads from: database.models.CloudUsage (daily_cost metric)
    
    RETURNS: {
        "vps": [{"timestamp": str, "value": float}],
        "aws": [{"timestamp": str, "value": float}]
    }
    """
    return multi_cloud_cost_trends(days=days)


@router.get("/department/forecast")
async def department_forecast(department: str, horizon_days: int = Query(30, ge=7, le=365)):
    """
    ENDPOINT: GET /api/forecast/department/forecast?department=Dev&horizon_days=30
    
    CALLED FROM: External API clients (not currently used by frontend)
    
    WHAT IT DOES:
    - Gets forecast for a specific department
    - Scales total forecast by department's allocation weight
    
    CONNECTS TO:
    - Calls: services.department_cost_forecast()
    - Which calls: services.arima_forecast_cost() (gets base forecast)
    - Uses: services_monitor.DEPARTMENT_ALLOCATIONS (department weight)
    - Math: Dept Forecast = Total Forecast × Dept Weight
    
    RETURNS: Same format as /usage endpoint, but scaled for department
    """
    return department_cost_forecast(department=department, horizon_days=horizon_days)
