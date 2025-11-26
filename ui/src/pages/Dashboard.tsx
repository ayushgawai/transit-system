import { useState } from 'react'
import clsx from 'clsx'
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts'

// Mock data - will be replaced with API calls
const kpiData = {
  onTimePerformance: 94.2,
  activeRoutes: 4,
  totalDepartures: 80,
  estimatedRevenue: 14087.5,
  activeAlerts: 3,
  avgDelay: 0,
}

const headwayData = [
  { time: '06:00', route14: 8, route38: 12, route22: 7 },
  { time: '07:00', route14: 6, route38: 10, route22: 8 },
  { time: '08:00', route14: 5, route38: 8, route22: 6 },
  { time: '09:00', route14: 7, route38: 11, route22: 7 },
  { time: '10:00', route14: 10, route38: 14, route22: 9 },
  { time: '11:00', route14: 12, route38: 15, route22: 11 },
]

const demandData = [
  { hour: '6AM', departures: 12, peak: 'off' },
  { hour: '7AM', departures: 28, peak: 'am' },
  { hour: '8AM', departures: 35, peak: 'am' },
  { hour: '9AM', departures: 22, peak: 'am' },
  { hour: '10AM', departures: 15, peak: 'off' },
  { hour: '11AM', departures: 14, peak: 'off' },
  { hour: '12PM', departures: 18, peak: 'off' },
  { hour: '4PM', departures: 25, peak: 'pm' },
  { hour: '5PM', departures: 38, peak: 'pm' },
  { hour: '6PM', departures: 32, peak: 'pm' },
]

const routeHealth = [
  { route: 'Blue Line', onTime: 100, reliability: 100, utilization: 65, status: 'healthy' },
  { route: 'Red Line', onTime: 87, reliability: 85, utilization: 78, status: 'warning' },
  { route: 'Green Line', onTime: 72, reliability: 68, utilization: 45, status: 'critical' },
  { route: 'Yellow Line', onTime: 95, reliability: 92, utilization: 55, status: 'healthy' },
]

const pieData = [
  { name: 'On-Time', value: 75, color: '#3FB950' },
  { name: 'Late', value: 20, color: '#D29922' },
  { name: 'Very Late', value: 5, color: '#F85149' },
]

function KPICard({ title, value, unit, change, severity, icon }: {
  title: string
  value: number | string
  unit?: string
  change?: number
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
          {change !== undefined && (
            <p className={clsx(
              'text-sm mt-1 flex items-center gap-1',
              change >= 0 ? 'text-transit-500' : 'text-severity-danger'
            )}>
              <svg className={clsx('w-4 h-4', change < 0 && 'rotate-180')} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
              {Math.abs(change)}% from last hour
            </p>
          )}
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

function InfoButton({ 
  tooltip, 
  contextType = 'metric',
  contextId,
  contextData 
}: { 
  tooltip: string
  contextType?: 'route' | 'metric' | 'chart' | 'alert'
  contextId?: string
  contextData?: Record<string, unknown>
}) {
  const [show, setShow] = useState(false)
  const [loading, setLoading] = useState(false)
  const [aiInsight, setAiInsight] = useState<string | null>(null)

  const handleClick = async () => {
    if (aiInsight) {
      // Toggle off if already showing AI insight
      setShow(!show)
      return
    }
    
    setShow(true)
    setLoading(true)
    
    try {
      const response = await fetch('http://localhost:8000/api/insights', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          context_type: contextType,
          context_id: contextId,
          context_data: contextData
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        setAiInsight(data.response)
      } else {
        setAiInsight(tooltip) // Fallback to static tooltip
      }
    } catch {
      setAiInsight(tooltip) // Fallback to static tooltip
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setShow(false)
    setAiInsight(null)
  }

  return (
    <div className="relative">
      <button
        onClick={handleClick}
        className={clsx(
          "w-5 h-5 rounded-full flex items-center justify-center transition-colors",
          aiInsight 
            ? "bg-transit-500 text-white" 
            : "bg-dark-border text-dark-muted hover:text-white hover:bg-severity-info"
        )}
      >
        {loading ? (
          <span className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin"></span>
        ) : (
          <span className="text-xs font-bold">i</span>
        )}
      </button>
      {show && (
        <div className="absolute z-50 right-0 top-6 w-80 p-4 rounded-lg bg-dark-surface border border-dark-border shadow-xl text-sm text-dark-text">
          <div className="flex items-start gap-2">
            <span className="text-transit-500 flex-shrink-0">🤖</span>
            <div className="flex-1">
              {loading ? (
                <span className="text-dark-muted">Getting AI insight...</span>
              ) : (
                <span className="whitespace-pre-wrap">{aiInsight || tooltip}</span>
              )}
            </div>
            <button 
              onClick={handleClose}
              className="text-dark-muted hover:text-white flex-shrink-0"
            >
              ✕
            </button>
          </div>
          {aiInsight && (
            <div className="mt-2 pt-2 border-t border-dark-border text-xs text-dark-muted flex items-center gap-1">
              <span className="text-transit-500">✨</span> AI-powered insight
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function Dashboard() {
  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        <KPICard
          title="On-Time Performance"
          value={kpiData.onTimePerformance}
          unit="%"
          change={1.5}
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
          change={-2}
          severity="info"
          icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>}
        />
        <KPICard
          title="Est. Revenue"
          value={`$${(kpiData.estimatedRevenue / 1000).toFixed(1)}K`}
          severity="success"
          icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
        />
        <KPICard
          title="Active Alerts"
          value={kpiData.activeAlerts}
          severity="warning"
          icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Headway Chart */}
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Live Headway Monitoring</h3>
              <p className="text-sm text-dark-muted">Minutes between departures by route</p>
            </div>
            <InfoButton 
              tooltip="Headway is the time between consecutive vehicles on a route." 
              contextType="chart"
              contextId="Headway Monitoring"
            />
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={headwayData}>
              <defs>
                <linearGradient id="colorRoute14" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3FB950" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3FB950" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorRoute38" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#58A6FF" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#58A6FF" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
              <XAxis dataKey="time" stroke="#8B949E" fontSize={12} />
              <YAxis stroke="#8B949E" fontSize={12} />
              <Tooltip
                contentStyle={{ background: '#0D1117', border: '1px solid #3FB950', borderRadius: '8px', color: '#FFFFFF' }}
                labelStyle={{ color: '#FFFFFF', fontWeight: 'bold' }}
                itemStyle={{ color: '#C9D1D9' }}
              />
              <Area type="monotone" dataKey="route14" name="Blue Line" stroke="#3FB950" fill="url(#colorRoute14)" strokeWidth={2} />
              <Area type="monotone" dataKey="route38" name="Red Line" stroke="#58A6FF" fill="url(#colorRoute38)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Demand Chart */}
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Departure Demand</h3>
              <p className="text-sm text-dark-muted">Hourly service frequency</p>
            </div>
            <InfoButton 
              tooltip="Shows when service is busiest." 
              contextType="chart"
              contextId="Departure Demand"
            />
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={demandData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
              <XAxis dataKey="hour" stroke="#8B949E" fontSize={12} />
              <YAxis stroke="#8B949E" fontSize={12} />
              <Tooltip
                contentStyle={{ background: '#0D1117', border: '1px solid #3FB950', borderRadius: '8px', color: '#FFFFFF' }}
                labelStyle={{ color: '#FFFFFF', fontWeight: 'bold' }}
                itemStyle={{ color: '#C9D1D9' }}
              />
              <Bar dataKey="departures" name="Departures" radius={[4, 4, 0, 0]}>
                {demandData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.peak === 'am' ? '#D29922' : entry.peak === 'pm' ? '#F85149' : '#3FB950'} 
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Route Health & Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Route Health Table */}
        <div className="lg:col-span-2 p-6 rounded-xl bg-dark-surface border border-dark-border">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Route Health Overview</h3>
              <p className="text-sm text-dark-muted">Real-time status by route</p>
            </div>
            <InfoButton 
              tooltip="Click for AI analysis of route health." 
              contextType="chart"
              contextId="Route Health Overview"
            />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-sm text-dark-muted border-b border-dark-border">
                  <th className="pb-3 font-medium">Route</th>
                  <th className="pb-3 font-medium">On-Time %</th>
                  <th className="pb-3 font-medium">Reliability</th>
                  <th className="pb-3 font-medium">Utilization</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">AI Insight</th>
                </tr>
              </thead>
              <tbody>
                {routeHealth.map((route) => (
                  <tr key={route.route} className="border-b border-dark-border/50 hover:bg-dark-hover transition-colors">
                    <td className="py-4">
                      <div className="flex items-center gap-2">
                        <span className="w-3 h-3 rounded-full" style={{ backgroundColor: route.route === 'Blue Line' ? '#58A6FF' : route.route === 'Red Line' ? '#F85149' : route.route === 'Green Line' ? '#3FB950' : '#D29922' }}></span>
                        <span className="font-medium text-white">{route.route}</span>
                      </div>
                    </td>
                    <td className="py-4">
                      <span className={clsx('font-mono', route.onTime >= 90 ? 'text-transit-500' : route.onTime >= 75 ? 'text-severity-warning' : 'text-severity-danger')}>
                        {route.onTime}%
                      </span>
                    </td>
                    <td className="py-4">
                      <div className="w-24 bg-dark-bg rounded-full h-2">
                        <div 
                          className={clsx('h-2 rounded-full', route.reliability >= 90 ? 'bg-transit-500' : route.reliability >= 75 ? 'bg-severity-warning' : 'bg-severity-danger')}
                          style={{ width: `${route.reliability}%` }}
                        ></div>
                      </div>
                    </td>
                    <td className="py-4 font-mono text-dark-text">{route.utilization}%</td>
                    <td className="py-4">
                      <SeverityBadge status={route.status as 'healthy' | 'warning' | 'critical'} />
                    </td>
                    <td className="py-4">
                      <InfoButton 
                        tooltip={`Click for AI analysis of ${route.route}`}
                        contextType="route"
                        contextId={route.route}
                        contextData={{
                          onTimePercent: route.onTime,
                          utilization: route.utilization,
                          status: route.status,
                          reliability: route.reliability
                        }}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* On-Time Distribution Pie */}
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Performance Distribution</h3>
            <InfoButton 
              tooltip="Click for AI analysis of performance distribution." 
              contextType="chart"
              contextId="Performance Distribution"
            />
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#0D1117', border: '1px solid #3FB950', borderRadius: '8px', color: '#FFFFFF' }}
                labelStyle={{ color: '#FFFFFF', fontWeight: 'bold' }}
                itemStyle={{ color: '#C9D1D9' }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-2">
            {pieData.map((item) => (
              <div key={item.name} className="flex items-center gap-2 text-sm">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }}></span>
                <span className="text-dark-muted">{item.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions & Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Alerts */}
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-4">Active Service Alerts</h3>
          <div className="space-y-3">
            <div className="p-3 rounded-lg bg-severity-danger/10 border border-severity-danger/30 flex items-start gap-3">
              <span className="text-severity-danger">⚠️</span>
              <div>
                <p className="font-medium text-white">Green Line - Significant Delays</p>
                <p className="text-sm text-dark-muted">28% below target on-time performance. Infrastructure check recommended.</p>
              </div>
            </div>
            <div className="p-3 rounded-lg bg-severity-warning/10 border border-severity-warning/30 flex items-start gap-3">
              <span className="text-severity-warning">🔔</span>
              <div>
                <p className="font-medium text-white">Red Line - Peak Hour Crowding</p>
                <p className="text-sm text-dark-muted">Capacity at 78% during AM peak. Consider adding service.</p>
              </div>
            </div>
            <div className="p-3 rounded-lg bg-severity-info/10 border border-severity-info/30 flex items-start gap-3">
              <span className="text-severity-info">ℹ️</span>
              <div>
                <p className="font-medium text-white">System Maintenance Scheduled</p>
                <p className="text-sm text-dark-muted">Routine maintenance planned for Sunday 2-4 AM.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Insights */}
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Data Insights</h3>
            <span className="text-xs text-dark-muted px-2 py-1 bg-dark-bg rounded">AI-Ready</span>
          </div>
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <span className="w-8 h-8 rounded-lg bg-transit-500/20 flex items-center justify-center text-transit-500">📈</span>
              <div>
                <p className="font-medium text-white">Revenue Trending Up</p>
                <p className="text-sm text-dark-muted">$14.1K estimated today, +3.2% vs. last week average</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="w-8 h-8 rounded-lg bg-severity-warning/20 flex items-center justify-center text-severity-warning">⏱️</span>
              <div>
                <p className="font-medium text-white">Headway Gaps Detected</p>
                <p className="text-sm text-dark-muted">Blue Line showing 15+ min gaps during 10-11 AM</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="w-8 h-8 rounded-lg bg-severity-info/20 flex items-center justify-center text-severity-info">🎯</span>
              <div>
                <p className="font-medium text-white">Efficiency Opportunity</p>
                <p className="text-sm text-dark-muted">Yellow Line at 55% utilization. Consider reducing off-peak frequency.</p>
              </div>
            </div>
          </div>
          <div className="mt-4 p-3 rounded-lg bg-gradient-to-r from-transit-500/10 to-severity-info/10 border border-transit-500/30">
            <p className="text-sm text-dark-muted">
              <span className="text-transit-500 font-medium">💬 Ask the Data Bot:</span> "Why is Green Line underperforming?" or "Show me peak hour trends"
            </p>
          </div>
        </div>
      </div>

      {/* Footer with Developer & Data Source Info */}
      <div className="mt-8 p-4 rounded-xl bg-dark-surface border border-dark-border">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-transit-500 to-severity-info flex items-center justify-center text-white font-bold">
                AG
              </div>
              <div>
                <p className="text-white font-medium">Ayush Gawai</p>
                <p className="text-xs text-dark-muted">MSDA Capstone Project</p>
              </div>
            </div>
            <div className="h-8 w-px bg-dark-border hidden md:block"></div>
            <div className="text-xs text-dark-muted">
              <p>San José State University</p>
              <p>Department of Applied Data Science</p>
            </div>
          </div>
          <div className="text-xs text-dark-muted text-center md:text-right">
            <p>📊 Data from: <span className="text-transit-500">Snowflake Analytics</span></p>
            <p>🔌 Source: TransitApp API + GTFS Feeds</p>
            <p className="mt-1 text-[10px]">© 2024 Ayush Gawai. All rights reserved.</p>
          </div>
        </div>
      </div>
    </div>
  )
}

