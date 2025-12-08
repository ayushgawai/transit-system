import { useState, useEffect } from 'react'
import { getApiBaseUrl } from '../utils/api'
import { useAgency } from '../contexts/AgencyContext'
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Legend
} from 'recharts'

interface LiveDeparture {
  departure_id: string
  stop_name: string
  route_name: string
  agency: string
  scheduled_time: string
  predicted_time: string
  delay_seconds: number | null
  is_realtime: boolean
  load_timestamp: string
  data_age_seconds: number
}

interface LiveDataStats {
  total_today: number
  streaming_count: number
  realtime_count: number
  avg_delay: number
  on_time_count: number
  latest_update: string
  freshness_seconds: number
}

export default function LiveData() {
  const { agency } = useAgency()
  const [liveDepartures, setLiveDepartures] = useState<LiveDeparture[]>([])
  const [stats, setStats] = useState<LiveDataStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

  const fetchLiveData = async () => {
    setLoading(true)
    try {
      const agencyParam = agency && agency !== 'All' ? `?agency=${agency}` : ''
      const response = await fetch(`${getApiBaseUrl()}/live-data${agencyParam}`)
      const data = await response.json()
      
      if (data.success) {
        setLiveDepartures(data.data.departures || [])
        setStats(data.data.stats || null)
        setLastRefresh(new Date())
      }
    } catch (err) {
      console.error('Error fetching live data:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLiveData()
    // Auto-refresh every 30 seconds for live data
    const interval = setInterval(fetchLiveData, 30000)
    return () => clearInterval(interval)
  }, [agency])

  const getFreshnessColor = (seconds: number) => {
    // Handle negative or invalid values
    if (seconds < 0 || seconds > 86400) return 'text-gray-400'
    if (seconds < 60) return 'text-green-500'
    if (seconds < 300) return 'text-yellow-500'
    return 'text-red-500'
  }

  const formatFreshness = (seconds: number) => {
    // Handle negative values (future timestamps) or very large values
    if (seconds < 0) return 'Just now'
    if (seconds > 86400) return `${Math.floor(seconds / 86400)}d ago`
    if (seconds < 60) return `${Math.floor(seconds)}s ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s ago`
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m ago`
  }

  const getDelayColor = (delay: number | null) => {
    if (delay === null) return 'text-gray-400'
    if (delay <= 0) return 'text-green-500'
    if (delay <= 300) return 'text-yellow-500'
    return 'text-red-500'
  }

  // Group by hour for charts
  const hourlyData = liveDepartures.reduce((acc, dep) => {
    const hour = new Date(dep.load_timestamp).getHours()
    const key = `${hour}:00`
    if (!acc[key]) {
      acc[key] = { hour: key, count: 0, realtime: 0, delayed: 0 }
    }
    acc[key].count++
    if (dep.is_realtime) acc[key].realtime++
    if (dep.delay_seconds && dep.delay_seconds > 0) acc[key].delayed++
    return acc
  }, {} as Record<string, { hour: string; count: number; realtime: number; delayed: number }>)

  const hourlyChartData = Object.values(hourlyData).sort((a, b) => 
    parseInt(a.hour) - parseInt(b.hour)
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Live Data Dashboard</h1>
          <p className="text-dark-muted">
            Today's real-time transit data • {agency === 'All' ? 'All Agencies' : agency}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={fetchLiveData}
            className="px-4 py-2 bg-transit-500 text-white rounded-lg hover:bg-transit-600 transition-colors"
          >
            Refresh Now
          </button>
          {stats && (
            <div className={`text-sm font-mono ${getFreshnessColor(stats.freshness_seconds)}`}>
              {formatFreshness(stats.freshness_seconds)}
            </div>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-dark-surface border border-dark-border">
            <div className="text-sm text-dark-muted mb-1">Total Today</div>
            <div className="text-2xl font-bold text-white">{stats.total_today.toLocaleString()}</div>
            <div className="text-xs text-dark-muted mt-1">departures</div>
          </div>
          
          <div className="p-4 rounded-xl bg-dark-surface border border-dark-border">
            <div className="text-sm text-dark-muted mb-1">Real-time</div>
            <div className="text-2xl font-bold text-green-400">{stats.realtime_count.toLocaleString()}</div>
            <div className="text-xs text-dark-muted mt-1">
              {stats.total_today > 0 ? ((stats.realtime_count / stats.total_today) * 100).toFixed(1) : 0}% of total
            </div>
          </div>
          
          <div className="p-4 rounded-xl bg-dark-surface border border-dark-border">
            <div className="text-sm text-dark-muted mb-1">Streaming</div>
            <div className="text-2xl font-bold text-blue-400">{stats.streaming_count.toLocaleString()}</div>
            <div className="text-xs text-dark-muted mt-1">from API</div>
          </div>
          
          <div className="p-4 rounded-xl bg-dark-surface border border-dark-border">
            <div className="text-sm text-dark-muted mb-1">Avg Delay</div>
            <div className={`text-2xl font-bold ${getDelayColor(stats.avg_delay)}`}>
              {stats.avg_delay !== 0 
                ? `${stats.avg_delay > 0 ? '+' : ''}${Math.round(stats.avg_delay)}s`
                : '0s'}
            </div>
            <div className="text-xs text-dark-muted mt-1">
              {stats.on_time_count.toLocaleString()} on-time ({stats.total_today > 0 ? ((stats.on_time_count / stats.total_today) * 100).toFixed(1) : 0}%)
            </div>
            {stats.avg_delay < 0 && (
              <div className="text-xs text-blue-400 mt-1">(Early departures)</div>
            )}
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Delay Severity Distribution */}
        <div className="p-4 rounded-xl bg-dark-surface border border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-4">Delay Severity Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={(() => {
              const severityData = liveDepartures.reduce((acc, dep) => {
                if (dep.delay_seconds === null || dep.delay_seconds <= 0) return acc
                let severity = 'Minor (0-5min)'
                if (dep.delay_seconds > 600) severity = 'Severe (>10min)'
                else if (dep.delay_seconds > 300) severity = 'Major (5-10min)'
                
                if (!acc[severity]) acc[severity] = 0
                acc[severity]++
                return acc
              }, {} as Record<string, number>)
              
              return [
                { severity: 'Minor (0-5min)', count: severityData['Minor (0-5min)'] || 0 },
                { severity: 'Major (5-10min)', count: severityData['Major (5-10min)'] || 0 },
                { severity: 'Severe (>10min)', count: severityData['Severe (>10min)'] || 0 }
              ]
            })()}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="severity" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', color: '#F3F4F6' }} />
              <Bar dataKey="count" fill="#EF4444" name="Delayed Departures" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Delay Trend Over Time */}
        <div className="p-4 rounded-xl bg-dark-surface border border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-4">Average Delay by Hour</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={(() => {
              const hourlyDelays = liveDepartures.reduce((acc, dep) => {
                if (dep.delay_seconds === null || dep.delay_seconds <= 0) return acc
                const hour = new Date(dep.load_timestamp).getHours()
                const key = `${hour}:00`
                if (!acc[key]) acc[key] = { hour: key, total: 0, count: 0 }
                acc[key].total += dep.delay_seconds
                acc[key].count++
                return acc
              }, {} as Record<string, { hour: string; total: number; count: number }>)
              
              return Object.values(hourlyDelays)
                .map(h => ({ ...h, avgDelay: Math.round(h.total / h.count) }))
                .sort((a, b) => parseInt(a.hour) - parseInt(b.hour))
            })()}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="hour" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" label={{ value: 'Delay (seconds)', angle: -90, position: 'insideLeft' }} />
              <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', color: '#F3F4F6' }} />
              <Line type="monotone" dataKey="avgDelay" stroke="#F59E0B" strokeWidth={2} name="Avg Delay (s)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Departures Table */}
      <div className="p-4 rounded-xl bg-dark-surface border border-dark-border">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Departures (Latest First)</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-dark-border">
                <th className="text-left py-2 text-dark-muted">Date</th>
                <th className="text-left py-2 text-dark-muted">Time</th>
                <th className="text-left py-2 text-dark-muted">Stop</th>
                <th className="text-left py-2 text-dark-muted">Route</th>
                <th className="text-left py-2 text-dark-muted">Agency</th>
                <th className="text-left py-2 text-dark-muted">Delay</th>
                <th className="text-left py-2 text-dark-muted">Status</th>
                <th className="text-left py-2 text-dark-muted">Data Age</th>
              </tr>
            </thead>
            <tbody>
              {liveDepartures.slice(0, 50).map((dep) => {
                const depTime = dep.predicted_time || dep.scheduled_time
                const depDate = depTime ? new Date(depTime) : null
                return (
                  <tr key={dep.departure_id} className="border-b border-dark-border hover:bg-dark-hover">
                    <td className="py-2 text-white text-xs">
                      {depDate ? depDate.toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="py-2 text-white font-mono text-xs">
                      {depDate ? depDate.toLocaleTimeString() : 'N/A'}
                    </td>
                    <td className="py-2 text-white">{dep.stop_name}</td>
                    <td className="py-2 text-white">{dep.route_name}</td>
                    <td className="py-2 text-dark-muted">{dep.agency}</td>
                    <td className={`py-2 font-mono text-xs ${getDelayColor(dep.delay_seconds)}`}>
                      {dep.delay_seconds !== null 
                        ? `${dep.delay_seconds > 0 ? '+' : ''}${dep.delay_seconds}s`
                        : 'N/A'}
                    </td>
                    <td className="py-2">
                      {dep.is_realtime ? (
                        <span className="px-2 py-1 rounded text-xs bg-green-500/20 text-green-400">Real-time</span>
                      ) : (
                        <span className="px-2 py-1 rounded text-xs bg-gray-500/20 text-gray-400">Scheduled</span>
                      )}
                    </td>
                    <td className={`py-2 font-mono text-xs ${getFreshnessColor(dep.data_age_seconds)}`}>
                      {formatFreshness(Math.max(0, dep.data_age_seconds))}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        {liveDepartures.length === 0 && !loading && (
          <div className="text-center py-8 text-dark-muted">
            No live data available for today
          </div>
        )}
      </div>

      {loading && (
        <div className="text-center py-8 text-dark-muted">Loading live data...</div>
      )}
    </div>
  )
}

