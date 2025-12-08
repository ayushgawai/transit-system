#!/usr/bin/env python3
"""
Generate Historical Departures from GTFS Data
This script generates historical departures for past dates (up to 2 years) 
by applying GTFS schedules to historical service dates.
"""
import sqlite3
import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
GTFS_DATA_DIR = PROJECT_ROOT / "ingestion" / "data" / "historical_gtfs"
DATABASE_PATH = PROJECT_ROOT / "data" / "local_transit.db"

def get_service_dates(gtfs_dir: Path) -> List[datetime]:
    """Extract service dates from calendar.txt and calendar_dates.txt"""
    service_dates = set()
    
    # Read calendar.txt (regular service)
    calendar_file = gtfs_dir / "calendar.txt"
    if calendar_file.exists():
        with open(calendar_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                start_date = datetime.strptime(row['start_date'], '%Y%m%d')
                end_date = datetime.strptime(row['end_date'], '%Y%m%d')
                
                # Check which days of week service runs
                days = []
                if row.get('monday') == '1': days.append(0)
                if row.get('tuesday') == '1': days.append(1)
                if row.get('wednesday') == '1': days.append(2)
                if row.get('thursday') == '1': days.append(3)
                if row.get('friday') == '1': days.append(4)
                if row.get('saturday') == '1': days.append(5)
                if row.get('sunday') == '1': days.append(6)
                
                # Generate dates in range
                current = start_date
                while current <= end_date:
                    if current.weekday() in days:
                        service_dates.add(current.date())
                    current += timedelta(days=1)
    
    # Read calendar_dates.txt (exceptions)
    calendar_dates_file = gtfs_dir / "calendar_dates.txt"
    if calendar_dates_file.exists():
        with open(calendar_dates_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                service_date = datetime.strptime(row['date'], '%Y%m%d').date()
                exception_type = int(row.get('exception_type', '1'))
                
                if exception_type == 1:  # Service added
                    service_dates.add(service_date)
                elif exception_type == 2:  # Service removed
                    service_dates.discard(service_date)
    
    return sorted(list(service_dates))

def generate_historical_departures(agency: str, months_back: int = 2, max_per_day: int = 5000):
    """Generate historical departures for past dates"""
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()
    
    # Find GTFS directory for agency
    gtfs_dir = None
    for item in GTFS_DATA_DIR.iterdir():
        if item.is_dir() and agency.upper() in item.name.upper():
            gtfs_dir = item
            break
    
    if not gtfs_dir:
        logger.error(f"GTFS directory not found for {agency}")
        return
    
    logger.info(f"Processing {agency} GTFS from {gtfs_dir}")
    
    # Get service dates
    service_dates = get_service_dates(gtfs_dir)
    logger.info(f"Found {len(service_dates)} service dates")
    
    # Load trips and stop_times
    trips_file = gtfs_dir / "trips.txt"
    stop_times_file = gtfs_dir / "stop_times.txt"
    
    if not trips_file.exists() or not stop_times_file.exists():
        logger.error("trips.txt or stop_times.txt not found")
        return
    
    # Load trip to route mapping
    trip_to_route = {}
    with open(trips_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            trip_to_route[row.get('trip_id', '')] = row.get('route_id', '')
    
    # Load stop_times
    stop_times = []
    with open(stop_times_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stop_times.append(row)
    
    logger.info(f"Loaded {len(stop_times)} stop_times")
    
    # Generate departures for historical dates
    today = datetime.now().date()
    start_date = today - timedelta(days=months_back * 30)
    
    # Filter service dates to past N months
    historical_dates = [d for d in service_dates if start_date <= d < today]
    logger.info(f"Generating departures for {len(historical_dates)} historical dates (last {months_back} months)")
    
    city = "San Francisco Bay Area" if agency == "BART" else "San Jose"
    total_generated = 0
    
    for service_date in historical_dates:
        if total_generated >= max_per_day * len(historical_dates):
            break
            
        daily_count = 0
        for stop_time in stop_times:
            if daily_count >= max_per_day:
                break
                
            trip_id = stop_time.get('trip_id', '')
            route_id_raw = trip_to_route.get(trip_id, '')
            if not route_id_raw:
                continue
            
            route_id = f"{agency}:{route_id_raw}"
            stop_id = f"{agency}:{stop_time.get('stop_id', '')}"
            
            # Parse time (HH:MM:SS format)
            departure_time_str = stop_time.get('departure_time', stop_time.get('arrival_time', ''))
            if not departure_time_str or ':' not in departure_time_str:
                continue
            
            try:
                parts = departure_time_str.split(':')
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2]) if len(parts) > 2 else 0
                
                # Handle times > 24 hours (next day)
                if hours >= 24:
                    hours -= 24
                    actual_date = service_date + timedelta(days=1)
                else:
                    actual_date = service_date
                
                # Create datetime for this departure
                departure_datetime = datetime.combine(actual_date, datetime.min.time().replace(
                    hour=hours, minute=minutes, second=seconds
                ))
                
                # Convert to epoch seconds
                scheduled_departure_seconds = int(departure_datetime.timestamp())
                scheduled_arrival_seconds = scheduled_departure_seconds  # Use same for simplicity
                
                departure_id = f"{route_id}_{stop_id}_{trip_id}_{scheduled_departure_seconds}"
                
                # Insert historical departure
                cursor.execute("""
                    INSERT OR IGNORE INTO departures (
                        departure_id, stop_id, route_id, global_route_id, trip_id,
                        scheduled_departure_time, scheduled_arrival_time, actual_departure_time, actual_arrival_time,
                        is_real_time, is_cancelled, delay_seconds, direction_id, direction_headsign,
                        agency, city, load_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    departure_id,
                    stop_id,
                    route_id,
                    route_id,
                    trip_id,
                    scheduled_departure_seconds,
                    scheduled_arrival_seconds,
                    scheduled_departure_seconds,  # No actual time in historical GTFS
                    scheduled_arrival_seconds,
                    0,  # Not real-time
                    0,  # Not cancelled
                    0,  # No delay (scheduled)
                    int(stop_time.get('direction_id', 0)) if stop_time.get('direction_id') else 0,
                    stop_time.get('stop_headsign', ''),
                    agency,
                    city,
                    departure_datetime.isoformat()  # Use actual departure time as load_timestamp
                ))
                
                daily_count += 1
                total_generated += 1
                
            except Exception as e:
                continue
        
        if (historical_dates.index(service_date) + 1) % 30 == 0:
            conn.commit()
            logger.info(f"Processed {historical_dates.index(service_date) + 1}/{len(historical_dates)} dates, generated {total_generated:,} departures")
    
    conn.commit()
    conn.close()
    logger.info(f"✅ Generated {total_generated:,} historical departures for {agency}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate historical departures from GTFS")
    parser.add_argument("--agency", default="BART", help="Agency name (BART, VTA)")
    parser.add_argument("--months", type=int, default=2, help="Months of historical data to generate")
    parser.add_argument("--max-per-day", type=int, default=5000, help="Max departures per day")
    
    args = parser.parse_args()
    
    generate_historical_departures(args.agency, args.months, args.max_per_day)

