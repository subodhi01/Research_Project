import React from "react"
import { BrowserRouter, Routes, Route } from "react-router-dom"
import Sidebar from "./components/finsight-dashboard/Sidebar"
import Overview from "./components/finsight-dashboard/Overview"
import ForecastPanel from "./components/forecasting-budget/ForecastPanel"
import DepartmentDashboard from "./components/finsight-dashboard/DepartmentDashboard"
import DashboardHeader from "./components/finsight-dashboard/DashboardHeader"
import InsightsPage from "./components/finsight-dashboard/InsightsPage"
import AnomalyDetectionPage from "./components/finsight-dashboard/AnomalyDetectionPage"
import ZeroTrustPage from "./components/finsight-dashboard/ZeroTrustPage"
import OptimizationPage from "./components/finsight-dashboard/OptimizationPage"
import LoginPage from "./components/auth/LoginPage"
import ProtectedRoute from "./components/auth/ProtectedRoute"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
      <div className="flex h-screen bg-slate-950 text-slate-50 overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <DashboardHeader />
          <main className="flex-1 overflow-y-auto">
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/forecast" element={<div className="p-6"><ForecastPanel /></div>} />
              <Route path="/insights" element={<InsightsPage />} />
              <Route path="/anomaly" element={<AnomalyDetectionPage />} />
                      <Route path="/zero-trust" element={<ZeroTrustPage />} />
                      <Route path="/optimization" element={<OptimizationPage />} />
              <Route path="/dept/:dept" element={<DepartmentDashboard />} />
            </Routes>
          </main>
        </div>
      </div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
