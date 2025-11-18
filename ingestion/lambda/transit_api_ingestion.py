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


def call_transitapp_api(api_key: str, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call TransitApp API v3.
    
    Args:
        api_key: TransitApp API key
        endpoint: API endpoint (relative to base URL)
        params: Query parameters
        
    Returns:
        API response as dictionary
    """
    base_url = "https://transit.land/api/v3"
    url = f"{base_url}/{endpoint}"
    
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API call failed: {str(e)}")
        raise


def fetch_agencies(api_key: str) -> list:
    """Fetch list of agencies from TransitApp API."""
    params = {
        "limit": 100,
        "served_by": "o-9q9-bart,o-9q9-caltrain"  # Example agencies
    }
    response = call_transitapp_api(api_key, "agencies", params)
    return response.get("agencies", [])


def fetch_departures(api_key: str, stop_id: Optional[str] = None, 
                     route_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch real-time departures from TransitApp API.
    
    Args:
        api_key: TransitApp API key
        stop_id: Optional stop ID to filter departures
        route_id: Optional route ID to filter departures
        
    Returns:
        Departures data
    """
    params = {}
    if stop_id:
        params["stop_id"] = stop_id
    if route_id:
        params["route_id"] = route_id
    params["limit"] = 100
    
    response = call_transitapp_api(api_key, "departures", params)
    return response


def fetch_alerts(api_key: str, agency_id: Optional[str] = None) -> Dict[str, Any]:
    """Fetch service alerts from TransitApp API."""
    params = {}
    if agency_id:
        params["agency_id"] = agency_id
    params["limit"] = 100
    
    response = call_transitapp_api(api_key, "alerts", params)
    return response


def fetch_routes(api_key: str, agency_id: Optional[str] = None) -> Dict[str, Any]:
    """Fetch routes information from TransitApp API."""
    params = {}
    if agency_id:
        params["agency_id"] = agency_id
    params["limit"] = 100
    
    response = call_transitapp_api(api_key, "routes", params)
    return response


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
        
        # Fetch agencies (once per run)
        try:
            agencies_data = fetch_agencies(api_key)
            agencies_key = f"transitapp/agencies/{date_partition}/agencies_{timestamp}.json"
            upload_to_s3(raw_bucket, agencies_key, agencies_data)
            results["files_uploaded"].append(agencies_key)
        except Exception as e:
            error_msg = f"Error fetching agencies: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        # Fetch departures (real-time data)
        try:
            departures_data = fetch_departures(api_key)
            departures_key = f"transitapp/departures/{date_partition}/departures_{timestamp}.json"
            upload_to_s3(raw_bucket, departures_key, departures_data)
            results["files_uploaded"].append(departures_key)
            
            # Optionally send to SQS for async processing
            if queue_url:
                send_to_sqs(queue_url, {
                    "type": "departures",
                    "s3_key": departures_key,
                    "bucket": raw_bucket,
                    "timestamp": timestamp
                })
        except Exception as e:
            error_msg = f"Error fetching departures: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        # Fetch alerts
        try:
            alerts_data = fetch_alerts(api_key)
            alerts_key = f"transitapp/alerts/{date_partition}/alerts_{timestamp}.json"
            upload_to_s3(raw_bucket, alerts_key, alerts_data)
            results["files_uploaded"].append(alerts_key)
        except Exception as e:
            error_msg = f"Error fetching alerts: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
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

