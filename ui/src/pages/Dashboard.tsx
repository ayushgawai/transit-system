import { useState, useEffect } from 'react'
import clsx from 'clsx'
import { useAgency } from '../contexts/AgencyContext'
import { getApiBaseUrl } from '../utils/api'
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'

// Helper functions removed - "Last updated" replaced with "Powered by Transit" logo in header

// AI-powered chart insights
async function getChartInsight(chartType: string, data: any[]): Promise<string> {
  try {
    const response = await fetch(`${getApiBaseUrl()}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: `Analyze this ${chartType} chart data and provide insights: ${JSON.stringify(data.slice(0, 10))}`
      })
    })
    const result = await response.json()
    return result.response || 'Unable to generate insight at this time.'
  } catch (err) {
    return 'Unable to generate insight. Please try again later.'
  }
}

// Inline insight button component
function ChartInsightButton({ chartType, data }: { chartType: string, data: any[] }) {
  const [showInsight, setShowInsight] = useState(false)
  const [insight, setInsight] = useState<string>('')
  const [loading, setLoading] = useState(false)

  const handleClick = async () => {
    if (showInsight) {
      setShowInsight(false)
      return
    }
    
    setLoading(true)
    setShowInsight(true)
    const result = await getChartInsight(chartType, data)
    setInsight(result)
    setLoading(false)
  }

  return (
    <div className="relative">
      <button
        onClick={handleClick}
        className="p-2 rounded-lg hover:bg-dark-hover transition-colors text-dark-muted hover:text-transit-500"
        title="Get AI insight about this chart"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </button>
      {showInsight && (
        <div className="absolute top-full right-0 mt-2 w-80 p-4 bg-dark-surface border border-dark-border rounded-lg shadow-xl z-50 max-h-64 overflow-y-auto">
          <div className="flex items-start justify-between mb-2">
            <h4 className="text-sm font-semibold text-white">AI Insight</h4>
            <button
              onClick={() => setShowInsight(false)}
              className="text-dark-muted hover:text-white"
            >
              ✕
            </button>
          </div>
          {loading ? (
            <p className="text-sm text-dark-muted">Loading insight...</p>
          ) : (
            <p className="text-sm text-dark-muted whitespace-pre-wrap">{insight}</p>
          )}
        </div>
      )}
    </div>
  )
}

interface KPIData {
  onTimePerformance: number
  activeRoutes: number
  totalDepartures: number
  estimatedRevenue: number
  activeAlerts: number
  avgDelay: number
}

interface RouteHealth {
  route: string
  route_id?: string
  onTime: number
  reliability: number
  utilization: number
  status: 'healthy' | 'warning' | 'critical'
  agency?: string
  city?: string
}

function KPICard({ title, value, unit, severity, icon }: {
  title: string
  value: number | string
  unit?: string
  severity: 'success' | 'warning' | 'danger' | 'info'
  icon: React.ReactNode
}) {
  const severityColors = {
    success: 'border-l-transit-500 bg-transit-500/10',
    warning: 'border-l-severity-warning bg-severity-warning/10',
    danger: 'border-l-severity-danger bg-severity-danger/10',
    info: 'border-l-severity-info bg-severity-info/10',
  }

  const iconColors = {
    success: 'text-transit-500',
    warning: 'text-severity-warning',
    danger: 'text-severity-danger',
    info: 'text-severity-info',
  }

  return (
    <div className={clsx(
      'relative p-5 rounded-xl bg-dark-surface border-l-4 card-hover',
      severityColors[severity]
    )}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-dark-muted mb-1">{title}</p>
          <p className="text-3xl font-bold text-white">
            {typeof value === 'number' ? value.toLocaleString() : value}
            {unit && <span className="text-lg font-normal text-dark-muted ml-1">{unit}</span>}
          </p>
        </div>
        <div className={clsx('p-3 rounded-lg bg-dark-bg', iconColors[severity])}>
          {icon}
        </div>
      </div>
    </div>
  )
}

function SeverityBadge({ status }: { status: 'healthy' | 'warning' | 'critical' }) {
  const config = {
    healthy: { color: 'bg-transit-500', text: 'Healthy', glow: 'glow-green' },
    warning: { color: 'bg-severity-warning', text: 'Warning', glow: 'glow-yellow' },
    critical: { color: 'bg-severity-danger', text: 'Critical', glow: 'glow-red' },
  }
  const { color, text, glow } = config[status]

  return (
    <span className={clsx('inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium', color, 'text-white', glow)}>
      <span className="w-1.5 h-1.5 rounded-full bg-white severity-pulse"></span>
      {text}
    </span>
  )
}

export default function Dashboard() {
  const { agency } = useAgency()
  const [kpiData, setKpiData] = useState<KPIData | null>(null)
  const [routeHealth, setRouteHealth] = useState<RouteHealth[]>([])
  const [routeComparison, setRouteComparison] = useState<{top10: any[], bottom10: any[]}>({top10: [], bottom10: []})
  const [delayAnalysis, setDelayAnalysis] = useState<any[]>([])
  const [utilizationData, setUtilizationData] = useState<any[]>([])
  const [hourlyDemand, setHourlyDemand] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [cityInfo, setCityInfo] = useState<string>('')

  useEffect(() => {
    fetchDashboardData()
  }, [agency])

  useEffect(() => {
    const fetchHourlyDemand = async () => {
      try {
        const url = agency === 'All'
          ? `${getApiBaseUrl()}/hourly-demand`
          : `${getApiBaseUrl()}/hourly-demand?agency=${agency}`
        const response = await fetch(url)
        const result = await response.json()
        if (result.success && result.data) {
          setHourlyDemand(result.data)
        } else {
          // Fallback: calculate from route health data
          const calculated = Array.from({ length: 24 }, (_, i) => {
            const totalDepts = routeHealth.reduce((sum, r) => sum + ((r as any).departures || 0), 0)
            const baseHourly = totalDepts > 0 ? Math.floor(totalDepts / 24) : 0
            const isPeak = (i >= 7 && i <= 9) || (i >= 17 && i <= 19)
            const multiplier = isPeak ? 1.8 : 0.6
            return {
              hour: `${i}:00`,
              departures: Math.max(0, Math.floor(baseHourly * multiplier)),
              peak: isPeak ? 'peak' : 'off-peak'
            }
          })
          setHourlyDemand(calculated)
        }
      } catch (err) {
        console.error('Error fetching hourly demand:', err)
        // Fallback
        const calculated = Array.from({ length: 24 }, (_, i) => ({
          hour: `${i}:00`,
          departures: 0,
          peak: (i >= 7 && i <= 9) || (i >= 17 && i <= 19) ? 'peak' : 'off-peak'
        }))
        setHourlyDemand(calculated)
      }
    }
    if (routeHealth.length > 0) {
      fetchHourlyDemand()
    }
  }, [agency, routeHealth])

  const fetchDashboardData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Fetch KPIs
      const kpiUrl = agency === 'All' 
        ? `${getApiBaseUrl()}/kpis`
        : `${getApiBaseUrl()}/kpis?agency=${encodeURIComponent(agency)}`
      const kpiResponse = await fetch(kpiUrl)
      if (!kpiResponse.ok) {
        throw new Error(`HTTP ${kpiResponse.status}: ${kpiResponse.statusText}`)
      }
      const kpiResult = await kpiResponse.json()
      
      if (kpiResult.success) {
        setKpiData(kpiResult.data)
      } else {
        setError(kpiResult.error || 'Failed to fetch KPIs')
      }

      // Fetch Route Health
      const healthUrl = agency === 'All'
        ? `${getApiBaseUrl()}/analytics/route-health`
        : `${getApiBaseUrl()}/analytics/route-health?agency=${agency}`
      const healthResponse = await fetch(healthUrl)
      if (!healthResponse.ok) {
        throw new Error(`HTTP ${healthResponse.status}: ${healthResponse.statusText}`)
      }
      const healthResult = await healthResponse.json()
      
      if (healthResult.success) {
        const routes = healthResult.data || []
        setRouteHealth(routes)
        
        // Extract city information from agency
        const agencyCityMap: Record<string, string> = {
          'BART': 'San Francisco Bay Area',
          'VTA': 'San Jose',
          'Caltrain': 'San Francisco Peninsula'
        }
        if (agency && agency !== 'All') {
          setCityInfo(agencyCityMap[agency] || agency)
        } else if (routes.length > 0) {
          // Try to get from route data
          const agencies = [...new Set(routes.map((r: RouteHealth) => r.agency).filter(Boolean))]
          if (agencies.length > 0) {
            const cities = agencies.map(a => agencyCityMap[a as string] || a).filter(Boolean)
            setCityInfo(cities.join(', ') || 'Unknown')
          }
        }
      }

      // Fetch route comparison (top 10 and bottom 10)
      const comparisonUrl = agency === 'All'
        ? `${getApiBaseUrl()}/analytics/route-comparison`
        : `${getApiBaseUrl()}/analytics/route-comparison?agency=${agency}`
      const comparisonResponse = await fetch(comparisonUrl)
      const comparisonResult = await comparisonResponse.json()
      if (comparisonResult.success) {
        setRouteComparison(comparisonResult.data || {top10: [], bottom10: []})
      }

      // Fetch delay analysis
      const delayUrl = agency === 'All'
        ? `${getApiBaseUrl()}/analytics/delay-analysis`
        : `${getApiBaseUrl()}/analytics/delay-analysis?agency=${agency}`
      const delayResponse = await fetch(delayUrl)
      const delayResult = await delayResponse.json()
      if (delayResult.success) {
        setDelayAnalysis(delayResult.data || [])
      }

      // Fetch utilization distribution
      const utilUrl = agency === 'All'
        ? `${getApiBaseUrl()}/analytics/utilization-distribution`
        : `${getApiBaseUrl()}/analytics/utilization-distribution?agency=${agency}`
      const utilResponse = await fetch(utilUrl)
      const utilResult = await utilResponse.json()
      if (utilResult.success) {
        setUtilizationData(utilResult.data || [])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-transit-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-dark-muted">Loading dashboard data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 bg-severity-danger/10 border border-severity-danger rounded-xl">
        <p className="text-severity-danger">Error: {error}</p>
        <button 
          onClick={fetchDashboardData}
          className="mt-4 px-4 py-2 bg-transit-500 text-white rounded hover:bg-transit-600"
        >
          Retry
        </button>
      </div>
    )
  }

  if (!kpiData) {
    return (
      <div className="p-6 bg-dark-surface border border-dark-border rounded-xl">
        <p className="text-dark-muted">No data available for {agency === 'All' ? 'selected agencies' : agency}</p>
      </div>
    )
  }

  // Prepare chart data based on actual metrics
  // Use utilization or departures for variation instead of on-time (which is all 95%)
  const utilizationChartData = utilizationData
    .slice(0, 10)
    .map(r => ({
      name: r.route.length > 20 ? r.route.substring(0, 20) + '...' : r.route,
      utilization: r.utilization,
      stops: r.stops,
      departures: r.departures
    }))
    .sort((a, b) => b.utilization - a.utilization)  // Highest first
  
  // Top vs Bottom routes by departures
  const topBottomChartData = [
    ...routeComparison.top10.map((r: any) => ({...r, category: 'Top 10'})),
    ...routeComparison.bottom10.map((r: any) => ({...r, category: 'Bottom 10'}))
  ]

  // Performance distribution by status
  const statusCounts = {
    healthy: routeHealth.filter(r => r.status === 'healthy').length,
    warning: routeHealth.filter(r => r.status === 'warning').length,
    critical: routeHealth.filter(r => r.status === 'critical').length,
  }

  return (
    <div className="space-y-6">
      {/* Agency & City Indicator */}
      <div className="p-4 rounded-xl bg-dark-surface border border-dark-border">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-dark-muted">
              Viewing data for: <span className="text-white font-semibold">{agency === 'All' ? 'All Agencies' : agency}</span>
            </p>
            {cityInfo && (
              <p className="text-sm text-dark-muted mt-1">
                Location: <span className="text-white font-semibold">{cityInfo}</span>
              </p>
            )}
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        <KPICard
          title="On-Time Performance"
          value={kpiData.onTimePerformance}
          unit="%"
          severity="success"
          icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
        />
        <KPICard
          title="Active Routes"
          value={kpiData.activeRoutes}
          severity="info"
          icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" /></svg>}
        />
        <KPICard
          title="Total Departures"
          value={kpiData.totalDepartures}
          severity="info"
          icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>}
        />
        <KPICard
          title="Active Alerts"
          value={kpiData.activeAlerts}
          severity="warning"
          icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>}
        />
        <KPICard
          title="Avg Delay"
          value={`${kpiData.avgDelay.toFixed(1)}`}
          unit="min"
          severity={kpiData.avgDelay > 5 ? 'danger' : kpiData.avgDelay > 2 ? 'warning' : 'success'}
          // description={kpiData.avgDelay > 0 ? "Average delay for delayed departures only" : "No delays recorded"}
          icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Route Utilization Comparison - Top 10 */}
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Route Utilization</h3>
              <p className="text-sm text-dark-muted">Top 10 routes by stops served</p>
            </div>
            <ChartInsightButton chartType="utilization" data={utilizationChartData} />
          </div>
          {utilizationChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={utilizationChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
                <XAxis dataKey="name" stroke="#8B949E" fontSize={10} angle={-45} textAnchor="end" height={80} />
                <YAxis stroke="#8B949E" fontSize={12} />
                <Tooltip
                  contentStyle={{ background: '#0D1117', border: '1px solid #3FB950', borderRadius: '8px', color: '#FFFFFF' }}
                  labelStyle={{ color: '#FFFFFF', fontWeight: 'bold' }}
                  itemStyle={{ color: '#C9D1D9' }}
                  formatter={(value: any) => [`${value}%`, 'Utilization']}
                />
                <Bar dataKey="utilization" name="Utilization %" radius={[4, 4, 0, 0]}>
                  {utilizationChartData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.utilization >= 70 ? '#3FB950' : entry.utilization >= 40 ? '#D29922' : '#8B949E'} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-8 text-dark-muted">No utilization data available</div>
          )}
        </div>

        {/* Hourly Demand Pattern */}
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Hourly Departure Demand</h3>
              <p className="text-sm text-dark-muted">Service frequency by hour</p>
            </div>
            <ChartInsightButton chartType="hourly-demand" data={hourlyDemand} />
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={hourlyDemand}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
              <XAxis dataKey="hour" stroke="#8B949E" fontSize={10} />
              <YAxis stroke="#8B949E" fontSize={12} />
              <Tooltip
                contentStyle={{ background: '#0D1117', border: '1px solid #3FB950', borderRadius: '8px', color: '#FFFFFF' }}
                labelStyle={{ color: '#FFFFFF', fontWeight: 'bold' }}
                itemStyle={{ color: '#C9D1D9' }}
              />
              <Bar dataKey="departures" name="Departures" radius={[4, 4, 0, 0]}>
                {hourlyDemand.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.peak === 'peak' ? '#D29922' : '#3FB950'} 
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top vs Bottom Routes Comparison */}
      {topBottomChartData.length > 0 && (
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Route Performance: Top 10 vs Bottom 10</h3>
              <p className="text-sm text-dark-muted">Comparison by total departures</p>
            </div>
            <ChartInsightButton chartType="top-bottom-routes" data={topBottomChartData} />
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topBottomChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
              <XAxis 
                dataKey="route" 
                stroke="#8B949E" 
                fontSize={9} 
                angle={-45} 
                textAnchor="end" 
                height={80}
                tickFormatter={(value) => value.length > 20 ? value.substring(0, 20) + '...' : value}
              />
              <YAxis stroke="#8B949E" />
              <Tooltip
                contentStyle={{ background: '#0D1117', border: '1px solid #3FB950', borderRadius: '8px', color: '#FFFFFF' }}
                labelStyle={{ color: '#FFFFFF', fontWeight: 'bold' }}
                itemStyle={{ color: '#C9D1D9' }}
              />
              <Bar dataKey="departures" name="Total Departures" radius={[4, 4, 0, 0]}>
                {topBottomChartData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.category === 'Top 10' ? '#3FB950' : '#8B949E'} 
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Delay Analysis - Routes with Most Delays */}
      {delayAnalysis.length > 0 && (
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Routes Requiring Attention</h3>
              <p className="text-sm text-dark-muted">Routes with most delays (from streaming data)</p>
            </div>
            <ChartInsightButton chartType="delay-analysis" data={delayAnalysis} />
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={delayAnalysis.slice(0, 10)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
              <XAxis 
                dataKey="route" 
                stroke="#8B949E" 
                fontSize={9} 
                angle={-45} 
                textAnchor="end" 
                height={80}
                tickFormatter={(value) => value.length > 20 ? value.substring(0, 20) + '...' : value}
              />
              <YAxis stroke="#8B949E" />
              <Tooltip
                contentStyle={{ background: '#0D1117', border: '1px solid #F85149', borderRadius: '8px', color: '#FFFFFF' }}
                labelStyle={{ color: '#FFFFFF', fontWeight: 'bold' }}
                itemStyle={{ color: '#C9D1D9' }}
                formatter={(value: any, name: string) => {
                  if (name === 'delay_percentage') return [`${value}%`, 'Delay %']
                  if (name === 'avg_delay_minutes') return [`${value} min`, 'Avg Delay']
                  return [value, name]
                }}
              />
              <Bar dataKey="delay_percentage" name="Delay %" radius={[4, 4, 0, 0]}>
                {delayAnalysis.slice(0, 10).map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.delay_percentage >= 30 ? '#F85149' : entry.delay_percentage >= 15 ? '#D29922' : '#8B949E'} 
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Utilization Distribution - Show variation */}
      {utilizationData.length > 0 && (
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Utilization Distribution</h3>
              <p className="text-sm text-dark-muted">Routes by stops served (shows network coverage variation)</p>
            </div>
            <ChartInsightButton chartType="utilization-distribution" data={utilizationData.slice(0, 15)} />
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={utilizationData.slice(0, 15).sort((a, b) => b.utilization - a.utilization)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
              <XAxis 
                dataKey="route" 
                stroke="#8B949E" 
                fontSize={9} 
                angle={-45} 
                textAnchor="end" 
                height={80}
                tickFormatter={(value) => value.length > 15 ? value.substring(0, 15) + '...' : value}
              />
              <YAxis stroke="#8B949E" domain={[0, 100]} />
              <Tooltip
                contentStyle={{ background: '#0D1117', border: '1px solid #3FB950', borderRadius: '8px', color: '#FFFFFF' }}
                labelStyle={{ color: '#FFFFFF', fontWeight: 'bold' }}
                itemStyle={{ color: '#C9D1D9' }}
                formatter={(value: any, name: string) => {
                  if (name === 'utilization') return [`${value}%`, 'Utilization']
                  if (name === 'stops') return [value, 'Stops Served']
                  return [value, name]
                }}
              />
              <Bar dataKey="utilization" name="Utilization %" radius={[4, 4, 0, 0]}>
                {utilizationData.slice(0, 15).sort((a, b) => b.utilization - a.utilization).map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.utilization >= 80 ? '#3FB950' : entry.utilization >= 50 ? '#D29922' : entry.utilization >= 25 ? '#8B949E' : '#6E7681'} 
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Agency Comparison */}
      {routeHealth.length > 0 && (
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Agency Performance Comparison</h3>
              <p className="text-sm text-dark-muted">Average metrics by transit agency</p>
            </div>
            <ChartInsightButton chartType="agency-comparison" data={routeHealth} />
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={(() => {
              const agencyStats: Record<string, {count: number, totalUtil: number, totalRel: number, totalDept: number}> = {}
              routeHealth.forEach(r => {
                const ag = r.agency || 'Unknown'
                if (!agencyStats[ag]) {
                  agencyStats[ag] = {count: 0, totalUtil: 0, totalRel: 0, totalDept: 0}
                }
                agencyStats[ag].count++
                agencyStats[ag].totalUtil += r.utilization
                agencyStats[ag].totalRel += r.reliability
                agencyStats[ag].totalDept += (r as any).departures || 0
              })
              return Object.entries(agencyStats).map(([agency, stats]) => ({
                agency,
                avgUtilization: Math.round((stats.totalUtil / stats.count) * 10) / 10,
                avgReliability: Math.round((stats.totalRel / stats.count) * 10) / 10,
                totalDepartures: stats.totalDept
              }))
            })()}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
              <XAxis dataKey="agency" stroke="#8B949E" fontSize={12} />
              <YAxis stroke="#8B949E" />
              <Tooltip
                contentStyle={{ background: '#0D1117', border: '1px solid #3FB950', borderRadius: '8px', color: '#FFFFFF' }}
                labelStyle={{ color: '#FFFFFF', fontWeight: 'bold' }}
                itemStyle={{ color: '#C9D1D9' }}
              />
              <Bar dataKey="avgUtilization" name="Avg Utilization %" fill="#3FB950" radius={[4, 4, 0, 0]} />
              <Bar dataKey="avgReliability" name="Avg Reliability %" fill="#58A6FF" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Footer with Developer & Data Source Info */}
      <div className="mt-8 p-4 rounded-xl bg-dark-surface border border-dark-border">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="text-xs text-dark-muted">
                <p>MSDA Capstone Project</p>
              </div>
            </div>
            <div className="h-8 w-px bg-dark-border hidden md:block"></div>
            <div className="text-xs text-dark-muted">
              <p>San José State University</p>
              <p>Department of Applied Data Science</p>
            </div>
          </div>
          <div className="text-xs text-dark-muted text-center md:text-right">
            <p>📊 Data from: <span className="text-transit-500">Snowflake Data Warehouse</span></p>
            <p>🔌 Source: GTFS Feeds (BART, VTA) + Transit API Streaming</p>
            <p>📍 Location: {cityInfo || 'San Francisco Bay Area, San Jose'}</p>
            <p className="mt-1 text-[10px]">© 2025 MSDA Capstone Project. All rights reserved.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
