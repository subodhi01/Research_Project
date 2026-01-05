import React, { useEffect, useState } from "react"
import { NavLink } from "react-router-dom"

function Sidebar() {
  const [currentUser, setCurrentUser] = useState(null)

  useEffect(() => {
    const load = () => {
      try {
        const raw = window.localStorage.getItem("finsightCurrentUser")
        if (raw) {
          setCurrentUser(JSON.parse(raw))
        } else {
          setCurrentUser(null)
        }
      } catch (e) {
        setCurrentUser(null)
      }
    }
    load()
    const onStorage = () => load()
    const onCustom = () => load()
    window.addEventListener("storage", onStorage)
    window.addEventListener("finsight-current-user-changed", onCustom)
    return () => {
      window.removeEventListener("storage", onStorage)
      window.removeEventListener("finsight-current-user-changed", onCustom)
    }
  }, [])

  const navItems = [
    { name: "Overview", path: "/" },
    { name: "Forecasting & Budget", path: "/forecast" },
    { name: "Insights", path: "/insights" },
    { name: "Anomaly Detection", path: "/anomaly" },
    { name: "Optimization", path: "/optimization" },
    { name: "Zero Trust Login", path: "/zero-trust" },
    { type: "separator", label: "Departments" },
    { name: "HR Monitor", path: "/dept/HR" },
    { name: "IT Monitor", path: "/dept/IT" },
    { name: "Dev Monitor", path: "/dept/Dev" },
    { name: "Management", path: "/dept/Management" },
  ]

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col min-h-screen">
      <div className="p-6 border-b border-slate-800">
        <h1 className="text-xl font-bold bg-gradient-to-r from-sky-400 to-indigo-400 bg-clip-text text-transparent">
          FinSight
        </h1>
        <p className="text-xs text-slate-500 mt-1">Cloud Cost Intelligence</p>
      </div>
      
      <nav className="flex-1 py-6 px-3 space-y-1">
        {navItems.map((item, idx) => (
          item.type === "separator" ? (
            <div key={idx} className="px-3 pt-4 pb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              {item.label}
            </div>
          ) : (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  isActive
                    ? "bg-slate-800 text-sky-400 border-l-2 border-sky-400"
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                }`
              }
            >
              {item.name}
            </NavLink>
          )
        ))}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-bold text-xs">
            {(currentUser && currentUser.username ? currentUser.username.slice(0, 2) : "AD").toUpperCase()}
          </div>
          <div>
            <div className="text-sm font-medium text-slate-200">
              {currentUser && currentUser.username ? currentUser.username : "Admin User"}
            </div>
            <div className="text-xs text-slate-500">
              {currentUser && currentUser.email ? currentUser.email : "admin@cloudcost.space"}
            </div>
          </div>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
