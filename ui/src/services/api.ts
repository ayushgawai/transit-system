import axios from 'axios'
import type { KPIData, Route, Stop, Alert, RouteHealth, Forecast, ApiResponse } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// KPIs
export async function fetchKPIs(): Promise<KPIData> {
  const response = await api.get<ApiResponse<KPIData>>('/kpis')
  return response.data.data
}

// Routes
export async function fetchRoutes(): Promise<Route[]> {
  const response = await api.get<ApiResponse<Route[]>>('/routes')
  return response.data.data
}

export async function fetchRouteById(id: string): Promise<Route> {
  const response = await api.get<ApiResponse<Route>>(`/routes/${id}`)
  return response.data.data
}

// Stops
export async function fetchStops(): Promise<Stop[]> {
  const response = await api.get<ApiResponse<Stop[]>>('/stops')
  return response.data.data
}

export async function fetchStopById(id: string): Promise<Stop> {
  const response = await api.get<ApiResponse<Stop>>(`/stops/${id}`)
  return response.data.data
}

// Alerts
export async function fetchAlerts(): Promise<Alert[]> {
  const response = await api.get<ApiResponse<Alert[]>>('/alerts')
  return response.data.data
}

// Route Health
export async function fetchRouteHealth(): Promise<RouteHealth[]> {
  const response = await api.get<ApiResponse<RouteHealth[]>>('/analytics/route-health')
  return response.data.data
}

// Forecasts
export async function fetchDemandForecast(hours: number = 6): Promise<Forecast[]> {
  const response = await api.get<ApiResponse<Forecast[]>>('/forecasts/demand', {
    params: { hours },
  })
  return response.data.data
}

export async function fetchDelayForecast(routeId: string): Promise<Forecast[]> {
  const response = await api.get<ApiResponse<Forecast[]>>(`/forecasts/delay/${routeId}`)
  return response.data.data
}

// Chatbot
export async function sendChatMessage(message: string): Promise<{ response: string; data?: unknown }> {
  const response = await api.post('/chat', { message })
  return response.data
}

// Health Check
export async function healthCheck(): Promise<{ status: string; version: string }> {
  const response = await api.get('/health')
  return response.data
}

export default api

