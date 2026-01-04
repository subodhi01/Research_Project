import React from "react"
import ZeroTrustPanel from "../zero-trust/ZeroTrustPanel"

function ZeroTrustPage() {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-slate-50">Zero Trust Login Risk</h1>
      <ZeroTrustPanel />
    </div>
  )
}

export default ZeroTrustPage


