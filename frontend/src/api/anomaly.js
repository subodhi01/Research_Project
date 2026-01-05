import api from "./client"

export async function getAnomalies() {
  const res = await api.get("/api/anomaly/detect")
  return res.data
}

export async function getCloudAnomalies(params) {
  const res = await api.get("/api/anomaly/detect/iforest", { params })
  return res.data
}

export async function getAnomalyMetrics(limit = 50, modelName) {
  const params = { limit }
  if (modelName) {
    params.model_name = modelName
  }
  const res = await api.get("/api/anomaly/metrics/model-runs", { params })
  return res.data
}
