/**
 * FORECAST BUDGET API CLIENT
 * ==========================
 * This file contains all frontend API functions for the forecast budget system.
 * 
 * CONNECTION FLOW:
 * 1. Called from: frontend/src/components/forecasting-budget/ForecastPanel.jsx
 * 2. Makes HTTP requests to: backend/routers/forecast.py endpoints
 * 3. Uses: api client from ./client.js (Axios instance with base URL)
 */

import api from "./client"

/**
 * Ingest VPS costs to database
 * 
 * CALLED FROM:
 * - ForecastPanel.jsx (line 27) - On component mount
 * 
 * CONNECTS TO:
 * - Backend: POST /api/forecast/ingest/vps
 * - Which calls: services.ingest_vps_daily_costs_to_db()
 * 
 * WHAT IT DOES:
 * - Converts CPU usage to daily costs and stores in database
 * - Must be called before forecasting to have cost data
 * 
 * RETURNS: {"rows": number_of_rows}
 */
export async function ingestVps(days = 60) {
  const res = await api.post(`/api/forecast/ingest/vps?days=${days}`)
  return res.data
}

/**
 * Ingest AWS costs to database
 * 
 * CALLED FROM:
 * - ForecastPanel.jsx (line 28) - On component mount
 * 
 * CONNECTS TO:
 * - Backend: POST /api/forecast/ingest/aws
 * - Which calls: services.ingest_aws_daily_costs_to_db()
 * - Which calls: aws_client.fetch_aws_costs() (AWS API)
 * 
 * WHAT IT DOES:
 * - Fetches AWS costs from AWS Cost Explorer API
 * - Stores daily AWS costs in database
 * 
 * RETURNS: {"rows": number_of_rows}
 */
export async function ingestAws(days = 60) {
  const res = await api.post(`/api/forecast/ingest/aws?days=${days}`)
  return res.data
}

/**
 * Get cost forecast using ARIMA model
 * 
 * CALLED FROM:
 * - ForecastPanel.jsx (line 30) - On component mount
 * 
 * CONNECTS TO:
 * - Backend: GET /api/forecast/usage?horizon_days=30
 * - Which calls: services.arima_forecast_cost()
 * 
 * WHAT IT DOES:
 * - Gets ARIMA forecast for next N days
 * - Returns historical costs (last 90 days) and forecasted costs
 * - Includes accuracy metrics (MAE, RMSE, MAPE)
 * 
 * RETURNS: {
 *   "run_id": int,
 *   "mae": float,
 *   "rmse": float,
 *   "mape": float,
 *   "history": [{"timestamp": str, "value": float}],
 *   "forecast": [{"timestamp": str, "value": float}]
 * }
 */
export async function getUsageForecast(horizonDays = 30) {
  const res = await api.get(`/api/forecast/usage?horizon_days=${horizonDays}`)
  return res.data
}

/**
 * Compare forecast to budget
 * 
 * CALLED FROM:
 * - ForecastPanel.jsx (line 31) - On component mount
 * - ForecastPanel.jsx (line 113) - When user clicks "Recalculate" button
 * 
 * CONNECTS TO:
 * - Backend: GET /api/forecast/budget?monthly_budget=3000&horizon_days=30
 * - Which calls: services.compare_forecast_to_budget()
 * 
 * WHAT IT DOES:
 * - Compares forecasted costs to monthly budget
 * - Calculates delta (projected - budget)
 * - Determines status: "on_track", "over_budget_risk", or "under_budget"
 * 
 * RETURNS: {
 *   "metrics": {"mae": float, "rmse": float, "mape": float},
 *   "budget": float,
 *   "projected_total": float,
 *   "delta": float,
 *   "status": str
 * }
 */
export async function getBudgetVsForecast(monthlyBudget, horizonDays = 30) {
  const res = await api.get(`/api/forecast/budget?monthly_budget=${monthlyBudget}&horizon_days=${horizonDays}`)
  return res.data
}

/**
 * Get historical forecast runs
 * 
 * CALLED FROM:
 * - ForecastPanel.jsx (line 32) - On component mount
 * 
 * CONNECTS TO:
 * - Backend: GET /api/forecast/runs?limit=20
 * - Which calls: services.list_forecast_runs()
 * 
 * WHAT IT DOES:
 * - Gets list of previous forecast runs with their accuracy metrics
 * - Used to display forecast accuracy over time chart
 * 
 * RETURNS: {
 *   "items": [{
 *     "id": int,
 *     "created_at": str,
 *     "mae": float,
 *     "rmse": float,
 *     "mape": float,
 *     ...
 *   }]
 * }
 */
export async function getForecastRuns(limit = 20) {
  const res = await api.get(`/api/forecast/runs?limit=${limit}`)
  return res.data
}

/**
 * Get budget allocation across departments
 * 
 * CALLED FROM:
 * - ForecastPanel.jsx (line 33) - On component mount
 * 
 * CONNECTS TO:
 * - Backend: GET /api/forecast/budget/allocation?monthly_budget=3000&horizon_days=30
 * - Which calls: services.compute_budget_allocation()
 * 
 * WHAT IT DOES:
 * - Allocates budget across departments based on weights
 * - Calculates projected costs per department
 * - Creates budget alerts if departments are over/under budget
 * 
 * RETURNS: {
 *   "summary": {...},
 *   "allocations": [{
 *     "department": str,
 *     "budget": float,
 *     "projected": float,
 *     "delta": float,
 *     "status": str
 *   }]
 * }
 */
export async function getBudgetAllocation(monthlyBudget, horizonDays = 30) {
  const res = await api.get(
    `/api/forecast/budget/allocation?monthly_budget=${monthlyBudget}&horizon_days=${horizonDays}`
  )
  return res.data
}

/**
 * Get scenario planning results
 * 
 * CALLED FROM:
 * - ForecastPanel.jsx (line 34) - On component mount
 * 
 * CONNECTS TO:
 * - Backend: GET /api/forecast/scenarios?budgets=2400&budgets=3000&budgets=3600
 * - Which calls: services.scenario_planning()
 * 
 * WHAT IT DOES:
 * - Tests multiple budget scenarios (e.g., 80%, 100%, 120% of current budget)
 * - Used for "what-if" analysis
 * 
 * RETURNS: {
 *   "items": [{
 *     "budget": float,
 *     "projected_total": float,
 *     "delta": float,
 *     "status": str
 *   }]
 * }
 */
export async function getForecastScenarios(budgets, horizonDays = 30) {
  const params = budgets.map((b) => `budgets=${b}`).join("&")
  const res = await api.get(`/api/forecast/scenarios?${params}&horizon_days=${horizonDays}`)
  return res.data
}

/**
 * Get forecast history (not currently used in ForecastPanel)
 * 
 * CALLED FROM: Not currently used
 * 
 * CONNECTS TO:
 * - Backend: GET /api/forecast/history?days=60
 * - Which calls: services.multi_cloud_cost_trends()
 */
export async function getForecastHistory(days = 60) {
  const res = await api.get(`/api/forecast/history?days=${days}`)
  return res.data
}

/**
 * Get budget recommendation based on company size
 * 
 * CALLED FROM:
 * - ForecastPanel.jsx (line 152) - When user clicks "Budget calculator" button
 * 
 * CONNECTS TO:
 * - Backend: POST /api/forecast/budget/recommendation
 * - Which calls: services_dataset.estimate_company_budget_profile()
 * 
 * WHAT IT DOES:
 * - Estimates recommended monthly budget based on:
 *   - Number of departments
 *   - Number of users
 *   - Environment (prod, dev, etc.)
 * - Uses historical dataset to calculate baseline and scale
 * 
 * RETURNS: {
 *   "recommended_monthly_budget": float,
 *   "baseline_monthly_budget": float,
 *   "scale_factor_departments": float,
 *   "per_department": [...]
 * }
 */
export async function getBudgetRecommendation(numDepartments, numUsers, environment = "prod") {
  const res = await api.post("/api/forecast/budget/recommendation", {
    num_departments: numDepartments,
    num_users: numUsers,
    environment,
  })
  return res.data
}
