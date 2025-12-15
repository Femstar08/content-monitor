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
            raw_input = json.load(f)
    else:
        # Fallback to default configuration for development
        raw_input = {
            "mode": "global",
            "startDate": "2024-01-01",
            "endDate": "2024-01-31",
            "maxDepth": 2,
            "includeDownloads": True,
            "allowedDomains": "aws.amazon.com\ndocs.aws.amazon.com",
            "generateDigest": True,
            "outputFormats": "text,json",
            "includeRawData": False
        }
    
    # Transform flat input to structured format
    return transform_input(raw_input)


def transform_input(raw_input: Dict[str, Any]) -> Dict[str, Any]:
    """Transform flat Apify input to structured format."""
    # Parse custom URLs from textarea
    custom_urls = []
    if raw_input.get("customUrls"):
        custom_urls = [url.strip() for url in raw_input["customUrls"].split('\n') if url.strip()]
    
    # Parse allowed domains from textarea
    allowed_domains = ["aws.amazon.com", "docs.aws.amazon.com"]  # default
    if raw_input.get("allowedDomains"):
        allowed_domains = [domain.strip() for domain in raw_input["allowedDomains"].split('\n') if domain.strip()]
    
    # Parse output formats from comma-separated string
    output_formats = ["text", "json"]  # default
    if raw_input.get("outputFormats"):
        output_formats = [fmt.strip() for fmt in raw_input["outputFormats"].split(',') if fmt.strip()]
    
    # Return structured configuration
    return {
        "mode": raw_input.get("mode", "global"),
        "profileId": raw_input.get("profileId"),
        "customUrls": custom_urls,
        "reportingPeriod": {
            "startDate": raw_input.get("startDate", "2024-01-01"),
            "endDate": raw_input.get("endDate", "2024-01-31")
        },
        "scrapingConfig": {
            "maxDepth": raw_input.get("maxDepth", 2),
            "includeDownloads": raw_input.get("includeDownloads", True),
            "allowedDomains": allowed_domains
        },
        "outputConfig": {
            "generateDigest": raw_input.get("generateDigest", True),
            "outputFormats": output_formats,
            "includeRawData": raw_input.get("includeRawData", False)
        }
    }


async def save_output(data: Any, filename: str = None) -> None:
    """Save output data to Apify dataset or local file."""
    # Try to use Apify dataset first
    try:
        from apify import Actor
        await Actor.push_data(data)
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
        
        # Import services for actual processing
        from .services.simple_discovery import SimpleSourceDiscovery
        from .services.simple_extractor import SimpleContentExtractor
        
        # Initialize services
        discovery_service = SimpleSourceDiscovery(input_config["scrapingConfig"])
        extraction_service = SimpleContentExtractor(input_config["scrapingConfig"])
        
        logger.info("Starting source discovery...")
        
        # Determine starting URLs based on mode
        starting_urls = []
        if input_config["mode"] == "custom" and input_config["customUrls"]:
            starting_urls = input_config["customUrls"]
        elif input_config["mode"] == "profile" and input_config["profileId"]:
            # For profile mode, you'd load profile-specific URLs from a database
            # For now, use default AWS URLs
            starting_urls = ["https://aws.amazon.com/whitepapers/", "https://docs.aws.amazon.com/"]
        else:
            # Global mode - comprehensive AWS monitoring
            starting_urls = [
                "https://aws.amazon.com/whitepapers/",
                "https://docs.aws.amazon.com/",
                "https://aws.amazon.com/blogs/security/",
                "https://aws.amazon.com/architecture/",
                "https://aws.amazon.com/getting-started/"
            ]
        
        # Discover sources (PDFs and documents)
        discovered_sources = await discovery_service.discover_sources(starting_urls)
        execution_result["sources_discovered"] = len(discovered_sources)
        logger.info(f"Discovered {len(discovered_sources)} sources")
        
        # Extract content from discovered sources
        extracted_content = []
        for source in discovered_sources:
            try:
                content = await extraction_service.extract_content(source)
                if content:
                    extracted_content.append(content)
                    execution_result["content_extracted"] += 1
            except Exception as e:
                logger.warning(f"Failed to extract content from {source.get('url', 'unknown')}: {e}")
                execution_result["errors"].append(f"Extraction failed for {source.get('url', 'unknown')}: {str(e)}")
        
        logger.info(f"Extracted content from {len(extracted_content)} sources")
        
        # Create comprehensive output
        sample_output = {
            "execution_summary": {
                "execution_id": execution_result["execution_id"],
                "started_at": execution_result["started_at"],
                "completed_at": datetime.now().isoformat(),
                "status": "completed",
                "sources_discovered": execution_result["sources_discovered"],
                "content_extracted": execution_result["content_extracted"],
                "changes_detected": 0,  # TODO: Implement change detection
                "digest_generated": input_config["outputConfig"]["generateDigest"],
                "_scrapedAt": datetime.now().isoformat(),
                "_source": "aws-content-monitor"
            },
            "sources": discovered_sources,
            "extracted_content": extracted_content[:10],  # Limit output size
            "configuration": input_config
        }
        
        # Save output
        await save_output(sample_output)
        
        logger.info("AWS Content Monitor completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        error_output = {
            "error": str(e),
            "status": "failed",
            "_scrapedAt": datetime.now().isoformat(),
            "_source": "aws-content-monitor"
        }
        await save_output(error_output)
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())