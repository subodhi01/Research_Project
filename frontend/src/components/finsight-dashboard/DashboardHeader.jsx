import React from "react"
import { useNavigate } from "react-router-dom"

function DashboardHeader() {
  const navigate = useNavigate()
  const currentUser = JSON.parse(localStorage.getItem("finsightCurrentUser") || "{}")

  const handleLogout = () => {
    localStorage.removeItem("authToken")
    localStorage.removeItem("finsightCurrentUser")
    window.dispatchEvent(new Event("finsight-current-user-changed"))
    navigate("/login")
  }

  return (
    <header className="w-full border-b border-slate-800 bg-slate-900/70 backdrop-blur">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-50">Cloud Cost Intelligence Platform</h1>
          <p className="text-sm text-slate-400">FinSight dashboard for multi-cloud spend, anomalies, and optimization</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-3 py-1 rounded-full text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">Real time</span>
          <span className="px-3 py-1 rounded-full text-xs bg-sky-500/10 text-sky-400 border border-sky-500/30">refresh every 2s</span>
          {currentUser.username && (
            <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-800/50 border border-slate-700">
              <span className="text-xs text-slate-300">{currentUser.username}</span>
              <button
                onClick={handleLogout}
                className="text-xs text-slate-400 hover:text-slate-200"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}

export default DashboardHeader
