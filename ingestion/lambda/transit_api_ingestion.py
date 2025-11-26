"""
TransitApp API Ingestion Lambda Function

This Lambda function:
1. Retrieves TransitApp API key from AWS Secrets Manager
2. Calls TransitApp API v3 to fetch real-time transit data
3. Writes raw JSON responses to S3
4. Optionally sends messages to SQS for async processing

Respects rate limits: 5 calls/minute, ~1,500 calls/month (free tier)
"""

import json
import os
import boto3
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
secrets_client = boto3.client('secretsmanager')
sqs_client = boto3.client('sqs')


def get_secret(secret_name: str) -> str:
    """Retrieve secret from AWS Secrets Manager."""
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret = response['SecretString']
        if secret_name.endswith('credentials'):
            # Parse JSON secret
            return json.loads(secret)
        return secret
    except Exception as e:
        logger.error(f"Error retrieving secret {secret_name}: {str(e)}")
        raise


def get_transitapp_api_key() -> str:
    """Get TransitApp API key from Secrets Manager."""
    secret_name = os.environ.get('TRANSIT_APP_API_KEY_SECRET', 'transit/transitapp-api-key-dev')
    api_key = get_secret(secret_name)
    return api_key


def call_transitapp_api(api_key: str, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Call TransitApp API v3.
    
    Args:
        api_key: TransitApp API key
        endpoint: API endpoint (relative to base URL, e.g., "public/stop_departures")
        params: Query parameters
        
    Returns:
        API response as dictionary
    """
    # TransitApp API base URL (not transit.land)
    base_url = "https://external.transitapp.com/v3"
    url = f"{base_url}/{endpoint}"
    
    # TransitApp API uses apiKey in headers, not query parameters
    headers = {
        "apiKey": api_key,
        "Accept-Language": "en",
        "Content-Type": "application/json"
    }
    
    params = params.copy() if params else {}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API call failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text[:500]}")
        raise


def fetch_nearby_stops(api_key: str, lat: float, lon: float, max_distance: int = 600) -> list:
    """
    Fetch nearby stops from TransitApp API.
    
    Args:
        api_key: TransitApp API key
        lat: Latitude
        lon: Longitude
        max_distance: Maximum distance in meters (default 600)
        
    Returns:
        List of nearby stops
    """
    params = {
        "lat": lat,
        "lon": lon,
        "max_distance": max_distance
    }
    response = call_transitapp_api(api_key, "public/nearby_stops", params)
    return response.get("stops", [])


def fetch_stop_departures(api_key: str, global_stop_id: str, 
                          max_num_departures: int = 10,
                          should_update_realtime: bool = True) -> Dict[str, Any]:
    """
    Fetch real-time departures for a specific stop from TransitApp API.
    
    Args:
        api_key: TransitApp API key
        global_stop_id: Global stop ID (e.g., "STM:88368" or "BART:12345")
        max_num_departures: Maximum number of departures per route (1-10, default 10)
        should_update_realtime: Whether to include real-time updates (default True)
        
    Returns:
        Departures data with route_departures
    """
    params = {
        "global_stop_id": global_stop_id,
        "max_num_departures": max(1, min(10, max_num_departures)),
        "should_update_realtime": "true" if should_update_realtime else "false"
    }
    
    response = call_transitapp_api(api_key, "public/stop_departures", params)
    return response


def fetch_multiple_stop_departures(api_key: str, stop_ids: list, 
                                   max_num_departures: int = 10) -> Dict[str, Any]:
    """
    Fetch departures for multiple stops at once.
    
    Args:
        api_key: TransitApp API key
        stop_ids: List of global stop IDs
        max_num_departures: Maximum departures per stop
        
    Returns:
        Dictionary mapping stop_id to departures data
    """
    results = {}
    for stop_id in stop_ids:
        try:
            results[stop_id] = fetch_stop_departures(api_key, stop_id, max_num_departures)
        except Exception as e:
            logger.error(f"Error fetching departures for stop {stop_id}: {str(e)}")
            results[stop_id] = {"error": str(e)}
    return results


def upload_to_s3(bucket: str, key: str, data: Dict[str, Any]) -> None:
    """Upload data to S3 as JSON."""
    try:
        json_data = json.dumps(data, default=str)
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json_data.encode('utf-8'),
            ContentType='application/json'
        )
        logger.info(f"Uploaded {key} to S3 bucket {bucket}")
    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        raise


def send_to_sqs(queue_url: str, message_body: Dict[str, Any]) -> None:
    """Send message to SQS queue."""
    try:
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body)
        )
        logger.info(f"Sent message to SQS queue {queue_url}")
    except Exception as e:
        logger.error(f"Error sending to SQS: {str(e)}")
        raise


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for TransitApp API ingestion.
    
    Event can be:
    - Scheduled event from EventBridge (every 5 minutes)
    - Manual invocation
    - SQS message trigger
    
    Returns:
        Status response
    """
    try:
        # Get configuration from environment
        raw_bucket = os.environ.get('RAW_DATA_BUCKET')
        queue_url = os.environ.get('INGESTION_QUEUE_URL')
        environment = os.environ.get('ENVIRONMENT', 'dev')
        
        if not raw_bucket:
            raise ValueError("RAW_DATA_BUCKET environment variable not set")
        
        # Get API key
        api_key = get_transitapp_api_key()
        
        # Get current timestamp for partitioning
        now = datetime.utcnow()
        date_partition = now.strftime("year=%Y/month=%m/day=%d/hour=%H")
        timestamp = now.isoformat()
        
        results = {
            "timestamp": timestamp,
            "status": "success",
            "files_uploaded": [],
            "errors": []
        }
        
        # Get monitoring locations from environment or use defaults (San Francisco area)
        # Format: "lat1,lon1|lat2,lon2" or single "lat,lon"
        monitoring_locations = os.environ.get('MONITORING_LOCATIONS', '37.7749,-122.4194')  # SF default
        max_distance = int(os.environ.get('MAX_STOP_DISTANCE', '2000'))  # 2km default
        
        # Parse monitoring locations
        locations = []
        for loc_str in monitoring_locations.split('|'):
            parts = loc_str.split(',')
            if len(parts) == 2:
                try:
                    locations.append((float(parts[0]), float(parts[1])))
                except ValueError:
                    logger.warning(f"Invalid location format: {loc_str}")
        
        if not locations:
            # Default to San Francisco
            locations = [(37.7749, -122.4194)]
        
        # Fetch nearby stops for each monitoring location
        all_stops = []
        for lat, lon in locations:
            try:
                stops = fetch_nearby_stops(api_key, lat, lon, max_distance)
                all_stops.extend(stops)
                logger.info(f"Found {len(stops)} stops near ({lat}, {lon})")
            except Exception as e:
                error_msg = f"Error fetching nearby stops for ({lat}, {lon}): {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # Save stops data
        if all_stops:
            stops_key = f"transitapp/stops/{date_partition}/stops_{timestamp}.json"
            upload_to_s3(raw_bucket, stops_key, {"stops": all_stops, "timestamp": timestamp})
            results["files_uploaded"].append(stops_key)
        
        # Fetch departures for each stop (limit to top stops to respect rate limits)
        # TransitApp API: 5 calls/minute, so we'll prioritize stops
        max_stops_to_monitor = int(os.environ.get('MAX_STOPS_TO_MONITOR', '10'))
        stops_to_monitor = all_stops[:max_stops_to_monitor]
        
        departures_data = {}
        for stop in stops_to_monitor:
            stop_id = stop.get("global_stop_id")
            if not stop_id:
                continue
                
            try:
                departures = fetch_stop_departures(api_key, stop_id, max_num_departures=10)
                departures_data[stop_id] = {
                    "stop": stop,
                    "departures": departures
                }
            except Exception as e:
                error_msg = f"Error fetching departures for stop {stop_id}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # Save departures data
        if departures_data:
            departures_key = f"transitapp/departures/{date_partition}/departures_{timestamp}.json"
            upload_to_s3(raw_bucket, departures_key, {
                "departures": departures_data,
                "timestamp": timestamp
            })
            results["files_uploaded"].append(departures_key)
            
            # Optionally send to SQS for async processing
            if queue_url:
                send_to_sqs(queue_url, {
                    "type": "departures",
                    "s3_key": departures_key,
                    "bucket": raw_bucket,
                    "timestamp": timestamp
                })
        
        # Update status if errors occurred
        if results["errors"]:
            results["status"] = "partial_success"
        
        logger.info(f"Ingestion completed: {len(results['files_uploaded'])} files uploaded, {len(results['errors'])} errors")
        
        return {
            "statusCode": 200,
            "body": json.dumps(results)
        }
        
    except Exception as e:
        error_msg = f"Lambda execution failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "error",
                "error": error_msg
            })
        }

