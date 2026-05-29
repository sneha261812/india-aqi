import axios from 'axios'

const BASE = import.meta.env.VITE_API_BASE_URL || ''

const api = axios.create({
  baseURL: `${BASE}/api`,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// ── AQI ────────────────────────────────────────────────────────────────────
export const getAllCitiesAQI  = ()          => api.get('/aqi/all')
export const getCityAQI       = (city)      => api.get(`/aqi/current/${encodeURIComponent(city)}`)
export const getCityHistory   = (city, days=30) => api.get(`/aqi/history/${encodeURIComponent(city)}?days=${days}`)
export const getAlerts        = ()          => api.get('/aqi/alerts')

// ── Forecast ───────────────────────────────────────────────────────────────
export const getCityForecast  = (city, hours=72) => api.get(`/forecast/${encodeURIComponent(city)}?hours=${hours}`)

// ── Chatbot ────────────────────────────────────────────────────────────────
export const sendChatMessage  = (message, history=[]) => api.post('/chat/message', { message, history })

// ── Health ─────────────────────────────────────────────────────────────────
export const analyseRisk      = (payload)   => api.post('/health/risk', payload)

// ── Devices ────────────────────────────────────────────────────────────────
export const getDevices       = (payload)   => api.post('/devices/recommend', payload)

// ── States ─────────────────────────────────────────────────────────────────
export const getStates        = ()          => api.get('/states/')

export default api
