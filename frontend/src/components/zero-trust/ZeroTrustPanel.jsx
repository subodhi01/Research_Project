import React, { useEffect, useState } from "react"
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts"
import { getZeroTrustUsers, getZeroTrustRecentEvents, getZeroTrustStats, zeroTrustLogin, getUserMonitoringData } from "../../api/zeroTrust"

function ZeroTrustPanel() {
  const [users, setUsers] = useState([])
  const [events, setEvents] = useState([])
  const [stats, setStats] = useState(null)
  const [selectedUser, setSelectedUser] = useState("")
  const [userMonitoring, setUserMonitoring] = useState(null)
  const [form, setForm] = useState({
    password_length: 0,
    used_special_characters: "no",
    keyboard_language: "",
    login_attempts: 1,
    was_capslock_on: "no",
    browser_tab_count: 1,
    challenge_sequence: "",
    timezone: "",
    typing_speed_wpm: 0,
  })
  const [lastResult, setLastResult] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const detectKeyboardLanguage = () => {
      try {
        const lang = navigator.language || navigator.userLanguage || "en-US"
        const langCode = lang.split("-")[0].toUpperCase()
        return langCode || "EN"
      } catch {
        return "EN"
      }
    }

    const detectBrowserTabs = () => {
      try {
        if (typeof Storage !== "undefined" && localStorage) {
          const tabCount = localStorage.getItem("browserTabCount")
          if (tabCount) {
            const count = parseInt(tabCount, 10)
            if (!isNaN(count) && count > 0) {
              return count
            }
          }
        }
        return 1
      } catch {
        return 1
      }
    }

    const detectTimezone = () => {
      try {
        return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC"
      } catch {
        return "UTC"
      }
    }

    setForm((prev) => ({
      ...prev,
      keyboard_language: detectKeyboardLanguage(),
      browser_tab_count: detectBrowserTabs(),
      timezone: detectTimezone(),
    }))
  }, [])

  const loadData = async () => {
    const [usersRes, eventsRes, statsRes] = await Promise.all([
      getZeroTrustUsers(),
      getZeroTrustRecentEvents(20),
      getZeroTrustStats(1440),
    ])
    setUsers(usersRes.items || [])
    setEvents(eventsRes.items || [])
    setStats(statsRes || null)
    if (!selectedUser && usersRes.items && usersRes.items.length > 0) {
      setSelectedUser(usersRes.items[0].username)
    }
  }

  const loadUserMonitoring = async (username) => {
    if (!username) {
      setUserMonitoring(null)
      return
    }
    try {
      const data = await getUserMonitoringData(username)
      setUserMonitoring(data)
    } catch (err) {
      console.error("Failed to load user monitoring:", err)
      setUserMonitoring(null)
    }
  }

  useEffect(() => {
    loadData()
    const id = setInterval(loadData, 8000)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    loadUserMonitoring(selectedUser)
    const id = setInterval(() => loadUserMonitoring(selectedUser), 10000)
    return () => clearInterval(id)
  }, [selectedUser])

  const onChangeField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const onSubmitLogin = async (e) => {
    e.preventDefault()
    if (!selectedUser) {
      return
    }
    setLoading(true)
    try {
      const payload = { ...form, username: selectedUser }
      const res = await zeroTrustLogin(payload)
      setLastResult({ user: selectedUser, result: res })
      const userInfo = users.find((u) => u.username === selectedUser)
      if (userInfo) {
        const sessionUser = {
          username: userInfo.username,
          full_name: userInfo.full_name,
          email: userInfo.email,
          department: userInfo.department,
          role: userInfo.role,
        }
        window.localStorage.setItem("finsightCurrentUser", JSON.stringify(sessionUser))
        window.dispatchEvent(new Event("finsight-current-user-changed"))
      }
      await loadData()
      await loadUserMonitoring(selectedUser)
    } catch (err) {
      setLastResult(null)
    } finally {
      setLoading(false)
    }
  }

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
    <div className="p-6 space-y-6">
      <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 flex flex-col gap-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">Zero Trust Login Risk</h2>
            <p className="text-xs text-slate-400">Real-time login risk scoring based on password hygiene and session behavior patterns</p>
          </div>
          <div className="text-xs text-slate-400 space-y-1 text-right">
            {stats && (
              <>
                <div>Total logins (24h): {stats.total_events}</div>
                <div>
                  High {stats.high} · Medium {stats.medium} · Low {stats.low}
                </div>
              </>
            )}
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 text-xs">
          <form onSubmit={onSubmitLogin} className="space-y-3 lg:col-span-1">
            <div className="space-y-1">
              <div className="text-slate-400 text-[11px]">User</div>
              <select
                className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-100 text-xs"
                value={selectedUser}
                onChange={(e) => setSelectedUser(e.target.value)}
              >
                <option value="">Select user</option>
                {users.map((u) => (
                  <option key={u.id} value={u.username}>
                    {u.username} {u.full_name ? `· ${u.full_name}` : ""} {u.department ? `· ${u.department}` : ""}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <div className="text-slate-400 text-[11px]">Password length</div>
                <input
                  type="number"
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-right text-slate-100 text-xs"
                  value={form.password_length}
                  min={4}
                  max={32}
                  onChange={(e) => onChangeField("password_length", Number(e.target.value) || 0)}
                />
              </div>
              <div className="space-y-1">
                <div className="text-slate-400 text-[11px]">Special characters</div>
                <select
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-100 text-xs"
                  value={form.used_special_characters}
                  onChange={(e) => onChangeField("used_special_characters", e.target.value)}
                >
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </div>
              <div className="space-y-1">
                <div className="text-slate-400 text-[11px]">Login attempts</div>
                <input
                  type="number"
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-right text-slate-100 text-xs"
                  value={form.login_attempts}
                  min={1}
                  max={20}
                  onChange={(e) => onChangeField("login_attempts", Number(e.target.value) || 0)}
                />
              </div>
              <div className="space-y-1">
                <div className="text-slate-400 text-[11px]">Caps Lock</div>
                <select
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-100 text-xs"
                  value={form.was_capslock_on}
                  onChange={(e) => onChangeField("was_capslock_on", e.target.value)}
                >
                  <option value="no">Off</option>
                  <option value="yes">On</option>
                </select>
              </div>
              <div className="space-y-1">
                <div className="text-slate-400 text-[11px]">Browser tabs</div>
                <input
                  type="number"
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-right text-slate-100 text-xs"
                  value={form.browser_tab_count}
                  min={1}
                  max={40}
                  onChange={(e) => onChangeField("browser_tab_count", Number(e.target.value) || 0)}
                />
              </div>
              <div className="space-y-1">
                <div className="text-slate-400 text-[11px]">Typing speed (WPM)</div>
                <input
                  type="number"
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-right text-slate-100 text-xs"
                  value={form.typing_speed_wpm}
                  min={10}
                  max={200}
                  onChange={(e) => onChangeField("typing_speed_wpm", Number(e.target.value) || 0)}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <div className="text-slate-400 text-[11px]">Keyboard language</div>
                <input
                  type="text"
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-100 text-xs"
                  value={form.keyboard_language}
                  onChange={(e) => onChangeField("keyboard_language", e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <div className="text-slate-400 text-[11px]">Timezone</div>
                <input
                  type="text"
                  className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-100 text-xs"
                  value={form.timezone}
                  onChange={(e) => onChangeField("timezone", e.target.value)}
                />
              </div>
            </div>
            <div className="bg-slate-950/50 border border-slate-800 rounded-lg px-3 py-2 text-[11px] text-slate-400">
              <strong className="text-slate-300">Login with Zero Trust:</strong> This performs a real login that scores your session using ML models, stores the risk assessment in the database, and updates user monitoring. The system analyzes password strength, typing patterns, and behavioral signals to assess risk.
            </div>
            <button
              type="submit"
              disabled={loading || !selectedUser}
              className="w-full mt-1 px-3 py-2 rounded-md bg-indigo-600 text-xs text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              {loading ? "Scoring login..." : "Login with Zero Trust"}
            </button>
            {lastResult && (
              <div className="mt-3 rounded-xl border border-slate-700 bg-slate-900/80 px-3 py-2 space-y-1">
                <div className="flex items-center justify-between">
                  <div className="text-[11px] text-slate-400">
                    Last login for {lastResult.user}
                  </div>
                  <span className={riskBadgeClass(lastResult.result.risk_level)}>
                    {lastResult.result.risk_level || "unknown"}
                  </span>
                </div>
                <div className="text-sm text-slate-100">
                  Risk score {lastResult.result.risk_score != null ? lastResult.result.risk_score.toFixed(2) : "n/a"}
                </div>
                {lastResult.result.reasons && lastResult.result.reasons.length > 0 && (
                  <div className="text-[11px] text-slate-400">
                    Triggers: {lastResult.result.reasons.join(", ")}
                  </div>
                )}
              </div>
            )}
          </form>
          <div className="lg:col-span-1 space-y-2">
            <div className="flex items-center justify-between">
              <div className="text-[11px] uppercase tracking-wide text-slate-500">Users</div>
              <div className="text-[11px] text-slate-500">{users.length} users</div>
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
              {users.map((u) => (
                <div
                  key={u.id}
                  className={`flex items-center justify-between rounded-xl border px-3 py-2 cursor-pointer transition-colors ${
                    selectedUser === u.username
                      ? "border-indigo-500/50 bg-indigo-500/10"
                      : "border-slate-800 bg-slate-900/70"
                  }`}
                  onClick={() => setSelectedUser(u.username)}
                >
                  <div>
                    <div className="text-sm font-medium text-slate-100">
                      {u.username} {u.full_name ? `· ${u.full_name}` : ""}
                    </div>
                    <div className="text-[11px] text-slate-400">
                      {u.department || "Unknown"} {u.role ? `· ${u.role}` : ""}
                    </div>
                  </div>
                  <div className="text-right text-[11px]">
                    {u.last_risk_level && (
                      <div className={riskBadgeClass(u.last_risk_level)}>{u.last_risk_level}</div>
                    )}
                    {u.last_risk_score != null && (
                      <div className="mt-1 text-slate-300">
                        {u.last_risk_score.toFixed(2)}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {users.length === 0 && <div className="text-[11px] text-slate-500">No users found</div>}
            </div>
          </div>
          <div className="lg:col-span-1 space-y-2">
            <div className="flex items-center justify-between">
              <div className="text-[11px] uppercase tracking-wide text-slate-500">Recent logins</div>
              <div className="text-[11px] text-slate-500">{events.length}</div>
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
              {events.map((e) => (
                <div
                  key={e.id}
                  className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/70 px-3 py-2"
                >
                  <div>
                    <div className="text-sm font-medium text-slate-100">{e.username}</div>
                    <div className="text-[11px] text-slate-500">
                      {e.created_at ? new Date(e.created_at).toLocaleTimeString() : ""}
                    </div>
                  </div>
                  <div className="text-right text-[11px]">
                    <div className={riskBadgeClass(e.risk_level)}>{e.risk_level}</div>
                    {e.risk_score != null && (
                      <div className="mt-1 text-slate-300">
                        {e.risk_score.toFixed(2)}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {events.length === 0 && <div className="text-[11px] text-slate-500">No login events yet</div>}
            </div>
          </div>
        </div>
      </section>

      {selectedUser && userMonitoring && userMonitoring.exists && (
        <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">User Monitoring: {userMonitoring.username}</h2>
              <p className="text-xs text-slate-400">
                {userMonitoring.full_name} · {userMonitoring.department} · {userMonitoring.role}
              </p>
            </div>
            <div className="text-xs text-slate-400 text-right">
              <div>Auto-monitoring active</div>
              <div>Updates every 10s</div>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
            <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-3">
              <div className="text-[11px] text-slate-500 mb-1">Total Logins</div>
              <div className="text-2xl font-bold text-slate-100">{userMonitoring.total_logins}</div>
            </div>
            <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-3">
              <div className="text-[11px] text-slate-500 mb-1">Avg Risk Score</div>
              <div className="text-2xl font-bold text-slate-100">{userMonitoring.avg_risk_score.toFixed(2)}</div>
            </div>
            <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-3">
              <div className="text-[11px] text-slate-500 mb-1">High Risk</div>
              <div className="text-2xl font-bold text-rose-400">{userMonitoring.high_risk_count}</div>
            </div>
            <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-3">
              <div className="text-[11px] text-slate-500 mb-1">Low Risk</div>
              <div className="text-2xl font-bold text-emerald-400">{userMonitoring.low_risk_count}</div>
            </div>
          </div>
          {userMonitoring.risk_trend && userMonitoring.risk_trend.length > 0 && (
            <div className="space-y-2">
              <div className="text-[11px] uppercase tracking-wide text-slate-500">Risk Trend (Last 30 Logins)</div>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={userMonitoring.risk_trend}>
                    <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      stroke="#94a3b8"
                      tick={{ fontSize: 10 }}
                      tickFormatter={(t) => (t ? new Date(t).toLocaleTimeString() : "")}
                    />
                    <YAxis stroke="#94a3b8" domain={[0, 1]} tick={{ fontSize: 10 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "#020617", borderColor: "#1e293b" }}
                      labelFormatter={(t) => (t ? new Date(t).toLocaleString() : "")}
                    />
                    <Line
                      type="monotone"
                      dataKey="risk_score"
                      stroke="#f43f5e"
                      strokeWidth={2}
                      dot={false}
                      name="Risk Score"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
          {userMonitoring.events && userMonitoring.events.length > 0 && (
            <div className="space-y-2">
              <div className="text-[11px] uppercase tracking-wide text-slate-500">Recent Login History</div>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {userMonitoring.events.slice(0, 10).map((e) => (
                  <div
                    key={e.id}
                    className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/70 px-3 py-2"
                  >
                    <div>
                      <div className="text-sm text-slate-100">
                        {e.created_at ? new Date(e.created_at).toLocaleString() : "Unknown time"}
                      </div>
                      {e.reasons && e.reasons.length > 0 && (
                        <div className="text-[11px] text-slate-400 mt-1">
                          Triggers: {e.reasons.join(", ")}
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
                ))}
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  )
}

export default ZeroTrustPanel
