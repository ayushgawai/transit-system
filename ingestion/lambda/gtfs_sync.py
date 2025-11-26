"""
GTFS Static Feed Sync Lambda Function

This Lambda function:
1. Downloads GTFS static feeds from public URLs
2. Extracts and validates GTFS data
3. Uploads to S3 in organized structure
4. Runs daily via EventBridge schedule

GTFS feeds are typically updated daily or weekly by transit agencies.
"""

import json
import os
import boto3
import requests
import zipfile
import io
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')


# GTFS feed URLs (public open data)
# These should be moved to configuration file in production
GTFS_FEEDS = [
    {
        "agency": "BART",
        "name": "Bay Area Rapid Transit",
        "url": "https://www.bart.gov/dev/schedules/google_transit.zip",
        "timezone": "America/Los_Angeles"
    },
    {
        "agency": "Caltrain",
        "name": "Caltrain",
        # Note: Caltrain's direct URL may redirect to HTML. Alternative sources:
        # - transit.land: https://transit.land/api/v2/feeds?operated_by=o-9q9-caltrain
        # - 511.org: https://511.org/open-data/transit
        # For now, using transit.land's feed URL if available, otherwise skip
        "url": "https://www.caltrain.com/developer/GTFS.zip",
        "timezone": "America/Los_Angeles",
        "enabled": False  # Disable until we find a working URL
    }
]


def download_gtfs_feed(url: str) -> bytes:
    """
    Download GTFS feed ZIP file from URL.
    
    Args:
        url: URL to GTFS feed ZIP file
        
    Returns:
        Binary content of ZIP file
    """
    try:
        logger.info(f"Downloading GTFS feed from {url}")
        # Follow redirects and set headers to avoid getting HTML pages
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; TransitSystem/1.0)',
            'Accept': 'application/zip, application/octet-stream, */*'
        }
        response = requests.get(url, timeout=120, headers=headers, allow_redirects=True)
        response.raise_for_status()
        
        # Check if we got HTML instead of ZIP (common issue with some transit agency sites)
        content_type = response.headers.get('Content-Type', '').lower()
        if 'html' in content_type:
            logger.warning(f"Received HTML instead of ZIP from {url}. Content-Type: {content_type}")
            raise ValueError(f"URL returned HTML instead of ZIP file. The feed URL may be incorrect or require authentication.")
        
        # Basic check: ZIP files should start with PK (ZIP file signature)
        if len(response.content) < 4 or response.content[:2] != b'PK':
            logger.error(f"Downloaded content does not appear to be a ZIP file (first bytes: {response.content[:20]})")
            raise ValueError("Downloaded content is not a valid ZIP file")
        
        logger.info(f"Successfully downloaded {len(response.content)} bytes")
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading GTFS feed: {str(e)}")
        raise


def validate_gtfs_structure(zip_content: bytes) -> bool:
    """
    Validate that ZIP contains required GTFS files.
    
    Required files: routes.txt, stops.txt, trips.txt, stop_times.txt, calendar.txt or calendar_dates.txt
    
    Args:
        zip_content: Binary content of GTFS ZIP file
        
    Returns:
        True if valid, False otherwise
    """
    required_files = ['routes.txt', 'stops.txt', 'trips.txt', 'stop_times.txt']
    optional_files = ['calendar.txt', 'calendar_dates.txt']
    
    try:
        with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
            file_list = zip_file.namelist()
            
            # Check required files
            for required_file in required_files:
                if required_file not in file_list:
                    logger.error(f"Missing required GTFS file: {required_file}")
                    return False
            
            # Check that at least one optional file exists
            has_calendar = any(f in file_list for f in optional_files)
            if not has_calendar:
                logger.warning("No calendar.txt or calendar_dates.txt found")
            
            logger.info(f"GTFS structure validated: {len(file_list)} files found")
            return True
            
    except zipfile.BadZipFile as e:
        logger.error(f"Invalid ZIP file: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error validating GTFS structure: {str(e)}")
        return False


def upload_gtfs_to_s3(bucket: str, agency: str, zip_content: bytes, 
                      feed_info: Dict[str, Any]) -> List[str]:
    """
    Upload GTFS feed to S3.
    
    Structure:
    gtfs/{agency}/raw/{date}/gtfs_feed.zip
    gtfs/{agency}/extracted/{date}/routes.txt
    gtfs/{agency}/extracted/{date}/stops.txt
    etc.
    
    Args:
        bucket: S3 bucket name
        agency: Agency identifier
        zip_content: Binary content of GTFS ZIP
        feed_info: Metadata about the feed
        
    Returns:
        List of S3 keys uploaded
    """
    uploaded_keys = []
    now = datetime.utcnow()
    date_partition = now.strftime("year=%Y/month=%m/day=%d")
    timestamp = now.isoformat()
    
    # Upload raw ZIP file
    raw_key = f"gtfs/{agency}/raw/{date_partition}/gtfs_feed_{timestamp}.zip"
    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=raw_key,
            Body=zip_content,
            ContentType='application/zip',
            Metadata={
                "agency": agency,
                "source_url": feed_info["url"],
                "timestamp": timestamp
            }
        )
        uploaded_keys.append(raw_key)
        logger.info(f"Uploaded raw GTFS feed to {raw_key}")
    except Exception as e:
        logger.error(f"Error uploading raw GTFS: {str(e)}")
        raise
    
    # Extract and upload individual files
    try:
        with zipfile.ZipFile(io.BytesIO(zip_content)) as zip_file:
            for file_name in zip_file.namelist():
                if file_name.endswith('.txt'):
                    # Read file content
                    file_content = zip_file.read(file_name)
                    
                    # Upload to S3
                    extracted_key = f"gtfs/{agency}/extracted/{date_partition}/{file_name}"
                    s3_client.put_object(
                        Bucket=bucket,
                        Key=extracted_key,
                        Body=file_content,
                        ContentType='text/plain',
                        Metadata={
                            "agency": agency,
                            "source_file": file_name,
                            "timestamp": timestamp
                        }
                    )
                    uploaded_keys.append(extracted_key)
                    logger.debug(f"Uploaded {file_name} to {extracted_key}")
        
        logger.info(f"Extracted and uploaded {len([f for f in uploaded_keys if f.endswith('.txt')])} GTFS files")
        
    except Exception as e:
        logger.error(f"Error extracting/uploading GTFS files: {str(e)}")
        # Don't fail if extraction fails - raw ZIP is already uploaded
    
    # Upload metadata JSON
    metadata_key = f"gtfs/{agency}/metadata/{date_partition}/metadata_{timestamp}.json"
    metadata = {
        "agency": agency,
        "name": feed_info.get("name"),
        "url": feed_info["url"],
        "timestamp": timestamp,
        "timezone": feed_info.get("timezone"),
        "files_uploaded": uploaded_keys
    }
    
    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=metadata_key,
            Body=json.dumps(metadata, indent=2),
            ContentType='application/json'
        )
        uploaded_keys.append(metadata_key)
        logger.info(f"Uploaded metadata to {metadata_key}")
    except Exception as e:
        logger.error(f"Error uploading metadata: {str(e)}")
    
    return uploaded_keys


def sync_gtfs_feed(feed_info: Dict[str, Any], bucket: str) -> Dict[str, Any]:
    """
    Sync a single GTFS feed.
    
    Args:
        feed_info: Dictionary with feed metadata (agency, url, etc.)
        bucket: S3 bucket name
        
    Returns:
        Result dictionary with status and uploaded keys
    """
    agency = feed_info["agency"]
    url = feed_info["url"]
    
    result = {
        "agency": agency,
        "status": "success",
        "uploaded_keys": [],
        "error": None
    }
    
    try:
        # Download feed
        zip_content = download_gtfs_feed(url)
        
        # Validate structure
        if not validate_gtfs_structure(zip_content):
            raise ValueError("GTFS structure validation failed")
        
        # Upload to S3
        uploaded_keys = upload_gtfs_to_s3(bucket, agency, zip_content, feed_info)
        result["uploaded_keys"] = uploaded_keys
        
        logger.info(f"Successfully synced GTFS feed for {agency}")
        
    except Exception as e:
        error_msg = f"Error syncing GTFS feed for {agency}: {str(e)}"
        logger.error(error_msg)
        result["status"] = "error"
        result["error"] = error_msg
    
    return result


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for GTFS feed sync.
    
    Event can be:
    - Scheduled event from EventBridge (daily at 2 AM UTC)
    - Manual invocation
    - S3 event (if triggered by feed update notification)
    
    Returns:
        Status response with sync results for each feed
    """
    try:
        # Get configuration from environment
        raw_bucket = os.environ.get('RAW_DATA_BUCKET')
        environment = os.environ.get('ENVIRONMENT', 'dev')
        
        if not raw_bucket:
            raise ValueError("RAW_DATA_BUCKET environment variable not set")
        
        # Get feeds from event or use default
        feeds = event.get('feeds', GTFS_FEEDS)
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "feeds_synced": [],
            "errors": []
        }
        
        # Sync each feed
        for feed_info in feeds:
            # Skip disabled feeds
            if feed_info.get("enabled", True) is False:
                logger.info(f"Skipping disabled feed: {feed_info.get('agency', 'UNKNOWN')}")
                continue
                
            feed_result = sync_gtfs_feed(feed_info, raw_bucket)
            results["feeds_synced"].append(feed_result)
            
            if feed_result["status"] == "error":
                results["errors"].append(feed_result["error"])
        
        # Update overall status
        if results["errors"]:
            results["status"] = "partial_success" if len(results["errors"]) < len(feeds) else "error"
        
        success_count = sum(1 for f in results["feeds_synced"] if f["status"] == "success")
        logger.info(f"GTFS sync completed: {success_count}/{len(feeds)} feeds synced successfully")
        
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

