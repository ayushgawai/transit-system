"""
Local Testing Script for Transit Data Ingestion

This script allows you to test ingestion locally before deploying to AWS Lambda.
It reads configuration from config/config.yaml and can either:
1. Save data to local files
2. Upload to S3 (if AWS credentials configured)
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import ingestion functions (lambda is a Python keyword, so we import from the lambda directory differently)
import importlib.util

# Load transit_api_ingestion module
spec1 = importlib.util.spec_from_file_location(
    "transit_api_ingestion", 
    project_root / "ingestion" / "lambda" / "transit_api_ingestion.py"
)
transit_api = importlib.util.module_from_spec(spec1)
spec1.loader.exec_module(transit_api)

# Load gtfs_sync module
spec2 = importlib.util.spec_from_file_location(
    "gtfs_sync",
    project_root / "ingestion" / "lambda" / "gtfs_sync.py"
)
gtfs_sync = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(gtfs_sync)

# Load config_loader module
spec3 = importlib.util.spec_from_file_location(
    "config_loader",
    project_root / "ingestion" / "lambda" / "config_loader.py"
)
config_loader = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(config_loader)

# Import functions
call_transitapp_api = transit_api.call_transitapp_api
fetch_nearby_stops = transit_api.fetch_nearby_stops
fetch_stop_departures = transit_api.fetch_stop_departures
fetch_multiple_stop_departures = transit_api.fetch_multiple_stop_departures

download_gtfs_feed = gtfs_sync.download_gtfs_feed
validate_gtfs_structure = gtfs_sync.validate_gtfs_structure
sync_gtfs_feed = gtfs_sync.sync_gtfs_feed
GTFS_FEEDS = gtfs_sync.GTFS_FEEDS

# Use config_loader for YAML files, but we'll also load secrets.yaml directly
import yaml

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


def load_config(config_path: str = "secrets.yaml") -> dict:
    """Load configuration from YAML file (secrets.yaml or config.yaml)."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        
        # Flatten nested structure if needed
        flattened = {}
        def flatten_dict(d, parent_key='', sep='_'):
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    flatten_dict(v, new_key, sep=sep)
                else:
                    flattened[new_key] = v
        flatten_dict(config)
        
        return flattened
    except FileNotFoundError:
        print(f"ERROR: Config file not found at {config_path}")
        return {}
    except Exception as e:
        print(f"ERROR loading config: {str(e)}")
        return {}


def load_config_from_yaml(config_path: str = "config/config.yaml") -> dict:
    """Load config from config.yaml (nested structure)."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"ERROR loading config: {str(e)}")
        return {}


def get_api_key(config: dict) -> str:
    """Get TransitApp API key from config or environment."""
    # Try direct key first (from secrets.yaml flattened)
    api_key = config.get("TRANSIT_APP_API_KEY")
    
    # Try nested structure (from config.yaml)
    if not api_key:
        api_key = config.get("transit_app", {}).get("api_key") if isinstance(config.get("transit_app"), dict) else None
    
    # Try environment variable
    if not api_key or api_key.startswith("${") or api_key.startswith("your_"):
        api_key = os.environ.get("TRANSIT_APP_API_KEY")
    
    if not api_key or api_key.startswith("your_"):
        raise ValueError("TransitApp API key not found. Please set TRANSIT_APP_API_KEY in secrets.yaml")
    return api_key


def save_to_local(data: dict, file_path: str):
    """Save data to local JSON file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, default=str, indent=2)
    print(f"✓ Saved to {file_path}")


def upload_to_s3(data: dict, bucket: str, key: str, config: dict):
    """Upload data to S3 if AWS credentials are configured."""
    try:
        region = config.get("aws", {}).get("region", "us-west-2")
        profile = os.environ.get("AWS_PROFILE")
        
        if profile:
            session = boto3.Session(profile_name=profile)
            s3_client = session.client('s3', region_name=region)
        else:
            s3_client = boto3.client('s3', region_name=region)
        
        json_data = json.dumps(data, default=str).encode('utf-8')
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json_data,
            ContentType='application/json'
        )
        print(f"✓ Uploaded to s3://{bucket}/{key}")
        return True
    except NoCredentialsError:
        print(f"⚠ AWS credentials not found, skipping S3 upload for {key}")
        return False
    except ClientError as e:
        print(f"⚠ Error uploading to S3: {str(e)}")
        return False
    except Exception as e:
        print(f"⚠ Error with S3 upload: {str(e)}")
        return False


def test_transitapp_api_ingestion(config: dict, use_s3: bool = False):
    """Test TransitApp API ingestion."""
    print("\n" + "="*60)
    print("Testing TransitApp API Ingestion")
    print("="*60)
    
    try:
        # Get API key
        api_key = get_api_key(config)
        if not api_key or api_key.startswith("your_") or api_key.startswith("YOUR_"):
            print("⚠️  WARNING: API key not configured or using placeholder value")
            print("   Please update secrets.yaml with your actual TransitApp API key")
            return
        print(f"✓ API key found: {api_key[:10]}...")
        
        # Get bucket name
        bucket = config.get("aws", {}).get("s3", {}).get("raw_data_bucket", "")
        if not bucket or bucket.startswith("transit-raw-data-"):
            print("⚠ S3 bucket not configured, saving to local files")
            use_s3 = False
        
        # Get timestamp
        now = datetime.utcnow()
        date_partition = now.strftime("year=%Y/month=%m/day=%d/hour=%H")
        timestamp = now.isoformat()
        
        # Create local output directory
        local_output_dir = "data/local_test"
        
        # Test TransitApp API endpoints
        # Default to San Francisco area for testing
        test_lat = 37.7749  # San Francisco
        test_lon = -122.4194
        
        # Test 1: Fetch nearby stops
        try:
            print(f"\nFetching nearby stops near ({test_lat}, {test_lon})...")
            stops = fetch_nearby_stops(api_key, test_lat, test_lon, max_distance=1000)
            print(f"✓ Found {len(stops)} nearby stops")
            
            # Save stops data
            stops_data = {"stops": stops, "location": {"lat": test_lat, "lon": test_lon}}
            local_file = f"{local_output_dir}/transitapp/stops/{date_partition}/stops_{timestamp}.json"
            save_to_local(stops_data, local_file)
            
            if use_s3:
                s3_key = f"transitapp/stops/{date_partition}/stops_{timestamp}.json"
                upload_to_s3(stops_data, bucket, s3_key, config)
            
            # Test 2: Fetch departures for the first stop (if available)
            if stops:
                first_stop = stops[0]
                stop_id = first_stop.get("global_stop_id")
                stop_name = first_stop.get("stop_name", stop_id)
                
                if stop_id:
                    print(f"\nFetching departures for stop: {stop_name} ({stop_id})...")
                    departures = fetch_stop_departures(api_key, stop_id, max_num_departures=10)
                    
                    # Count departures
                    route_count = len(departures.get("route_departures", []))
                    total_departures = sum(
                        len(rd.get("itineraries", [{}])[0].get("schedule_items", []))
                        for rd in departures.get("route_departures", [])
                    )
                    print(f"✓ Found {total_departures} departures across {route_count} routes")
                    
                    # Save departures data
                    departures_data = {
                        "stop": first_stop,
                        "departures": departures,
                        "timestamp": timestamp
                    }
                    local_file = f"{local_output_dir}/transitapp/departures/{date_partition}/departures_{timestamp}.json"
                    save_to_local(departures_data, local_file)
                    
                    if use_s3:
                        s3_key = f"transitapp/departures/{date_partition}/departures_{timestamp}.json"
                        upload_to_s3(departures_data, bucket, s3_key, config)
                else:
                    print("⚠ No stop_id found in first stop, skipping departures test")
            else:
                print("⚠ No stops found, skipping departures test")
                
        except Exception as e:
            print(f"✗ Error testing TransitApp API: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        
        print("\n✓ TransitApp API ingestion test completed")
        
    except Exception as e:
        print(f"\n✗ TransitApp API ingestion test failed: {str(e)}")
        raise


def test_gtfs_sync(config: dict, use_s3: bool = False):
    """Test GTFS feed sync."""
    print("\n" + "="*60)
    print("Testing GTFS Feed Sync")
    print("="*60)
    
    try:
        # Get bucket name (from flattened config or nested)
        bucket = config.get("AWS_S3_RAW_BUCKET") or config.get("aws", {}).get("s3", {}).get("raw_data_bucket", "")
        if not bucket or bucket.startswith("transit-raw-data-") or "{AWS_ACCOUNT_ID}" in bucket:
            print("⚠ S3 bucket not configured, saving to local files")
            use_s3 = False
        
        # Get feeds from config (try flattened first, then nested)
        feeds = None
        if "GTFS_FEEDS" in config:
            feeds = config["GTFS_FEEDS"]
        else:
            feeds = config.get("gtfs", {}).get("feeds", GTFS_FEEDS) if isinstance(config.get("gtfs"), dict) else GTFS_FEEDS
        
        # Test each feed
        for feed_info in feeds:
            # Skip disabled feeds
            if feed_info.get("enabled", True) is False:
                agency = feed_info.get("agency", "UNKNOWN")
                print(f"\n⚠ Skipping disabled feed: {agency}")
                continue
                
            agency = feed_info.get("agency", "UNKNOWN")
            url = feed_info.get("url")
            
            print(f"\nTesting GTFS sync for {agency}...")
            print(f"URL: {url}")
            
            try:
                if use_s3:
                    # Use the Lambda function logic
                    result = sync_gtfs_feed(feed_info, bucket)
                    if result["status"] == "success":
                        print(f"✓ {agency} GTFS feed synced successfully")
                    else:
                        print(f"✗ {agency} GTFS sync failed: {result.get('error')}")
                else:
                    # Download and validate locally
                    zip_content = download_gtfs_feed(url)
                    if validate_gtfs_structure(zip_content):
                        # Save locally
                        local_file = f"data/local_test/gtfs/{agency}/raw/{datetime.utcnow().strftime('year=%Y/month=%m/day=%d')}/gtfs_feed_{datetime.utcnow().isoformat()}.zip"
                        save_to_local({"content_length": len(zip_content)}, local_file.replace(".zip", "_info.json"))
                        with open(local_file, 'wb') as f:
                            f.write(zip_content)
                        print(f"✓ {agency} GTFS feed downloaded and validated")
                    else:
                        print(f"✗ {agency} GTFS feed validation failed")
                        
            except Exception as e:
                print(f"✗ Error syncing {agency}: {str(e)}")
                continue
        
        print("\n✓ GTFS sync test completed")
        
    except Exception as e:
        print(f"\n✗ GTFS sync test failed: {str(e)}")
        raise


def main():
    """Main function."""
    print("="*60)
    print("Transit System - Local Ingestion Test")
    print("="*60)
    
    # Load config from secrets.yaml (this is the main config file with actual credentials)
    project_root = Path(__file__).parent.parent
    secrets_path = project_root / "secrets.yaml"
    
    # Load from secrets.yaml (required file)
    if not secrets_path.exists():
        print(f"\nERROR: secrets.yaml not found at {secrets_path}")
        print(f"   Please create secrets.yaml in project root and fill in your credentials")
        return 1
    
    print(f"\nLoading secrets from: {secrets_path}")
    try:
        config = load_config(str(secrets_path))
        print("✓ Secrets loaded")
    except Exception as e:
        print(f"ERROR loading secrets.yaml: {e}")
        return 1
    
    # Check if S3 should be used
    use_s3 = os.environ.get("USE_S3", "false").lower() == "true"
    aws_profile = os.environ.get("AWS_PROFILE")
    
    if use_s3:
        if aws_profile:
            print(f"✓ Using AWS profile: {aws_profile}")
        else:
            print("⚠ USE_S3=true but AWS_PROFILE not set, using default AWS credentials")
    
    # Test TransitApp API ingestion
    try:
        test_transitapp_api_ingestion(config, use_s3=use_s3)
    except Exception as e:
        print(f"\n✗ TransitApp API test failed: {str(e)}")
        return 1
    
    # Test GTFS sync (optional - comment out if you want to skip)
    try:
        test_gtfs_sync(config, use_s3=use_s3)
    except Exception as e:
        print(f"\n✗ GTFS sync test failed: {str(e)}")
        return 1
    
    print("\n" + "="*60)
    print("✓ All local tests completed successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Verify data in local files or S3")
    print("2. If using S3, setup Snowpipe to load into Snowflake")
    print("3. Run dbt transformations")
    print("4. Test dashboards and chatbot")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

