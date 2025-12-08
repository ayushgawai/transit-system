"""
Warehouse Configuration Manager
Handles switching between Redshift and Snowflake based on config.yaml
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
import boto3
import json

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_FILE = PROJECT_ROOT / 'config.yaml'

class WarehouseConfig:
    """Manages warehouse configuration and connections"""
    
    def __init__(self):
        self.config = self._load_config()
        self.warehouse_type = self.config.get('warehouse', {}).get('type', 'redshift')
        self._secrets = None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.yaml"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def _load_secrets(self):
        """Load secrets from AWS Secrets Manager"""
        if self._secrets is not None:
            return self._secrets
        
        try:
            session = boto3.Session(profile_name='transit-system')
            secrets_client = session.client('secretsmanager', region_name='us-west-2')
            
            # Load Snowflake secrets
            try:
                snowflake_secret_name = f"transit/snowflake-{os.getenv('ENVIRONMENT', 'dev')}"
                snowflake_secret = json.loads(
                    secrets_client.get_secret_value(SecretId=snowflake_secret_name)['SecretString']
                )
            except:
                snowflake_secret = {}
            
            # Load Redshift secrets (if stored)
            try:
                redshift_secret_name = f"transit/redshift-{os.getenv('ENVIRONMENT', 'dev')}"
                redshift_secret = json.loads(
                    secrets_client.get_secret_value(SecretId=redshift_secret_name)['SecretString']
                )
            except:
                redshift_secret = {}
            
            # Load Transit API key
            try:
                transit_secret_name = f"transit/transitapp-api-{os.getenv('ENVIRONMENT', 'dev')}"
                transit_secret = json.loads(
                    secrets_client.get_secret_value(SecretId=transit_secret_name)['SecretString']
                )
            except:
                transit_secret = {}
            
            self._secrets = {
                'snowflake': snowflake_secret,
                'redshift': redshift_secret,
                'transit_api': transit_secret
            }
            
            return self._secrets
        except Exception as e:
            print(f"Warning: Could not load secrets from AWS: {e}")
            return {}
    
    def get_warehouse_type(self) -> str:
        """Get current warehouse type"""
        return self.warehouse_type
    
    def is_redshift(self) -> bool:
        """Check if using Redshift"""
        return self.warehouse_type == 'redshift'
    
    def is_snowflake(self) -> bool:
        """Check if using Snowflake"""
        return self.warehouse_type == 'snowflake'
    
    def get_redshift_config(self) -> Dict[str, Any]:
        """Get Redshift connection configuration"""
        secrets = self._load_secrets()
        config = self.config.get('warehouse', {}).get('redshift', {})
        
        # Merge with secrets if available
        if 'redshift' in secrets:
            config.update(secrets['redshift'])
        
        return config
    
    def get_snowflake_config(self) -> Dict[str, Any]:
        """Get Snowflake connection configuration"""
        secrets = self._load_secrets()
        config = self.config.get('warehouse', {}).get('snowflake', {})
        
        # Merge with secrets if available
        if 'snowflake' in secrets:
            config.update(secrets['snowflake'])
        
        return config
    
    def get_transit_api_key(self) -> Optional[str]:
        """Get Transit API key from secrets"""
        secrets = self._load_secrets()
        return secrets.get('transit_api', {}).get('api_key') or os.getenv('TRANSIT_API_KEY')
    
    def get_connection_string(self) -> str:
        """Get appropriate connection string based on warehouse type"""
        if self.is_redshift():
            redshift_config = self.get_redshift_config()
            return (
                f"postgresql://{redshift_config.get('user', 'awsuser')}:"
                f"{redshift_config.get('password', '')}@"
                f"{redshift_config.get('host', '')}:"
                f"{redshift_config.get('port', 5439)}/"
                f"{redshift_config.get('database', 'transit_db')}"
            )
        else:
            # Snowflake connection string format
            snowflake_config = self.get_snowflake_config()
            return (
                f"snowflake://{snowflake_config.get('user', '')}:"
                f"{snowflake_config.get('password', '')}@"
                f"{snowflake_config.get('account', '')}/"
                f"{snowflake_config.get('database', '')}/"
                f"{snowflake_config.get('schema', '')}?"
                f"warehouse={snowflake_config.get('warehouse', '')}&"
                f"role={snowflake_config.get('role', '')}"
            )
    
    def get_dbt_target(self) -> str:
        """Get dbt target name based on warehouse type"""
        if self.is_redshift():
            return 'redshift'
        else:
            return 'snowflake'
    
    def get_config(self) -> Dict[str, Any]:
        """Get full config dictionary"""
        return self.config
    
    def get_initial_load_date(self) -> str:
        """Get initial GTFS load date from config"""
        return self.config.get('data_sources', {}).get('gtfs', {}).get('initial_load_date', '2025-08-01')
    
    def is_incremental_enabled(self) -> bool:
        """Check if incremental loading is enabled"""
        return self.config.get('data_sources', {}).get('gtfs', {}).get('incremental', True)
    
    def is_streaming_enabled(self) -> bool:
        """Check if streaming is enabled"""
        return self.config.get('data_sources', {}).get('transit_api', {}).get('streaming_enabled', True)

# Global instance
_warehouse_config = None

def get_warehouse_config() -> WarehouseConfig:
    """Get global warehouse config instance"""
    global _warehouse_config
    if _warehouse_config is None:
        _warehouse_config = WarehouseConfig()
    return _warehouse_config

