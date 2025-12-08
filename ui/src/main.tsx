import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { AgencyProvider } from './contexts/AgencyContext'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AgencyProvider>
        <App />
      </AgencyProvider>
    </BrowserRouter>
  </React.StrictMode>,
)

