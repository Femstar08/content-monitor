# AWS Content Monitor

A flexible document monitoring system that tracks changes across AWS content and generates intelligence digests.

## Features

- **Flexible Resource Profiles**: Define exactly what AWS content to monitor
- **Automated Content Discovery**: Discover content from RSS feeds and user-defined sources
- **Change Detection**: Track changes at the section level with impact scoring
- **Intelligence Digests**: Generate human-readable reports explaining what changed and why it matters
- **Multiple Output Formats**: Text, HTML, PDF, and JSON outputs
- **Apify Compatible**: Structured output schema for integration with Apify platform

## Usage

### As an Apify Actor

1. **Global AWS Monitoring**: Monitor all AWS announcements and documentation
2. **Resource Profile Mode**: Monitor specific AWS document collections
3. **Custom URL Mode**: Monitor any set of AWS-related URLs

### Input Configuration

```json
{
  "mode": "global",
  "reportingPeriod": {
    "startDate": "2024-01-01",
    "endDate": "2024-01-31"
  },
  "scrapingConfig": {
    "maxDepth": 2,
    "includeDownloads": true,
    "allowedDomains": ["aws.amazon.com", "docs.aws.amazon.com"]
  },
  "outputConfig": {
    "generateDigest": true,
    "outputFormats": ["text", "json"],
    "includeRawData": false
  }
}
```

### Output Schema

The actor outputs structured data compatible with Apify's dataset format:

- **Content Sources**: Discovered AWS content with metadata
- **Changes**: Detected changes with classification and impact scores
- **Digests**: Intelligence reports with human-readable summaries
- **Execution Summary**: Metrics and status information

## Architecture

The system follows a modular pipeline architecture:

1. **Resource Profile Manager**: Manages user-defined monitoring configurations
2. **Source Discovery Engine**: Discovers content from feeds and profiles
3. **Content Extractor**: Normalizes content from various formats
4. **Version Manager**: Tracks document versions and changes
5. **Change Detector**: Identifies and classifies changes
6. **Intelligence Digest Generator**: Creates human-readable reports

## Development

### Setup

```bash
pip install -r requirements.txt
pip install -e .
```

### Testing

```bash
pytest
```

### Running Locally

```bash
python -m src.main
```

## License

MIT License
