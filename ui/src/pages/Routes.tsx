import { useState, useEffect } from 'react'
import { getApiBaseUrl } from '../utils/api'
import clsx from 'clsx'
import { useAgency } from '../contexts/AgencyContext'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface Route {
  id: string
  name: string
  short_name?: string
  long_name?: string
  color: string
  agency: string
  city?: string
  type: number
  onTime?: number
  reliability?: number
  utilization?: number
  revenue?: number
  total_departures?: number
}

export default function Routes() {
  const { agency } = useAgency()
  const [routes, setRoutes] = useState<Route[]>([])
  const [selectedRoute, setSelectedRoute] = useState<Route | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchRoutes()
  }, [agency])

  useEffect(() => {
    if (routes.length > 0 && !selectedRoute) {
      setSelectedRoute(routes[0])
    }
  }, [routes])

  const fetchRoutes = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const url = agency === 'All'
        ? `${getApiBaseUrl()}/routes`
        : `${getApiBaseUrl()}/routes?agency=${agency}`
      
      const response = await fetch(url)
      const result = await response.json()
      
      if (result.success) {
        const fetchedRoutes = result.data.map((r: any) => ({
          ...r,
          color: r.color ? `#${r.color}` : '#3FB950',
          onTime: r.onTime ?? 100.0, // Default to 100% if not provided (GTFS scheduled data)
          reliability: r.reliability ?? 100.0,
          utilization: r.utilization ?? 0,
          revenue: r.revenue || 0,
          total_departures: r.total_departures || 0,
        }))
        setRoutes(fetchedRoutes)
        if (fetchedRoutes.length > 0) {
          setSelectedRoute(fetchedRoutes[0])
        }
      } else {
        setError(result.error || 'Failed to fetch routes')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch routes')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-transit-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-dark-muted">Loading routes...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 bg-severity-danger/10 border border-severity-danger rounded-xl">
        <p className="text-severity-danger">Error: {error}</p>
        <button 
          onClick={fetchRoutes}
          className="mt-4 px-4 py-2 bg-transit-500 text-white rounded hover:bg-transit-600"
        >
          Retry
        </button>
      </div>
    )
  }

  if (routes.length === 0) {
    return (
      <div className="p-6 bg-dark-surface border border-dark-border rounded-xl">
        <p className="text-dark-muted">No routes available for {agency === 'All' ? 'selected agencies' : agency}</p>
      </div>
    )
  }

  const routeTypeName = (type: number) => {
    switch (type) {
      case 1: return 'Subway'
      case 2: return 'Rail'
      case 3: return 'Bus'
      case 4: return 'Ferry'
      default: return 'Transit'
    }
  }

  return (
    <div className="space-y-6">
      {/* Agency Indicator */}
      <div className="p-4 rounded-xl bg-dark-surface border border-dark-border">
        <p className="text-sm text-dark-muted">
          Viewing routes for: <span className="text-white font-semibold">{agency === 'All' ? 'All Agencies' : agency}</span>
        </p>
      </div>

      {/* Route Selector */}
      <div className="flex gap-4 overflow-x-auto pb-2">
        {routes.map((route) => (
          <button
            key={route.id}
            onClick={() => setSelectedRoute(route)}
            className={clsx(
              'flex-shrink-0 p-4 rounded-xl border-2 transition-all',
              selectedRoute?.id === route.id
                ? 'bg-dark-surface border-transit-500'
                : 'bg-dark-surface/50 border-dark-border hover:border-dark-muted'
            )}
          >
            <div className="flex items-center gap-3">
              <div className="w-4 h-4 rounded-full" style={{ backgroundColor: route.color }}></div>
              <span className="font-medium text-white">{route.long_name || route.name}</span>
            </div>
            <div className="mt-2 text-2xl font-bold" style={{ color: route.color }}>
              {(route.onTime ?? 100.0).toFixed(1)}%
            </div>
            <div className="text-xs text-dark-muted">On-Time</div>
          </button>
        ))}
      </div>

      {selectedRoute && (
        <>
          {/* Route Details */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Route Info Card */}
            <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ backgroundColor: selectedRoute.color + '20' }}>
                  <div className="w-6 h-6 rounded-full" style={{ backgroundColor: selectedRoute.color }}></div>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">{selectedRoute.name}</h2>
                  <p className="text-sm text-dark-muted">{selectedRoute.agency} • {routeTypeName(selectedRoute.type)}</p>
                </div>
              </div>

              <div className="space-y-4">
                {selectedRoute.long_name && (
                  <div className="flex justify-between py-2 border-b border-dark-border/50">
                    <span className="text-dark-muted">Route Name</span>
                    <span className="text-white font-medium text-right max-w-[200px]">{selectedRoute.long_name}</span>
                  </div>
                )}
                <div className="flex justify-between py-2 border-b border-dark-border/50">
                  <span className="text-dark-muted">Agency</span>
                  <span className="text-white font-medium">{selectedRoute.agency}</span>
                </div>
                {selectedRoute.city && (
                  <div className="flex justify-between py-2 border-b border-dark-border/50">
                    <span className="text-dark-muted">Location</span>
                    <span className="text-white font-medium">{selectedRoute.city}</span>
                  </div>
                )}
                <div className="flex justify-between py-2 border-b border-dark-border/50">
                  <span className="text-dark-muted">Type</span>
                  <span className="text-white font-medium">{routeTypeName(selectedRoute.type)}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-dark-border/50">
                  <span className="text-dark-muted">Route ID</span>
                  <span className="text-white font-medium font-mono text-sm">{selectedRoute.id}</span>
                </div>
                {selectedRoute.total_departures && (
                  <div className="flex justify-between py-2">
                    <span className="text-dark-muted">Total Departures</span>
                    <span className="text-white font-medium">{selectedRoute.total_departures.toLocaleString()}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Performance Metrics */}
            <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
              <h3 className="text-lg font-semibold text-white mb-4">Performance Metrics</h3>
              
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-dark-muted">On-Time Performance</span>
                    <span className="font-bold" style={{ color: (selectedRoute.onTime ?? 100) >= 90 ? '#3FB950' : (selectedRoute.onTime ?? 100) >= 75 ? '#D29922' : '#F85149' }}>
                      {(selectedRoute.onTime ?? 100.0).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-dark-bg rounded-full h-3">
                    <div 
                      className="h-3 rounded-full transition-all duration-500"
                      style={{ 
                        width: `${Math.min(selectedRoute.onTime ?? 100, 100)}%`,
                        backgroundColor: (selectedRoute.onTime ?? 100) >= 90 ? '#3FB950' : (selectedRoute.onTime ?? 100) >= 75 ? '#D29922' : '#F85149'
                      }}
                    ></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-dark-muted">Reliability Score</span>
                    <span className="font-bold" style={{ color: (selectedRoute.reliability || 0) >= 90 ? '#3FB950' : (selectedRoute.reliability || 0) >= 75 ? '#D29922' : '#F85149' }}>
                      {(selectedRoute.reliability || 0).toFixed(1)}/100
                    </span>
                  </div>
                  <div className="w-full bg-dark-bg rounded-full h-3">
                    <div 
                      className="h-3 rounded-full transition-all duration-500"
                      style={{ 
                        width: `${Math.min(selectedRoute.reliability || 0, 100)}%`,
                        backgroundColor: (selectedRoute.reliability || 0) >= 90 ? '#3FB950' : (selectedRoute.reliability || 0) >= 75 ? '#D29922' : '#F85149'
                      }}
                    ></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-dark-muted">Capacity Utilization</span>
                    <span className="font-bold text-severity-info">{(selectedRoute.utilization || 0).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-dark-bg rounded-full h-3">
                    <div 
                      className="h-3 rounded-full bg-severity-info transition-all duration-500"
                      style={{ width: `${Math.min(selectedRoute.utilization || 0, 100)}%` }}
                    ></div>
                  </div>
                </div>

                {selectedRoute.revenue && selectedRoute.revenue > 0 && (
                  <div className="pt-4 border-t border-dark-border">
                    <div className="flex justify-between">
                      <span className="text-dark-muted">Est. Daily Revenue</span>
                      <span className="text-2xl font-bold text-transit-500">${selectedRoute.revenue.toLocaleString()}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* AI Insights */}
            <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
              <h3 className="text-lg font-semibold text-white mb-4">Status</h3>
              
              <div className="space-y-4">
                {(selectedRoute.onTime ?? 100) < 80 ? (
                  <div className="p-3 rounded-lg bg-severity-danger/10 border border-severity-danger/30">
                    <div className="flex items-start gap-2">
                      <span className="text-severity-danger">🔴</span>
                      <div>
                        <p className="font-medium text-white">Critical Performance</p>
                        <p className="text-sm text-dark-muted mt-1">
                          Route is {(100 - (selectedRoute.onTime ?? 100)).toFixed(1)}% below target.
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (selectedRoute.onTime ?? 100) < 90 ? (
                  <div className="p-3 rounded-lg bg-severity-warning/10 border border-severity-warning/30">
                    <div className="flex items-start gap-2">
                      <span className="text-severity-warning">🟡</span>
                      <div>
                        <p className="font-medium text-white">Monitor Closely</p>
                        <p className="text-sm text-dark-muted mt-1">
                          Performance at {(selectedRoute.onTime ?? 100).toFixed(1)}% - approaching threshold.
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 rounded-lg bg-transit-500/10 border border-transit-500/30">
                    <div className="flex items-start gap-2">
                      <span className="text-transit-500">🟢</span>
                      <div>
                        <p className="font-medium text-white">Healthy Performance</p>
                        <p className="text-sm text-dark-muted mt-1">
                          Route is performing well above target.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {(selectedRoute.utilization || 0) < 50 && (
                  <div className="p-3 rounded-lg bg-severity-info/10 border border-severity-info/30">
                    <div className="flex items-start gap-2">
                      <span className="text-severity-info">💡</span>
                      <div>
                        <p className="font-medium text-white">Efficiency Opportunity</p>
                        <p className="text-sm text-dark-muted mt-1">
                          At {(selectedRoute.utilization || 0).toFixed(1)}% utilization, consider optimizing service frequency.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {(selectedRoute.utilization || 0) > 75 && (
                  <div className="p-3 rounded-lg bg-severity-warning/10 border border-severity-warning/30">
                    <div className="flex items-start gap-2">
                      <span className="text-severity-warning">📈</span>
                      <div>
                        <p className="font-medium text-white">High Demand</p>
                        <p className="text-sm text-dark-muted mt-1">
                          At {(selectedRoute.utilization || 0).toFixed(1)}% capacity. Consider adding service during peak hours.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
