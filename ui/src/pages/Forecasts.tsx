import { useState } from 'react'
import clsx from 'clsx'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'

// 6-hour forecast data
const forecast6h = [
  { time: 'Now', actual: 42, predicted: 42 },
  { time: '+1h', actual: null, predicted: 48 },
  { time: '+2h', actual: null, predicted: 55 },
  { time: '+3h', actual: null, predicted: 62 },
  { time: '+4h', actual: null, predicted: 58 },
  { time: '+5h', actual: null, predicted: 45 },
  { time: '+6h', actual: null, predicted: 38 },
]

// 24-hour forecast data
const forecast24h = [
  { time: '6AM', predicted: 35 },
  { time: '8AM', predicted: 65 },
  { time: '10AM', predicted: 45 },
  { time: '12PM', predicted: 50 },
  { time: '2PM', predicted: 55 },
  { time: '4PM', predicted: 70 },
  { time: '6PM', predicted: 85 },
  { time: '8PM', predicted: 60 },
  { time: '10PM', predicted: 35 },
  { time: '12AM', predicted: 15 },
]

// 7-day forecast data
const forecast7d = [
  { day: 'Today', departures: 480, revenue: 14200, onTime: 94 },
  { day: 'Tomorrow', departures: 520, revenue: 15100, onTime: 92 },
  { day: 'Day 3', departures: 490, revenue: 14500, onTime: 93 },
  { day: 'Day 4', departures: 510, revenue: 14900, onTime: 91 },
  { day: 'Day 5', departures: 550, revenue: 16200, onTime: 88 },
  { day: 'Day 6', departures: 320, revenue: 9800, onTime: 96 },
  { day: 'Day 7', departures: 280, revenue: 8500, onTime: 97 },
]

const delayPredictions = [
  { route: 'Blue Line', currentDelay: 0, predictedDelay: 2, confidence: 92, trend: 'stable' },
  { route: 'Red Line', currentDelay: 3, predictedDelay: 5, confidence: 85, trend: 'increasing' },
  { route: 'Green Line', currentDelay: 8, predictedDelay: 12, confidence: 78, trend: 'increasing' },
  { route: 'Yellow Line', currentDelay: 1, predictedDelay: 1, confidence: 95, trend: 'stable' },
]

const crowdingForecast = [
  { hour: '6AM', predicted: 35 },
  { hour: '7AM', predicted: 65 },
  { hour: '8AM', predicted: 85 },
  { hour: '9AM', predicted: 75 },
  { hour: '10AM', predicted: 45 },
  { hour: '11AM', predicted: 40 },
  { hour: '12PM', predicted: 50 },
  { hour: '5PM', predicted: 90 },
  { hour: '6PM', predicted: 80 },
]

// Custom tooltip style
const tooltipStyle = {
  contentStyle: { background: '#0D1117', border: '1px solid #3FB950', borderRadius: '8px', color: '#FFFFFF' },
  labelStyle: { color: '#FFFFFF', fontWeight: 'bold' },
  itemStyle: { color: '#C9D1D9' }
}

export default function Forecasts() {
  const [forecastWindow, setForecastWindow] = useState<'6h' | '24h' | '7d'>('6h')

  const getWindowLabel = () => {
    switch (forecastWindow) {
      case '6h': return 'Next 6 Hours'
      case '24h': return 'Next 24 Hours'
      case '7d': return 'Next 7 Days'
    }
  }

  const getPredictionCards = () => {
    switch (forecastWindow) {
      case '6h':
        return { peak: 62, peakTime: 'In 3 hours', revenue: '$2.4K', onTime: '94.2%', onTimeNote: 'Stable' }
      case '24h':
        return { peak: 85, peakTime: 'At 6 PM', revenue: '$14.2K', onTime: '91.2%', onTimeNote: 'PM Peak concern' }
      case '7d':
        return { peak: 550, peakTime: 'Day 5 (Friday)', revenue: '$98.2K', onTime: '93.0%', onTimeNote: 'Weekend improvement' }
    }
  }

  const cards = getPredictionCards()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Forecasts & Predictions</h1>
          <p className="text-dark-muted">ML-powered demand and performance predictions</p>
        </div>
        <div className="flex gap-2">
          {(['6h', '24h', '7d'] as const).map((window) => (
            <button
              key={window}
              onClick={() => setForecastWindow(window)}
              className={clsx(
                'px-4 py-2 rounded-lg transition-colors font-medium',
                forecastWindow === window
                  ? 'bg-transit-500 text-white'
                  : 'bg-dark-surface border border-dark-border text-dark-muted hover:text-white hover:border-transit-500'
              )}
            >
              {window}
            </button>
          ))}
        </div>
      </div>

      {/* Active Window Indicator */}
      <div className="p-3 rounded-lg bg-transit-500/10 border border-transit-500/30">
        <p className="text-transit-500 font-medium">
          📊 Showing forecast for: <span className="text-white">{getWindowLabel()}</span>
        </p>
      </div>

      {/* Prediction Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 rounded-xl bg-dark-surface border border-dark-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-dark-muted text-sm">Predicted Peak Demand</span>
            <span className="text-xs px-2 py-1 rounded-full bg-severity-info/20 text-severity-info">{cards.peakTime}</span>
          </div>
          <div className="text-3xl font-bold text-white">{cards.peak}</div>
          <div className="text-sm text-dark-muted">{forecastWindow === '7d' ? 'departures/day' : 'departures/hour'}</div>
        </div>

        <div className="p-5 rounded-xl bg-dark-surface border border-dark-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-dark-muted text-sm">Expected Revenue ({forecastWindow})</span>
            <span className="text-xs px-2 py-1 rounded-full bg-transit-500/20 text-transit-500">High confidence</span>
          </div>
          <div className="text-3xl font-bold text-white">{cards.revenue}</div>
          <div className="text-sm text-dark-muted">predicted revenue</div>
        </div>

        <div className="p-5 rounded-xl bg-dark-surface border border-dark-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-dark-muted text-sm">On-Time Forecast</span>
            <span className="text-xs px-2 py-1 rounded-full bg-severity-warning/20 text-severity-warning">{cards.onTimeNote}</span>
          </div>
          <div className="text-3xl font-bold text-white">{cards.onTime}</div>
          <div className="text-sm text-dark-muted">expected average</div>
        </div>
      </div>

      {/* Charts based on selected window */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Main Forecast Chart */}
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-4">Demand Forecast ({getWindowLabel()})</h3>
          <ResponsiveContainer width="100%" height={250}>
            {forecastWindow === '7d' ? (
              <LineChart data={forecast7d}>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
                <XAxis dataKey="day" stroke="#8B949E" />
                <YAxis stroke="#8B949E" />
                <Tooltip {...tooltipStyle} />
                <Line type="monotone" dataKey="departures" name="Departures" stroke="#58A6FF" strokeWidth={2} dot={{ fill: '#58A6FF' }} />
              </LineChart>
            ) : forecastWindow === '24h' ? (
              <AreaChart data={forecast24h}>
                <defs>
                  <linearGradient id="color24h" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#58A6FF" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#58A6FF" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
                <XAxis dataKey="time" stroke="#8B949E" />
                <YAxis stroke="#8B949E" />
                <Tooltip {...tooltipStyle} />
                <Area type="monotone" dataKey="predicted" name="Predicted" stroke="#58A6FF" fill="url(#color24h)" strokeWidth={2} />
              </AreaChart>
            ) : (
              <AreaChart data={forecast6h}>
                <defs>
                  <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3FB950" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3FB950" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#A371F7" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#A371F7" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
                <XAxis dataKey="time" stroke="#8B949E" />
                <YAxis stroke="#8B949E" />
                <Tooltip {...tooltipStyle} />
                <Area type="monotone" dataKey="actual" name="Actual" stroke="#3FB950" fill="url(#colorActual)" strokeWidth={2} />
                <Area type="monotone" dataKey="predicted" name="Predicted" stroke="#A371F7" fill="url(#colorPredicted)" strokeWidth={2} strokeDasharray="5 5" />
              </AreaChart>
            )}
          </ResponsiveContainer>
        </div>

        {/* Crowding Forecast */}
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-4">Crowding Forecast</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={crowdingForecast}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
              <XAxis dataKey="hour" stroke="#8B949E" />
              <YAxis stroke="#8B949E" domain={[0, 100]} />
              <Tooltip 
                {...tooltipStyle}
                formatter={(value: number) => [`${value}%`, 'Capacity']}
              />
              <Area 
                type="monotone" 
                dataKey="predicted" 
                name="Crowding %" 
                stroke="#F85149" 
                fill="#F85149" 
                fillOpacity={0.3} 
                strokeWidth={2} 
              />
            </AreaChart>
          </ResponsiveContainer>
          <div className="mt-4 p-3 rounded-lg bg-severity-danger/10 border border-severity-danger/30">
            <p className="text-sm text-severity-danger">
              ⚠️ 5 PM forecasted at 90% capacity. Consider adding extra service.
            </p>
          </div>
        </div>
      </div>

      {/* Delay Predictions Table */}
      <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
        <h3 className="text-lg font-semibold text-white mb-4">Route Delay Predictions</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-sm text-dark-muted border-b border-dark-border">
                <th className="pb-3 font-medium">Route</th>
                <th className="pb-3 font-medium">Current Delay</th>
                <th className="pb-3 font-medium">Predicted (2h)</th>
                <th className="pb-3 font-medium">Trend</th>
                <th className="pb-3 font-medium">Confidence</th>
                <th className="pb-3 font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {delayPredictions.map((route) => (
                <tr key={route.route} className="border-b border-dark-border/50">
                  <td className="py-4 font-medium text-white">{route.route}</td>
                  <td className="py-4">
                    <span className={clsx(
                      'font-mono',
                      route.currentDelay <= 2 ? 'text-transit-500' : route.currentDelay <= 5 ? 'text-severity-warning' : 'text-severity-danger'
                    )}>
                      {route.currentDelay} min
                    </span>
                  </td>
                  <td className="py-4">
                    <span className={clsx(
                      'font-mono',
                      route.predictedDelay <= 2 ? 'text-transit-500' : route.predictedDelay <= 5 ? 'text-severity-warning' : 'text-severity-danger'
                    )}>
                      {route.predictedDelay} min
                    </span>
                  </td>
                  <td className="py-4">
                    <span className={clsx(
                      'flex items-center gap-1',
                      route.trend === 'stable' ? 'text-transit-500' : 'text-severity-danger'
                    )}>
                      {route.trend === 'stable' ? '→' : '↑'} {route.trend}
                    </span>
                  </td>
                  <td className="py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-dark-bg rounded-full h-2">
                        <div 
                          className="h-2 rounded-full bg-severity-info"
                          style={{ width: `${route.confidence}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-dark-muted">{route.confidence}%</span>
                    </div>
                  </td>
                  <td className="py-4">
                    {route.trend === 'increasing' && route.predictedDelay > 5 ? (
                      <span className="px-2 py-1 rounded text-xs bg-severity-danger/20 text-severity-danger">
                        Review Schedule
                      </span>
                    ) : (
                      <span className="px-2 py-1 rounded text-xs bg-transit-500/20 text-transit-500">
                        Monitor
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Model Info */}
      <div className="p-4 rounded-xl bg-severity-info/10 border border-severity-info/30">
        <div className="flex items-start gap-3">
          <span className="text-severity-info text-xl">🤖</span>
          <div>
            <h4 className="font-medium text-white">About These Predictions</h4>
            <p className="text-sm text-dark-muted mt-1">
              Forecasts are generated using Snowflake ML time-series models trained on historical transit data. 
              Confidence scores indicate prediction reliability based on historical accuracy. 
              Models are retrained daily for improved accuracy.
            </p>
            <p className="text-xs text-dark-muted mt-2">
              Developed by <span className="text-transit-500 font-medium">Ayush Gawai</span> | SJSU Applied Data Science
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
