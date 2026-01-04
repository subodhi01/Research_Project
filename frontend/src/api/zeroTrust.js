import api from "./client"

export async function zeroTrustLogin(payload) {
  const res = await api.post("/api/zero-trust/login", payload)
  return res.data
}

export async function getZeroTrustUsers() {
  const res = await api.get("/api/zero-trust/users")
  return res.data
}

export async function getZeroTrustRecentEvents(limit = 20) {
  const res = await api.get(`/api/zero-trust/login-events/recent?limit=${limit}`)
  return res.data
}

export async function getZeroTrustStats(windowMinutes = 1440) {
  const res = await api.get(`/api/zero-trust/stats?window_minutes=${windowMinutes}`)
  return res.data
}

export async function getUserMonitoringData(username) {
  const res = await api.get(`/api/zero-trust/users/${username}/monitoring`)
  return res.data
}


