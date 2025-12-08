import { useState, useEffect } from 'react'
import { getApiBaseUrl, getBackendBaseUrl } from '../utils/api'
import clsx from 'clsx'

interface AgencyData {
  stops_count: number
  routes_count: number
  departures_count: number
  stops_samples: any[]
  routes_samples: any[]
  departures_samples: any[]
  city: string
}

interface AdminStatus {
  snowflake: {
    status: string
    error?: string
  }
  local_database: {
    status: string
    stops_count?: number
    routes_count?: number
    departures_count?: number
    stops_samples?: any[]
    routes_samples?: any[]
    departures_samples?: any[]
    agencies?: string[]
    agency_data?: Record<string, AgencyData>
    stops_last_update?: string
    routes_last_update?: string
    departures_last_update?: string
    streaming_count?: number
    streaming_status?: string
    error?: string
  }
  api: {
    status: string
    endpoint: string
    docs: string
  }
  pipelines: {
    batch_dag: {
      name: string
      status: string
      schedule: string
      last_run?: string
      next_run?: string
      airflow_url?: string
    }
    incremental_dag: {
      name: string
      status: string
      schedule: string
      last_run?: string
      next_run?: string
      airflow_url?: string
    }
    ml_dag?: {
      name: string
      status: string
      schedule: string
      last_run?: string
      next_run?: string
      airflow_url?: string
    }
    streaming: {
      status: string
      last_refresh?: string
    }
  }
  timestamp: string
}

interface StreamingStatus {
  is_running: boolean
  pid?: number
}

export default function Admin() {
  const [status, setStatus] = useState<AdminStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [streamingStatus, setStreamingStatus] = useState<StreamingStatus | null>(null)

  useEffect(() => {
    fetchAdminStatus()
    fetchStreamingStatus()
    // Manual refresh only - no auto-reload
    // const interval = setInterval(fetchAdminStatus, 30000)
    // return () => clearInterval(interval)
  }, [])

  const fetchStreamingStatus = async () => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/admin/streaming-status`)
      const result = await response.json()
      if (result.success) {
        setStreamingStatus(result.data)
      }
    } catch (err) {
      console.error('Error fetching streaming status:', err)
    }
  }

  const fetchAdminStatus = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${getApiBaseUrl()}/admin/status`, {
        cache: 'no-cache',
        headers: {
          'Cache-Control': 'no-cache'
        }
      })
      const data = await response.json()
      if (data.success) {
        setStatus(data.data)
        setError(null)
      } else {
        setError(data.error || 'Failed to fetch admin status')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch admin status')
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const colors = {
      connected: 'bg-green-500/20 text-green-400 border border-green-500/50',
      operational: 'bg-green-500/20 text-green-400 border border-green-500/50',
      active: 'bg-green-500/20 text-green-400 border border-green-500/50',
      scheduled: 'bg-blue-500/20 text-blue-400 border border-blue-500/50',
      disconnected: 'bg-red-500/20 text-red-400 border border-red-500/50',
      error: 'bg-red-500/20 text-red-400 border border-red-500/50',
      snowflake_data: 'bg-green-500/20 text-green-400 border border-green-500/50',
      not_used: 'bg-gray-500/20 text-gray-400 border border-gray-500/50',
    }
    return (
      <span className={`px-2 py-1 rounded text-xs font-semibold ${colors[status as keyof typeof colors] || 'bg-gray-500/20 text-gray-400 border border-gray-500/50'}`}>
        {status.toUpperCase()}
      </span>
    )
  }

  const formatTimestamp = (ts: string | null | undefined) => {
    if (!ts) return 'N/A'
    try {
      return new Date(ts).toLocaleString()
    } catch {
      return ts
    }
  }

  if (loading) {
    return (
      <div className="p-8 bg-dark-bg min-h-screen">
        <div className="text-center text-white">Loading admin status...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8 bg-dark-bg min-h-screen">
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-red-400">
          Error: {error}
        </div>
      </div>
    )
  }

  if (!status) {
    return (
      <div className="p-8 bg-dark-bg min-h-screen">
        <div className="text-center text-white">No status data available</div>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6 bg-dark-bg min-h-screen">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white">Admin Panel</h1>
        <button
          onClick={fetchAdminStatus}
          className="px-4 py-2 bg-transit-500 text-white rounded-lg hover:bg-transit-600 transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Service Status */}
      <div className="bg-dark-surface rounded-xl border border-dark-border p-6">
        <h2 className="text-xl font-semibold mb-4 text-white">Service Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border border-dark-border rounded-lg p-4 bg-dark-bg">
            <div className="flex justify-between items-center mb-2">
              <span className="font-medium text-white">Snowflake</span>
              {getStatusBadge(status.snowflake.status)}
            </div>
            {status.snowflake.error && (
              <p className="text-sm text-red-400 mt-2">{status.snowflake.error.substring(0, 100)}...</p>
            )}
          </div>
          <div className="border border-dark-border rounded-lg p-4 bg-dark-bg">
            <div className="flex justify-between items-center mb-2">
              <span className="font-medium text-white">Data Source</span>
              {getStatusBadge(status.local_database.status)}
            </div>
            <p className="text-xs text-dark-muted mt-2">Data from Snowflake tables</p>
            {status.local_database.error && (
              <p className="text-sm text-red-400 mt-2">{status.local_database.error}</p>
            )}
          </div>
          <div className="border border-dark-border rounded-lg p-4 bg-dark-bg">
            <div className="flex justify-between items-center mb-2">
              <span className="font-medium text-white">API</span>
              {getStatusBadge(status.api.status)}
            </div>
            <div className="space-y-1">
              <div>
                <a href={`${getBackendBaseUrl()}/docs`} target="_blank" rel="noopener noreferrer" className="text-sm text-transit-500 hover:underline">
                  API Docs
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Data Counts */}
      <div className="bg-dark-surface rounded-xl border border-dark-border p-6">
        <h2 className="text-xl font-semibold mb-4 text-white">Data Counts (Snowflake)</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border border-dark-border rounded-lg p-4 bg-dark-bg">
            <div className="text-3xl font-bold text-transit-500">
              {status.local_database.stops_count?.toLocaleString() || 0}
            </div>
            <div className="text-sm text-dark-muted mt-1">Stops</div>
            <div className="text-xs text-dark-muted mt-2">
              Last updated: {formatTimestamp(status.local_database.stops_last_update)}
            </div>
          </div>
          <div className="border border-dark-border rounded-lg p-4 bg-dark-bg">
            <div className="text-3xl font-bold text-transit-500">
              {status.local_database.routes_count?.toLocaleString() || 0}
            </div>
            <div className="text-sm text-dark-muted mt-1">Routes</div>
            <div className="text-xs text-dark-muted mt-2">
              Last updated: {formatTimestamp(status.local_database.routes_last_update)}
            </div>
          </div>
          <div className="border border-dark-border rounded-lg p-4 bg-dark-bg">
            <div className="text-3xl font-bold text-transit-500">
              {status.local_database.departures_count?.toLocaleString() || 0}
            </div>
            <div className="text-sm text-dark-muted mt-1">Departures</div>
            <div className="text-xs text-dark-muted mt-2">
              Last updated: {formatTimestamp(status.local_database.departures_last_update)}
            </div>
          </div>
        </div>
        {status.local_database.agency_data && Object.keys(status.local_database.agency_data).length > 0 && (
          <div className="mt-4 p-4 bg-dark-bg rounded-lg border border-dark-border">
            <h3 className="text-sm font-semibold mb-3 text-white">Data by Agency (BART & VTA):</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(status.local_database.agency_data)
                .filter(([agency]) => agency === 'BART' || agency === 'VTA') // Only show BART and VTA
                .map(([agency, data]: [string, any]) => (
                <div key={agency} className="border border-dark-border rounded-lg p-4 bg-dark-surface">
                  <div className="font-semibold text-white text-lg mb-2">{agency}</div>
                  <div className="text-sm text-dark-muted mb-3">Location: {data.city || 'Unknown'}</div>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div>
                      <div className="text-xl font-bold text-transit-500">{data.stops_count?.toLocaleString() || 0}</div>
                      <div className="text-xs text-dark-muted">Stops</div>
                    </div>
                    <div>
                      <div className="text-xl font-bold text-transit-500">{data.routes_count?.toLocaleString() || 0}</div>
                      <div className="text-xs text-dark-muted">Routes</div>
                    </div>
                    <div>
                      <div className="text-xl font-bold text-transit-500">{data.departures_count?.toLocaleString() || 0}</div>
                      <div className="text-xs text-dark-muted">Departures</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Streaming Data Status */}
      {status.local_database.streaming_count !== undefined && (
        <div className="bg-dark-surface rounded-xl border-2 border-transit-500/50 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Streaming Data (Live)</h2>
            <div className="flex gap-2 items-center">
              {streamingStatus?.is_running ? (
                <>
                  <span className="px-3 py-2 bg-green-500/20 text-green-400 rounded-lg text-sm font-medium">
                    ● Running (PID: {streamingStatus.pid})
                  </span>
                  <button
                    onClick={async () => {
                      const response = await fetch(`${getApiBaseUrl()}/admin/streaming/stop`, { method: 'POST' })
                      const result = await response.json()
                      if (result.success) {
                        alert('Streaming producer stopped')
                        fetchAdminStatus()
                        fetchStreamingStatus()
                      } else {
                        alert(`Error: ${result.error}`)
                      }
                    }}
                    className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm"
                  >
                    ⏹ Stop Streaming
                  </button>
                </>
              ) : (
                <button
                  onClick={async () => {
                    const response = await fetch(`${getApiBaseUrl()}/admin/streaming/start`, { method: 'POST' })
                    const result = await response.json()
                    if (result.success) {
                      alert(`Streaming producer started! PID: ${result.data.pid}`)
                      fetchAdminStatus()
                      fetchStreamingStatus()
                    } else {
                      alert(`Error: ${result.error}`)
                    }
                  }}
                  className="px-4 py-2 bg-transit-500 text-white rounded-lg hover:bg-transit-600 transition-colors text-sm"
                >
                  ▶ Start Streaming
                </button>
              )}
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border-2 border-transit-500/50 rounded-lg p-4 bg-dark-bg">
              <div className="flex items-center gap-2 mb-2">
                <span className={`w-3 h-3 rounded-full ${status.local_database.streaming_status === 'active' ? 'bg-transit-500 animate-pulse' : 'bg-gray-500'}`}></span>
                <span className="font-semibold text-white">Streaming Status</span>
              </div>
              <div className="text-2xl font-bold text-transit-500">
                {status.local_database.streaming_status === 'active' ? 'ACTIVE' : 'INACTIVE'}
              </div>
              <div className="text-sm text-dark-muted mt-1">
                Recent data (last hour): {status.local_database.streaming_count?.toLocaleString() || 0} records
              </div>
              {status.local_database.streaming_table_count !== undefined && (
                <div className="text-xs text-dark-muted mt-1">
                  Total in streaming table: {status.local_database.streaming_table_count?.toLocaleString() || 0}
                </div>
              )}
              {status.pipelines.streaming.last_refresh && (
                <div className="text-xs text-dark-muted mt-1 font-mono">
                  Last refresh: {new Date(status.pipelines.streaming.last_refresh).toLocaleString()}
                </div>
              )}
            </div>
            <div className="border border-dark-border rounded-lg p-4 bg-dark-bg">
              <div className="font-medium text-white mb-2">Streaming Method</div>
              <div className="text-sm text-dark-muted">
                <div>• TransitApp API (Real-time)</div>
                <div>• Kafka (Local Development)</div>
                <div className="text-xs text-dark-muted mt-2">
                  Data stored in LANDING_STREAMING_DEPARTURES, then merged via dbt
                </div>
              </div>
            </div>
            <div className="border border-dark-border rounded-lg p-4 bg-dark-bg">
              <div className="font-medium text-white mb-2">Data Flow</div>
              <div className="text-xs text-dark-muted space-y-1">
                <div>1. TransitApp API → LANDING_STREAMING_DEPARTURES</div>
                <div>2. dbt transforms → STAGING.STG_DEPARTURES</div>
                <div>3. Available in all dashboards</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pipeline Status - DAGs & dbt */}
      {status.pipelines && (
        <div className="bg-dark-surface rounded-xl border border-dark-border p-6">
          <h2 className="text-xl font-semibold mb-4 text-white">Data Pipeline Status (Airflow DAGs & dbt)</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Batch DAG */}
            {status.pipelines.batch_dag && (
              <div className="border border-dark-border rounded-lg p-4 bg-dark-bg">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium text-sm text-white">Batch DAG</span>
                  {getStatusBadge(status.pipelines.batch_dag.status || 'scheduled')}
                </div>
                <div className="text-xs text-white mb-1">
                  <strong>{status.pipelines.batch_dag.name || 'unified_ingestion_dag'}</strong>
                </div>
                <div className="text-xs text-dark-muted mb-1">
                  Schedule: {status.pipelines.batch_dag.schedule || 'Every 12 hours'}
                </div>
                {status.pipelines.batch_dag.last_run && (
                  <div className="text-xs text-dark-muted mb-1">
                    Last run: {new Date(status.pipelines.batch_dag.last_run).toLocaleString()}
                  </div>
                )}
                <div className="text-xs text-transit-500 space-y-1 mt-1">
                  {status.pipelines.batch_dag.airflow_url_local && (
                    <div>
                      <a href={status.pipelines.batch_dag.airflow_url_local} target="_blank" rel="noopener noreferrer" className="hover:underline">
                        View in Airflow →
                      </a>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Transformation DAG */}
            {status.pipelines.incremental_dag && (
              <div className="border border-dark-border rounded-lg p-4 bg-dark-bg">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium text-sm text-white">dbt Transformations</span>
                  {getStatusBadge(status.pipelines.incremental_dag.status || 'scheduled')}
                </div>
                <div className="text-xs text-white mb-1">
                  <strong>{status.pipelines.incremental_dag.name || 'dbt_landing_to_raw, dbt_raw_to_transform, dbt_transform_to_analytics'}</strong>
                </div>
                <div className="text-xs text-dark-muted mb-1">
                  Schedule: {status.pipelines.incremental_dag.schedule || 'Triggered after ingestion'}
                </div>
                <div className="text-xs text-dark-muted mb-1">
                  Uses: <strong>dbt</strong> for transformations
                </div>
                {status.pipelines.incremental_dag.last_run && (
                  <div className="text-xs text-dark-muted mb-1">
                    Last run: {new Date(status.pipelines.incremental_dag.last_run).toLocaleString()}
                  </div>
                )}
                <div className="text-xs text-transit-500 space-y-1 mt-1">
                  {status.pipelines.incremental_dag.airflow_url_local && (
                    <div>
                      <a href={status.pipelines.incremental_dag.airflow_url_local} target="_blank" rel="noopener noreferrer" className="hover:underline">
                        View in Airflow →
                      </a>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ML DAG */}
            {status.pipelines.ml_dag && (
              <div className="border border-dark-border rounded-lg p-4 bg-dark-bg">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium text-sm text-white">ML Forecast DAG</span>
                  {getStatusBadge(status.pipelines.ml_dag.status || 'scheduled')}
                </div>
                <div className="text-xs text-white mb-1">
                  <strong>{status.pipelines.ml_dag.name || 'ml_forecast_dag'}</strong>
                </div>
                <div className="text-xs text-dark-muted mb-1">
                  Schedule: {status.pipelines.ml_dag.schedule || 'Daily at 3 AM UTC'}
                </div>
                {status.pipelines.ml_dag.last_run && (
                  <div className="text-xs text-dark-muted mb-1">
                    Last run: {new Date(status.pipelines.ml_dag.last_run).toLocaleString()}
                  </div>
                )}
                <div className="text-xs text-transit-500 space-y-1 mt-1">
                  {status.pipelines.ml_dag.airflow_url_local && (
                    <div>
                      <a href={status.pipelines.ml_dag.airflow_url_local} target="_blank" rel="noopener noreferrer" className="hover:underline">
                        View in Airflow →
                      </a>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Streaming Status */}
            {status.pipelines.streaming && (
              <div className="border border-dark-border rounded-lg p-4 bg-dark-bg">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium text-sm text-white">Streaming</span>
                  {getStatusBadge(status.pipelines.streaming.status || 'inactive')}
                </div>
                <div className="text-xs text-dark-muted mb-1">
                  Real-time API ingestion
                </div>
                {status.pipelines.streaming.last_refresh && (
                  <div className="text-xs text-dark-muted mb-1">
                    Last refresh: {new Date(status.pipelines.streaming.last_refresh).toLocaleString()}
                  </div>
                )}
                <div className="text-xs text-dark-muted">
                  Method: TransitApp API → LANDING_STREAMING_DEPARTURES
                </div>
              </div>
            )}
          </div>

          {/* dbt Models Info */}
          <div className="mt-4 p-4 bg-dark-bg rounded-lg border border-dark-border">
            <h3 className="text-sm font-semibold mb-2 text-white">dbt Models & Transformations</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div>
                <strong className="text-white">Staging Models (landing_to_raw):</strong>
                <ul className="list-disc list-inside text-dark-muted mt-1">
                  <li>stg_gtfs_stops</li>
                  <li>stg_gtfs_routes</li>
                  <li>stg_gtfs_trips</li>
                  <li>stg_gtfs_stop_times</li>
                  <li>stg_streaming_departures</li>
                </ul>
              </div>
              <div>
                <strong className="text-white">Analytics Marts (transform_to_analytics):</strong>
                <ul className="list-disc list-inside text-dark-muted mt-1">
                  <li>reliability_metrics</li>
                  <li>crowding_metrics</li>
                  <li>revenue_metrics</li>
                  <li>route_health</li>
                </ul>
              </div>
              <div>
                <strong className="text-white">dbt Location:</strong>
                <div className="text-dark-muted mt-1">
                  <code className="text-xs">dbt/transit_dbt/models/</code>
                </div>
                <div className="text-dark-muted mt-2">
                  <strong>dbt Docs:</strong>
                  <div className="mt-1">Run: <code className="text-xs">dbt docs generate && dbt docs serve</code></div>
                  <div className="text-transit-500 mt-1">
                    <div>Local: <a href="http://localhost:8080" target="_blank" rel="noopener noreferrer" className="underline">http://localhost:8080</a></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Sample Data by Agency - BART and VTA Only */}
      {status.local_database.agency_data && Object.keys(status.local_database.agency_data).length > 0 && (
        <div className="bg-dark-surface rounded-xl border border-dark-border p-6">
          <h2 className="text-xl font-semibold mb-4 text-white">Sample Data by Agency (BART & VTA)</h2>
          <p className="text-sm text-dark-muted mb-4">
            Note: Data is stored in Snowflake tables with 'AGENCY_NAME' column. BART (Heavy Rail/Subway) and VTA (Bus/Light Rail) 
            use the same GTFS structure but are filtered by agency.
          </p>
          
          {Object.entries(status.local_database.agency_data)
            .filter(([agency]) => agency === 'BART' || agency === 'VTA') // Only show BART and VTA
            .map(([agency, data]: [string, any]) => (
            <div key={agency} className="mb-8 border-2 border-dark-border rounded-lg p-4 bg-dark-bg">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">
                  {agency} - {data.city || 'Unknown Location'}
                </h3>
                <div className="text-sm text-dark-muted">
                  {data.stops_count?.toLocaleString() || 0} stops, {data.routes_count?.toLocaleString() || 0} routes, {data.departures_count?.toLocaleString() || 0} departures
                </div>
              </div>

              {/* Routes Sample */}
              {data.routes_samples && data.routes_samples.length > 0 && (
                <div className="mb-4">
                  <h4 className="font-semibold mb-2 text-sm text-white">Routes Sample ({data.routes_samples.length} records)</h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-xs border border-dark-border">
                      <thead className="bg-dark-surface">
                        <tr>
                          {Object.keys(data.routes_samples[0]).map(key => (
                            <th key={key} className="px-2 py-1 text-left border border-dark-border text-xs text-white">{key}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {data.routes_samples.map((row: any, idx: number) => (
                          <tr key={idx} className="border-b border-dark-border">
                            {Object.values(row).map((val: any, i: number) => (
                              <td key={i} className="px-2 py-1 border border-dark-border text-xs text-dark-muted">{String(val || 'N/A')}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Stops Sample */}
              {data.stops_samples && data.stops_samples.length > 0 && (
                <div className="mb-4">
                  <h4 className="font-semibold mb-2 text-sm text-white">Stops Sample ({data.stops_samples.length} records)</h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-xs border border-dark-border">
                      <thead className="bg-dark-surface">
                        <tr>
                          {Object.keys(data.stops_samples[0]).map(key => (
                            <th key={key} className="px-2 py-1 text-left border border-dark-border text-xs text-white">{key}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {data.stops_samples.map((row: any, idx: number) => (
                          <tr key={idx} className="border-b border-dark-border">
                            {Object.values(row).map((val: any, i: number) => (
                              <td key={i} className="px-2 py-1 border border-dark-border text-xs text-dark-muted">{String(val || 'N/A')}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Departures Sample */}
              {data.departures_samples && data.departures_samples.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2 text-sm text-white">Departures Sample ({data.departures_samples.length} records)</h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-xs border border-dark-border">
                      <thead className="bg-dark-surface">
                        <tr>
                          {Object.keys(data.departures_samples[0]).map(key => (
                            <th key={key} className="px-2 py-1 text-left border border-dark-border text-xs text-white">{key}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {data.departures_samples.map((row: any, idx: number) => (
                          <tr key={idx} className="border-b border-dark-border">
                            {Object.values(row).map((val: any, i: number) => (
                              <td key={i} className="px-2 py-1 border border-dark-border text-xs text-dark-muted">{String(val || 'N/A')}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Overall Sample Data (if no agency breakdown) */}
      {(!status.local_database.agency_data || Object.keys(status.local_database.agency_data).length === 0) && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Sample Data (All Agencies)</h2>
          
          {/* Stops Sample */}
          {status.local_database.stops_samples && status.local_database.stops_samples.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold mb-2">Stops (Sample - {status.local_database.stops_samples.length} records)</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm border">
                  <thead className="bg-gray-50">
                    <tr>
                      {Object.keys(status.local_database.stops_samples[0]).map(key => (
                        <th key={key} className="px-4 py-2 text-left border">{key}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {status.local_database.stops_samples.map((row, idx) => (
                      <tr key={idx} className="border-b">
                        {Object.values(row).map((val, i) => (
                          <td key={i} className="px-4 py-2 border">{String(val || 'N/A')}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Routes Sample */}
          {status.local_database.routes_samples && status.local_database.routes_samples.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold mb-2">Routes (Sample - {status.local_database.routes_samples.length} records)</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm border">
                  <thead className="bg-gray-50">
                    <tr>
                      {Object.keys(status.local_database.routes_samples[0]).map(key => (
                        <th key={key} className="px-4 py-2 text-left border">{key}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {status.local_database.routes_samples.map((row, idx) => (
                      <tr key={idx} className="border-b">
                        {Object.values(row).map((val, i) => (
                          <td key={i} className="px-4 py-2 border">{String(val || 'N/A')}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Departures Sample */}
          {status.local_database.departures_samples && status.local_database.departures_samples.length > 0 && (
            <div>
              <h3 className="font-semibold mb-2">Departures (Sample - {status.local_database.departures_samples.length} records)</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm border">
                  <thead className="bg-gray-50">
                    <tr>
                      {Object.keys(status.local_database.departures_samples[0]).map(key => (
                        <th key={key} className="px-4 py-2 text-left border">{key}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {status.local_database.departures_samples.map((row, idx) => (
                      <tr key={idx} className="border-b">
                        {Object.values(row).map((val, i) => (
                          <td key={i} className="px-4 py-2 border">{String(val || 'N/A')}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Last Updated */}
      <div className="text-sm text-dark-muted text-right">
        Last refreshed: {formatTimestamp(status.timestamp)}
      </div>
    </div>
  )
}

