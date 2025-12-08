"""
Transit Ops Dashboard - FastAPI Backend
Connects React frontend to Snowflake data
Developed by Ayush Gawai - SJSU ADS Capstone Project
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
import os
import sys
from pathlib import Path
from contextlib import contextmanager

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Warehouse config
from config.warehouse_config import get_warehouse_config

# LLM Integration
try:
    from llm.chat_handler import ChatHandler
except ImportError:
    ChatHandler = None

# Perplexity API Key - loaded from AWS Secrets Manager
def get_perplexity_api_key() -> str:
    """Get Perplexity API key from AWS Secrets Manager or environment variable"""
    # First try environment variable (for local dev)
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if api_key:
        return api_key
    
    # Try AWS Secrets Manager
    try:
        from config.warehouse_config import get_warehouse_config
        config = get_warehouse_config()
        secrets = config._load_secrets()
        perplexity_secret = secrets.get('perplexity', {})
        if isinstance(perplexity_secret, dict):
            api_key = perplexity_secret.get('api_key') or perplexity_secret.get('PERPLEXITY_API_KEY')
        else:
            api_key = perplexity_secret
        
        if api_key:
            return api_key
    except Exception as e:
        print(f"Warning: Could not load Perplexity API key from Secrets Manager: {e}")
    
    raise ValueError("PERPLEXITY_API_KEY not found in environment or AWS Secrets Manager")

app = FastAPI(
    title="Transit Ops API",
    description="Backend API for Transit Operations Dashboard",
    version="1.0.0"
)
# CORS configuration - single middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dh8gl1kmj1ckc.cloudfront.net",  # CloudFront frontend
        "http://localhost:3000",  # Local development (Vite default)
        "http://localhost:5173",  # Vite dev server (alternative)
        "http://127.0.0.1:3000",  # Localhost IP
        "http://127.0.0.1:5173",  # Localhost IP alternative
        "*"  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "transit-ops-api"}

# Snowflake connection settings - Use environment variables (injected from Secrets Manager by ECS)
# ECS automatically injects secrets as environment variables, so we don't need to call Secrets Manager directly
# Warehouse connection - uses config to select Redshift or Snowflake
from api.warehouse_connection import get_warehouse_connection

# Alias for backward compatibility
get_snowflake_connection = get_warehouse_connection

# ==================== MODELS ====================

class ApiResponse(BaseModel):
    success: bool
    data: Any
    error: Optional[str] = None
    timestamp: str = datetime.now().isoformat()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    data: Optional[Any] = None

# ==================== ENDPOINTS ====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    config = get_warehouse_config()
    warehouse_type = config.get_warehouse_type()
    
    try:
        with get_warehouse_connection() as conn:
            cursor = conn.cursor()
            if config.is_redshift():
                cursor.execute("SELECT CURRENT_TIMESTAMP")
            else:
                cursor.execute("SELECT CURRENT_TIMESTAMP()")
            cursor.close()
        return {"status": "healthy", "version": "1.0.0", "database": f"{warehouse_type} connected"}
    except Exception as e:
        return {"status": "degraded", "version": "1.0.0", "database": str(e), "warehouse": warehouse_type}

@app.get("/api/kpis")
async def get_kpis(agency: Optional[str] = None):
    """Get current KPI metrics"""
    try:
        # Try Snowflake first
        try:
            with get_snowflake_connection() as conn:
                cursor = conn.cursor()
                config = get_warehouse_config()
                snowflake_config = config.get_snowflake_config()
                database = snowflake_config.get('database', 'USER_DB_HORNET')
                agency_filter = f"AND r.AGENCY = '{agency}'" if agency and agency != "All" else ""
                # Use GTFS data directly since RELIABILITY_METRICS may not exist
                reliability_query = f"""
                    SELECT 
                        95.0 as avg_on_time,  -- Default since we don't have delay data in GTFS
                        90.0 as avg_reliability,
                        COUNT(DISTINCT r.ROUTE_ID) as active_routes,
                        COUNT(*) as total_departures,
                        0.0 as avg_delay
                    FROM {database}.ANALYTICS.STG_GTFS_ROUTES r
                    INNER JOIN {database}.ANALYTICS.STG_GTFS_TRIPS t ON r.ROUTE_ID = t.ROUTE_ID
                    INNER JOIN {database}.ANALYTICS.STG_GTFS_STOP_TIMES st ON t.TRIP_ID = st.TRIP_ID
                    WHERE 1=1 {agency_filter}
                """
                cursor.execute(reliability_query)
                row = cursor.fetchone()
                
                kpi_data = {
                    "onTimePerformance": round(row[0] or 94.2, 1),
                    "activeRoutes": row[2] or 0,
                    "totalDepartures": row[3] or 0,
                    "estimatedRevenue": 0,  # No revenue data
                    "activeAlerts": 0,  # No alerts data
                    "avgDelay": round(row[4] or 0, 1) if row[4] else 0
                }
                
                return ApiResponse(success=True, data=kpi_data)
        except Exception as e:
            # No fallback - return error if Snowflake fails
            return ApiResponse(success=False, data={}, error=f"Snowflake query failed: {str(e)}")
    except Exception as e:
        return ApiResponse(success=False, data={}, error=str(e))

@app.get("/api/routes")
async def get_routes(agency: Optional[str] = None):
    """Get all routes with metrics"""
    try:
        # Try Snowflake first
        try:
            with get_snowflake_connection() as conn:
                cursor = conn.cursor()
                config = get_warehouse_config()
                snowflake_config = config.get_snowflake_config()
                database = snowflake_config.get('database', 'USER_DB_HORNET')
                agency_filter = f"AND r.AGENCY = '{agency}'" if agency and agency != "All" else ""
                query = f"""
                    SELECT 
                        r.ROUTE_ID,
                        r.ROUTE_SHORT_NAME,
                        r.ROUTE_LONG_NAME,
                        r.ROUTE_COLOR,
                        r.AGENCY as AGENCY_NAME,
                        95.0 as ON_TIME_PCT,  -- Default since GTFS doesn't have delay data
                        90.0 as RELIABILITY_SCORE,
                        0.0 as UTILIZATION,
                        0.0 as REVENUE
                    FROM {database}.ANALYTICS.STG_GTFS_ROUTES r
                    WHERE 1=1 {agency_filter}
                """
                cursor.execute(query)
                rows = cursor.fetchall()
                
                # Get actual utilization and revenue from stop_times
                formatted_routes = []
                for row in rows:
                    route_id = row[0]
                    route_short = row[1] or ""
                    route_long = row[2] or ""
                    # Use route_long_name for display (contains source <-> destination)
                    route_name = route_long if route_long else route_short if route_short else "Unknown"
                    
                    # Calculate actual utilization from stop_times
                    utilization_query = f"""
                        SELECT COUNT(DISTINCT st.STOP_ID) as stop_count
                        FROM {database}.ANALYTICS.STG_GTFS_STOP_TIMES st
                        INNER JOIN {database}.ANALYTICS.STG_GTFS_TRIPS t ON st.TRIP_ID = t.TRIP_ID
                        WHERE t.ROUTE_ID = %s
                    """
                    cursor.execute(utilization_query, (route_id,))
                    util_row = cursor.fetchone()
                    utilization = (util_row[0] / 10.0) if util_row and util_row[0] else 60.0  # Normalize to percentage
                    
                    # Calculate estimated revenue (departures * avg fare)
                    revenue_query = f"""
                        SELECT COUNT(*) as departure_count
                        FROM {database}.ANALYTICS.STG_GTFS_STOP_TIMES st
                        INNER JOIN {database}.ANALYTICS.STG_GTFS_TRIPS t ON st.TRIP_ID = t.TRIP_ID
                        WHERE t.ROUTE_ID = %s
                    """
                    cursor.execute(revenue_query, (route_id,))
                    rev_row = cursor.fetchone()
                    departure_count = rev_row[0] if rev_row and rev_row[0] else 0
                    # Estimate: 25 passengers per departure * $2.50 avg fare
                    revenue = departure_count * 25 * 2.50
                    
                    formatted_routes.append({
                        "id": route_id,
                        "name": route_name,
                        "short_name": route_short,
                        "long_name": route_long,
                        "color": f"#{row[3] or '3FB950'}",
                        "agency": row[4] or "BART",
                        "type": "Subway",
                        "onTime": round(row[5] or 90, 1),
                        "reliability": round(row[6] or 85, 1),
                        "utilization": round(utilization, 1),
                        "revenue": round(revenue, 2)
                    })
                
                return ApiResponse(success=True, data=formatted_routes)
        except Exception as e:
            # No fallback - return error if Snowflake fails
            return ApiResponse(success=False, data=[], error=f"Snowflake query failed: {str(e)}")
    except Exception as e:
        return ApiResponse(success=False, data=[], error=str(e))

@app.get("/api/analytics/route-health")
async def get_route_health(agency: Optional[str] = None):
    """Get route health overview with actual metrics"""
    try:
        with get_snowflake_connection() as conn:
            cursor = conn.cursor()
            config = get_warehouse_config()
            snowflake_config = config.get_snowflake_config()
            database = snowflake_config.get('database', 'USER_DB_HORNET')
            agency_filter = f"AND r.AGENCY = '{agency}'" if agency and agency != "All" else ""
            
            # Calculate actual metrics: departures, stops, utilization
            query = f"""
                SELECT 
                    r.ROUTE_ID,
                    r.ROUTE_LONG_NAME,
                    r.ROUTE_SHORT_NAME,
                    r.AGENCY,
                    COUNT(st.STOP_ID) as TOTAL_DEPARTURES,
                    COUNT(DISTINCT st.STOP_ID) as UNIQUE_STOPS,
                    COUNT(DISTINCT t.TRIP_ID) as TRIP_COUNT
                FROM {database}.ANALYTICS.STG_GTFS_ROUTES r
                INNER JOIN {database}.ANALYTICS.STG_GTFS_TRIPS t ON r.ROUTE_ID = t.ROUTE_ID
                INNER JOIN {database}.ANALYTICS.STG_GTFS_STOP_TIMES st ON t.TRIP_ID = st.TRIP_ID
                WHERE 1=1 {agency_filter}
                GROUP BY r.ROUTE_ID, r.ROUTE_LONG_NAME, r.ROUTE_SHORT_NAME, r.AGENCY
                ORDER BY TOTAL_DEPARTURES DESC
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            
            if not rows:
                return ApiResponse(success=True, data=[])
            
            # Calculate statistics for normalization
            all_departures = [row[4] for row in rows]
            all_stops = [row[5] for row in rows]
            max_departures = max(all_departures) if all_departures else 1
            max_stops = max(all_stops) if all_stops else 1
            avg_departures = sum(all_departures) / len(all_departures) if all_departures else 1
            avg_stops = sum(all_stops) / len(all_stops) if all_stops else 1
            
            # Check for delay data in streaming table
            delay_query = f"""
                SELECT 
                    ROUTE_SHORT_NAME,
                    ROUTE_LONG_NAME,
                    AGENCY,
                    COUNT(*) as total,
                    COUNT(CASE WHEN DELAY_SECONDS > 0 THEN 1 END) as delayed,
                    AVG(CASE WHEN DELAY_SECONDS > 0 THEN DELAY_SECONDS END) as avg_delay_sec
                FROM {database}.ANALYTICS.LANDING_STREAMING_DEPARTURES
                WHERE DELAY_SECONDS IS NOT NULL {agency_filter.replace('r.AGENCY', 'AGENCY')}
                GROUP BY ROUTE_SHORT_NAME, ROUTE_LONG_NAME, AGENCY
            """
            cursor.execute(delay_query)
            delay_data = {row[0] or row[1]: {'delayed': row[4], 'total': row[3], 'avg_delay': row[5] or 0} 
                         for row in cursor.fetchall()}
            
            health_data = []
            for row in rows:
                route_id = row[0]
                route_long = row[1]
                route_short = row[2]
                route_agency = row[3]
                departures = row[4]
                stops = row[5]
                trips = row[6]
                
                route_name = route_long or route_short or route_id
                
                # Calculate utilization (stops per route normalized)
                utilization = (stops / max_stops * 100) if max_stops > 0 else 0
                
                # Calculate on-time performance from streaming data if available
                on_time = 95.0  # Default
                if route_short in delay_data or route_long in delay_data:
                    delay_info = delay_data.get(route_short) or delay_data.get(route_long)
                    if delay_info and delay_info['total'] > 0:
                        delayed_pct = (delay_info['delayed'] / delay_info['total']) * 100
                        on_time = max(0, 100 - delayed_pct)
                
                # Calculate reliability score based on utilization and departures
                # Routes with more departures and stops are more reliable
                departures_score = min(100, (departures / avg_departures) * 50) if avg_departures > 0 else 50
                stops_score = min(100, (stops / avg_stops) * 50) if avg_stops > 0 else 50
                reliability = (departures_score + stops_score) / 2
                
                health_data.append({
                    "route": route_name,
                    "route_id": route_id,
                    "onTime": round(on_time, 1),
                    "reliability": round(reliability, 1),
                    "utilization": round(utilization, 1),
                    "departures": departures,
                    "stops": stops,
                    "trips": trips,
                    "status": "healthy" if on_time >= 90 and reliability >= 80 else "warning" if on_time >= 75 else "critical"
                })
            
            # Sort by on-time (lowest first) for variation
            health_data.sort(key=lambda x: x["onTime"])
            
            return ApiResponse(success=True, data=health_data)
    except Exception as e:
        return ApiResponse(success=False, data=[], error=f"Snowflake query failed: {str(e)}")

@app.get("/api/analytics/route-comparison")
async def get_route_comparison(agency: Optional[str] = None):
    """Get top 10 and bottom 10 routes by various metrics"""
    try:
        with get_snowflake_connection() as conn:
            cursor = conn.cursor()
            config = get_warehouse_config()
            snowflake_config = config.get_snowflake_config()
            database = snowflake_config.get('database', 'USER_DB_HORNET')
            agency_filter = f"AND r.AGENCY = '{agency}'" if agency and agency != "All" else ""
            
            # Get routes with departures, stops, and utilization
            query = f"""
                SELECT 
                    r.ROUTE_ID,
                    r.ROUTE_LONG_NAME,
                    r.ROUTE_SHORT_NAME,
                    r.AGENCY,
                    COUNT(st.STOP_ID) as TOTAL_DEPARTURES,
                    COUNT(DISTINCT st.STOP_ID) as UNIQUE_STOPS,
                    COUNT(DISTINCT t.TRIP_ID) as TRIP_COUNT
                FROM {database}.ANALYTICS.STG_GTFS_ROUTES r
                INNER JOIN {database}.ANALYTICS.STG_GTFS_TRIPS t ON r.ROUTE_ID = t.ROUTE_ID
                INNER JOIN {database}.ANALYTICS.STG_GTFS_STOP_TIMES st ON t.TRIP_ID = st.TRIP_ID
                WHERE 1=1 {agency_filter}
                GROUP BY r.ROUTE_ID, r.ROUTE_LONG_NAME, r.ROUTE_SHORT_NAME, r.AGENCY
                ORDER BY TOTAL_DEPARTURES DESC
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            
            if not rows:
                return ApiResponse(success=True, data={"top10": [], "bottom10": []})
            
            # Format routes
            routes = []
            for row in rows:
                route_name = row[1] or row[2] or row[0]
                routes.append({
                    "route": route_name,
                    "route_id": row[0],
                    "agency": row[3],
                    "departures": row[4],
                    "stops": row[5],
                    "trips": row[6],
                    "utilization": round((row[5] / max([r[5] for r in rows]) * 100) if rows else 0, 1)
                })
            
            return ApiResponse(success=True, data={
                "top10": routes[:10],
                "bottom10": routes[-10:] if len(routes) >= 10 else routes
            })
    except Exception as e:
        return ApiResponse(success=False, data={}, error=str(e))

@app.get("/api/analytics/delay-analysis")
async def get_delay_analysis(agency: Optional[str] = None):
    """Get routes with most delays for problem identification"""
    try:
        with get_snowflake_connection() as conn:
            cursor = conn.cursor()
            config = get_warehouse_config()
            snowflake_config = config.get_snowflake_config()
            database = snowflake_config.get('database', 'USER_DB_HORNET')
            agency_filter = f"AND AGENCY = '{agency}'" if agency and agency != "All" else ""
            
            query = f"""
                SELECT 
                    ROUTE_SHORT_NAME,
                    ROUTE_LONG_NAME,
                    AGENCY,
                    COUNT(*) as total_departures,
                    COUNT(CASE WHEN DELAY_SECONDS > 0 THEN 1 END) as delayed_count,
                    COUNT(CASE WHEN DELAY_SECONDS <= 0 THEN 1 END) as on_time_count,
                    AVG(CASE WHEN DELAY_SECONDS > 0 THEN DELAY_SECONDS END) as avg_delay_seconds,
                    MAX(DELAY_SECONDS) as max_delay_seconds
                FROM {database}.ANALYTICS.LANDING_STREAMING_DEPARTURES
                WHERE DELAY_SECONDS IS NOT NULL {agency_filter}
                GROUP BY ROUTE_SHORT_NAME, ROUTE_LONG_NAME, AGENCY
                HAVING COUNT(*) > 5
                ORDER BY delayed_count DESC, avg_delay_seconds DESC
                LIMIT 15
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            
            delay_routes = []
            for row in rows:
                route_name = row[1] or row[0] or "Unknown"
                total = row[3]
                delayed = row[4]
                on_time = row[5]
                avg_delay = row[6] or 0
                max_delay = row[7] or 0
                delay_pct = (delayed / total * 100) if total > 0 else 0
                on_time_pct = (on_time / total * 100) if total > 0 else 0
                
                delay_routes.append({
                    "route": route_name,
                    "agency": row[2],
                    "total_departures": total,
                    "delayed_count": delayed,
                    "on_time_count": on_time,
                    "delay_percentage": round(delay_pct, 1),
                    "on_time_percentage": round(on_time_pct, 1),
                    "avg_delay_minutes": round(avg_delay / 60, 1),
                    "max_delay_minutes": round(max_delay / 60, 1)
                })
            
            return ApiResponse(success=True, data=delay_routes)
    except Exception as e:
        # If no streaming data, return empty
        return ApiResponse(success=True, data=[])

@app.get("/api/analytics/utilization-distribution")
async def get_utilization_distribution(agency: Optional[str] = None):
    """Get utilization distribution across routes"""
    try:
        with get_snowflake_connection() as conn:
            cursor = conn.cursor()
            config = get_warehouse_config()
            snowflake_config = config.get_snowflake_config()
            database = snowflake_config.get('database', 'USER_DB_HORNET')
            agency_filter = f"AND r.AGENCY = '{agency}'" if agency and agency != "All" else ""
            
            query = f"""
                SELECT 
                    r.ROUTE_LONG_NAME,
                    r.ROUTE_SHORT_NAME,
                    r.AGENCY,
                    COUNT(DISTINCT st.STOP_ID) as stop_count,
                    COUNT(st.STOP_ID) as departure_count
                FROM {database}.ANALYTICS.STG_GTFS_ROUTES r
                INNER JOIN {database}.ANALYTICS.STG_GTFS_TRIPS t ON r.ROUTE_ID = t.ROUTE_ID
                INNER JOIN {database}.ANALYTICS.STG_GTFS_STOP_TIMES st ON t.TRIP_ID = st.TRIP_ID
                WHERE 1=1 {agency_filter}
                GROUP BY r.ROUTE_LONG_NAME, r.ROUTE_SHORT_NAME, r.AGENCY
                ORDER BY stop_count DESC
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            
            if not rows:
                return ApiResponse(success=True, data=[])
            
            max_stops = max([row[3] for row in rows]) if rows else 1
            
            utilization_data = []
            for row in rows:
                route_name = row[0] or row[1] or "Unknown"
                stops = row[3]
                departures = row[4]
                utilization = (stops / max_stops * 100) if max_stops > 0 else 0
                
                utilization_data.append({
                    "route": route_name,
                    "agency": row[2],
                    "stops": stops,
                    "departures": departures,
                    "utilization": round(utilization, 1)
                })
            
            return ApiResponse(success=True, data=utilization_data)
    except Exception as e:
        return ApiResponse(success=False, data=[], error=str(e))

@app.get("/api/agencies")
async def get_agencies():
    """Get list of available agencies"""
    try:
        config = get_warehouse_config()
        snowflake_config = config.get_snowflake_config()
        database = snowflake_config.get('database', 'USER_DB_HORNET')
        with get_snowflake_connection() as conn:
            cursor = conn.cursor()
            query = f"""
                SELECT DISTINCT AGENCY
                FROM {database}.ANALYTICS.STG_GTFS_ROUTES
                WHERE AGENCY IS NOT NULL
                ORDER BY AGENCY
            """
            cursor.execute(query)
            agencies = [row[0] for row in cursor.fetchall()]
            return ApiResponse(success=True, data=agencies)
    except Exception as e:
        # No fallback - return error if Snowflake fails
        return ApiResponse(success=False, data=[], error=f"Snowflake query failed: {str(e)}")

@app.get("/api/cities")
async def get_cities():
    """Get list of available cities"""
    try:
        config = get_warehouse_config()
        snowflake_config = config.get_snowflake_config()
        database = snowflake_config.get('database', 'USER_DB_HORNET')
        with get_snowflake_connection() as conn:
            cursor = conn.cursor()
            # GTFS stops don't have city, use agency as city identifier
            query = f"""
                SELECT DISTINCT AGENCY
                FROM {database}.ANALYTICS.STG_GTFS_ROUTES
                WHERE AGENCY IS NOT NULL
                ORDER BY AGENCY
            """
            cursor.execute(query)
            cities = [row[0] for row in cursor.fetchall()]
            return ApiResponse(success=True, data=cities)
    except Exception as e:
        # No fallback - return error if Snowflake fails
        return ApiResponse(success=False, data=[], error=f"Snowflake query failed: {str(e)}")

@app.get("/api/stops")
async def get_stops(agency: Optional[str] = None, limit: int = 100):
    """Get all stops"""
    # Try Snowflake first, fallback to local DB
    try:
        with get_snowflake_connection() as conn:
            cursor = conn.cursor()
            config = get_warehouse_config()
            snowflake_config = config.get_snowflake_config()
            database = snowflake_config.get('database', 'USER_DB_HORNET')
            agency_filter = f"AND r.AGENCY = '{agency}'" if agency and agency != "All" else ""
            query = f"""
                SELECT 
                    s.STOP_ID,
                    s.STOP_NAME,
                    s.STOP_LAT,
                    s.STOP_LON,
                    r.AGENCY as AGENCY_NAME,
                    COUNT(DISTINCT st.STOP_ID) as TOTAL_DEPARTURES,
                    COUNT(DISTINCT r.ROUTE_ID) as ROUTES_SERVED,
                    0.0 as AVG_DELAY,  -- GTFS doesn't have delay data
                    COUNT(*) as ON_TIME_COUNT,  -- All are considered on-time in GTFS
                    COUNT(*) as TOTAL_WITH_DELAY
                FROM {database}.ANALYTICS.STG_GTFS_STOPS s
                INNER JOIN {database}.ANALYTICS.STG_GTFS_STOP_TIMES st ON s.STOP_ID = st.STOP_ID
                INNER JOIN {database}.ANALYTICS.STG_GTFS_TRIPS t ON st.TRIP_ID = t.TRIP_ID
                INNER JOIN {database}.ANALYTICS.STG_GTFS_ROUTES r ON t.ROUTE_ID = r.ROUTE_ID
                WHERE 1=1 {agency_filter}
                GROUP BY s.STOP_ID, s.STOP_NAME, s.STOP_LAT, s.STOP_LON, r.AGENCY
                LIMIT {limit}
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            
            formatted_stops = []
            for row in rows:
                total_departures = int(row[5]) if row[5] else 0
                routes_served = int(row[6]) if row[6] else 0
                avg_delay = float(row[7]) if row[7] else 0
                on_time_count = int(row[8]) if row[8] else 0
                total_with_delay = int(row[9]) if row[9] else 0
                on_time_pct = (on_time_count / total_with_delay * 100) if total_with_delay > 0 else 100
                
                formatted_stops.append({
                    "id": row[0],
                    "name": row[1] or "Unknown Stop",
                    "lat": float(row[2]) if row[2] else 37.7749,
                    "lon": float(row[3]) if row[3] else -122.4194,
                    "agency": row[4] if row[4] else None,
                    "departures": total_departures,
                    "routes_served": routes_served,
                    "avg_delay": round(avg_delay, 1),
                    "on_time_pct": round(on_time_pct, 1),
                    "status": "active" if total_departures > 0 else "inactive"
                })
            
            return ApiResponse(success=True, data=formatted_stops)
    except Exception as e:
        # No fallback - return error if Snowflake fails
        return ApiResponse(success=False, data=[], error=f"Snowflake query failed: {str(e)}")

@app.get("/api/live-data")
async def get_live_data(agency: Optional[str] = None):
    """Get today's live/streaming data with freshness indicators"""
    try:
        # Use Snowflake only
        from datetime import datetime, timedelta
        
        with get_snowflake_connection() as conn:
            cursor = conn.cursor()
            
            # Get today's date
            today = datetime.now().date()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            
            config = get_warehouse_config()
            snowflake_config = config.get_snowflake_config()
            database = snowflake_config.get('database', 'USER_DB_HORNET')
            # Query today's streaming departures from Snowflake
            # Get data from last 7 days to show recent streaming data
            week_ago = datetime.now() - timedelta(days=7)
            agency_filter = f"AND d.AGENCY = '{agency}'" if agency and agency != "All" else ""
            query = f"""
                SELECT 
                    d.ID as DEPARTURE_ID,
                    d.GLOBAL_STOP_ID as STOP_ID,
                    d.GLOBAL_ROUTE_ID as ROUTE_ID,
                    d.AGENCY as AGENCY_NAME,
                    d.SCHEDULED_DEPARTURE_TIME,
                    d.DEPARTURE_TIME as ACTUAL_DEPARTURE_TIME,
                    d.DELAY_SECONDS,
                    COALESCE(d.CONSUMED_AT, TO_TIMESTAMP_NTZ(d.TIMESTAMP)) as LOAD_TIMESTAMP,
                    d.STOP_NAME,
                    d.ROUTE_SHORT_NAME,
                    d.ROUTE_LONG_NAME
                FROM {database}.ANALYTICS.LANDING_STREAMING_DEPARTURES d
                WHERE (d.CONSUMED_AT >= %s OR (d.TIMESTAMP IS NOT NULL AND TO_TIMESTAMP_NTZ(d.TIMESTAMP) >= %s))
                {agency_filter}
                ORDER BY COALESCE(d.CONSUMED_AT, TO_TIMESTAMP_NTZ(d.TIMESTAMP)) DESC NULLS LAST
                LIMIT 1000
            """
            cursor.execute(query, (week_ago, week_ago))
            rows = cursor.fetchall()
            
            # Format departures
            departures = []
            for row in rows:
                # Row structure: [DEPARTURE_ID, STOP_ID, ROUTE_ID, AGENCY_NAME, SCHEDULED_DEPARTURE_TIME, 
                #                ACTUAL_DEPARTURE_TIME, DELAY_SECONDS, LOAD_TIMESTAMP, STOP_NAME, 
                #                ROUTE_SHORT_NAME, ROUTE_LONG_NAME]
                route_name = row[9] or row[10] or str(row[2]) if len(row) > 10 else str(row[2])
                stop_name = row[8] if len(row) > 8 and row[8] else str(row[1])
                
                # Parse load timestamp (row[7] is LOAD_TIMESTAMP)
                load_ts = None
                if len(row) > 7 and row[7]:
                    try:
                        if isinstance(row[7], datetime):
                            load_ts = row[7]
                        else:
                            load_ts_str = str(row[7])
                            load_ts = datetime.fromisoformat(load_ts_str.replace('Z', '+00:00'))
                    except:
                        load_ts = datetime.now()
                else:
                    load_ts = datetime.now()
                
                # Calculate data age
                now = datetime.now()
                if load_ts.tzinfo:
                    now = datetime.now(load_ts.tzinfo)
                data_age = max(0, (now - load_ts).total_seconds())
                
                # Convert epoch timestamps to ISO strings
                scheduled_time = None
                predicted_time = None
                if len(row) > 4 and row[4]:
                    if isinstance(row[4], (int, float)):
                        scheduled_time = datetime.fromtimestamp(row[4]).isoformat()
                    else:
                        scheduled_time = str(row[4])
                if len(row) > 5 and row[5]:
                    if isinstance(row[5], (int, float)):
                        predicted_time = datetime.fromtimestamp(row[5]).isoformat()
                    else:
                        predicted_time = str(row[5])
                
                departures.append({
                    "departure_id": str(row[0]) if len(row) > 0 else "",
                    "stop_name": stop_name,
                    "route_name": route_name,
                    "agency": row[3] if len(row) > 3 and row[3] else None,
                    "scheduled_time": scheduled_time,
                    "predicted_time": predicted_time,
                    "delay_seconds": float(row[6]) if len(row) > 6 and row[6] is not None else None,
                    "is_realtime": True,  # All streaming data is real-time
                    "load_timestamp": load_ts.isoformat() if load_ts else None,
                    "data_age_seconds": data_age
                })
            
            # Calculate stats
            streaming_count = len(departures)  # All are from streaming
            realtime_count = len(departures)  # All are real-time
            # Only consider delays that are not None
            delays = [d["delay_seconds"] for d in departures if d["delay_seconds"] is not None]
            avg_delay = sum(delays) / len(delays) if delays else 0
            on_time_count = sum(1 for d in departures if d["delay_seconds"] is not None and -300 <= d["delay_seconds"] <= 300)
            
            latest_update = max([d["load_timestamp"] for d in departures]) if departures else None
            # Get minimum data age (most recent data)
            data_ages = [d["data_age_seconds"] for d in departures if d["data_age_seconds"] >= 0]
            freshness_seconds = min(data_ages) if data_ages else 0
            
            stats = {
                "total_today": len(departures),
                "streaming_count": streaming_count,
                "realtime_count": realtime_count,
                "avg_delay": avg_delay,
                "on_time_count": on_time_count,
                "latest_update": latest_update,
                "freshness_seconds": freshness_seconds
            }
            
            return ApiResponse(success=True, data={
                "departures": departures,
                "stats": stats
            })
    except Exception as e:
        return ApiResponse(success=False, data={}, error=str(e))


@app.get("/api/admin/status")
async def get_admin_status():
    """Get admin panel status - service status, data counts, samples"""
    # Initialize streaming_count at function start to avoid UnboundLocalError
    streaming_count = 0
    streaming_table_count = 0
    
    try:
        # Try Snowflake first
        try:
            with get_snowflake_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT CURRENT_TIMESTAMP()")
                cursor.close()
            snowflake_status = "connected"
            snowflake_error = None
        except Exception as e:
            snowflake_status = "disconnected"
            snowflake_error = str(e)

        # Get data from Snowflake (not local SQLite)
        local_db_status = "not_used"
        local_db_data = {}
        
        if snowflake_status == "connected":
            try:
                config = get_warehouse_config()
                snowflake_config = config.get_snowflake_config()
                database = snowflake_config.get('database', 'USER_DB_HORNET')
                
                with get_snowflake_connection() as conn:
                    cursor = conn.cursor()
                    from datetime import datetime, timedelta
                    
                    # Get counts from Snowflake - use ANALYTICS schema (actual location)
                    cursor.execute(f"SELECT COUNT(*) FROM {database}.ANALYTICS.STG_GTFS_STOPS")
                    stops_count = cursor.fetchone()[0]
                    
                    cursor.execute(f"SELECT COUNT(*) FROM {database}.ANALYTICS.STG_GTFS_ROUTES")
                    routes_count = cursor.fetchone()[0]
                    
                    cursor.execute(f"SELECT COUNT(*) FROM {database}.ANALYTICS.STG_GTFS_STOP_TIMES")
                    departures_count = cursor.fetchone()[0]
                    
                    # Get agencies from Snowflake - check AGENCY column in routes
                    cursor.execute(f"SELECT DISTINCT AGENCY FROM {database}.ANALYTICS.STG_GTFS_ROUTES WHERE AGENCY IS NOT NULL ORDER BY AGENCY")
                    agencies = [row[0] for row in cursor.fetchall()]
                    
                    # Get counts and samples per agency from Snowflake
                    agency_data = {}
                    for agency_name in agencies:
                        # Counts per agency - routes have AGENCY column
                        cursor.execute(f"SELECT COUNT(*) FROM {database}.ANALYTICS.STG_GTFS_ROUTES WHERE AGENCY = %s", (agency_name,))
                        agency_routes_count = cursor.fetchone()[0]
                        
                        # Stops don't have agency directly, but we can count routes
                        agency_stops_count = 0  # Will calculate from routes
                        
                        # Stop times count (departures)
                        cursor.execute(f"""
                            SELECT COUNT(*) 
                            FROM {database}.ANALYTICS.STG_GTFS_STOP_TIMES st
                            INNER JOIN {database}.ANALYTICS.STG_GTFS_TRIPS t ON st.TRIP_ID = t.TRIP_ID
                            INNER JOIN {database}.ANALYTICS.STG_GTFS_ROUTES r ON t.ROUTE_ID = r.ROUTE_ID
                            WHERE r.AGENCY = %s
                        """, (agency_name,))
                        agency_departures_count = cursor.fetchone()[0]
                        
                        # Samples per agency (ordered by first available timestamp DESC)
                        cursor.execute(f"SELECT * FROM {database}.ANALYTICS.STG_GTFS_ROUTES WHERE AGENCY = %s LIMIT 5", (agency_name,))
                        agency_routes_rows = cursor.fetchall()
                        columns = [desc[0] for desc in cursor.description]
                        agency_routes_samples = [dict(zip(columns, row)) for row in agency_routes_rows]
                        
                        # Get stops for this agency (via routes)
                        cursor.execute(f"""
                            SELECT DISTINCT s.*
                            FROM {database}.ANALYTICS.STG_GTFS_STOPS s
                            INNER JOIN {database}.ANALYTICS.STG_GTFS_STOP_TIMES st ON s.STOP_ID = st.STOP_ID
                            INNER JOIN {database}.ANALYTICS.STG_GTFS_TRIPS t ON st.TRIP_ID = t.TRIP_ID
                            INNER JOIN {database}.ANALYTICS.STG_GTFS_ROUTES r ON t.ROUTE_ID = r.ROUTE_ID
                            WHERE r.AGENCY = %s
                            LIMIT 5
                        """, (agency_name,))
                        agency_stops_rows = cursor.fetchall()
                        columns = [desc[0] for desc in cursor.description]
                        agency_stops_samples = [dict(zip(columns, row)) for row in agency_stops_rows]
                        
                        # Get stop times samples
                        cursor.execute(f"""
                            SELECT st.*
                            FROM {database}.ANALYTICS.STG_GTFS_STOP_TIMES st
                            INNER JOIN {database}.ANALYTICS.STG_GTFS_TRIPS t ON st.TRIP_ID = t.TRIP_ID
                            INNER JOIN {database}.ANALYTICS.STG_GTFS_ROUTES r ON t.ROUTE_ID = r.ROUTE_ID
                            WHERE r.AGENCY = %s
                            LIMIT 5
                        """, (agency_name,))
                        agency_departures_rows = cursor.fetchall()
                        columns = [desc[0] for desc in cursor.description]
                        agency_departures_samples = [dict(zip(columns, row)) for row in agency_departures_rows]
                        
                        # Get city for agency (stops don't have city, use agency name)
                        agency_city = agency_name  # Use agency name as city identifier
                        
                        agency_data[agency_name] = {
                            "stops_count": agency_stops_count,
                            "routes_count": agency_routes_count,
                            "departures_count": agency_departures_count,
                            "stops_samples": agency_stops_samples,
                            "routes_samples": agency_routes_samples,
                            "departures_samples": agency_departures_samples,
                            "city": agency_city
                        }
                    
                    # Get overall sample data (limit 10 for each table)
                    cursor.execute(f"SELECT * FROM {database}.ANALYTICS.STG_GTFS_STOPS LIMIT 10")
                    stops_rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    stops_samples = [dict(zip(columns, row)) for row in stops_rows]
                    
                    cursor.execute(f"SELECT * FROM {database}.ANALYTICS.STG_GTFS_ROUTES LIMIT 10")
                    routes_rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    routes_samples = [dict(zip(columns, row)) for row in routes_rows]
                    
                    cursor.execute(f"SELECT * FROM {database}.ANALYTICS.STG_GTFS_STOP_TIMES LIMIT 10")
                    departures_rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    departures_samples = [dict(zip(columns, row)) for row in departures_rows]
                    
                    # Get latest timestamps (if available) - GTFS tables may not have LOAD_TIMESTAMP
                    stops_last_update = None
                    routes_last_update = None
                    departures_last_update = None
                    
                    # Check for streaming data from ANALYTICS.LANDING_STREAMING_DEPARTURES
                    one_hour_ago = (datetime.utcnow() - timedelta(hours=1))
                    streaming_count = 0
                    streaming_table_count = 0
                    try:
                        # Check CONSUMED_AT or TIMESTAMP column
                        cursor.execute(f"""
                            SELECT COUNT(*) 
                            FROM {database}.ANALYTICS.LANDING_STREAMING_DEPARTURES 
                            WHERE CONSUMED_AT >= %s OR TIMESTAMP >= %s
                        """, (one_hour_ago, one_hour_ago.isoformat()))
                        streaming_count = cursor.fetchone()[0]
                        cursor.execute(f"SELECT COUNT(*) FROM {database}.ANALYTICS.LANDING_STREAMING_DEPARTURES")
                        streaming_table_count = cursor.fetchone()[0]
                    except Exception as e:
                        # Try alternative column names
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {database}.ANALYTICS.LANDING_STREAMING_DEPARTURES")
                            streaming_table_count = cursor.fetchone()[0]
                            # If table exists but no recent data, count is 0
                            streaming_count = 0
                        except:
                            streaming_count = 0
                            streaming_table_count = 0
                    
                    local_db_data = {
                        "stops_count": stops_count,
                        "routes_count": routes_count,
                        "departures_count": departures_count,
                        "stops_samples": stops_samples,
                        "routes_samples": routes_samples,
                        "departures_samples": departures_samples,
                        "agencies": agencies,
                        "agency_data": agency_data,
                        "stops_last_update": stops_last_update.isoformat() if stops_last_update else None,
                        "routes_last_update": routes_last_update.isoformat() if routes_last_update else None,
                        "departures_last_update": departures_last_update.isoformat() if departures_last_update else None,
                        "streaming_count": streaming_count,
                        "streaming_table_count": streaming_table_count,
                        "streaming_status": "active" if streaming_count > 0 else "inactive"
                    }
                    local_db_status = "snowflake_data"
            except Exception as e:
                local_db_status = "error"
                local_db_data = {"error": str(e)}
        
        # Check API status
        api_status = "operational"
        
        # Pipeline status - check Airflow DAGs if available
        pipeline_status = {
            "batch_dag": {
                "name": "unified_ingestion_dag",
                "status": "scheduled",
                "schedule": "Every 12 hours",
                "last_run": None,
                "next_run": None,
                "airflow_url_local": "http://localhost:8080/dags/unified_ingestion_dag/grid"
            },
            "incremental_dag": {
                "name": "dbt_landing_to_raw, dbt_raw_to_transform, dbt_transform_to_analytics",
                "status": "scheduled",
                "schedule": "Triggered after ingestion",
                "last_run": None,
                "next_run": None,
                "airflow_url_local": "http://localhost:8080/dags/unified_ingestion_dag/grid"
            },
            "ml_dag": {
                "name": "ml_forecast_dag",
                "status": "scheduled",
                "schedule": "Daily at 3 AM UTC",
                "last_run": None,
                "next_run": None,
                "airflow_url_local": "http://localhost:8080/dags/ml_forecast_dag/grid"
            },
            "streaming": {
                "status": "active" if streaming_count > 0 else "inactive",
                "last_refresh": None
            }
        }
        
        # Try to get streaming last refresh timestamp from Snowflake
        if snowflake_status == "connected":
            try:
                config = get_warehouse_config()
                snowflake_config = config.get_snowflake_config()
                database = snowflake_config.get('database', 'USER_DB_HORNET')
                with get_snowflake_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"""
                        SELECT MAX(COALESCE(CONSUMED_AT, CURRENT_TIMESTAMP())) 
                        FROM {database}.ANALYTICS.LANDING_STREAMING_DEPARTURES 
                        WHERE CONSUMED_AT IS NOT NULL OR TIMESTAMP IS NOT NULL
                    """)
                    last_refresh = cursor.fetchone()[0]
                    if last_refresh:
                        pipeline_status["streaming"]["last_refresh"] = last_refresh.isoformat() if hasattr(last_refresh, 'isoformat') else str(last_refresh)
            except:
                pass
        
        # Try to check Airflow DAG status (if Airflow is running)
        try:
            import requests
            airflow_url = "http://localhost:8080/api/v1/dags"
            response = requests.get(airflow_url, timeout=2, auth=('airflow', 'airflow'))
            if response.status_code == 200:
                dags_data = response.json()
                for dag_info in dags_data.get('dags', []):
                    dag_id = dag_info.get('dag_id')
                    if dag_id == 'unified_ingestion_dag':
                        pipeline_status["batch_dag"]["status"] = "paused" if dag_info.get('is_paused', False) else "active"
                        pipeline_status["batch_dag"]["last_run"] = dag_info.get('last_parsed_time')
                    elif dag_id == 'ml_forecast_dag':
                        pipeline_status["ml_dag"]["status"] = "paused" if dag_info.get('is_paused', False) else "active"
                        pipeline_status["ml_dag"]["last_run"] = dag_info.get('last_parsed_time')
        except:
            # Airflow not running or not accessible
            pipeline_status["batch_dag"]["status"] = "airflow_not_running"
            pipeline_status["incremental_dag"]["status"] = "airflow_not_running"
            pipeline_status["ml_dag"]["status"] = "airflow_not_running"
        
        return ApiResponse(success=True, data={
            "snowflake": {
                "status": snowflake_status,
                "error": snowflake_error
            },
            "local_database": {
                "status": local_db_status,
                **local_db_data
            },
            "api": {
                "status": api_status,
                "endpoint": "http://localhost:8000",
                "docs": "http://localhost:8000/docs"
            },
            "pipelines": pipeline_status,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return ApiResponse(success=False, data={}, error=str(e))


# Global variable to track streaming process
_streaming_process = None

@app.get("/api/admin/streaming-status")
async def get_streaming_status():
    """Get streaming producer status"""
    global _streaming_process
    
    is_running = _streaming_process is not None and _streaming_process.poll() is None
    
    return ApiResponse(success=True, data={
        "is_running": is_running,
        "pid": _streaming_process.pid if is_running else None
    })

@app.post("/api/admin/streaming/start")
async def start_streaming():
    """Start the streaming producer"""
    global _streaming_process
    
    try:
        # Check if already running
        if _streaming_process is not None and _streaming_process.poll() is None:
            return ApiResponse(success=False, data={}, error="Streaming is already running")
        
        from pathlib import Path
        import subprocess
        import sys
        
        # Get project root
        project_root = Path(__file__).parent.parent
        script_path = project_root / "ingestion" / "transit_streaming_producer.py"
        
        if not script_path.exists():
            return ApiResponse(success=False, data={}, error="Streaming script not found")
        
        # Start the streaming producer in background
        _streaming_process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(project_root),
            start_new_session=True  # Detach from parent
        )
        
        return ApiResponse(success=True, data={
            "message": "Streaming producer started",
            "pid": _streaming_process.pid
        })
    except Exception as e:
        return ApiResponse(success=False, data={}, error=str(e))

@app.post("/api/admin/streaming/stop")
async def stop_streaming():
    """Stop the streaming producer"""
    global _streaming_process
    import subprocess
    
    try:
        if _streaming_process is None or _streaming_process.poll() is not None:
            return ApiResponse(success=False, data={}, error="Streaming is not running")
        
        # Terminate the process
        _streaming_process.terminate()
        
        # Wait up to 5 seconds for graceful shutdown
        try:
            _streaming_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't stop
            _streaming_process.kill()
            _streaming_process.wait()
        
        _streaming_process = None
        
        return ApiResponse(success=True, data={
            "message": "Streaming producer stopped"
        })
    except Exception as e:
        return ApiResponse(success=False, data={}, error=str(e))


@app.get("/api/alerts")
async def get_alerts():
    """Get active alerts"""
    try:
        query = """
            SELECT 
                ALERT_ID,
                HEADER_TEXT,
                DESCRIPTION_TEXT,
                CAUSE,
                EFFECT,
                LOAD_TIMESTAMP
            FROM STAGING.STG_ALERTS
            WHERE LOAD_TIMESTAMP >= DATEADD(day, -7, CURRENT_TIMESTAMP())
            ORDER BY LOAD_TIMESTAMP DESC
            LIMIT 20
        """
        alerts = execute_query(query)
        
        formatted_alerts = []
        for a in alerts:
            effect = (a.get("EFFECT") or "").upper()
            alert_type = "danger" if "DELAY" in effect or "SUSPEND" in effect else "warning" if "MODIFIED" in effect else "info"
            
            formatted_alerts.append({
                "id": a.get("ALERT_ID"),
                "type": alert_type,
                "title": a.get("HEADER_TEXT", "Service Alert"),
                "description": a.get("DESCRIPTION_TEXT", ""),
                "timestamp": str(a.get("LOAD_TIMESTAMP"))
            })
        
        return ApiResponse(success=True, data=formatted_alerts)
    except Exception as e:
        return ApiResponse(success=False, data=[], error=str(e))

@app.get("/api/forecasts/demand")
async def get_demand_forecast(hours: int = 6, agency: Optional[str] = None):
    """Get demand forecast for next N hours"""
    try:
        # Try Snowflake first
        try:
            with get_snowflake_connection() as conn:
                cursor = conn.cursor()
                # Snowflake ML forecast query would go here
                # For now, fall through to local fallback
                raise Exception("Snowflake ML not available - using fallback")
        except Exception:
            # Fallback to local database forecast
            from .ml_forecast_fallback import generate_demand_forecast
            forecasts = generate_demand_forecast(agency=agency, hours=hours)
            return ApiResponse(success=True, data=forecasts)
    except Exception as e:
        return ApiResponse(success=False, data=[], error=str(e))

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint powered by Perplexity LLM
    Answers questions about transit data with AI insights
    """
    try:
        # Get Snowflake connection for data queries
        snowflake_conn = None
        try:
            snowflake_conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        except Exception as e:
            print(f"Snowflake connection failed: {e}")
        
        # Initialize chat handler
        chat_handler = ChatHandler(
            api_key=get_perplexity_api_key(),
            snowflake_conn=snowflake_conn
        )
        
        # Process the message
        result = chat_handler.process_message(request.message)
        
        # Close Snowflake connection
        if snowflake_conn:
            snowflake_conn.close()
        
        if result["success"]:
            return ChatResponse(
                response=result["response"],
                data=result.get("data")
            )
        else:
            return ChatResponse(
                response=result["response"],
                data=None
            )
            
    except Exception as e:
        return ChatResponse(
            response=f"I'm having trouble processing your request. Please try again or contact the developer (Ayush Gawai). Error: {str(e)[:100]}",
            data=None
        )


class InsightRequest(BaseModel):
    """Request model for AI insights"""
    context_type: str  # 'route', 'metric', 'chart', 'alert'
    context_id: Optional[str] = None  # e.g., route_id
    context_data: Optional[dict] = None  # Additional data


@app.post("/api/insights")
async def get_ai_insight(request: InsightRequest):
    """
    Get AI-powered insight for a specific context (i button)
    Powers the "i" buttons throughout the dashboard
    """
    try:
        # Build a context-specific question
        if request.context_type == "route":
            route_id = request.context_id or "Unknown"
            data = request.context_data or {}
            otp = data.get("onTimePercent", "N/A")
            util = data.get("utilization", "N/A")
            status = data.get("status", "N/A")
            question = f"Give me a brief 2-3 sentence analysis and recommendation for {route_id} route. Current status: {status}, On-time: {otp}%, Utilization: {util}%. What should operations do?"
            
        elif request.context_type == "metric":
            metric_name = request.context_id or "metric"
            value = request.context_data.get("value", "N/A") if request.context_data else "N/A"
            question = f"Briefly explain what the {metric_name} metric of {value} means for transit operations and if any action is needed."
            
        elif request.context_type == "chart":
            chart_name = request.context_id or "chart"
            question = f"What insights can you provide about the {chart_name}? What patterns should operations watch for?"
            
        elif request.context_type == "alert":
            alert_title = request.context_id or "alert"
            description = request.context_data.get("description", "") if request.context_data else ""
            question = f"This alert was triggered: '{alert_title}' - {description}. What should operations do about it?"
            
        else:
            question = f"Provide a brief insight about: {request.context_type}"
        
        # Get Snowflake connection
        snowflake_conn = None
        try:
            snowflake_conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        except:
            pass
        
        # Get AI insight
        chat_handler = ChatHandler(
            api_key=get_perplexity_api_key(),
            snowflake_conn=snowflake_conn
        )
        
        result = chat_handler.process_message(question)
        
        if snowflake_conn:
            snowflake_conn.close()
        
        return ChatResponse(
            response=result["response"] if result["success"] else "Unable to generate insight at this time.",
            data=None
        )
        
    except Exception as e:
        return ChatResponse(
            response=f"Insight unavailable. Error: {str(e)[:50]}",
            data=None
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

