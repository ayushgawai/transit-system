#!/usr/bin/env python3
"""
Continuous Streaming Service
Runs in background, continuously fetching streaming data from TransitApp API
"""
import sys
import time
import signal
from pathlib import Path
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('streaming_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import the streaming fetch function
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestion.fetch_streaming_data import fetch_and_save_streaming_data

# Global flag for graceful shutdown
running = True

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    global running
    logger.info("Received shutdown signal, stopping streaming service...")
    running = False

def main():
    """Main streaming service loop"""
    global running
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting continuous streaming service...")
    logger.info("Fetch interval: 60 seconds")
    logger.info("Press Ctrl+C to stop")
    
    fetch_count = 0
    error_count = 0
    
    while running:
        try:
            logger.info(f"Fetching streaming data (attempt {fetch_count + 1})...")
            result = fetch_and_save_streaming_data()
            
            if result and result.get('success'):
                count = result.get('count', 0)
                fetch_count += 1
                logger.info(f"✅ Successfully fetched {count} streaming records (total fetches: {fetch_count})")
                error_count = 0  # Reset error count on success
            else:
                error_count += 1
                logger.warning(f"⚠️ Fetch returned no data (errors: {error_count})")
                
        except Exception as e:
            error_count += 1
            logger.error(f"❌ Error fetching streaming data: {str(e)} (errors: {error_count})")
            
            # If too many consecutive errors, wait longer
            if error_count >= 5:
                logger.warning("Too many consecutive errors, waiting 5 minutes before retry...")
                for _ in range(300):  # 5 minutes
                    if not running:
                        break
                    time.sleep(1)
                error_count = 0
        
        # Wait 60 seconds before next fetch (respects rate limits)
        if running:
            for _ in range(60):
                if not running:
                    break
                time.sleep(1)
    
    logger.info("Streaming service stopped")

if __name__ == "__main__":
    main()

