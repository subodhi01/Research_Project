import React, { useEffect, useState } from "react"
import { getRealtimeEvents } from "../../api/auth"

function RealtimeEventsPanel() {
  const [events, setEvents] = useState([])
  const [lastUpdate, setLastUpdate] = useState(null)

  const loadEvents = async () => {
    try {
      const since = lastUpdate || new Date(Date.now() - 60000).toISOString()
      const data = await getRealtimeEvents(since, 20)
      if (data.items && data.items.length > 0) {
        setEvents((prev) => {
          const newEvents = data.items.filter(
            (e) => !prev.find((p) => p.id === e.id)
          )
          return [...newEvents, ...prev].slice(0, 50)
        })
        setLastUpdate(new Date().toISOString())
      }
    } catch (err) {
      console.error("Failed to load realtime events:", err)
    }
  }

  useEffect(() => {
    loadEvents()
    const id = setInterval(loadEvents, 2000)
    return () => clearInterval(id)
  }, [])

  const riskBadgeClass = (level) => {
    if (level === "high") {
      return "px-2 py-1 rounded-full text-[11px] bg-rose-500/10 text-rose-400 border border-rose-500/40"
    }
    if (level === "medium") {
      return "px-2 py-1 rounded-full text-[11px] bg-amber-500/10 text-amber-400 border border-amber-500/40"
    }
    if (level === "low") {
      return "px-2 py-1 rounded-full text-[11px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/40"
    }
    return "px-2 py-1 rounded-full text-[11px] bg-slate-700/50 text-slate-300 border border-slate-600/60"
  }

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold">Real-Time Login Events</h2>
          <p className="text-xs text-slate-400">Live zero-trust login monitoring</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
          <span className="text-xs text-slate-400">Live</span>
        </div>
      </div>
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {events.length === 0 ? (
          <div className="text-center py-8 text-sm text-slate-500">
            No login events yet. Events will appear here in real-time.
          </div>
        ) : (
          events.map((e) => (
            <div
              key={e.id}
              className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/70 px-3 py-2 animate-fade-in"
            >
              <div>
                <div className="text-sm font-medium text-slate-100">{e.username}</div>
                <div className="text-[11px] text-slate-500">
                  {e.created_at ? new Date(e.created_at).toLocaleString() : ""}
                </div>
                {e.reasons && e.reasons.length > 0 && (
                  <div className="text-[11px] text-slate-400 mt-1">
                    {e.reasons.join(", ")}
                  </div>
                )}
              </div>
              <div className="text-right text-[11px]">
                <div className={riskBadgeClass(e.risk_level)}>{e.risk_level}</div>
                {e.risk_score != null && (
                  <div className="mt-1 text-slate-300">{e.risk_score.toFixed(2)}</div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default RealtimeEventsPanel

