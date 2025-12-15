"""
Main entry point for AWS Content Monitor.
"""
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

from .models.base import DateRange
from .models.apify_schema import ApifyOutputAdapter
from .utils.logger import setup_logger


def load_input() -> Dict[str, Any]:
    """Load input configuration from Apify or command line."""
    # Try to load from Apify input first
    input_path = os.environ.get('APIFY_INPUT_PATH', './apify_storage/key_value_stores/default/INPUT.json')
    
    if os.path.exists(input_path):
        with open(input_path, 'r') as f:
            return json.load(f)
    
    # Fallback to default configuration for development
    return {
        "mode": "global",
        "reportingPeriod": {
            "startDate": "2024-01-01",
            "endDate": "2024-01-31"
        },
        "scrapingConfig": {
            "maxDepth": 2,
            "includeDownloads": True,
            "allowedDomains": ["aws.amazon.com", "docs.aws.amazon.com"]
        },
        "outputConfig": {
            "generateDigest": True,
            "outputFormats": ["text", "json"],
            "includeRawData": False
        }
    }


def save_output(data: Any, filename: str = None) -> None:
    """Save output data to Apify dataset or local file."""
    # Try to use Apify dataset first
    try:
        from apify import Actor
        Actor.push_data(data)
        return
    except ImportError:
        pass
    
    # Fallback to local file output
    output_dir = os.environ.get('APIFY_DEFAULT_DATASET_PATH', './output')
    os.makedirs(output_dir, exist_ok=True)
    
    if filename is None:
        filename = f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    output_path = os.path.join(output_dir, filename)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"Output saved to: {output_path}")


async def main():
    """Main execution function."""
    logger = setup_logger()
    logger.info("Starting AWS Content Monitor")
    
    try:
        # Load input configuration
        input_config = load_input()
        logger.info(f"Loaded configuration: {input_config}")
        
        # Parse reporting period
        period_config = input_config["reportingPeriod"]
        reporting_period = DateRange(
            start_date=datetime.fromisoformat(period_config["startDate"]),
            end_date=datetime.fromisoformat(period_config["endDate"])
        )
        
        # Initialize execution result
        execution_result = {
            "execution_id": f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "started_at": datetime.now().isoformat(),
            "mode": input_config["mode"],
            "status": "running",
            "sources_discovered": 0,
            "content_extracted": 0,
            "changes_detected": 0,
            "digest_generated": False,
            "errors": []
        }
        
        # TODO: Implement actual processing logic
        # This is a placeholder for the core implementation
        logger.info("Processing logic will be implemented in subsequent tasks")
        
        # For now, create a sample output to demonstrate the schema
        sample_output = {
            "execution_summary": {
                "execution_id": execution_result["execution_id"],
                "started_at": execution_result["started_at"],
                "completed_at": datetime.now().isoformat(),
                "status": "completed",
                "sources_discovered": 0,
                "content_extracted": 0,
                "changes_detected": 0,
                "digest_generated": False,
                "_scrapedAt": datetime.now().isoformat(),
                "_source": "aws-content-monitor"
            }
        }
        
        # Save output
        save_output(sample_output)
        
        logger.info("AWS Content Monitor completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        error_output = {
            "error": str(e),
            "status": "failed",
            "_scrapedAt": datetime.now().isoformat(),
            "_source": "aws-content-monitor"
        }
        save_output(error_output)
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())