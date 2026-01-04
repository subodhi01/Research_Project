import api from "./client"

export async function login(username, password, zeroTrustMetrics = {}) {
  const res = await api.post("/api/auth/login", {
    username,
    password,
    ...zeroTrustMetrics,
  })
  return res.data
}

export async function getCurrentUser() {
  const res = await api.get("/api/auth/me")
  return res.data
}

export async function getRealtimeEvents(since = null, limit = 50) {
  const params = { limit }
  if (since) {
    params.since = since
  }
  const res = await api.get("/api/auth/realtime/events", { params })
  return res.data
}

