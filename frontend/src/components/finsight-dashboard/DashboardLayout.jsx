import React from "react"

function DashboardLayout({ children }) {
  return (
    <main className="flex-1 w-full max-w-7xl mx-auto">
      {children}
    </main>
  )
}

export default DashboardLayout
