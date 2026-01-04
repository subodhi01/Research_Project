import React, { useEffect, useState } from "react"
import { Navigate } from "react-router-dom"
import { getCurrentUser } from "../../api/auth"

function ProtectedRoute({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem("authToken")
      if (!token) {
        setIsAuthenticated(false)
        setLoading(false)
        return
      }

      try {
        await getCurrentUser()
        setIsAuthenticated(true)
      } catch (err) {
        setIsAuthenticated(false)
        localStorage.removeItem("authToken")
        localStorage.removeItem("finsightCurrentUser")
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-slate-400">Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return children
}

export default ProtectedRoute

