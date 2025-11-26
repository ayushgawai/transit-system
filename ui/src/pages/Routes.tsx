import { useState } from 'react'
import clsx from 'clsx'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'

const routes = [
  {
    id: 'blue',
    name: 'Blue Line',
    color: '#58A6FF',
    agency: 'BART',
    type: 'Subway',
    stops: 12,
    avgHeadway: 8,
    onTime: 100,
    reliability: 100,
    utilization: 65,
    revenue: 4500,
    direction: 'Daly City ↔ Dublin',
    peakFrequency: '5 min',
    offPeakFrequency: '10 min',
  },
  {
    id: 'red',
    name: 'Red Line',
    color: '#F85149',
    agency: 'BART',
    type: 'Subway',
    stops: 15,
    avgHeadway: 10,
    onTime: 87,
    reliability: 85,
    utilization: 78,
    revenue: 5200,
    direction: 'Millbrae ↔ Richmond',
    peakFrequency: '6 min',
    offPeakFrequency: '12 min',
  },
  {
    id: 'green',
    name: 'Green Line',
    color: '#3FB950',
    agency: 'BART',
    type: 'Subway',
    stops: 10,
    avgHeadway: 12,
    onTime: 72,
    reliability: 68,
    utilization: 45,
    revenue: 2100,
    direction: 'Berryessa ↔ Daly City',
    peakFrequency: '8 min',
    offPeakFrequency: '15 min',
  },
  {
    id: 'yellow',
    name: 'Yellow Line',
    color: '#D29922',
    agency: 'BART',
    type: 'Subway',
    stops: 8,
    avgHeadway: 15,
    onTime: 95,
    reliability: 92,
    utilization: 55,
    revenue: 2287,
    direction: 'Antioch ↔ SF',
    peakFrequency: '10 min',
    offPeakFrequency: '20 min',
  },
]

const hourlyPerformance = [
  { hour: '6AM', onTime: 98, departures: 12 },
  { hour: '7AM', onTime: 95, departures: 24 },
  { hour: '8AM', onTime: 88, departures: 32 },
  { hour: '9AM', onTime: 92, departures: 28 },
  { hour: '10AM', onTime: 96, departures: 18 },
  { hour: '11AM', onTime: 98, departures: 15 },
  { hour: '12PM', onTime: 97, departures: 16 },
  { hour: '1PM', onTime: 95, departures: 14 },
  { hour: '2PM', onTime: 94, departures: 16 },
  { hour: '3PM', onTime: 90, departures: 22 },
  { hour: '4PM', onTime: 85, departures: 30 },
  { hour: '5PM', onTime: 82, departures: 35 },
  { hour: '6PM', onTime: 88, departures: 28 },
]

export default function Routes() {
  const [selectedRoute, setSelectedRoute] = useState(routes[0])

  return (
    <div className="space-y-6">
      {/* Route Selector */}
      <div className="flex gap-4 overflow-x-auto pb-2">
        {routes.map((route) => (
          <button
            key={route.id}
            onClick={() => setSelectedRoute(route)}
            className={clsx(
              'flex-shrink-0 p-4 rounded-xl border-2 transition-all',
              selectedRoute.id === route.id
                ? 'bg-dark-surface border-transit-500'
                : 'bg-dark-surface/50 border-dark-border hover:border-dark-muted'
            )}
          >
            <div className="flex items-center gap-3">
              <div className="w-4 h-4 rounded-full" style={{ backgroundColor: route.color }}></div>
              <span className="font-medium text-white">{route.name}</span>
            </div>
            <div className="mt-2 text-2xl font-bold" style={{ color: route.color }}>
              {route.onTime}%
            </div>
            <div className="text-xs text-dark-muted">On-Time</div>
          </button>
        ))}
      </div>

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
              <p className="text-sm text-dark-muted">{selectedRoute.agency} • {selectedRoute.type}</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex justify-between py-2 border-b border-dark-border/50">
              <span className="text-dark-muted">Direction</span>
              <span className="text-white font-medium">{selectedRoute.direction}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-dark-border/50">
              <span className="text-dark-muted">Stops</span>
              <span className="text-white font-medium">{selectedRoute.stops}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-dark-border/50">
              <span className="text-dark-muted">Peak Frequency</span>
              <span className="text-white font-medium">{selectedRoute.peakFrequency}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-dark-border/50">
              <span className="text-dark-muted">Off-Peak Frequency</span>
              <span className="text-white font-medium">{selectedRoute.offPeakFrequency}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-dark-border/50">
              <span className="text-dark-muted">Avg Headway</span>
              <span className="text-white font-medium">{selectedRoute.avgHeadway} min</span>
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-4">Performance Metrics</h3>
          
          <div className="space-y-6">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-dark-muted">On-Time Performance</span>
                <span className="font-bold" style={{ color: selectedRoute.onTime >= 90 ? '#3FB950' : selectedRoute.onTime >= 75 ? '#D29922' : '#F85149' }}>
                  {selectedRoute.onTime}%
                </span>
              </div>
              <div className="w-full bg-dark-bg rounded-full h-3">
                <div 
                  className="h-3 rounded-full transition-all duration-500"
                  style={{ 
                    width: `${selectedRoute.onTime}%`,
                    backgroundColor: selectedRoute.onTime >= 90 ? '#3FB950' : selectedRoute.onTime >= 75 ? '#D29922' : '#F85149'
                  }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-2">
                <span className="text-dark-muted">Reliability Score</span>
                <span className="font-bold" style={{ color: selectedRoute.reliability >= 90 ? '#3FB950' : selectedRoute.reliability >= 75 ? '#D29922' : '#F85149' }}>
                  {selectedRoute.reliability}/100
                </span>
              </div>
              <div className="w-full bg-dark-bg rounded-full h-3">
                <div 
                  className="h-3 rounded-full transition-all duration-500"
                  style={{ 
                    width: `${selectedRoute.reliability}%`,
                    backgroundColor: selectedRoute.reliability >= 90 ? '#3FB950' : selectedRoute.reliability >= 75 ? '#D29922' : '#F85149'
                  }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-2">
                <span className="text-dark-muted">Capacity Utilization</span>
                <span className="font-bold text-severity-info">{selectedRoute.utilization}%</span>
              </div>
              <div className="w-full bg-dark-bg rounded-full h-3">
                <div 
                  className="h-3 rounded-full bg-severity-info transition-all duration-500"
                  style={{ width: `${selectedRoute.utilization}%` }}
                ></div>
              </div>
            </div>

            <div className="pt-4 border-t border-dark-border">
              <div className="flex justify-between">
                <span className="text-dark-muted">Est. Daily Revenue</span>
                <span className="text-2xl font-bold text-transit-500">${selectedRoute.revenue.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* AI Insights */}
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-4">AI Insights</h3>
          
          <div className="space-y-4">
            {selectedRoute.onTime < 80 ? (
              <div className="p-3 rounded-lg bg-severity-danger/10 border border-severity-danger/30">
                <div className="flex items-start gap-2">
                  <span className="text-severity-danger">🔴</span>
                  <div>
                    <p className="font-medium text-white">Critical Performance</p>
                    <p className="text-sm text-dark-muted mt-1">
                      Route is {100 - selectedRoute.onTime}% below target. Consider:
                    </p>
                    <ul className="text-sm text-dark-muted mt-2 space-y-1 list-disc list-inside">
                      <li>Increasing service frequency</li>
                      <li>Reviewing schedule timing</li>
                      <li>Infrastructure inspection</li>
                    </ul>
                  </div>
                </div>
              </div>
            ) : selectedRoute.onTime < 90 ? (
              <div className="p-3 rounded-lg bg-severity-warning/10 border border-severity-warning/30">
                <div className="flex items-start gap-2">
                  <span className="text-severity-warning">🟡</span>
                  <div>
                    <p className="font-medium text-white">Monitor Closely</p>
                    <p className="text-sm text-dark-muted mt-1">
                      Performance at {selectedRoute.onTime}% - approaching threshold.
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

            {selectedRoute.utilization < 50 && (
              <div className="p-3 rounded-lg bg-severity-info/10 border border-severity-info/30">
                <div className="flex items-start gap-2">
                  <span className="text-severity-info">💡</span>
                  <div>
                    <p className="font-medium text-white">Efficiency Opportunity</p>
                    <p className="text-sm text-dark-muted mt-1">
                      At {selectedRoute.utilization}% utilization, consider reducing off-peak frequency to optimize costs.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {selectedRoute.utilization > 75 && (
              <div className="p-3 rounded-lg bg-severity-warning/10 border border-severity-warning/30">
                <div className="flex items-start gap-2">
                  <span className="text-severity-warning">📈</span>
                  <div>
                    <p className="font-medium text-white">High Demand</p>
                    <p className="text-sm text-dark-muted mt-1">
                      At {selectedRoute.utilization}% capacity. Consider adding service during peak hours.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Hourly Performance Chart */}
      <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
        <h3 className="text-lg font-semibold text-white mb-4">Hourly Performance - {selectedRoute.name}</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={hourlyPerformance}>
            <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
            <XAxis dataKey="hour" stroke="#8B949E" fontSize={12} />
            <YAxis stroke="#8B949E" fontSize={12} domain={[70, 100]} />
            <Tooltip
              contentStyle={{ background: '#0D1117', border: '1px solid #3FB950', borderRadius: '8px', color: '#FFFFFF' }}
              labelStyle={{ color: '#FFFFFF', fontWeight: 'bold' }}
              itemStyle={{ color: '#C9D1D9' }}
            />
            <Line 
              type="monotone" 
              dataKey="onTime" 
              name="On-Time %" 
              stroke={selectedRoute.color} 
              strokeWidth={3}
              dot={{ fill: selectedRoute.color, strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

