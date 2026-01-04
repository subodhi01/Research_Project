import React, { useEffect, useState } from "react"
import { getRealtimeEvents } from "../../api/auth"

function AdminLoginDetailsPanel() {
  const [events, setEvents] = useState([])
  const [expandedEvent, setExpandedEvent] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)

  const loadEvents = async () => {
    try {
      const since = lastUpdate || new Date(Date.now() - 3600000).toISOString()
      const data = await getRealtimeEvents(since, 100)
      if (data.items && data.items.length > 0) {
        setEvents(data.items)
        setLastUpdate(new Date().toISOString())
      }
    } catch (err) {
      console.error("Failed to load login events:", err)
    }
  }

  useEffect(() => {
    loadEvents()
    const id = setInterval(loadEvents, 5000)
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

  const formatMetric = (key, value) => {
    if (value === null || value === undefined) return "N/A"
    if (typeof value === "boolean") return value ? "Yes" : "No"
    if (typeof value === "number") {
      if (key.includes("wpm") || key.includes("speed")) {
        return `${value.toFixed(1)} WPM`
      }
      return value.toString()
    }
    return String(value)
  }

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold">Admin: Login Details & Analysis</h2>
          <p className="text-xs text-slate-400">Complete login metrics and risk analysis for all users</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
          <span className="text-xs text-slate-400">Auto-refresh</span>
          <span className="text-xs text-slate-500">({events.length} events)</span>
        </div>
      </div>
      <div className="space-y-3 max-h-[600px] overflow-y-auto">
        {events.length === 0 ? (
          <div className="text-center py-8 text-sm text-slate-500">
            No login events found. Events will appear here as users log in.
          </div>
        ) : (
          events.map((e) => (
            <div
              key={e.id}
              className="rounded-xl border border-slate-800 bg-slate-900/70 overflow-hidden"
            >
              <div
                className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-slate-800/50 transition-colors"
                onClick={() => setExpandedEvent(expandedEvent === e.id ? null : e.id)}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <div className="text-sm font-medium text-slate-100">{e.username}</div>
                    <span className={riskBadgeClass(e.risk_level)}>{e.risk_level}</span>
                    {e.risk_score != null && (
                      <span className="text-xs text-slate-400">
                        Risk: {e.risk_score.toFixed(3)}
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    {e.created_at ? new Date(e.created_at).toLocaleString() : "Unknown time"}
                  </div>
                  {e.reasons && e.reasons.length > 0 && (
                    <div className="text-[11px] text-slate-400 mt-1">
                      Flags: {e.reasons.join(", ")}
                    </div>
                  )}
                </div>
                <div className="text-slate-400 text-xs">
                  {expandedEvent === e.id ? "▼" : "▶"}
                </div>
              </div>

              {expandedEvent === e.id && e.payload && (
                <div className="border-t border-slate-800 px-4 py-4 bg-slate-950/50">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="space-y-3">
                      <div className="text-[11px] uppercase tracking-wide text-slate-500 mb-2">
                        Password Analysis
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-slate-400">Password Length:</span>
                          <span className="text-slate-200 font-mono">
                            {formatMetric("password_length", e.payload.password_length)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Special Characters:</span>
                          <span className="text-slate-200">
                            {formatMetric("used_special_characters", e.payload.used_special_characters)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="text-[11px] uppercase tracking-wide text-slate-500 mb-2">
                        Typing Behavior
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-slate-400">Typing Speed (WPM):</span>
                          <span className="text-slate-200 font-mono">
                            {formatMetric("typing_speed_wpm", e.payload.typing_speed_wpm)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Caps Lock:</span>
                          <span className="text-slate-200">
                            {formatMetric("was_capslock_on", e.payload.was_capslock_on)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="text-[11px] uppercase tracking-wide text-slate-500 mb-2">
                        Browser Environment
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-slate-400">Browser Tabs:</span>
                          <span className="text-slate-200 font-mono">
                            {formatMetric("browser_tab_count", e.payload.browser_tab_count)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Keyboard Language:</span>
                          <span className="text-slate-200">
                            {formatMetric("keyboard_language", e.payload.keyboard_language)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Timezone:</span>
                          <span className="text-slate-200 text-[10px]">
                            {formatMetric("timezone", e.payload.timezone)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="text-[11px] uppercase tracking-wide text-slate-500 mb-2">
                        Login Attempts
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-slate-400">Attempt Count:</span>
                          <span className="text-slate-200 font-mono">
                            {formatMetric("login_attempts", e.payload.login_attempts)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Challenge Sequence:</span>
                          <span className="text-slate-200 text-[10px] font-mono">
                            {formatMetric("challenge_sequence", e.payload.challenge_sequence)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {e.reasons && e.reasons.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-slate-800">
                      <div className="text-[11px] uppercase tracking-wide text-slate-500 mb-2">
                        Risk Flags Detected
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {e.reasons.map((reason, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/30"
                          >
                            {reason.replace(/_/g, " ")}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="mt-4 pt-4 border-t border-slate-800">
                    <div className="text-[11px] uppercase tracking-wide text-slate-500 mb-2">
                      Raw Payload Data
                    </div>
                    <pre className="text-[10px] text-slate-400 bg-slate-950 p-2 rounded overflow-x-auto">
                      {JSON.stringify(e.payload, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default AdminLoginDetailsPanel

