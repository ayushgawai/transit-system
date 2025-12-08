"""
Lambda function for scheduled streaming data fetch
Runs every 1 hour via EventBridge
"""
import json
import sys
from pathlib import Path
import subprocess

def lambda_handler(event, context):
    """
    Lambda handler for EventBridge scheduled streaming data fetch
    """
    try:
        # Import the streaming script
        project_root = Path(__file__).parent.parent
        script_path = project_root / "ingestion" / "fetch_streaming_data.py"
        
        if not script_path.exists():
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Streaming script not found',
                    'path': str(script_path)
                })
            }
        
        # Run the streaming script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(project_root)
        )
        
        if result.returncode == 0:
            # Parse output to get count
            output = result.stdout
            count = 0
            if "Successfully fetched" in output or "streaming departures" in output:
                import re
                match = re.search(r'(\d+) streaming departures', output)
                if match:
                    count = int(match.group(1))
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'count': count,
                    'message': f'Successfully fetched {count} streaming records',
                    'output': output[-500:]  # Last 500 chars
                })
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'success': False,
                    'error': result.stderr or 'Script execution failed',
                    'output': result.stdout[-500:]
                })
            }
            
    except subprocess.TimeoutExpired:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': 'Streaming fetch timed out'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

