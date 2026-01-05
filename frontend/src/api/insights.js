import api from "./client"

export async function getInsightsSummary(defaultBudget = 3000) {
  const res = await api.get(`/api/insights/summary?default_budget=${defaultBudget}`)
  return res.data
}

export async function getRoleInsight(role, defaultBudget = 3000) {
  const res = await api.get(`/api/insights/role/${role}?default_budget=${defaultBudget}`)
  return res.data
}

export async function getInsightStory(defaultBudget = 3000) {
  const res = await api.get(`/api/insights/story?default_budget=${defaultBudget}`)
  return res.data
}
