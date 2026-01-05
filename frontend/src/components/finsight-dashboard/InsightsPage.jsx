import React, { useEffect, useState } from "react"
import { getInsightsSummary, getRoleInsight, getInsightStory } from "../../api/insights"
import { getForecastHistory } from "../../api/forecast"
import { submitFeedback } from "../../api/ux"

function InsightsPage() {
  const [summary, setSummary] = useState(null)
  const [finance, setFinance] = useState(null)
  const [it, setIt] = useState(null)
  const [dev, setDev] = useState(null)
  const [management, setManagement] = useState(null)
  const [budget, setBudget] = useState(3000)
  const [loading, setLoading] = useState(false)
  const [story, setStory] = useState(null)
  const [heatmap, setHeatmap] = useState(null)
  const [feedbackRating, setFeedbackRating] = useState(null)
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)

  useEffect(() => {
    loadInsights(3000)
  }, [])

  const loadInsights = async (b) => {
    setLoading(true)
    const s = await getInsightsSummary(b)
    const f = await getRoleInsight("finance", b)
    const itRole = await getRoleInsight("it", b)
    const d = await getRoleInsight("dev", b)
    const m = await getRoleInsight("management", b)
    const storyRes = await getInsightStory(b)
    const history = await getForecastHistory(30)
    setSummary(s)
    setFinance(f)
    setIt(itRole)
    setDev(d)
    setManagement(m)
    setStory(storyRes)
    setHeatmap(history)
    setLoading(false)
  }

  const handleBudgetChange = async (e) => {
    const value = Number(e.target.value) || 0
    setBudget(value)
  }

  const handleApplyBudget = async () => {
    if (budget <= 0) return
    await loadInsights(budget)
  }

  const handleFeedback = async (rating) => {
    if (feedbackSubmitted) return
    setFeedbackRating(rating)
    try {
      await submitFeedback({
        page: "insights",
        component: "FinSightInsights",
        rating,
        comment: "",
        user_email: "",
      })
      setFeedbackSubmitted(true)
    } catch (e) {
      setFeedbackSubmitted(false)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-50">FinSight Insights</h1>
          <p className="text-sm text-slate-400">AI-assisted summaries for Finance, IT, Dev, and Management</p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="text-slate-400">Scenario budget</span>
          <input
            type="number"
            className="w-28 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-right text-slate-100 text-xs"
            value={budget}
            onChange={handleBudgetChange}
          />
          <button
            type="button"
            onClick={handleApplyBudget}
            disabled={loading || budget <= 0}
            className="px-3 py-1 rounded-md bg-sky-600 text-xs text-white hover:bg-sky-500 disabled:opacity-50"
          >
            Run Scenario
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="text-xs uppercase tracking-wide text-slate-500 mb-2">Budget posture</div>
          <div className="text-lg font-semibold text-slate-50 mb-1">
            {summary ? summary.forecast.status.replace(/_/g, " ") : "--"}
          </div>
          <div className="text-xs text-slate-400">
            {summary ? summary.nlg : "Loading insights"}
          </div>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="text-xs uppercase tracking-wide text-slate-500 mb-2">Potential monthly savings</div>
          <div className="text-3xl font-bold text-emerald-400">
            {summary ? `$${summary.recommendations.total_positive_saving.toFixed(2)}` : "--"}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Impact level: <span className="font-semibold">{summary ? summary.recommendations.impact_level : "--"}</span>
          </div>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="text-xs uppercase tracking-wide text-slate-500 mb-2">Critical departments</div>
          <div className="text-3xl font-bold text-rose-400">
            {summary ? summary.monitor.filter(m => m.status === "critical").length : "--"}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Warning departments: {summary ? summary.monitor.filter(m => m.status === "warning").length : "--"}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 space-y-3">
          <div className="text-xs uppercase tracking-wide text-slate-500 mb-1">Narrative story</div>
          <p className="text-sm text-slate-300 leading-relaxed min-h-[80px]">
            {story ? story.story : "Generating story from forecast, anomalies, and monitoring data."}
          </p>
          {story && story.resource_insights && story.resource_insights.length > 0 && (
            <ul className="mt-2 space-y-1 text-xs text-slate-400">
              {story.resource_insights.map((r) => (
                <li key={r.title} className="flex items-start gap-2">
                  <span className="mt-1 h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  <span>{r.text}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs uppercase tracking-wide text-slate-500">Insights feedback</div>
            {feedbackSubmitted && (
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                Saved
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 text-xs">
            <button
              type="button"
              onClick={() => handleFeedback(1)}
              disabled={feedbackSubmitted}
              className={`px-3 py-1 rounded-md border text-xs ${
                feedbackRating === 1
                  ? "bg-emerald-500/20 border-emerald-500/50 text-emerald-300"
                  : "bg-slate-900 border-slate-700 text-slate-200"
              } disabled:opacity-50`}
            >
              Helpful
            </button>
            <button
              type="button"
              onClick={() => handleFeedback(-1)}
              disabled={feedbackSubmitted}
              className={`px-3 py-1 rounded-md border text-xs ${
                feedbackRating === -1
                  ? "bg-rose-500/20 border-rose-500/50 text-rose-300"
                  : "bg-slate-900 border-slate-700 text-slate-200"
              } disabled:opacity-50`}
            >
              Not helpful
            </button>
          </div>
          <p className="text-[11px] text-slate-500">
            Feedback helps tune forecasts, narratives, and optimization signals over time.
          </p>
        </div>
      </div>

      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs uppercase tracking-wide text-slate-500 mb-1">Multi-cloud cost heatmap</div>
            <p className="text-xs text-slate-400">VPS and AWS daily cost intensity for the last 30 days</p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <div className="inline-flex flex-col gap-2 min-w-full">
            <HeatmapRow label="VPS" data={heatmap?.vps || []} />
            <HeatmapRow label="AWS" data={heatmap?.aws || []} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <InsightCard title="Finance" insight={finance?.insight} accent="from-emerald-400 to-sky-400" />
        <InsightCard title="IT / Ops" insight={it?.insight} accent="from-sky-400 to-indigo-400" />
        <InsightCard title="Developers" insight={dev?.insight} accent="from-indigo-400 to-fuchsia-400" />
        <InsightCard title="Management" insight={management?.insight} accent="from-amber-400 to-rose-400" />
      </div>
    </div>
  )
}

function InsightCard({ title, insight, accent }) {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col gap-3">
      <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r ${accent} text-slate-900`}>
        {title}
      </div>
      <p className="text-sm text-slate-300 leading-relaxed min-h-[80px]">
        {insight || "Insights will appear here once the engines have enough data."}
      </p>
    </div>
  )
}

function HeatmapRow({ label, data }) {
  const max = data.reduce((m, d) => (d.value > m ? d.value : m), 0)
  return (
    <div className="flex items-center gap-2">
      <div className="w-12 text-[11px] text-slate-400">{label}</div>
      <div className="flex-1 flex gap-1">
        {data.map((d) => {
          const intensity = max > 0 ? d.value / max : 0
          const alpha = 0.1 + intensity * 0.9
          const color = intensity > 0.66 ? `rgba(248, 113, 113, ${alpha})` : intensity > 0.33 ? `rgba(251, 146, 60, ${alpha})` : `rgba(52, 211, 153, ${alpha})`
          return (
            <div
              key={d.timestamp}
              className="h-6 w-4 rounded-sm border border-slate-800"
              style={{ backgroundColor: color }}
              title={`${label} ${d.timestamp.slice(0, 10)}: $${d.value.toFixed(2)}`}
            />
          )
        })}
      </div>
    </div>
  )
}

export default InsightsPage
