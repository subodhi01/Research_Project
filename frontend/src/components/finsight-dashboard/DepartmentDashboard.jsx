import React, { useEffect, useState, useRef } from "react"
import { useParams } from "react-router-dom"
import { getRealtimeStats, getRecommendations, deployRecommendation } from "../../api/monitor"
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts"

function DepartmentDashboard() {
  const { dept } = useParams()
  const [stats, setStats] = useState(null)
  const [history, setHistory] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [deploying, setDeploying] = useState(null)
  const [alert, setAlert] = useState(null)
  const timerRef = useRef(null)

  useEffect(() => {
    setHistory([])
    setAlert(null)

    const fetchStats = async () => {
      try {
        const data = await getRealtimeStats(dept)
        setStats(data)
        setHistory(prev => {
          const newHist = [...prev, { 
            time: new Date().toLocaleTimeString(), 
            cpu: data.cpu_usage, 
            mem: data.memory_usage,
            netSent: data.network_sent_mb,
            netRecv: data.network_recv_mb
          }]
          return newHist.slice(-20)
        })
      } catch (e) {
        console.error(e)
      }
    }

    const fetchRecs = async () => {
      try {
        const recs = await getRecommendations(dept)
        setRecommendations(recs)
      } catch (e) {
        console.error(e)
      }
    }

    fetchStats()
    fetchRecs()

    timerRef.current = setInterval(fetchStats, 2000)

    return () => clearInterval(timerRef.current)
  }, [dept])

  const handleDeploy = async (recId) => {
    setDeploying(recId)
    try {
      const res = await deployRecommendation(recId)
      if (res.status === "success") {
        setAlert({ type: "success", message: res.message })
      } else if (res.status === "rolled_back") {
        setAlert({ type: "error", message: res.message })
      }
      const recs = await getRecommendations(dept)
      setRecommendations(recs)
    } catch (e) {
      setAlert({ type: "error", message: "Deployment failed" })
    } finally {
      setDeploying(null)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-50">{dept} Department Monitor</h1>
          <p className="text-sm text-slate-400 mt-1">Real-time VPS slice monitoring</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-medium border ${
          stats?.status === 'critical' ? 'bg-rose-500/10 text-rose-400 border-rose-500/50' :
          stats?.status === 'warning' ? 'bg-amber-500/10 text-amber-400 border-amber-500/50' :
          'bg-emerald-500/10 text-emerald-400 border-emerald-500/50'
        }`}>
          System Status: {stats?.status?.toUpperCase() || "LOADING..."}
        </span>
      </header>

      {alert && (
        <div className={`p-4 rounded-lg border ${alert.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-200' : 'bg-rose-500/10 border-rose-500/30 text-rose-200'}`}>
          <p className="font-semibold">{alert.type === 'success' ? 'Success' : 'Rollback Triggered'}</p>
          <p className="text-sm">{alert.message}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-xs mb-2">CPU Usage</div>
          <div className="text-3xl font-bold text-sky-400">{stats?.cpu_usage || 0}%</div>
          <div className="text-xs text-slate-500 mt-1">System: {stats?.system_cpu || 0}%</div>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-xs mb-2">Memory Usage</div>
          <div className="text-3xl font-bold text-purple-400">{stats?.memory_usage || 0}%</div>
          <div className="text-xs text-slate-500 mt-1">System: {stats?.system_memory || 0}%</div>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-xs mb-2">Process Count</div>
          <div className="text-3xl font-bold text-emerald-400">{stats?.process_count || 0}</div>
          <div className="text-xs text-slate-500 mt-1">System: {stats?.system_processes || 0}</div>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-xs mb-2">Load Average</div>
          <div className="text-3xl font-bold text-amber-400">{stats?.load_average || 0}</div>
          <div className="text-xs text-slate-500 mt-1">System: {stats?.system_load || 0}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
          <h3 className="text-slate-400 text-sm mb-4">Real-time CPU Usage (%)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history}>
                <defs>
                  <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#38bdf8" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#94a3b8" fontSize={10} />
                <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={10} />
                <Tooltip contentStyle={{ backgroundColor: "#020617", borderColor: "#1e293b" }} />
                <Area type="monotone" dataKey="cpu" stroke="#38bdf8" fillOpacity={1} fill="url(#cpuGradient)" isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
          <h3 className="text-slate-400 text-sm mb-4">Real-time Memory Usage (%)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history}>
                <defs>
                  <linearGradient id="memGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#94a3b8" fontSize={10} />
                <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={10} />
                <Tooltip contentStyle={{ backgroundColor: "#020617", borderColor: "#1e293b" }} />
                <Area type="monotone" dataKey="mem" stroke="#a855f7" fillOpacity={1} fill="url(#memGradient)" isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
          <h3 className="text-slate-400 text-sm mb-4">Network I/O (MB)</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-slate-300 text-sm">Sent</span>
              <span className="text-lg font-semibold text-blue-400">{stats?.network_sent_mb || 0} MB</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-300 text-sm">Received</span>
              <span className="text-lg font-semibold text-green-400">{stats?.network_recv_mb || 0} MB</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
          <h3 className="text-slate-400 text-sm mb-4">Disk I/O (MB)</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-slate-300 text-sm">Read</span>
              <span className="text-lg font-semibold text-cyan-400">{stats?.disk_read_mb || 0} MB</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-300 text-sm">Write</span>
              <span className="text-lg font-semibold text-orange-400">{stats?.disk_write_mb || 0} MB</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4">Optimization Recommendations</h2>
        {recommendations.length === 0 ? (
          <p className="text-slate-500 text-sm">No active recommendations. System running optimally.</p>
        ) : (
          <div className="space-y-4">
            {recommendations.map((rec) => (
              <div key={rec.id} className="flex items-center justify-between bg-slate-800/50 p-4 rounded-lg border border-slate-700">
                <div>
                  <div className="font-medium text-slate-200">{rec.action} {rec.resource_id}</div>
                  <div className="text-sm text-slate-400">{rec.reason}</div>
                  <div className="text-xs text-slate-500 mt-1">
                    {rec.current_type}  a0 a0<span className="text-emerald-400">{rec.recommended_type}</span>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="text-sm font-medium text-emerald-400">
                      {rec.estimated_monthly_saving > 0 ? `+$${rec.estimated_monthly_saving}/mo` : `-$${Math.abs(rec.estimated_monthly_saving)}/mo`}
                    </div>
                    <div className="text-xs text-slate-500">Impact</div>
                  </div>
                  {rec.status === 'proposed' && (
                    <button 
                      onClick={() => handleDeploy(rec.id)}
                      disabled={deploying === rec.id}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg font-medium transition-colors disabled:opacity-50"
                    >
                      {deploying === rec.id ? "Deploying..." : "One-Click Deploy"}
                    </button>
                  )}
                   {rec.status === 'deployed' && (
                    <span className="px-3 py-1 bg-emerald-500/20 text-emerald-400 text-xs rounded border border-emerald-500/30">Deployed</span>
                  )}
                  {rec.status === 'rolled_back' && (
                    <span className="px-3 py-1 bg-rose-500/20 text-rose-400 text-xs rounded border border-rose-500/30">Rolled Back</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default DepartmentDashboard
