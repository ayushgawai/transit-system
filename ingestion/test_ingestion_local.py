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
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import ingestion functions
from ingestion.lambda.transit_api_ingestion import (
    call_transitapp_api,
    fetch_agencies,
    fetch_departures,
    fetch_alerts,
    fetch_routes
)
from ingestion.lambda.gtfs_sync import (
    download_gtfs_feed,
    validate_gtfs_structure,
    sync_gtfs_feed,
    GTFS_FEEDS
)
from ingestion.lambda.config_loader import load_config

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


def get_api_key(config: dict) -> str:
    """Get TransitApp API key from config or environment."""
    api_key = config.get("transit_app", {}).get("api_key")
    if not api_key or api_key.startswith("${"):
        api_key = os.environ.get("TRANSIT_APP_API_KEY")
    if not api_key:
        raise ValueError("TransitApp API key not found in config or environment variables")
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
        
        # Test API endpoints
        endpoints_to_test = [
            ("agencies", lambda: fetch_agencies(api_key)),
            ("departures", lambda: fetch_departures(api_key)),
            ("alerts", lambda: fetch_alerts(api_key)),
            ("routes", lambda: fetch_routes(api_key)),
        ]
        
        for endpoint_name, fetch_func in endpoints_to_test:
            try:
                print(f"\nFetching {endpoint_name}...")
                data = fetch_func()
                
                # Save locally
                local_file = f"{local_output_dir}/transitapp/{endpoint_name}/{date_partition}/{endpoint_name}_{timestamp}.json"
                save_to_local(data, local_file)
                
                # Upload to S3 if configured
                if use_s3:
                    s3_key = f"transitapp/{endpoint_name}/{date_partition}/{endpoint_name}_{timestamp}.json"
                    upload_to_s3(data, bucket, s3_key, config)
                
                print(f"✓ {endpoint_name} fetched successfully")
                
            except Exception as e:
                print(f"✗ Error fetching {endpoint_name}: {str(e)}")
                continue
        
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
        # Get bucket name
        bucket = config.get("aws", {}).get("s3", {}).get("raw_data_bucket", "")
        if not bucket or bucket.startswith("transit-raw-data-"):
            print("⚠ S3 bucket not configured, saving to local files")
            use_s3 = False
        
        # Get feeds from config
        feeds = config.get("gtfs", {}).get("feeds", GTFS_FEEDS)
        
        # Test each feed
        for feed_info in feeds:
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
    
    # Load config
    config_path = os.environ.get("CONFIG_PATH", "config/config.yaml")
    print(f"\nLoading config from: {config_path}")
    config = load_config(config_path)
    print("✓ Config loaded")
    
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

