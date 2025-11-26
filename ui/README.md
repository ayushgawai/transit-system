# Transit Ops Dashboard - React UI

A modern, dark-themed React dashboard for transit operations monitoring.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## 📁 Project Structure

```
ui/
├── public/
│   └── transit-icon.svg       # App favicon
├── src/
│   ├── components/
│   │   └── Layout.tsx         # Main layout with sidebar
│   ├── pages/
│   │   ├── Dashboard.tsx      # Main dashboard
│   │   ├── Routes.tsx         # Route explorer
│   │   ├── Analytics.tsx      # Deep analytics
│   │   ├── MapView.tsx        # Geographic view
│   │   ├── Forecasts.tsx      # ML predictions
│   │   ├── DataQuery.tsx      # Chatbot interface
│   │   └── BIDashboard.tsx    # BI embed page
│   ├── services/
│   │   └── api.ts             # API client
│   ├── types/
│   │   └── index.ts           # TypeScript types
│   ├── App.tsx                # Routes setup
│   ├── main.tsx               # Entry point
│   └── index.css              # Global styles
├── Dockerfile                 # Production build
├── nginx.conf                 # Nginx config for Docker
└── package.json
```

## 🎨 Design System

### Colors
- **Primary (Transit Green):** `#3FB950`
- **Background:** `#0D1117` (deep black)
- **Surface:** `#161B22` (dark gray)
- **Border:** `#30363D`

### Severity Colors
- 🟢 Success: `#3FB950`
- 🟡 Warning: `#D29922`
- 🔴 Danger: `#F85149`
- 🔵 Info: `#58A6FF`

## 🔌 API Integration

The frontend expects a backend API at `/api`. In development, this is proxied to `http://localhost:8000`.

### Endpoints Used
- `GET /api/kpis` - KPI metrics
- `GET /api/routes` - Route data
- `GET /api/stops` - Stop locations
- `GET /api/alerts` - Service alerts
- `GET /api/analytics/route-health` - Route health
- `GET /api/forecasts/demand` - Demand predictions
- `POST /api/chat` - Chatbot queries

## 🐳 Docker

```bash
# Build
docker build -t transit-ui .

# Run
docker run -p 3000:80 transit-ui
```

## 📊 Features

1. **Dashboard** - KPIs, charts, alerts
2. **Routes** - Per-route performance
3. **Analytics** - Trends and heatmaps
4. **Map View** - Geographic visualization
5. **Forecasts** - ML predictions
6. **Data Query** - Natural language chatbot
7. **BI Dashboard** - Tableau/PowerBI embeds

## 🔧 Environment Variables

```env
VITE_API_URL=http://localhost:8000/api
```

## 📦 Dependencies

- React 18
- React Router
- Recharts (charts)
- React-Leaflet (maps)
- Tailwind CSS
- Axios

## 🎓 SJSU ADS Capstone Project

Built as part of the Applied Data Science program at San José State University.

