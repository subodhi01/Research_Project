import React from "react"
import OptimizePanel from "../optimization-engine/OptimizePanel"

function OptimizationPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-50">Optimization Engine</h1>
        <p className="text-sm text-slate-400 mt-1">
          ML-powered recommendations for cloud cost optimization and resource right-sizing
        </p>
      </div>
      <OptimizePanel />
    </div>
  )
}

export default OptimizationPage

