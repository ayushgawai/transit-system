"""
Local SQLite Database Access
Provides functions to query the local SQLite database when Snowflake is unavailable
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "local_transit.db"


@contextmanager
def get_local_connection():
    """Context manager for local SQLite connections"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
    finally:
        conn.close()


def get_kpis_from_local(agency: Optional[str] = None) -> Dict[str, Any]:
    """Get KPIs from local database"""
    with get_local_connection() as conn:
        cursor = conn.cursor()
        
        # Build agency filter - use 'agency' column (not 'agency_name')
        agency_filter = ""
        params = []
        if agency and agency != "All":
            agency_filter = "WHERE d.agency = ?"
            params.append(agency)
        
        # Total departures
        if agency_filter:
            query = f"SELECT COUNT(*) as total FROM departures d {agency_filter}"
        else:
            query = "SELECT COUNT(*) as total FROM departures d"
        cursor.execute(query, params)
        total_departures = cursor.fetchone()[0] or 0
        
        # On-time performance (departures with delay <= 5 minutes)
        # Note: GTFS data has delay_seconds = 0 (scheduled), so all are "on-time"
        if agency_filter:
            query = f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN delay_seconds <= 300 AND delay_seconds >= -300 THEN 1 ELSE 0 END) as on_time
                FROM departures d
                {agency_filter} AND delay_seconds IS NOT NULL
            """
        else:
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN delay_seconds <= 300 AND delay_seconds >= -300 THEN 1 ELSE 0 END) as on_time
                FROM departures d
                WHERE delay_seconds IS NOT NULL
            """
        cursor.execute(query, params)
        row = cursor.fetchone()
        on_time_count = row[1] if row else 0
        total_with_delay = row[0] if row else 0
        # For GTFS data (delay_seconds = 0), assume 100% on-time
        on_time_pct = (on_time_count / total_with_delay * 100) if total_with_delay > 0 else 100.0
        
        # Active routes - use 'agency' column
        query = "SELECT COUNT(DISTINCT route_id) as total FROM routes r"
        if agency and agency != "All":
            query += " WHERE r.agency = ?"
            cursor.execute(query, [agency])
        else:
            cursor.execute(query)
        active_routes = cursor.fetchone()[0] or 0
        
        # Average delay (filter outliers: only delays between 0 and 30 minutes)
        # SQLite doesn't support PERCENTILE_CONT, so we'll use AVG with outlier filtering
        # Convert to minutes for display
        if agency_filter:
            delay_query = f"""
                SELECT AVG(delay_seconds) as avg_delay
                FROM departures d
                {agency_filter} AND delay_seconds IS NOT NULL 
                AND delay_seconds >= 0 AND delay_seconds <= 1800
            """
        else:
            delay_query = """
                SELECT AVG(delay_seconds) as avg_delay
                FROM departures d
                WHERE delay_seconds IS NOT NULL 
                AND delay_seconds >= 0 AND delay_seconds <= 1800
            """
        cursor.execute(delay_query, params)
        delay_row = cursor.fetchone()
        avg_delay_seconds = delay_row[0] if delay_row and delay_row[0] is not None else 0
        
        # Convert to minutes and round to 1 decimal
        avg_delay = round(avg_delay_seconds / 60.0, 1) if avg_delay_seconds > 0 else 0
        
        # Active alerts (placeholder - we don't have alerts table populated yet)
        active_alerts = 0
        
        # Estimated revenue (placeholder - would need fare data)
        est_revenue = 0
        
        return {
            "on_time_performance": round(on_time_pct, 1),
            "active_routes": active_routes,
            "total_departures": total_departures,
            "est_revenue": est_revenue,
            "active_alerts": active_alerts,
            "avg_delay": avg_delay
        }


def get_routes_from_local(agency: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get routes from local database with performance metrics"""
    with get_local_connection() as conn:
        cursor = conn.cursor()
        
        # Get routes with performance data
        query = """
            SELECT 
                r.*,
                COUNT(DISTINCT d.departure_id) as total_departures,
                COUNT(DISTINCT CASE WHEN d.delay_seconds IS NOT NULL AND d.delay_seconds <= 300 AND d.delay_seconds >= -300 THEN d.departure_id END) as on_time_count,
                AVG(CASE WHEN d.delay_seconds IS NOT NULL THEN d.delay_seconds ELSE NULL END) as avg_delay_seconds
            FROM routes r
            LEFT JOIN departures d ON r.route_id = d.route_id
        """
        params = []
        if agency and agency != "All":
            query += " WHERE r.agency = ?"
            params.append(agency)
        query += " GROUP BY r.route_id"
        query += " ORDER BY r.route_name"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Get max departures for utilization calculation
        max_deps_query = "SELECT MAX(cnt) FROM (SELECT COUNT(*) as cnt FROM departures GROUP BY route_id)"
        cursor.execute(max_deps_query)
        max_deps = cursor.fetchone()[0] or 1
        
        routes = []
        for row in rows:
            total_deps = row["total_departures"] or 0
            on_time_count = row["on_time_count"] or 0
            
            # Calculate on-time percentage
            if total_deps > 0:
                on_time_pct = (on_time_count / total_deps * 100) if on_time_count > 0 else 100.0
            else:
                on_time_pct = 100.0
            
            # Calculate reliability
            avg_delay = row["avg_delay_seconds"] if row["avg_delay_seconds"] is not None else 0
            reliability = max(0, min(100, 100 - (avg_delay / 60 / 5 * 100))) if avg_delay > 0 else 100.0
            
            # Calculate utilization (normalized)
            utilization = min(100, (total_deps / max_deps * 100)) if max_deps > 0 else 50
            
            routes.append({
                "id": row["route_id"],
                "name": row["route_name"] or row["route_short_name"] or row["route_id"],
                "short_name": row["route_short_name"],
                "long_name": row["route_long_name"],
                "agency": row["agency"],
                "city": row["city"] if "city" in row.keys() else None,
                "type": row["route_type"] if "route_type" in row.keys() else 3,
                "color": row["route_color"] if "route_color" in row.keys() else "#0066CC",
                "onTime": round(on_time_pct, 1),
                "reliability": round(reliability, 1),
                "utilization": round(utilization, 1),
                "total_departures": total_deps
            })
        
        return routes


def get_stops_from_local(agency: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Get stops from local database"""
    with get_local_connection() as conn:
        cursor = conn.cursor()
        
        # Build query with proper WHERE clause handling
        if agency and agency != "All":
            query = """
                SELECT s.*, COUNT(d.departure_id) as departure_count
                FROM stops s
                LEFT JOIN departures d ON s.stop_id = d.stop_id
                WHERE s.agency = ?
                GROUP BY s.stop_id
                LIMIT ?
            """
            params = [agency, limit]
        else:
            query = """
                SELECT s.*, COUNT(d.departure_id) as departure_count
                FROM stops s
                LEFT JOIN departures d ON s.stop_id = d.stop_id
                GROUP BY s.stop_id
                LIMIT ?
            """
            params = [limit]
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        stops = []
        for row in rows:
            stops.append({
                "id": row["stop_id"],
                "name": row["stop_name"],
                "lat": row["stop_lat"],
                "lon": row["stop_lon"],
                "agency": row["agency"],
                "departures": row["departure_count"] if row["departure_count"] else 0,
                "status": "active" if row["departure_count"] and row["departure_count"] > 0 else "inactive"
            })
        
        return stops


def get_route_health_from_local(agency: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get route health metrics from local database"""
    with get_local_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT 
                r.route_id,
                r.route_name,
                r.route_short_name,
                r.route_long_name,
                r.agency,
                r.city,
                COUNT(DISTINCT d.departure_id) as total_departures,
                COUNT(DISTINCT CASE WHEN d.delay_seconds IS NOT NULL AND d.delay_seconds <= 300 AND d.delay_seconds >= -300 THEN d.departure_id END) as on_time_count,
                AVG(CASE WHEN d.delay_seconds IS NOT NULL THEN d.delay_seconds ELSE NULL END) as avg_delay_seconds
            FROM routes r
            LEFT JOIN departures d ON r.route_id = d.route_id
        """
        params = []
        if agency and agency != "All":
            query += " WHERE r.agency = ?"
            params.append(agency)
        query += " GROUP BY r.route_id, r.route_name, r.route_short_name, r.route_long_name, r.agency, r.city"
        query += " HAVING total_departures > 0"
        query += " ORDER BY total_departures DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Get max departures for utilization normalization
        max_deps_query = "SELECT MAX(cnt) FROM (SELECT COUNT(*) as cnt FROM departures GROUP BY route_id)"
        cursor.execute(max_deps_query)
        max_deps = cursor.fetchone()[0] or 1
        
        routes = []
        for row in rows:
            total = row["total_departures"] if row["total_departures"] else 0
            on_time = row["on_time_count"] if row["on_time_count"] else 0
            
            # For GTFS data (delay_seconds = 0), all are on-time
            # If no delay data, assume 100% on-time (scheduled service)
            if total > 0:
                on_time_pct = (on_time / total * 100) if on_time > 0 else 100.0
            else:
                on_time_pct = 100.0
            
            avg_delay = row["avg_delay_seconds"] if row["avg_delay_seconds"] is not None else 0
            
            # Reliability: inverse of delay (if delay is 0, reliability is 100)
            reliability = max(0, min(100, 100 - (avg_delay / 60 / 5 * 100))) if avg_delay > 0 else 100.0
            
            # Utilization: normalized based on departures (0-100%)
            utilization = min(100, (total / max_deps * 100)) if max_deps > 0 else 50
            
            # Determine status
            if on_time_pct >= 90:
                status = "healthy"
            elif on_time_pct >= 75:
                status = "warning"
            else:
                status = "critical"
            
            # Get route name (prefer long_name, then short_name, then route_name, then route_id)
            route_name = row["route_long_name"] or row["route_short_name"] or row["route_name"] or row["route_id"]
            
            routes.append({
                "route": route_name,
                "route_id": row["route_id"],
                "onTime": round(on_time_pct, 1),
                "reliability": round(reliability, 1),
                "utilization": round(utilization, 1),
                "status": status,
                "agency": row["agency"],
                "city": row["city"] or "Unknown"
            })
        
        return routes


def get_available_agencies() -> List[str]:
    """Get list of available agencies in the database"""
    with get_local_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT agency FROM routes WHERE agency IS NOT NULL ORDER BY agency")
        return [row[0] for row in cursor.fetchall()]


def get_available_cities() -> List[str]:
    """Get list of available cities in the database"""
    with get_local_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT city FROM routes WHERE city IS NOT NULL AND city != '' ORDER BY city")
        return [row[0] for row in cursor.fetchall()]

