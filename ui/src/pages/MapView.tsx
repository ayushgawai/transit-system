import { useState, useEffect } from 'react'
import clsx from 'clsx'

// SF Bay Area stops (real coordinates)
const stops = [
  { id: 1, name: 'Civic Center / UN Plaza', lat: 37.7794, lon: -122.4139, departures: 40, routes: ['Blue', 'Red'], status: 'active' },
  { id: 2, name: '16th St Mission', lat: 37.7649, lon: -122.4194, departures: 35, routes: ['Blue'], status: 'active' },
  { id: 3, name: '24th St Mission', lat: 37.7524, lon: -122.4182, departures: 28, routes: ['Blue'], status: 'active' },
  { id: 4, name: 'Powell St', lat: 37.7844, lon: -122.4079, departures: 52, routes: ['Blue', 'Red', 'Yellow'], status: 'alert' },
  { id: 5, name: 'Montgomery St', lat: 37.7894, lon: -122.4013, departures: 48, routes: ['Blue', 'Red', 'Green'], status: 'active' },
  { id: 6, name: 'Embarcadero', lat: 37.7928, lon: -122.3968, departures: 55, routes: ['Blue', 'Red', 'Green', 'Yellow'], status: 'active' },
  { id: 7, name: 'Glen Park', lat: 37.7329, lon: -122.4344, departures: 22, routes: ['Blue'], status: 'active' },
  { id: 8, name: 'Balboa Park', lat: 37.7210, lon: -122.4474, departures: 18, routes: ['Blue', 'Green'], status: 'active' },
  { id: 9, name: 'Daly City', lat: 37.7064, lon: -122.4693, departures: 30, routes: ['Blue', 'Green', 'Yellow'], status: 'active' },
  { id: 10, name: 'Colma', lat: 37.6846, lon: -122.4669, departures: 15, routes: ['Yellow'], status: 'active' },
]

const routeColors: Record<string, string> = {
  Blue: '#58A6FF',
  Red: '#F85149',
  Green: '#3FB950',
  Yellow: '#D29922',
}

export default function MapView() {
  const [selectedStop, setSelectedStop] = useState<typeof stops[0] | null>(null)
  const [mapLayer, setMapLayer] = useState<'demand' | 'performance'>('demand')
  const [mapLoaded, setMapLoaded] = useState(false)

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

    // Check if map already exists
    if ((mapContainer as any)._leaflet_id) {
      return
    }

    // Create map centered on SF
    const map = L.map('transit-map').setView([37.7749, -122.4194], 12)

    // Add dark tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 20
    }).addTo(map)

    // Add stop markers
    stops.forEach((stop) => {
      const color = stop.status === 'alert' ? '#F85149' : '#3FB950'
      const size = mapLayer === 'demand' ? Math.max(10, stop.departures / 3) : 15

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

      marker.bindPopup(`
        <div style="background: #161B22; color: white; padding: 8px; border-radius: 8px; min-width: 150px;">
          <strong style="color: #3FB950;">${stop.name}</strong>
          <div style="margin-top: 4px; font-size: 12px; color: #8B949E;">
            ${stop.departures} departures today
          </div>
          <div style="margin-top: 4px; display: flex; gap: 4px;">
            ${stop.routes.map(r => `<span style="background: ${routeColors[r]}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px;">${r}</span>`).join('')}
          </div>
        </div>
      `)

      marker.on('click', () => {
        setSelectedStop(stop)
      })
    })

    return () => {
      map.remove()
    }
  }, [mapLoaded, mapLayer])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Geographic View</h1>
          <p className="text-dark-muted">Transit network visualization - San Francisco Bay Area</p>
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
              <span className="text-sm text-dark-muted">Routes:</span>
              {Object.entries(routeColors).map(([name, color]) => (
                <div key={name} className="flex items-center gap-2">
                  <div className="w-4 h-1 rounded" style={{ backgroundColor: color }}></div>
                  <span className="text-sm text-white">{name}</span>
                </div>
              ))}
            </div>
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-transit-500"></div>
                <span className="text-dark-muted">Active</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-severity-danger"></div>
                <span className="text-dark-muted">Alert</span>
              </div>
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
                  <div className="flex items-center gap-2 mt-1">
                    {stop.routes.map((route) => (
                      <span
                        key={route}
                        className="px-2 py-0.5 rounded text-xs font-medium text-white"
                        style={{ backgroundColor: routeColors[route] }}
                      >
                        {route}
                      </span>
                    ))}
                  </div>
                  <div className="text-xs text-dark-muted mt-1">
                    {stop.departures} departures today
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
                  <span className="text-dark-muted">Departures</span>
                  <span className="text-white font-medium">{selectedStop.departures}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-dark-muted">Coordinates</span>
                  <span className="text-white font-mono text-xs">
                    {selectedStop.lat.toFixed(4)}, {selectedStop.lon.toFixed(4)}
                  </span>
                </div>
                <div className="pt-2 border-t border-dark-border">
                  <span className="text-dark-muted">Routes:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedStop.routes.map((route) => (
                      <span
                        key={route}
                        className="px-2 py-1 rounded text-xs font-medium text-white"
                        style={{ backgroundColor: routeColors[route] }}
                      >
                        {route} Line
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Developer Credit */}
          <div className="p-3 rounded-lg bg-dark-bg border border-dark-border text-center">
            <p className="text-xs text-dark-muted">
              Map by <span className="text-transit-500">Ayush Gawai</span>
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
