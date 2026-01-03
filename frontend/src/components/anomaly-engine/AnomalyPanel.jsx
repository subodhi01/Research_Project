import React, { useEffect, useState, useRef } from "react"
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts"
import { getAnomalies } from "../../api/anomaly"

function AnomalyPanel() {
  const [data, setData] = useState([])
  const [count, setCount] = useState(0)
  const timerRef = useRef(null)

  useEffect(() => {
    const load = async () => {
      const res = await getAnomalies()
      setData(res.anomalies || [])
      setCount(res.count || 0)
    }
    load()
    timerRef.current = setInterval(load, 5000)
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [])

  return (
    <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Cost Anomalies</h2>
          <p className="text-xs text-slate-400">Streaming anomaly feed on daily cost</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-semibold text-rose-400">{count}</p>
          <p className="text-xs text-slate-400">flagged spikes</p>
        </div>
      </div>
      <div className=" h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <XAxis dataKey="transaction_id" stroke="#94a3b8" tickMargin={8} />
            <YAxis stroke="#94a3b8" />
            <Tooltip contentStyle={{ backgroundColor: "#020617", borderColor: "#1e293b" }} />
            <Bar dataKey="cost" fill="#fb7185" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}

export default AnomalyPanel
