# BI Dashboard Specifications

## Dashboard Overview

The Transit Service Reliability & Demand Planning System includes multiple dashboard views for different user personas:

1. **Service Reliability Monitor** - For operations managers
2. **Demand & Crowding Heatmap** - For capacity planners
3. **Revenue Overlay Panel** - For finance/executive teams
4. **Forecasting Panel** - For planning teams
5. **Decision Support Table** - For decision-makers

## Technology Options

### Option 1: Snowsight (Recommended - Free, Built-in)
- **Pros**: Free, built into Snowflake, no additional setup
- **Cons**: Limited customization compared to dedicated BI tools
- **Setup**: Log into Snowflake → Navigate to Snowsight → Create worksheets → Build charts

### Option 2: Amazon QuickSight
- **Pros**: Native AWS integration, good visualization capabilities
- **Cons**: Free tier limited (1 user, 10GB SPICE)
- **Setup**: 
  1. Create QuickSight account
  2. Add Snowflake as data source
  3. Import datasets
  4. Create dashboards

### Option 3: Metabase (Self-hosted)
- **Pros**: Open-source, unlimited users, great for internal teams
- **Cons**: Requires self-hosting infrastructure
- **Setup**: 
  1. Deploy Metabase (Docker or cloud instance)
  2. Add Snowflake data source
  3. Create dashboards using SQL queries

## Dashboard Specifications

### 1. Service Reliability Monitor

**Purpose**: Monitor on-time performance, delays, and service consistency

**Key Metrics**:
- On-time performance % by route
- Average delay in minutes
- Headway consistency (CV)
- Reliability score (composite metric)

**Visualizations**:
- Bar chart: On-time performance by route (last 7 days)
- Line chart: Delay distribution by hour of day
- Heatmap: Reliability score by route and hour
- Table: Top routes by reliability issues

**Queries**: See `snowsight_queries/reliability_dashboard.sql`

**Filters**:
- Date range (default: last 7 days)
- Route selection
- Time of day (hour range)

---

### 2. Demand & Crowding Heatmap

**Purpose**: Identify busy stops/routes/times and capacity constraints

**Key Metrics**:
- Boardings by stop/route/hour
- Demand intensity score
- Occupancy ratio
- Crowding percentage

**Visualizations**:
- Heatmap: Boardings by stop and hour (color-coded by intensity)
- Bar chart: Top routes by total demand
- Line chart: Peak vs off-peak demand comparison
- Scatter plot: Demand vs crowding correlation

**Queries**: See `snowsight_queries/demand_crowding_dashboard.sql`

**Filters**:
- Date range (default: last 7 days)
- Route selection
- Stop selection
- Time period (morning peak, evening peak, midday, off-peak)

---

### 3. Revenue Overlay Panel

**Purpose**: Link service reliability and ridership to financial impact

**Key Metrics**:
- Estimated revenue by route
- Revenue loss due to delays
- Revenue opportunity from improving reliability
- Cost per passenger

**Visualizations**:
- Bar chart: Revenue by route (last 7 days)
- Stacked bar: Revenue breakdown (base vs loss vs opportunity)
- Correlation chart: On-time performance vs revenue
- Table: Top revenue loss routes

**Queries**: See `snowsight_queries/revenue_dashboard.sql`

**Filters**:
- Date range (default: last 7 days)
- Route selection
- Revenue threshold

---

### 4. Forecasting Panel

**Purpose**: View ML predictions for demand, delays, and crowding

**Key Metrics**:
- Predicted boardings (next 24h)
- Predicted delays (next 48h)
- Predicted crowding (next 24h)
- Forecast confidence intervals

**Visualizations**:
- Line chart: Forecast vs historical average (by route)
- Bar chart: Predicted demand by hour (next 24h)
- Heatmap: Predicted delays by route and hour
- Gauge: Predicted crowding status (current + next few hours)

**Queries**: See `snowsight_queries/forecasting_dashboard.sql`

**Filters**:
- Forecast horizon (12h, 24h, 48h)
- Route selection
- Forecast type (demand, delay, crowding)

---

### 5. Decision Support Table

**Purpose**: Ranked actionable recommendations for operations

**Key Metrics**:
- Recommendation type (fleet reallocation, frequency increase, etc.)
- Priority score (0-100)
- Revenue impact
- Implementation complexity (future)

**Visualizations**:
- Table: Ranked recommendations with priority scores
- Pie chart: Distribution of recommendation types
- Bar chart: Revenue impact by recommendation type
- Card widgets: Summary metrics (total recommendations, high-priority count)

**Queries**: See `snowsight_queries/decision_support_dashboard.sql`

**Filters**:
- Priority threshold (show only high-priority)
- Recommendation type
- Route selection

---

## Dashboard Setup Instructions

### Snowsight Setup

1. **Connect to Snowflake**: Log into Snowflake account
2. **Navigate to Snowsight**: Click on "Snowsight" in left sidebar
3. **Create Worksheets**: 
   - Create new worksheet for each dashboard
   - Copy SQL queries from `snowsight_queries/` folder
   - Run queries to verify results
4. **Build Visualizations**:
   - Click "Chart" button in results
   - Select chart type (bar, line, heatmap, etc.)
   - Configure axes, colors, filters
5. **Create Dashboard**:
   - Click "Dashboards" → "New Dashboard"
   - Add worksheets/charts as tiles
   - Arrange and resize tiles
   - Add filters that apply to all tiles

### QuickSight Setup

1. **Create Account**: Sign up for QuickSight (free tier available)
2. **Add Data Source**:
   - Click "New analysis" → "New dataset"
   - Select "Snowflake" as data source
   - Enter Snowflake connection details
   - Select database: `TRANSIT_DB`
3. **Import Datasets**:
   - Import tables from `MARTS` schema
   - Import tables from `ML` schema
4. **Create Visualizations**:
   - Use QuickSight visual builder
   - Reference dashboard specifications above
5. **Create Dashboard**:
   - Combine visualizations into dashboard
   - Add filters and parameters
   - Publish dashboard

### Metabase Setup

1. **Deploy Metabase**:
   ```bash
   docker run -d -p 3000:3000 \
     -e MB_DB_TYPE=postgres \
     -e MB_DB_DBNAME=metabase \
     metabase/metabase
   ```
2. **Configure**:
   - Access Metabase at http://localhost:3000
   - Complete initial setup
3. **Add Data Source**:
   - Click "Add database" → "Snowflake"
   - Enter Snowflake connection details
4. **Create Dashboards**:
   - Create new dashboard for each view
   - Add SQL questions using queries from `snowsight_queries/`
   - Build visualizations
   - Add filters and parameters

---

## Refresh Intervals & Live Data Streaming

### Data Ingestion
- **TransitApp API**: Polled every 5 minutes via Lambda (respects API rate limits)
- **GTFS Static Feeds**: Synced daily
- **Snowpipe**: Auto-loads new S3 files into Snowflake (near real-time, ~1-2 min latency)

### Dashboard Refresh Strategy
For **live/streaming dashboards**, we use a simple auto-refresh approach:

1. **Auto-Refresh Dashboards** (Recommended - Simplest):
   - Dashboards query Snowflake directly
   - Auto-refresh every 30-60 seconds (configurable in BI tool)
   - No additional infrastructure needed
   - Works with Snowsight, QuickSight, Metabase
   - **Why this works**: Data arrives every 5 minutes, dashboards refresh faster to show latest data

2. **Refresh Intervals by Dashboard Type**:
   - **Real-time metrics** (departures, delays): Auto-refresh every 30 seconds
   - **Historical aggregations**: Auto-refresh every 2-5 minutes (after dbt transformations)
   - **Forecasts**: Refresh daily at 3 AM UTC (after ML model refresh)
   - **Decision support**: Refresh daily at 3 AM UTC (after metrics refresh)

### Why Not Kafka/Flink?
- **Overkill**: We only poll 5 times/minute (API rate limit)
- **Cost**: Kafka/Flink require dedicated infrastructure (not free-tier friendly)
- **Complexity**: Adds unnecessary operational overhead
- **AWS-native is sufficient**: Lambda + S3 + Snowpipe provides near real-time data flow

### Optional: WebSocket Push (Future Enhancement)
If true push updates are needed later, we can add:
- API Gateway WebSocket endpoint
- Lambda function that pushes updates when new data arrives
- Dashboard connects via WebSocket for instant updates
- Still AWS-native, no Kafka/Flink needed

---

## Dashboard Access Control

- **Operations Team**: Full access to all dashboards
- **Planning Team**: Access to demand, crowding, forecasting dashboards
- **Finance Team**: Access to revenue overlay panel
- **Executive Team**: Read-only access to all dashboards, focused on decision support table

Configure access in Snowflake (for Snowsight) or BI tool admin panel (for QuickSight/Metabase).

