import React from "react"
import AnomalyPanel from "../anomaly-engine/AnomalyPanel"
import OptimizePanel from "../optimization-engine/OptimizePanel"
import RealtimeEventsPanel from "./RealtimeEventsPanel"
import AdminLoginDetailsPanel from "./AdminLoginDetailsPanel"

function Overview() {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-slate-50">System Overview</h1>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <AnomalyPanel />
        <OptimizePanel />
      </div>
      <RealtimeEventsPanel />
      <AdminLoginDetailsPanel />
    </div>
  )
}

export default Overview
