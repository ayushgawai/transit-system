"""
ML Forecast Fallback
Generates forecasts from local database when Snowflake is unavailable
"""
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta
import sqlite3
from contextlib import contextmanager

DB_PATH = Path(__file__).parent.parent / "data" / "local_transit.db"

@contextmanager
def get_local_connection():
    """Context manager for local SQLite connections"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def generate_demand_forecast(agency: str = None, hours: int = 24) -> List[Dict[str, Any]]:
    """
    Generate demand forecast from local database historical patterns
    Uses time-of-day and day-of-week patterns from historical data
    """
    with get_local_connection() as conn:
        cursor = conn.cursor()
        
        # Get historical patterns by hour and day of week
        agency_filter = ""
        params = []
        if agency and agency != "All":
            agency_filter = "WHERE agency = ?"
            params.append(agency)
        
        # Get average departures by hour and day of week from last 30 days
        query = f"""
            SELECT 
                CAST(strftime('%H', datetime(scheduled_departure_time, 'unixepoch')) AS INTEGER) as hour_of_day,
                CAST(strftime('%w', datetime(scheduled_departure_time, 'unixepoch')) AS INTEGER) as day_of_week,
                COUNT(*) as avg_departures
            FROM departures
            {agency_filter}
            AND scheduled_departure_time IS NOT NULL
            AND datetime(scheduled_departure_time, 'unixepoch') >= datetime('now', '-30 days')
            GROUP BY hour_of_day, day_of_week
        """
        cursor.execute(query, params)
        patterns = {f"{row[0]}_{row[1]}": row[2] for row in cursor.fetchall()}
        
        # Generate forecast for next N hours
        forecasts = []
        now = datetime.now()
        base_demand = 50  # Default if no historical data
        
        for i in range(hours):
            forecast_time = now + timedelta(hours=i)
            hour = forecast_time.hour
            day_of_week = forecast_time.weekday()
            
            # Get pattern for this hour/day
            pattern_key = f"{hour}_{day_of_week}"
            predicted = patterns.get(pattern_key, base_demand)
            
            # Apply peak hour multipliers
            is_morning_peak = 7 <= hour <= 9
            is_evening_peak = 17 <= hour <= 19
            if is_morning_peak or is_evening_peak:
                predicted = int(predicted * 1.3)
            else:
                predicted = int(predicted * 0.8)
            
            forecasts.append({
                "time": forecast_time.strftime("%Y-%m-%d %H:00"),
                "predicted": predicted,
                "actual": None,
                "confidence": "medium"
            })
        
        return forecasts

def generate_delay_forecast(route_id: str, hours: int = 24) -> List[Dict[str, Any]]:
    """
    Generate delay forecast for a specific route
    """
    with get_local_connection() as conn:
        cursor = conn.cursor()
        
        # Get average delay for this route by hour
        query = """
            SELECT 
                CAST(strftime('%H', datetime(scheduled_departure_time, 'unixepoch')) AS INTEGER) as hour_of_day,
                AVG(delay_seconds) as avg_delay
            FROM departures
            WHERE route_id = ?
            AND delay_seconds IS NOT NULL
            AND delay_seconds > 0
            AND delay_seconds <= 1800
            AND datetime(scheduled_departure_time, 'unixepoch') >= datetime('now', '-30 days')
            GROUP BY hour_of_day
        """
        cursor.execute(query, (route_id,))
        delay_patterns = {row[0]: row[1] / 60.0 for row in cursor.fetchall()}  # Convert to minutes
        
        # Generate forecast
        forecasts = []
        now = datetime.now()
        
        for i in range(hours):
            forecast_time = now + timedelta(hours=i)
            hour = forecast_time.hour
            
            predicted_delay = delay_patterns.get(hour, 0)
            if predicted_delay < 0:
                predicted_delay = 0
            
            forecasts.append({
                "time": forecast_time.strftime("%Y-%m-%d %H:00"),
                "predicted_delay_minutes": round(predicted_delay, 1),
                "confidence": "medium"
            })
        
        return forecasts

