import { Outlet, NavLink } from 'react-router-dom'
import { useState } from 'react'
import clsx from 'clsx'
import { useAgency } from '../contexts/AgencyContext'

// Cities where TransitApp operates
const cities = [
  { id: 'sf', name: 'San Francisco', country: 'USA', flag: '🇺🇸' },
  { id: 'nyc', name: 'New York City', country: 'USA', flag: '🇺🇸' },
  { id: 'toronto', name: 'Toronto', country: 'Canada', flag: '🇨🇦' },
  { id: 'montreal', name: 'Montreal', country: 'Canada', flag: '🇨🇦' },
  { id: 'london', name: 'London', country: 'UK', flag: '🇬🇧' },
  { id: 'paris', name: 'Paris', country: 'France', flag: '🇫🇷' },
  { id: 'berlin', name: 'Berlin', country: 'Germany', flag: '🇩🇪' },
  { id: 'sydney', name: 'Sydney', country: 'Australia', flag: '🇦🇺' },
]

// Icons (inline SVG for simplicity)
const icons = {
  dashboard: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
    </svg>
  ),
  routes: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
    </svg>
  ),
  analytics: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  map: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  forecast: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  ),
  chat: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  ),
  bi: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  ),
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: icons.dashboard },
  { name: 'Routes', href: '/routes', icon: icons.routes },
  { name: 'Analytics', href: '/analytics', icon: icons.analytics },
  { name: 'Map View', href: '/map', icon: icons.map },
  { name: 'Forecasts', href: '/forecasts', icon: icons.forecast },
  { name: 'Live Data', href: '/live-data', icon: icons.analytics },
  { name: 'Data Query', href: '/query', icon: icons.chat },
  { name: 'BI Dashboard', href: '/bi-dashboard', icon: icons.bi },
  { name: 'Admin', href: '/admin', icon: icons.analytics },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [selectedCity, setSelectedCity] = useState(cities[0])
  const [showCityDropdown, setShowCityDropdown] = useState(false)
  const { agency, setAgency, availableAgencies } = useAgency()
  const [showAgencyDropdown, setShowAgencyDropdown] = useState(false)

  return (
    <div className="min-h-screen bg-dark-bg bg-grid-pattern">
      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 flex flex-col bg-dark-surface border-r border-dark-border transition-all duration-300',
          sidebarOpen ? 'w-64' : 'w-20'
        )}
      >
        {/* Logo Section */}
        <div className="flex items-center gap-3 px-4 py-6 border-b border-dark-border">
          {/* Transit Logo */}
          <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-transit-500 flex items-center justify-center">
            <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          </div>
          {sidebarOpen && (
            <div className="flex flex-col">
              <span className="text-lg font-bold text-white">Transit Ops</span>
              <span className="text-xs text-dark-muted">SJSU ADS Project</span>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group',
                  isActive
                    ? 'bg-transit-500/20 text-transit-500 border-l-2 border-transit-500'
                    : 'text-dark-muted hover:text-white hover:bg-dark-hover'
                )
              }
            >
              <span className="flex-shrink-0">{item.icon}</span>
              {sidebarOpen && <span className="font-medium">{item.name}</span>}
            </NavLink>
          ))}
        </nav>

        {/* SJSU Logo & Developer Info at bottom */}
        <div className="px-4 py-4 border-t border-dark-border">
          {sidebarOpen ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-dark-muted">
                <div className="w-8 h-8 bg-white rounded flex items-center justify-center">
                  <span className="text-xs font-bold text-black">SJSU</span>
                </div>
                <div className="text-xs">
                  <div className="font-semibold text-white">Applied Data Science</div>
                  <div>San José State University</div>
                </div>
              </div>
              <div className="text-xs text-dark-muted border-t border-dark-border/50 pt-2">
                <div className="text-[10px] mt-1">MSDA Capstone Project © 2025</div>
              </div>
            </div>
          ) : (
            <div className="w-8 h-8 mx-auto bg-white rounded flex items-center justify-center">
              <span className="text-xs font-bold text-black">SJSU</span>
            </div>
          )}
        </div>

        {/* Toggle Button */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="absolute -right-3 top-20 w-6 h-6 bg-dark-surface border border-dark-border rounded-full flex items-center justify-center text-dark-muted hover:text-white hover:bg-transit-500 transition-colors"
        >
          <svg className={clsx('w-4 h-4 transition-transform', !sidebarOpen && 'rotate-180')} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      </aside>

      {/* Main Content */}
      <main className={clsx('transition-all duration-300', sidebarOpen ? 'ml-64' : 'ml-20')}>
        {/* Header */}
        <header className="sticky top-0 z-40 glass border-b border-dark-border">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-semibold text-white">Transit Operations Dashboard</h1>
              
              {/* Agency Selector */}
              <div className="relative">
                <button
                  onClick={() => setShowAgencyDropdown(!showAgencyDropdown)}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-dark-surface border border-dark-border hover:border-transit-500 transition-colors"
                >
                  <span className="text-white text-sm font-medium">{agency === 'All' ? 'All Agencies' : agency}</span>
                  <svg className={clsx('w-4 h-4 text-dark-muted transition-transform', showAgencyDropdown && 'rotate-180')} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                
                {showAgencyDropdown && (
                  <div className="absolute top-full left-0 mt-2 w-48 py-2 bg-dark-surface border border-dark-border rounded-xl shadow-xl z-50">
                    <div className="px-3 py-1 text-xs text-dark-muted border-b border-dark-border mb-1">Select Transit Agency</div>
                    {availableAgencies.map((ag) => {
                      // Color code agencies
                      const agencyColor = ag === 'BART' ? '#FFD700' : ag === 'VTA' ? '#00A0E3' : '#3FB950'
                      return (
                        <button
                          key={ag}
                          onClick={() => {
                            setAgency(ag)
                            setShowAgencyDropdown(false)
                          }}
                          className={clsx(
                            'w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-dark-hover transition-colors',
                            agency === ag && 'bg-transit-500/10'
                          )}
                        >
                          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: agencyColor }}></div>
                          <div className="text-sm text-white">{ag === 'All' ? 'All Agencies' : ag}</div>
                          {agency === ag && (
                            <span className="ml-auto text-transit-500">✓</span>
                          )}
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>
              
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-transit-500/20 text-transit-500 text-sm">
                <span className="w-2 h-2 rounded-full bg-transit-500 live-pulse"></span>
                Live
              </div>
            </div>
            <div className="flex items-center gap-4">
              {/* Powered by Transit Logo */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-dark-muted">Powered by</span>
                <img 
                  src="/transit-logo.png" 
                  alt="Transit" 
                  className="h-8 object-contain opacity-90 hover:opacity-100 transition-opacity"
                  onError={(e) => {
                    // Fallback if image doesn't load
                    const target = e.currentTarget
                    target.style.display = 'none'
                    const fallback = document.createElement('span')
                    fallback.className = 'text-sm font-semibold text-transit-500'
                    fallback.textContent = 'TRANSIT'
                    target.parentElement?.appendChild(fallback)
                  }}
                />
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

