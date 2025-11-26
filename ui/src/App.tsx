import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Routes_ from './pages/Routes'
import Analytics from './pages/Analytics'
import MapView from './pages/MapView'
import Forecasts from './pages/Forecasts'
import DataQuery from './pages/DataQuery'
import BIDashboard from './pages/BIDashboard'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="routes" element={<Routes_ />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="map" element={<MapView />} />
        <Route path="forecasts" element={<Forecasts />} />
        <Route path="query" element={<DataQuery />} />
        <Route path="bi-dashboard" element={<BIDashboard />} />
      </Route>
    </Routes>
  )
}

export default App

