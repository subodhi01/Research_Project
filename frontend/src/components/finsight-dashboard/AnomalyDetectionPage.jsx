import React, { useEffect, useState } from "react"
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from "recharts"
import { getCloudAnomalies, getAnomalyMetrics } from "../../api/anomaly"

const DEPARTMENTS = ["HR", "IT", "Dev", "Management"]

function AnomalyDetectionPage() {
  const [anomalies, setAnomalies] = useState([])
  const [count, setCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [department, setDepartment] = useState("Dev")
  const [metrics, setMetrics] = useState([])
  const [metricsLoading, setMetricsLoading] = useState(false)

  const load = async (dept) => {
    setLoading(true)
    try {
      const params = { window_hours: 24, contamination: 0.1 }
      if (dept) {
        params.department = dept
      }
      const res = await getCloudAnomalies(params)
      setAnomalies(res.anomalies || [])
      setCount(res.count || 0)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load(department)
  }, [department])

  useEffect(() => {
    const loadMetrics = async () => {
      setMetricsLoading(true)
      try {
        const res = await getAnomalyMetrics(50, "iforest_vs_z")
        const items = res.items || []
        const series = items
          .slice()
          .reverse()
          .map((r) => ({
            time: r.created_at,
            precision: r.precision,
            recall: r.recall,
            f1: r.f1,
            accuracy: r.accuracy,
          }))
        setMetrics(series)
      } finally {
        setMetricsLoading(false)
      }
    }
    loadMetrics()
  }, [])

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-50">Anomaly Detection</h1>
          <p className="text-sm text-slate-400">Explainable anomalies from live department metrics</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-semibold text-rose-400">{count}</p>
          <p className="text-xs text-slate-400">anomalies detected</p>
        </div>
      </div>
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
        <div className="px-6 py-3 border-b border-slate-800 flex items-center justify-between">
          <span className="text-sm font-medium text-slate-300">Recent anomalies</span>
          <div className="flex items-center gap-3">
            <label className="text-xs text-slate-400">
              Department
              <select
                className="ml-2 bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded px-2 py-1"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
              >
                {DEPARTMENTS.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </label>
            {loading && <span className="text-xs text-slate-500">Loading...</span>}
          </div>
        </div>
        <div className="max-h-[520px] overflow-y-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-900">
              <tr>
                <th className="px-4 py-2 text-left text-slate-400 font-medium">Time</th>
                <th className="px-4 py-2 text-left text-slate-400 font-medium">Department</th>
                <th className="px-4 py-2 text-left text-slate-400 font-medium">Resource</th>
                <th className="px-4 py-2 text-left text-slate-400 font-medium">Severity</th>
                <th className="px-4 py-2 text-left text-slate-400 font-medium">CPU</th>
                <th className="px-4 py-2 text-left text-slate-400 font-medium">Memory</th>
                <th className="px-4 py-2 text-left text-slate-400 font-medium">Load Avg</th>
                <th className="px-4 py-2 text-left text-slate-400 font-medium">Daily Cost</th>
                <th className="px-4 py-2 text-left text-slate-400 font-medium">Explanation</th>
              </tr>
            </thead>
            <tbody>
              {anomalies.map((a, idx) => {
                const severityColor =
                  a.severity === "high"
                    ? "text-rose-400"
                    : a.severity === "moderate"
                    ? "text-amber-400"
                    : "text-slate-300"
                return (
                  <tr key={idx} className="border-t border-slate-800 hover:bg-slate-900/60">
                    <td className="px-4 py-2 text-slate-300 whitespace-nowrap">{a.timestamp}</td>
                    <td className="px-4 py-2 text-slate-300 whitespace-nowrap">{a.department}</td>
                    <td className="px-4 py-2 text-slate-300 whitespace-nowrap">{a.resource_id}</td>
                    <td className="px-4 py-2 font-medium whitespace-nowrap">
                      <span className={severityColor}>{a.severity}</span>
                    </td>
                    <td className="px-4 py-2 text-slate-300 whitespace-nowrap">{a.cpu_pct.toFixed(2)}</td>
                    <td className="px-4 py-2 text-slate-300 whitespace-nowrap">{a.mem_pct.toFixed(2)}</td>
                    <td className="px-4 py-2 text-slate-300 whitespace-nowrap">{a.load_avg.toFixed(2)}</td>
                    <td className="px-4 py-2 text-slate-300 whitespace-nowrap">{a.daily_cost.toFixed(2)}</td>
                    <td className="px-4 py-2 text-slate-200 max-w-xl">{a.explanation}</td>
                  </tr>
                )
              })}
              {!loading && anomalies.length === 0 && (
                <tr>
                  <td colSpan={9} className="px-4 py-10 text-center text-slate-500">
                    No anomalies detected for this department.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs uppercase tracking-wide text-slate-500 mb-1">Anomaly model accuracy</div>
            <div className="text-xs text-slate-400">Isolation Forest vs cost threshold over recent evaluations</div>
          </div>
          {metricsLoading && <span className="text-xs text-slate-500">Loading metrics...</span>}
        </div>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={metrics}>
              <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
              <XAxis dataKey="time" stroke="#94a3b8" tickFormatter={(t) => (t || "").slice(5, 16)} />
              <YAxis stroke="#94a3b8" domain={[0, 1]} />
              <Tooltip contentStyle={{ backgroundColor: "#020617", borderColor: "#1e293b" }} />
              <Legend />
              <Line type="monotone" dataKey="precision" stroke="#22c55e" strokeWidth={2} dot={false} name="Precision" />
              <Line type="monotone" dataKey="recall" stroke="#38bdf8" strokeWidth={2} dot={false} name="Recall" />
              <Line type="monotone" dataKey="f1" stroke="#f97316" strokeWidth={2} dot={false} name="F1" />
              <Line type="monotone" dataKey="accuracy" stroke="#8b5cf6" strokeWidth={2} dot={false} name="Accuracy" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

export default AnomalyDetectionPage
