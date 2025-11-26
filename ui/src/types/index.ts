// Transit Data Types

export interface Route {
  id: string
  name: string
  color: string
  agency: string
  type: 'Bus' | 'Subway' | 'Rail' | 'Tram'
  stops: number
  avgHeadway: number
  onTime: number
  reliability: number
  utilization: number
  revenue: number
  direction: string
  peakFrequency: string
  offPeakFrequency: string
}

export interface Stop {
  id: string
  name: string
  lat: number
  lon: number
  departures: number
  routes: string[]
  status: 'active' | 'alert' | 'inactive'
}

export interface Departure {
  id: string
  routeId: string
  stopId: string
  scheduledTime: Date
  actualTime: Date | null
  delay: number
  status: 'ON_TIME' | 'LATE' | 'VERY_LATE' | 'CANCELLED'
}

export interface KPIData {
  onTimePerformance: number
  activeRoutes: number
  totalDepartures: number
  estimatedRevenue: number
  activeAlerts: number
  avgDelay: number
}

export interface RouteHealth {
  route: string
  onTime: number
  reliability: number
  utilization: number
  status: 'healthy' | 'warning' | 'critical'
}

export interface Alert {
  id: string
  type: 'info' | 'warning' | 'danger'
  title: string
  description: string
  routeId?: string
  timestamp: Date
}

export interface Forecast {
  time: string
  actual: number | null
  predicted: number | null
  confidence?: number
}

export interface ChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  data?: {
    type: 'chart' | 'table' | 'metric'
    content: unknown
  }
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean
  data: T
  error?: string
  timestamp: string
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  total: number
  page: number
  pageSize: number
}

