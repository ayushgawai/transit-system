import { useState, useEffect } from 'react'
import { getApiBaseUrl } from '../utils/api'
import clsx from 'clsx'
import { useAgency } from '../contexts/AgencyContext'

export default function MapView() {
  const { agency } = useAgency()
  const [stops, setStops] = useState<any[]>([])
  const [selectedStop, setSelectedStop] = useState<any | null>(null)
  const [mapLayer, setMapLayer] = useState<'demand' | 'performance'>('demand')
  const [mapLoaded, setMapLoaded] = useState(false)
  const [loading, setLoading] = useState(true)
  const [cityInfo, setCityInfo] = useState<string>('')

  useEffect(() => {
    fetchStops()
  }, [agency])

  const fetchStops = async () => {
    setLoading(true)
    try {
      const url = agency === 'All'
        ? `${getApiBaseUrl()}/stops?limit=100`
        : `${getApiBaseUrl()}/stops?agency=${agency}&limit=100`
      
      const response = await fetch(url)
      const result = await response.json()
      
      if (result.success && result.data) {
        const fetchedStops = result.data.map((s: any) => ({
          id: s.id,
          name: s.name,
          lat: s.lat,
          lon: s.lon,
          departures: s.departures || 0,
          routes: [],
          status: s.status || 'active',
          agency: s.agency
        }))
        setStops(fetchedStops)
        
        // Extract city info from agency
        const agencyCityMap: Record<string, string> = {
          'BART': 'San Francisco Bay Area',
          'VTA': 'San Jose',
          'Caltrain': 'San Francisco Peninsula'
        }
        if (agency && agency !== 'All') {
          setCityInfo(agencyCityMap[agency] || agency)
        } else if (fetchedStops.length > 0) {
          const firstStop = fetchedStops[0]
          if (firstStop.agency) {
            setCityInfo(agencyCityMap[firstStop.agency] || firstStop.agency)
          }
        }
      }
    } catch (err) {
      console.error('Error fetching stops:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Dynamically load Leaflet
    const loadLeaflet = async () => {
      if (typeof window !== 'undefined' && !window.L) {
        const L = await import('leaflet')
        window.L = L.default
      }
      setMapLoaded(true)
    }
    loadLeaflet()
  }, [])

  useEffect(() => {
    if (!mapLoaded || typeof window === 'undefined' || !window.L) return

    const L = window.L
    const mapContainer = document.getElementById('transit-map')
    if (!mapContainer) return

    // Remove existing map if it exists
    if ((mapContainer as any)._leaflet_id) {
      const existingMap = (mapContainer as any)._leaflet_map
      if (existingMap) {
        existingMap.remove()
        delete (mapContainer as any)._leaflet_id
        delete (mapContainer as any)._leaflet_map
      }
    }

    // Default center (SF Bay Area) if no stops
    let centerLat = 37.7749
    let centerLon = -122.4194
    let zoom = 10

    if (stops.length > 0) {
      // Calculate center from stops
      centerLat = stops.reduce((sum, s) => sum + s.lat, 0) / stops.length
      centerLon = stops.reduce((sum, s) => sum + s.lon, 0) / stops.length
      zoom = 12
    }

    // Create map
    const map = L.map('transit-map').setView([centerLat, centerLon], zoom)
    ;(mapContainer as any)._leaflet_map = map

    // Add dark tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 20
    }).addTo(map)

    // Add stop markers
    const markers: any[] = []
    if (stops.length > 0) {
      stops.forEach((stop) => {
        try {
          // Color coding based on map layer and metrics
          let color = '#8B949E' // default grey for 0
          if (mapLayer === 'demand') {
            // Color by total departures (grey for 0, green for 1+, dark green for more)
            const departures = stop.departures || 0
            if (departures === 0) color = '#8B949E' // Grey for 0
            else if (departures === 1) color = '#3FB950' // Green for 1
            else if (departures > 1 && departures <= 10) color = '#238636' // Dark green for 2-10
            else if (departures > 10 && departures <= 50) color = '#1a5f28' // Darker green for 11-50
            else color = '#0e3a16' // Darkest green for 50+
          } else {
            // Color by performance (on-time percentage)
            const onTimePct = (stop as any).on_time_pct || 100
            if (onTimePct >= 90) color = '#3FB950' // Excellent - green
            else if (onTimePct >= 75) color = '#D29922' // Good - yellow
            else if (onTimePct >= 60) color = '#F85149' // Poor - red
            else color = '#8B949E' // Very poor - gray
          }
          
          const size = mapLayer === 'demand' 
            ? Math.max(8, Math.min(25, Math.sqrt((stop.departures || 0) / 10))) 
            : 15

          const icon = L.divIcon({
            html: `
              <div style="
                width: ${size}px;
                height: ${size}px;
                background: ${color};
                border: 2px solid white;
                border-radius: 50%;
                box-shadow: 0 0 10px ${color}80;
              "></div>
            `,
            className: 'custom-marker',
            iconSize: [size, size],
          })

          const marker = L.marker([stop.lat, stop.lon], { icon }).addTo(map)
          markers.push(marker)

          const routesServed = (stop as any).routes_served || 0
          const avgDelay = (stop as any).avg_delay || 0
          const onTimePct = (stop as any).on_time_pct || 100
          
          marker.bindPopup(`
            <div style="background: #161B22; color: white; padding: 10px; border-radius: 8px; min-width: 200px;">
              <strong style="color: #3FB950; font-size: 14px;">${stop.name || 'Unknown Stop'}</strong>
              ${stop.agency ? `<div style="margin-top: 4px; font-size: 11px; color: #8B949E;">Agency: ${stop.agency}</div>` : ''}
              <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #30363D;">
                <div style="font-size: 12px; color: #C9D1D9; margin-top: 4px;">
                  <strong>Total Departures:</strong> ${(stop.departures || 0).toLocaleString()}
                </div>
                <div style="font-size: 12px; color: #C9D1D9; margin-top: 4px;">
                  <strong>Routes Served:</strong> ${routesServed}
                </div>
                ${avgDelay > 0 ? `<div style="font-size: 12px; color: #C9D1D9; margin-top: 4px;">
                  <strong>Avg Delay:</strong> ${avgDelay.toFixed(1)} min
                </div>` : ''}
                <div style="font-size: 12px; color: #C9D1D9; margin-top: 4px;">
                  <strong>On-Time %:</strong> ${onTimePct.toFixed(1)}%
                </div>
              </div>
            </div>
          `)

          marker.on('click', () => {
            setSelectedStop(stop)
          })
        } catch (err) {
          console.error('Error adding marker:', err)
        }
      })
    } else {
      // Show message if no stops
      L.popup()
        .setLatLng([centerLat, centerLon])
        .setContent('<div style="color: #8B949E;">No stops available for selected agency</div>')
        .openOn(map)
    }
    
    // Store markers for cleanup
    ;(mapContainer as any)._leaflet_markers = markers

    return () => {
      if (map) {
        map.remove()
      }
    }
  }, [mapLoaded, mapLayer, stops])

  return (
    <div className="space-y-6">
      {/* Agency Indicator */}
      <div className="p-4 rounded-xl bg-dark-surface border border-dark-border">
        <p className="text-sm text-dark-muted">
          Viewing stops for: <span className="text-white font-semibold">{agency === 'All' ? 'All Agencies' : agency}</span>
          {cityInfo && (
            <> • Location: <span className="text-white font-semibold">{cityInfo}</span></>
          )}
        </p>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Geographic View</h1>
          <p className="text-dark-muted">Transit network visualization{loading ? ' (Loading...)' : ` - ${stops.length} stops`}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setMapLayer('demand')}
            className={clsx(
              'px-4 py-2 rounded-lg transition-colors',
              mapLayer === 'demand' ? 'bg-transit-500 text-white' : 'bg-dark-surface border border-dark-border text-dark-muted hover:text-white'
            )}
          >
            Demand Heatmap
          </button>
          <button
            onClick={() => setMapLayer('performance')}
            className={clsx(
              'px-4 py-2 rounded-lg transition-colors',
              mapLayer === 'performance' ? 'bg-transit-500 text-white' : 'bg-dark-surface border border-dark-border text-dark-muted hover:text-white'
            )}
          >
            Performance Map
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Map Container */}
        <div className="lg:col-span-3 rounded-xl bg-dark-surface border border-dark-border overflow-hidden">
          <div id="transit-map" className="h-[600px] w-full" style={{ background: '#0D1117' }}></div>

          {/* Map Legend */}
          <div className="p-4 border-t border-dark-border flex items-center justify-between">
            <div className="flex items-center gap-6">
              <span className="text-sm text-dark-muted">
                {stops.length > 0 ? `${stops.length} stops shown` : 'No stops available'}
              </span>
            </div>
            <div className="flex items-center gap-4 text-sm">
              {mapLayer === 'demand' ? (
                <>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-transit-500"></div>
                    <span className="text-dark-muted">High Demand (1000+)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-severity-info"></div>
                    <span className="text-dark-muted">Medium (500-1000)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-severity-warning"></div>
                    <span className="text-dark-muted">Low (100-500)</span>
                  </div>
                </>
              ) : (
                <>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-transit-500"></div>
                    <span className="text-dark-muted">Excellent (90%+)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-severity-warning"></div>
                    <span className="text-dark-muted">Good (75-90%)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-severity-danger"></div>
                    <span className="text-dark-muted">Poor (&lt;75%)</span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Stop List */}
          <div className="p-4 rounded-xl bg-dark-surface border border-dark-border">
            <h3 className="text-lg font-semibold text-white mb-4">Transit Stops</h3>
            <div className="space-y-2 max-h-[350px] overflow-y-auto">
              {stops.map((stop) => (
                <button
                  key={stop.id}
                  onClick={() => setSelectedStop(stop)}
                  className={clsx(
                    'w-full p-3 rounded-lg text-left transition-colors',
                    selectedStop?.id === stop.id
                      ? 'bg-transit-500/20 border border-transit-500'
                      : 'bg-dark-bg hover:bg-dark-hover border border-transparent'
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-white text-sm">{stop.name}</span>
                    {stop.status === 'alert' && (
                      <span className="w-2 h-2 rounded-full bg-severity-danger animate-pulse"></span>
                    )}
                  </div>
                  {stop.agency && (
                    <div className="text-xs text-dark-muted mt-1">
                      Agency: {stop.agency}
                    </div>
                  )}
                  <div className="text-xs text-dark-muted mt-1 space-y-1">
                    <div>Total Departures: {(stop.departures || 0).toLocaleString()}</div>
                    <div>Routes Served: {(stop as any).routes_served || 0}</div>
                    {(stop as any).avg_delay > 0 && (
                      <div>Avg Delay: {(stop as any).avg_delay.toFixed(1)} min</div>
                    )}
                    <div>On-Time: {((stop as any).on_time_pct || 100).toFixed(1)}%</div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Selected Stop Details */}
          {selectedStop && (
            <div className="p-4 rounded-xl bg-dark-surface border border-dark-border">
              <h3 className="text-lg font-semibold text-white mb-3">{selectedStop.name}</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-dark-muted">Status</span>
                  <span className={selectedStop.status === 'active' ? 'text-transit-500' : 'text-severity-danger'}>
                    {selectedStop.status === 'active' ? '● Active' : '⚠ Alert'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-dark-muted">Total Departures</span>
                  <span className="text-white font-medium">{(selectedStop.departures || 0).toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-dark-muted">Routes Served</span>
                  <span className="text-white font-medium">{(selectedStop as any).routes_served || 0}</span>
                </div>
                {(selectedStop as any).avg_delay > 0 && (
                  <div className="flex justify-between">
                    <span className="text-dark-muted">Avg Delay</span>
                    <span className="text-white font-medium">{(selectedStop as any).avg_delay.toFixed(1)} min</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-dark-muted">On-Time %</span>
                  <span className="text-white font-medium">{((selectedStop as any).on_time_pct || 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-dark-muted">Coordinates</span>
                  <span className="text-white font-mono text-xs">
                    {selectedStop.lat.toFixed(4)}, {selectedStop.lon.toFixed(4)}
                  </span>
                </div>
                {selectedStop.agency && (
                  <div className="pt-2 border-t border-dark-border">
                    <span className="text-dark-muted">Agency:</span>
                    <span className="text-white font-medium ml-2">{selectedStop.agency}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Developer Credit */}
          <div className="p-3 rounded-lg bg-dark-bg border border-dark-border text-center">
            <p className="text-xs text-dark-muted">
              Transit Operations Dashboard | SJSU Applied Data Science
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

// Extend Window interface for Leaflet
declare global {
  interface Window {
    L: any
  }
}
