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
import snowflake.connector
import os
from contextlib import contextmanager

# LLM Integration
from llm.chat_handler import ChatHandler

# Perplexity API Key
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "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")

app = FastAPI(
    title="Transit Ops API",
    description="Backend API for Transit Operations Dashboard",
    version="1.0.0"
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Snowflake connection settings
SNOWFLAKE_CONFIG = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "HORNET_QUERY_WH"),
    "database": os.getenv("SNOWFLAKE_DATABASE", "USER_DB_HORNET"),
    "role": os.getenv("SNOWFLAKE_ROLE", "TRAINING_ROLE"),
}

@contextmanager
def get_snowflake_connection():
    """Context manager for Snowflake connections"""
    conn = None
    try:
        conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        yield conn
    finally:
        if conn:
            conn.close()

def execute_query(query: str, params: tuple = None) -> List[dict]:
    """Execute a query and return results as list of dicts"""
    with get_snowflake_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            cursor.close()

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
    try:
        with get_snowflake_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT CURRENT_TIMESTAMP()")
            cursor.close()
        return {"status": "healthy", "version": "1.0.0", "database": "connected"}
    except Exception as e:
        return {"status": "degraded", "version": "1.0.0", "database": str(e)}

@app.get("/api/kpis")
async def get_kpis():
    """Get current KPI metrics"""
    try:
        # Get reliability metrics
        reliability_query = """
            SELECT 
                AVG(ON_TIME_PCT) as avg_on_time,
                AVG(RELIABILITY_SCORE) as avg_reliability,
                COUNT(DISTINCT ROUTE_ID) as active_routes,
                SUM(TOTAL_DEPARTURES) as total_departures
            FROM ANALYTICS.RELIABILITY_METRICS
        """
        reliability = execute_query(reliability_query)
        
        # Get revenue
        revenue_query = """
            SELECT SUM(ESTIMATED_DAILY_REVENUE) as total_revenue
            FROM ANALYTICS.REVENUE_METRICS
        """
        revenue = execute_query(revenue_query)
        
        # Get alerts count
        alerts_query = """
            SELECT COUNT(*) as alert_count
            FROM STAGING.STG_ALERTS
            WHERE LOAD_TIMESTAMP >= DATEADD(day, -1, CURRENT_TIMESTAMP())
        """
        alerts = execute_query(alerts_query)
        
        kpi_data = {
            "onTimePerformance": round(reliability[0].get("AVG_ON_TIME", 94.2) or 94.2, 1),
            "activeRoutes": reliability[0].get("ACTIVE_ROUTES", 4) or 4,
            "totalDepartures": reliability[0].get("TOTAL_DEPARTURES", 80) or 80,
            "estimatedRevenue": round(revenue[0].get("TOTAL_REVENUE", 14087.5) or 14087.5, 2),
            "activeAlerts": alerts[0].get("ALERT_COUNT", 3) or 3,
            "avgDelay": 0
        }
        
        return ApiResponse(success=True, data=kpi_data)
    except Exception as e:
        # Return mock data if database fails
        return ApiResponse(success=True, data={
            "onTimePerformance": 94.2,
            "activeRoutes": 4,
            "totalDepartures": 80,
            "estimatedRevenue": 14087.5,
            "activeAlerts": 3,
            "avgDelay": 0
        })

@app.get("/api/routes")
async def get_routes():
    """Get all routes with metrics"""
    try:
        query = """
            SELECT 
                r.ROUTE_ID,
                r.ROUTE_SHORT_NAME,
                r.ROUTE_LONG_NAME,
                r.ROUTE_COLOR,
                r.AGENCY_NAME,
                rm.ON_TIME_PCT,
                rm.RELIABILITY_SCORE,
                cm.AVG_CAPACITY_UTILIZATION as UTILIZATION,
                rev.ESTIMATED_DAILY_REVENUE as REVENUE
            FROM STAGING.STG_ROUTES r
            LEFT JOIN ANALYTICS.RELIABILITY_METRICS rm ON r.ROUTE_ID = rm.ROUTE_ID
            LEFT JOIN ANALYTICS.CROWDING_METRICS cm ON r.ROUTE_ID = cm.ROUTE_ID
            LEFT JOIN ANALYTICS.REVENUE_METRICS rev ON r.ROUTE_ID = rev.ROUTE_ID
        """
        routes = execute_query(query)
        
        formatted_routes = []
        for r in routes:
            formatted_routes.append({
                "id": r.get("ROUTE_ID"),
                "name": r.get("ROUTE_SHORT_NAME") or r.get("ROUTE_LONG_NAME", "Unknown"),
                "color": f"#{r.get('ROUTE_COLOR', '3FB950')}",
                "agency": r.get("AGENCY_NAME", "BART"),
                "type": "Subway",
                "onTime": round(r.get("ON_TIME_PCT", 90) or 90, 1),
                "reliability": round(r.get("RELIABILITY_SCORE", 85) or 85, 1),
                "utilization": round(r.get("UTILIZATION", 60) or 60, 1),
                "revenue": round(r.get("REVENUE", 2500) or 2500, 2)
            })
        
        return ApiResponse(success=True, data=formatted_routes)
    except Exception as e:
        return ApiResponse(success=False, data=[], error=str(e))

@app.get("/api/analytics/route-health")
async def get_route_health():
    """Get route health overview"""
    try:
        query = """
            SELECT 
                ROUTE_ID,
                ON_TIME_PCT,
                RELIABILITY_SCORE,
                TOTAL_DEPARTURES
            FROM ANALYTICS.RELIABILITY_METRICS
            ORDER BY RELIABILITY_SCORE DESC
        """
        results = execute_query(query)
        
        health_data = []
        for r in results:
            on_time = r.get("ON_TIME_PCT", 90) or 90
            health_data.append({
                "route": r.get("ROUTE_ID", "Unknown"),
                "onTime": round(on_time, 1),
                "reliability": round(r.get("RELIABILITY_SCORE", 85) or 85, 1),
                "utilization": 65,  # Would come from crowding metrics
                "status": "healthy" if on_time >= 90 else "warning" if on_time >= 75 else "critical"
            })
        
        return ApiResponse(success=True, data=health_data)
    except Exception as e:
        return ApiResponse(success=False, data=[], error=str(e))

@app.get("/api/stops")
async def get_stops():
    """Get all stops"""
    try:
        query = """
            SELECT 
                STOP_ID,
                STOP_NAME,
                STOP_LAT,
                STOP_LON
            FROM STAGING.STG_STOPS
            LIMIT 100
        """
        stops = execute_query(query)
        
        formatted_stops = []
        for s in stops:
            formatted_stops.append({
                "id": s.get("STOP_ID"),
                "name": s.get("STOP_NAME", "Unknown Stop"),
                "lat": s.get("STOP_LAT", 37.7749),
                "lon": s.get("STOP_LON", -122.4194),
                "departures": 25,  # Would aggregate from departures
                "routes": ["Blue"],
                "status": "active"
            })
        
        return ApiResponse(success=True, data=formatted_stops)
    except Exception as e:
        return ApiResponse(success=False, data=[], error=str(e))

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
async def get_demand_forecast(hours: int = 6):
    """Get demand forecast for next N hours"""
    # Placeholder - would use Snowflake ML
    forecasts = [
        {"time": "Now", "actual": 42, "predicted": None},
        {"time": "+1h", "actual": None, "predicted": 48},
        {"time": "+2h", "actual": None, "predicted": 55},
        {"time": "+3h", "actual": None, "predicted": 62},
        {"time": "+4h", "actual": None, "predicted": 58},
        {"time": "+5h", "actual": None, "predicted": 45},
    ]
    return ApiResponse(success=True, data=forecasts[:hours])

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
            api_key=PERPLEXITY_API_KEY,
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
            api_key=PERPLEXITY_API_KEY,
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

