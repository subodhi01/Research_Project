/**
 * FORECAST PANEL COMPONENT
 * ========================
 * Main React component that displays forecast and budget data.
 * 
 * CONNECTION FLOW:
 * 1. Rendered in: App.jsx (main application component)
 * 2. Imports API functions from: frontend/src/api/forecast.js
 * 3. API functions call: backend/routers/forecast.py endpoints
 * 4. Endpoints call: backend/forecasting_budget/services.py functions
 * 5. Services read/write: database via models.py
 * 
 * DATA FLOW:
 * Component Mount → API Calls → Backend Endpoints → Services → Database → Response → State Update → UI Render
 */

import React, { useEffect, useState } from "react"
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, AreaChart, Area, BarChart, Bar, Legend } from "recharts"
// Import API functions that make HTTP requests to backend
import { ingestVps, ingestAws, getUsageForecast, getBudgetVsForecast, getForecastRuns, getBudgetAllocation, getForecastScenarios, getBudgetRecommendation } from "../../api/forecast"
import { trackMetric } from "../../api/ux"

function ForecastPanel() {
  const [series, setSeries] = useState([])
  const [forecast, setForecast] = useState([])
  const [metrics, setMetrics] = useState(null)
  const [budgetResult, setBudgetResult] = useState(null)
  const [runs, setRuns] = useState([])
  const [allocations, setAllocations] = useState(null)
  const [scenarios, setScenarios] = useState([])
  const [loading, setLoading] = useState(false)
  const [budget, setBudget] = useState(3000)
  const [growth, setGrowth] = useState(0)
  const [savings, setSavings] = useState(0)
  const [companyDepartments, setCompanyDepartments] = useState(4)
  const [companyUsers, setCompanyUsers] = useState(200)
  const [companyBudget, setCompanyBudget] = useState(null)
  const [companyBudgetLoading, setCompanyBudgetLoading] = useState(false)

  /**
   * COMPONENT MOUNT EFFECT
   * ======================
   * Runs once when component is first rendered.
   * 
   * DATA FLOW:
   * 1. ingestVps(60) → POST /api/forecast/ingest/vps
   *    - Converts CPU usage to daily costs
   *    - Stores in database (CloudUsage table)
   * 
   * 2. ingestAws(60) → POST /api/forecast/ingest/aws
   *    - Fetches AWS costs from AWS API
   *    - Stores in database (CloudUsage table)
   * 
   * 3. getUsageForecast(30) → GET /api/forecast/usage
   *    - Gets ARIMA forecast for next 30 days
   *    - Returns: history (last 90 days), forecast (next 30 days), metrics (MAE, RMSE, MAPE)
   *    - Sets: series (history), forecast (predictions), metrics
   * 
   * 4. getBudgetVsForecast(budget, 30) → GET /api/forecast/budget
   *    - Compares forecast to budget
   *    - Returns: budget, projected_total, delta, status
   *    - Sets: budgetResult
   * 
   * 5. getForecastRuns(20) → GET /api/forecast/runs
   *    - Gets historical forecast runs
   *    - Used for accuracy over time chart
   *    - Sets: runs
   * 
   * 6. getBudgetAllocation(budget, 30) → GET /api/forecast/budget/allocation
   *    - Allocates budget across departments
   *    - Returns: summary + allocations per department
   *    - Sets: allocations
   * 
   * 7. getForecastScenarios([budget * 0.8, budget, budget * 1.2], 30) → GET /api/forecast/scenarios
   *    - Tests 3 scenarios: 80%, 100%, 120% of budget
   *    - Returns: results for each scenario
   *    - Sets: scenarios
   */
  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        // Step 1: Ingest costs (convert CPU usage to costs, fetch AWS costs)
        await ingestVps(60)  // Calls: api/forecast.js -> POST /api/forecast/ingest/vps
        await ingestAws(60)  // Calls: api/forecast.js -> POST /api/forecast/ingest/aws
      } catch (e) {}
      
      // Step 2: Get forecast (ARIMA model predicts next 30 days)
      const usage = await getUsageForecast(30)  // Calls: api/forecast.js -> GET /api/forecast/usage
      // Sets: series (history), forecast (predictions), metrics (MAE, RMSE, MAPE)
      setMetrics({ mae: usage.mae, rmse: usage.rmse, mape: usage.mape })
      setSeries(usage.history || [])      // Historical costs (last 90 days)
      setForecast(usage.forecast || [])    // Forecasted costs (next 30 days)
      
      // Step 3: Compare forecast to budget
      const budgetRes = await getBudgetVsForecast(budget, 30)  // Calls: api/forecast.js -> GET /api/forecast/budget
      setBudgetResult(budgetRes)  // Contains: budget, projected_total, delta, status
      
      // Step 4: Get historical forecast runs (for accuracy chart)
      const runsRes = await getForecastRuns(20)  // Calls: api/forecast.js -> GET /api/forecast/runs
      setRuns(runsRes.items || [])
      
      // Step 5: Get department budget allocations
      const allocRes = await getBudgetAllocation(budget, 30)  // Calls: api/forecast.js -> GET /api/forecast/budget/allocation
      setAllocations(allocRes)  // Contains: summary + allocations per department
      
      // Step 6: Get scenario planning (test multiple budgets)
      const scenarioRes = await getForecastScenarios([budget * 0.8, budget, budget * 1.2], 30)  // Calls: api/forecast.js -> GET /api/forecast/scenarios
      setScenarios(scenarioRes.items || [])  // Results for 80%, 100%, 120% budget scenarios
      
      try {
        await trackMetric("forecast_panel_loaded", "overview")
      } catch (e) {}
      setLoading(false)
    }
    load()
  }, [])

  /**
   * DATA TRANSFORMATION FOR CHARTS
   * ==============================
   * Merges historical and forecast data for the main forecast chart.
   * 
   * INPUT:
   * - series: Historical costs from getUsageForecast() (last 90 days)
   * - forecast: Forecasted costs from getUsageForecast() (next 30 days)
   * 
   * OUTPUT:
   * - merged: Array with {time, actual, forecast} for chart display
   *   - actual: Historical cost values (green line)
   *   - forecast: Forecasted cost values (blue line)
   */
  const merged = series.map((h) => {
    const f = forecast.find((x) => x.timestamp === h.timestamp)
    return { time: h.timestamp, actual: h.value, forecast: f ? f.value : null }
  })

  /**
   * SCENARIO ADJUSTMENT
   * ===================
   * Applies growth and savings factors to scenario projections.
   * 
   * INPUT:
   * - scenarios: Results from getForecastScenarios() (base projections)
   * - growth: User-selected growth percentage (-20%, 0%, +20%, +40%)
   * - savings: User-selected savings percentage (0%, 10%, 20%, 30%)
   * 
   * MATH:
   * - growthFactor = 1 + (growth / 100)  // e.g., +20% = 1.2
   * - savingsFactor = 1 - (savings / 100)  // e.g., 20% savings = 0.8
   * - projected_adjusted = projected_total × growthFactor × savingsFactor
   * 
   * OUTPUT:
   * - adjustedScenarios: Scenarios with adjusted projections
   *   - Used in scenario planning bar chart (orange bars)
   */
  const adjustedScenarios = scenarios.map((s) => {
    const growthFactor = 1 + growth / 100
    const savingsFactor = 1 - savings / 100
    const projectedAdjusted = s.projected_total * growthFactor * savingsFactor
    return {
      ...s,
      projected_adjusted: projectedAdjusted,
    }
  })

  return (
    <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold">Forecasting and Budget Intelligence</h2>
          <p className="text-xs text-slate-400">Virtual VPS instances daily spend forecast with budget risk</p>
        </div>
        <div className="flex flex-col items-end gap-3 text-xs">
          <div className="flex items-center gap-4">
          <div className="flex items-center gap-1">
            <span className="text-slate-400">Budget</span>
            <input
              type="number"
              className="w-24 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-right text-slate-100 text-xs"
              value={budget}
              onChange={(e) => setBudget(Number(e.target.value) || 0)}
            />
          </div>
          <div className="flex items-center gap-1">
            <span className="text-slate-400">Growth</span>
            <select
              className="bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-100 text-xs"
              value={growth}
              onChange={(e) => setGrowth(Number(e.target.value) || 0)}
            >
              <option value={-20}>-20%</option>
              <option value={0}>0%</option>
              <option value={20}>+20%</option>
              <option value={40}>+40%</option>
            </select>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-slate-400">Savings</span>
            <select
              className="bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-100 text-xs"
              value={savings}
              onChange={(e) => setSavings(Number(e.target.value) || 0)}
            >
              <option value={0}>0%</option>
              <option value={10}>10%</option>
              <option value={20}>20%</option>
              <option value={30}>30%</option>
            </select>
          </div>
          {/* 
            RECALCULATE BUTTON
            ==================
            When clicked, recalculates budget comparison with new budget value.
            
            CALLS:
            - getBudgetVsForecast(budget, 30) → GET /api/forecast/budget
            - Updates: budgetResult state
            - Triggers: Re-render of budget status display and charts
          */}
          <button
            type="button"
            onClick={async () => {
              setLoading(true)
              const budgetRes = await getBudgetVsForecast(budget, 30)  // Calls: api/forecast.js -> GET /api/forecast/budget
              setBudgetResult(budgetRes)  // Updates budget comparison result
              setLoading(false)
            }}
            className="px-3 py-1 rounded-md bg-sky-600 text-xs text-white hover:bg-sky-500 disabled:opacity-50"
            disabled={loading || budget <= 0}
          >
            Recalculate
          </button>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1">
              <span className="text-slate-400">Company departments</span>
              <input
                type="number"
                className="w-20 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-right text-slate-100 text-xs"
                value={companyDepartments}
                min={1}
                onChange={(e) => setCompanyDepartments(Number(e.target.value) || 0)}
              />
            </div>
            <div className="flex items-center gap-1">
              <span className="text-slate-400">Users</span>
              <input
                type="number"
                className="w-24 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-right text-slate-100 text-xs"
                value={companyUsers}
                min={1}
                onChange={(e) => setCompanyUsers(Number(e.target.value) || 0)}
              />
            </div>
            {/* 
              BUDGET CALCULATOR BUTTON
              ========================
              Calculates recommended budget based on company size.
              
              CALLS:
              - getBudgetRecommendation(companyDepartments, companyUsers, "prod")
                → POST /api/forecast/budget/recommendation
              - Backend calls: services_dataset.estimate_company_budget_profile()
              - Uses: CSV dataset to calculate baseline and scale by departments
              
              RETURNS:
              - recommended_monthly_budget: Scaled budget based on company size
              - baseline_monthly_budget: Average from historical dataset
              - scale_factor_departments: Scaling factor
              - per_department: Budget allocation per department
              
              DISPLAYS:
              - Recommended monthly budget
              - Scale factor information
              - Top department estimates
            */}
            <button
              type="button"
              onClick={async () => {
                if (companyDepartments <= 0 || companyUsers <= 0) {
                  return
                }
                setCompanyBudgetLoading(true)
                try {
                  const result = await getBudgetRecommendation(companyDepartments, companyUsers, "prod")  // Calls: api/forecast.js -> POST /api/forecast/budget/recommendation
                  setCompanyBudget(result)  // Updates company budget recommendation
                } finally {
                  setCompanyBudgetLoading(false)
                }
              }}
              className="px-3 py-1 rounded-md bg-emerald-600 text-xs text-white hover:bg-emerald-500 disabled:opacity-50"
              disabled={companyBudgetLoading || companyDepartments <= 0 || companyUsers <= 0}
            >
              Budget calculator
            </button>
          </div>
        </div>
      </div>
      {companyBudget && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="space-y-1">
            <div className="text-slate-400">Recommended monthly budget</div>
            <div className="text-lg font-semibold text-slate-100">
              ${companyBudget.recommended_monthly_budget.toFixed(2)}
            </div>
            <div className="text-[11px] text-slate-500">
              Baseline dataset company: ${companyBudget.baseline_monthly_budget.toFixed(2)} per month
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-slate-400">Scale by departments</div>
            <div className="text-sm font-semibold text-slate-100">
              x{companyBudget.scale_factor_departments.toFixed(2)} for {companyBudget.num_departments} departments
            </div>
            <div className="text-[11px] text-slate-500">
              Profile users: {companyBudget.num_users}
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-slate-400">Top department estimates</div>
            <div className="flex flex-wrap gap-2">
              {(companyBudget.per_department || []).slice(0, 4).map((d) => (
                <div key={d.department} className="px-2 py-1 rounded-md bg-slate-900 border border-slate-700">
                  <div className="text-[11px] text-slate-400">{d.department}</div>
                  <div className="text-sm font-semibold text-slate-100">
                    ${d.recommended_monthly_budget.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div className="space-y-1">
          <div className="text-slate-400">Forecast error</div>
          <div className="flex gap-3 text-slate-100">
            <div>
              <div className="text-slate-400 text-[11px]">MAE</div>
              <div className="text-sm font-semibold">{metrics ? metrics.mae.toFixed(2) : "--"}</div>
            </div>
            <div>
              <div className="text-slate-400 text-[11px]">RMSE</div>
              <div className="text-sm font-semibold">{metrics ? metrics.rmse.toFixed(2) : "--"}</div>
            </div>
            <div>
              <div className="text-slate-400 text-[11px]">MAPE</div>
              <div className="text-sm font-semibold">{metrics ? `${metrics.mape.toFixed(1)}%` : "--"}</div>
            </div>
          </div>
        </div>
        <div className="space-y-1">
          <div className="text-slate-400">Budget vs projection</div>
          <div className="flex gap-3 text-slate-100">
            <div>
              <div className="text-slate-400 text-[11px]">Budget</div>
              <div className="text-sm font-semibold">{budgetResult ? `$${budgetResult.budget.toFixed(2)}` : "--"}</div>
            </div>
            <div>
              <div className="text-slate-400 text-[11px]">Projected</div>
              <div className="text-sm font-semibold">
                {budgetResult ? `$${budgetResult.projected_total.toFixed(2)}` : "--"}
              </div>
            </div>
            <div>
              <div className="text-slate-400 text-[11px]">Delta</div>
              <div className="text-sm font-semibold">
                {budgetResult ? `$${budgetResult.delta.toFixed(2)}` : "--"}
              </div>
            </div>
          </div>
        </div>
        <div className="space-y-1">
          <div className="text-slate-400">Status</div>
          <div className="flex items-center gap-2">
            <span
              className={
                budgetResult?.status === "over_budget_risk"
                  ? "px-2 py-1 rounded-full text-[11px] bg-rose-500/10 text-rose-400 border border-rose-500/40"
                  : budgetResult?.status === "under_budget"
                  ? "px-2 py-1 rounded-full text-[11px] bg-emerald-500/10 text-emerald-400 border-emerald-500/40"
                  : "px-2 py-1 rounded-full text-[11px] bg-sky-500/10 text-sky-400 border-sky-500/40"
              }
            >
              {budgetResult ? budgetResult.status.replace(/_/g, " ") : "waiting"}
            </span>
          </div>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        <div className="space-y-1">
          <div className="text-slate-400">Forecast accuracy over time</div>
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={runs.map((r) => ({ time: r.created_at, mae: r.mae, mape: r.mape }))}>
                <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                <XAxis dataKey="time" stroke="#94a3b8" tickMargin={8} tickFormatter={(t) => (t || "").slice(5, 16)} />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: "#020617", borderColor: "#1e293b" }} />
                <Line type="monotone" dataKey="mae" stroke="#22c55e" strokeWidth={2} dot={false} name="MAE" />
                <Line type="monotone" dataKey="mape" stroke="#38bdf8" strokeWidth={2} dot={false} name="MAPE" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="space-y-1">
          <div className="text-slate-400">Predictive budget allocation by department</div>
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={(allocations?.allocations || []).map((a) => ({ name: a.department, budget: a.budget, projected: a.projected }))}>
                <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: "#020617", borderColor: "#1e293b" }} />
                <Legend />
                <Bar dataKey="budget" fill="#22c55e" name="Budget" />
                <Bar dataKey="projected" fill="#fb7185" name="Projected" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      {/* 
        MAIN FORECAST CHART
        ===================
        Displays historical costs vs forecasted costs.
        
        DATA SOURCE:
        - merged: Combined history + forecast data
        - actual: Historical costs from getUsageForecast() (green line)
        - forecast: Forecasted costs from getUsageForecast() (blue line)
        
        SHOWS:
        - Last 90 days of actual costs
        - Next 30 days of forecasted costs
        - Visual comparison of actual vs predicted
      */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={merged}>
            <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
            <XAxis dataKey="time" stroke="#94a3b8" tickMargin={8} tickFormatter={(t) => t.slice(5, 10)} />
            <YAxis stroke="#94a3b8" />
            <Tooltip contentStyle={{ backgroundColor: "#020617", borderColor: "#1e293b" }} />
            <Line type="monotone" dataKey="actual" stroke="#22c55e" strokeWidth={2} dot={false} name="Actual" />
            <Line type="monotone" dataKey="forecast" stroke="#38bdf8" strokeWidth={2} dot={false} name="Forecast" />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="h-32">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={budgetResult ? [{
              name: "Budget",
              budget: budgetResult.budget,
              projected: budgetResult.projected_total,
            }] : []}
          >
            <XAxis dataKey="name" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip contentStyle={{ backgroundColor: "#020617", borderColor: "#1e293b" }} />
            <Area type="monotone" dataKey="budget" stroke="#22c55e" fill="#22c55e33" name="Budget" />
            <Area type="monotone" dataKey="projected" stroke="#fb7185" fill="#fb718533" name="Projected" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      {/* 
        SCENARIO PLANNING CHART
        =======================
        Shows multiple budget scenarios with growth/savings adjustments.
        
        DATA SOURCE:
        - adjustedScenarios: Results from getForecastScenarios() with growth/savings applied
        - budget: User-set budget amounts (80%, 100%, 120% of current)
        - projected: Base forecasted costs (blue bars)
        - projectedAdjusted: Forecast with growth/savings factors (orange bars)
        
        SHOWS:
        - Green bars: Budget amounts for each scenario
        - Blue bars: Base projected costs (no adjustments)
        - Orange bars: Adjusted projections (with growth/savings factors)
        - Helps visualize "what-if" scenarios
      */}
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={adjustedScenarios.map((s) => ({
              name: `$${s.budget.toFixed(0)}`,
              budget: s.budget,
              projected: s.projected_total,
              projectedAdjusted: s.projected_adjusted,
            }))}
          >
            <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
            <XAxis dataKey="name" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip contentStyle={{ backgroundColor: "#020617", borderColor: "#1e293b" }} />
            <Legend />
            <Bar dataKey="budget" fill="#22c55e" name="Budget" />
            <Bar dataKey="projected" fill="#38bdf8" name="Projected base" />
            <Bar dataKey="projectedAdjusted" fill="#f97316" name="Projected with scenarios" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}

export default ForecastPanel
