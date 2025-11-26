import { AreaChart, Area, BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter, Cell } from 'recharts'

const weeklyTrend = [
  { day: 'Mon', onTime: 92, revenue: 12500, departures: 450 },
  { day: 'Tue', onTime: 94, revenue: 13200, departures: 480 },
  { day: 'Wed', onTime: 91, revenue: 12800, departures: 460 },
  { day: 'Thu', onTime: 95, revenue: 14100, departures: 490 },
  { day: 'Fri', onTime: 88, revenue: 15200, departures: 520 },
  { day: 'Sat', onTime: 96, revenue: 9800, departures: 320 },
  { day: 'Sun', onTime: 97, revenue: 8500, departures: 280 },
]

const delayDistribution = [
  { delay: '0-2 min', count: 450, color: '#3FB950' },
  { delay: '2-5 min', count: 280, color: '#3FB950' },
  { delay: '5-10 min', count: 120, color: '#D29922' },
  { delay: '10-15 min', count: 45, color: '#F85149' },
  { delay: '15+ min', count: 15, color: '#F85149' },
]

const hourlyHeatmap = [
  { hour: '6AM', mon: 85, tue: 88, wed: 86, thu: 90, fri: 82 },
  { hour: '7AM', mon: 78, tue: 82, wed: 80, thu: 85, fri: 75 },
  { hour: '8AM', mon: 72, tue: 78, wed: 75, thu: 80, fri: 70 },
  { hour: '9AM', mon: 88, tue: 90, wed: 87, thu: 92, fri: 85 },
  { hour: '10AM', mon: 95, tue: 96, wed: 94, thu: 97, fri: 93 },
  { hour: '5PM', mon: 70, tue: 75, wed: 72, thu: 78, fri: 68 },
  { hour: '6PM', mon: 75, tue: 80, wed: 77, thu: 82, fri: 72 },
]

const reliabilityVsRevenue = [
  { route: 'Blue', reliability: 100, revenue: 4500, size: 65 },
  { route: 'Red', reliability: 85, revenue: 5200, size: 78 },
  { route: 'Green', reliability: 68, revenue: 2100, size: 45 },
  { route: 'Yellow', reliability: 92, revenue: 2287, size: 55 },
]

export default function Analytics() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Analytics Dashboard</h1>
          <p className="text-dark-muted">Deep dive into transit performance metrics</p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 rounded-lg bg-dark-surface border border-dark-border text-dark-muted hover:text-white transition-colors">
            Last 7 Days
          </button>
          <button className="px-4 py-2 rounded-lg bg-transit-500 text-white font-medium">
            Export Report
          </button>
        </div>
      </div>

      {/* Trend Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weekly On-Time Trend */}
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-4">Weekly On-Time Performance</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={weeklyTrend}>
              <defs>
                <linearGradient id="colorOnTime" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3FB950" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3FB950" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
              <XAxis dataKey="day" stroke="#8B949E" />
              <YAxis stroke="#8B949E" domain={[80, 100]} />
              <Tooltip 
                contentStyle={{ background: '#0D1117', border: '1px solid #3FB950', borderRadius: '8px', color: '#FFFFFF' }}
                labelStyle={{ color: '#FFFFFF', fontWeight: 'bold' }}
                itemStyle={{ color: '#C9D1D9' }}
              />
              <Area type="monotone" dataKey="onTime" name="On-Time %" stroke="#3FB950" fill="url(#colorOnTime)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Revenue Trend */}
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-4">Weekly Revenue Trend</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={weeklyTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
              <XAxis dataKey="day" stroke="#8B949E" />
              <YAxis stroke="#8B949E" />
              <Tooltip 
                contentStyle={{ background: '#161B22', border: '1px solid #30363D', borderRadius: '8px' }}
                formatter={(value: number) => [`$${value.toLocaleString()}`, 'Revenue']}
              />
              <Bar dataKey="revenue" name="Revenue" fill="#58A6FF" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Delay Distribution & Heatmap */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Delay Distribution */}
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-4">Delay Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={delayDistribution} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
              <XAxis type="number" stroke="#8B949E" />
              <YAxis dataKey="delay" type="category" stroke="#8B949E" width={80} />
              <Tooltip 
                contentStyle={{ background: '#0D1117', border: '1px solid #3FB950', borderRadius: '8px', color: '#FFFFFF' }}
                labelStyle={{ color: '#FFFFFF', fontWeight: 'bold' }}
                itemStyle={{ color: '#C9D1D9' }}
              />
              <Bar dataKey="count" name="Departures" radius={[0, 4, 4, 0]}>
                {delayDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-4 text-sm text-dark-muted">
            <span className="text-transit-500">●</span> On-Time (0-5 min) | 
            <span className="text-severity-warning ml-2">●</span> Late (5-10 min) | 
            <span className="text-severity-danger ml-2">●</span> Very Late (10+ min)
          </div>
        </div>

        {/* Reliability vs Revenue Scatter */}
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-4">Reliability vs Revenue</h3>
          <p className="text-sm text-dark-muted mb-4">Bubble size = utilization %</p>
          <ResponsiveContainer width="100%" height={220}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
              <XAxis type="number" dataKey="reliability" name="Reliability" stroke="#8B949E" domain={[60, 100]} />
              <YAxis type="number" dataKey="revenue" name="Revenue" stroke="#8B949E" />
              <Tooltip 
                contentStyle={{ background: '#161B22', border: '1px solid #30363D', borderRadius: '8px' }}
                formatter={(value: number, name: string) => [name === 'Revenue' ? `$${value}` : `${value}%`, name]}
              />
              <Scatter data={reliabilityVsRevenue} fill="#58A6FF">
                {reliabilityVsRevenue.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.reliability >= 90 ? '#3FB950' : entry.reliability >= 75 ? '#D29922' : '#F85149'}
                  />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Performance Heatmap */}
      <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
        <h3 className="text-lg font-semibold text-white mb-4">Hourly Performance Heatmap</h3>
        <p className="text-sm text-dark-muted mb-4">On-time % by hour and day of week (darker = better)</p>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-dark-muted text-sm">
                <th className="p-2 text-left">Hour</th>
                <th className="p-2 text-center">Mon</th>
                <th className="p-2 text-center">Tue</th>
                <th className="p-2 text-center">Wed</th>
                <th className="p-2 text-center">Thu</th>
                <th className="p-2 text-center">Fri</th>
              </tr>
            </thead>
            <tbody>
              {hourlyHeatmap.map((row) => (
                <tr key={row.hour}>
                  <td className="p-2 text-white font-medium">{row.hour}</td>
                  {['mon', 'tue', 'wed', 'thu', 'fri'].map((day) => {
                    const value = row[day as keyof typeof row] as number
                    const bgOpacity = (value - 60) / 40 // Normalize 60-100 to 0-1
                    return (
                      <td key={day} className="p-2 text-center">
                        <div 
                          className="w-full h-10 rounded flex items-center justify-center font-mono text-sm"
                          style={{ 
                            backgroundColor: value >= 90 ? `rgba(63, 185, 80, ${bgOpacity})` 
                              : value >= 75 ? `rgba(210, 153, 34, ${bgOpacity})` 
                              : `rgba(248, 81, 73, ${bgOpacity})`,
                            color: 'white'
                          }}
                        >
                          {value}%
                        </div>
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Key Insights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-transit-500/10 border border-transit-500/30">
          <div className="text-3xl font-bold text-transit-500 mb-2">92.4%</div>
          <div className="text-sm text-white font-medium">Average Weekly On-Time</div>
          <div className="text-xs text-dark-muted mt-1">↑ 2.1% vs last week</div>
        </div>
        <div className="p-4 rounded-xl bg-severity-info/10 border border-severity-info/30">
          <div className="text-3xl font-bold text-severity-info mb-2">$86.1K</div>
          <div className="text-sm text-white font-medium">Weekly Revenue</div>
          <div className="text-xs text-dark-muted mt-1">↑ 5.3% vs last week</div>
        </div>
        <div className="p-4 rounded-xl bg-severity-warning/10 border border-severity-warning/30">
          <div className="text-3xl font-bold text-severity-warning mb-2">5-6 PM</div>
          <div className="text-sm text-white font-medium">Worst Performance Window</div>
          <div className="text-xs text-dark-muted mt-1">Focus area for improvement</div>
        </div>
      </div>
    </div>
  )
}

