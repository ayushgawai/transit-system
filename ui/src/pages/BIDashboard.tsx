import { useState } from 'react'
import clsx from 'clsx'

const dashboards = [
  {
    id: 'tableau-ops',
    name: 'Operations Dashboard',
    platform: 'Tableau',
    description: 'Real-time operations monitoring with live KPIs',
    embedUrl: '', // Will be set when Tableau is configured
    lastUpdated: '2 min ago',
    status: 'pending',
  },
  {
    id: 'powerbi-exec',
    name: 'Executive Summary',
    platform: 'Power BI',
    description: 'High-level metrics for leadership review',
    embedUrl: '',
    lastUpdated: '1 hour ago',
    status: 'pending',
  },
  {
    id: 'tableau-routes',
    name: 'Route Performance',
    platform: 'Tableau',
    description: 'Detailed route-by-route analysis',
    embedUrl: '',
    lastUpdated: '5 min ago',
    status: 'pending',
  },
  {
    id: 'snowsight',
    name: 'Snowsight Analytics',
    platform: 'Snowflake',
    description: 'Direct Snowflake dashboard',
    embedUrl: '',
    lastUpdated: '1 min ago',
    status: 'pending',
  },
]

export default function BIDashboard() {
  const [selectedDashboard, setSelectedDashboard] = useState(dashboards[0])
  const [embedUrl, setEmbedUrl] = useState('')
  const [showConfig, setShowConfig] = useState(false)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">BI Dashboards</h1>
          <p className="text-dark-muted">Embedded Tableau, Power BI, and Snowsight dashboards</p>
        </div>
        <button
          onClick={() => setShowConfig(!showConfig)}
          className="px-4 py-2 rounded-lg bg-dark-surface border border-dark-border text-dark-muted hover:text-white transition-colors"
        >
          ⚙️ Configure Embed URLs
        </button>
      </div>

      {/* Configuration Panel */}
      {showConfig && (
        <div className="p-6 rounded-xl bg-dark-surface border border-dark-border">
          <h3 className="text-lg font-semibold text-white mb-4">Dashboard Configuration</h3>
          <p className="text-sm text-dark-muted mb-4">
            Enter the embed URLs for your BI dashboards. These URLs can be found in your Tableau Server/Cloud or Power BI service.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {dashboards.map((dashboard) => (
              <div key={dashboard.id} className="space-y-2">
                <label className="text-sm text-white font-medium">{dashboard.name}</label>
                <input
                  type="url"
                  placeholder={`https://${dashboard.platform.toLowerCase()}.example.com/embed/...`}
                  className="w-full px-3 py-2 rounded-lg bg-dark-bg border border-dark-border text-white placeholder-dark-muted text-sm focus:outline-none focus:border-transit-500"
                />
              </div>
            ))}
          </div>
          <button className="mt-4 px-4 py-2 rounded-lg bg-transit-500 text-white font-medium">
            Save Configuration
          </button>
        </div>
      )}

      {/* Dashboard Selector */}
      <div className="flex gap-3 overflow-x-auto pb-2">
        {dashboards.map((dashboard) => (
          <button
            key={dashboard.id}
            onClick={() => setSelectedDashboard(dashboard)}
            className={clsx(
              'flex-shrink-0 p-4 rounded-xl border-2 transition-all min-w-[200px]',
              selectedDashboard.id === dashboard.id
                ? 'bg-dark-surface border-transit-500'
                : 'bg-dark-surface/50 border-dark-border hover:border-dark-muted'
            )}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">
                {dashboard.platform === 'Tableau' ? '📊' : dashboard.platform === 'Power BI' ? '📈' : '❄️'}
              </span>
              <span className="font-medium text-white">{dashboard.name}</span>
            </div>
            <div className="text-xs text-dark-muted">{dashboard.platform}</div>
            <div className="flex items-center gap-2 mt-2 text-xs">
              {dashboard.status === 'pending' ? (
                <span className="px-2 py-0.5 rounded-full bg-severity-warning/20 text-severity-warning">
                  Not Configured
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded-full bg-transit-500/20 text-transit-500">
                  Active
                </span>
              )}
            </div>
          </button>
        ))}
      </div>

      {/* Dashboard Embed Area */}
      <div className="rounded-xl bg-dark-surface border border-dark-border overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-dark-border flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">{selectedDashboard.name}</h2>
            <p className="text-sm text-dark-muted">{selectedDashboard.description}</p>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-dark-muted">Last updated: {selectedDashboard.lastUpdated}</span>
            <button className="p-2 rounded-lg hover:bg-dark-hover transition-colors" title="Refresh">
              <svg className="w-5 h-5 text-dark-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            <button className="p-2 rounded-lg hover:bg-dark-hover transition-colors" title="Full Screen">
              <svg className="w-5 h-5 text-dark-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
            </button>
          </div>
        </div>

        {/* Embed Container */}
        <div className="h-[600px] flex items-center justify-center bg-dark-bg">
          {selectedDashboard.embedUrl ? (
            <iframe
              src={selectedDashboard.embedUrl}
              className="w-full h-full border-0"
              title={selectedDashboard.name}
              allowFullScreen
            />
          ) : (
            <div className="text-center p-8">
              <div className="text-6xl mb-6">
                {selectedDashboard.platform === 'Tableau' ? '📊' : selectedDashboard.platform === 'Power BI' ? '📈' : '❄️'}
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">{selectedDashboard.platform} Dashboard</h3>
              <p className="text-dark-muted mb-6 max-w-md">
                Configure the embed URL to display your {selectedDashboard.platform} dashboard here.
              </p>
              
              <div className="bg-dark-surface rounded-xl p-6 max-w-lg mx-auto text-left">
                <h4 className="font-medium text-white mb-3">Quick Setup Guide:</h4>
                {selectedDashboard.platform === 'Tableau' && (
                  <ol className="text-sm text-dark-muted space-y-2 list-decimal list-inside">
                    <li>Publish your workbook to Tableau Server/Cloud</li>
                    <li>Go to Share → Copy Embed Code</li>
                    <li>Extract the URL from the iframe src attribute</li>
                    <li>Paste it in the configuration above</li>
                  </ol>
                )}
                {selectedDashboard.platform === 'Power BI' && (
                  <ol className="text-sm text-dark-muted space-y-2 list-decimal list-inside">
                    <li>Publish your report to Power BI Service</li>
                    <li>Go to File → Embed Report → Website or Portal</li>
                    <li>Copy the embed URL</li>
                    <li>Paste it in the configuration above</li>
                  </ol>
                )}
                {selectedDashboard.platform === 'Snowflake' && (
                  <ol className="text-sm text-dark-muted space-y-2 list-decimal list-inside">
                    <li>Create a dashboard in Snowsight</li>
                    <li>Click Share → Get Link</li>
                    <li>Enable "Anyone with the link can view"</li>
                    <li>Paste the link in the configuration above</li>
                  </ol>
                )}
              </div>

              <div className="mt-6 p-4 rounded-lg bg-severity-info/10 border border-severity-info/30 max-w-lg mx-auto">
                <p className="text-sm text-severity-info">
                  💡 <strong>Tip:</strong> You can also link directly to external dashboards using the button below.
                </p>
                <button className="mt-3 px-4 py-2 rounded-lg bg-severity-info text-white font-medium">
                  Open in New Tab →
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Direct Links */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <a
          href="https://tableau.com"
          target="_blank"
          rel="noopener noreferrer"
          className="p-4 rounded-xl bg-dark-surface border border-dark-border hover:border-transit-500 transition-colors group"
        >
          <div className="flex items-center gap-3">
            <span className="text-2xl">📊</span>
            <div>
              <div className="font-medium text-white group-hover:text-transit-500 transition-colors">
                Tableau Server
              </div>
              <div className="text-sm text-dark-muted">Open in new tab</div>
            </div>
            <svg className="w-5 h-5 text-dark-muted ml-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </div>
        </a>
        
        <a
          href="https://app.powerbi.com"
          target="_blank"
          rel="noopener noreferrer"
          className="p-4 rounded-xl bg-dark-surface border border-dark-border hover:border-transit-500 transition-colors group"
        >
          <div className="flex items-center gap-3">
            <span className="text-2xl">📈</span>
            <div>
              <div className="font-medium text-white group-hover:text-transit-500 transition-colors">
                Power BI Service
              </div>
              <div className="text-sm text-dark-muted">Open in new tab</div>
            </div>
            <svg className="w-5 h-5 text-dark-muted ml-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </div>
        </a>
        
        <a
          href="https://app.snowflake.com"
          target="_blank"
          rel="noopener noreferrer"
          className="p-4 rounded-xl bg-dark-surface border border-dark-border hover:border-transit-500 transition-colors group"
        >
          <div className="flex items-center gap-3">
            <span className="text-2xl">❄️</span>
            <div>
              <div className="font-medium text-white group-hover:text-transit-500 transition-colors">
                Snowsight
              </div>
              <div className="text-sm text-dark-muted">Open in new tab</div>
            </div>
            <svg className="w-5 h-5 text-dark-muted ml-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </div>
        </a>
      </div>
    </div>
  )
}

