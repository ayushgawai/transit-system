"""
Shared utility functions for Lambda functions
"""

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger()


def load_config_from_s3(bucket: str, key: str) -> Dict[str, Any]:
    """Load configuration file from S3."""
    import boto3
    s3_client = boto3.client('s3')
    
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        config_content = response['Body'].read().decode('utf-8')
        return json.loads(config_content) if key.endswith('.json') else {}
    except Exception as e:
        logger.error(f"Error loading config from S3: {str(e)}")
        raise


def parse_s3_event(event: Dict[str, Any]) -> list:
    """Parse S3 event and return list of S3 object keys."""
    records = event.get('Records', [])
    keys = []
    
    for record in records:
        if record.get('eventSource') == 'aws:s3':
            s3_info = record.get('s3', {})
            bucket = s3_info.get('bucket', {}).get('name')
            key = s3_info.get('object', {}).get('key')
            if bucket and key:
                keys.append({'bucket': bucket, 'key': key})
    
    return keys


def validate_json_structure(data: Dict[str, Any], required_fields: list) -> bool:
    """Validate that dictionary contains required fields."""
    for field in required_fields:
        if field not in data:
            logger.warning(f"Missing required field: {field}")
            return False
    return True

