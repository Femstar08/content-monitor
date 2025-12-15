# 🚀 Apify Actor Standalone Usage Guide

## Overview

Your Apify actor is a **completely independent scraping engine** that can run without your backend or frontend. Here's how to use it in different scenarios:

## 🎯 Deployment Options

### Option 1: Full Stack (All Components)

```
Frontend (Vercel) → Backend (VPS) → Apify Actor (Cloud)
```

**Best for**: Full-featured web application with user management

### Option 2: Backend + Apify Only

```
Backend (VPS) → Apify Actor (Cloud)
```

**Best for**: API-only service, integrations with other systems

### Option 3: Apify Actor Only (Standalone)

```
Apify Actor (Cloud) ← Direct API calls/Console/CLI
```

**Best for**: Simple scraping jobs, scheduled monitoring, one-off tasks

## 🔧 Standalone Usage Methods

### 1. Apify Console (Easiest)

1. Go to https://console.apify.com/actors
2. Find your "aws-content-monitor" actor
3. Click "Start"
4. Provide input JSON:

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
    "outputFormats": ["json"],
    "includeRawData": false
  }
}
```

5. Monitor progress and download results

### 2. Direct API Integration

Perfect for integrating with your own systems:

```python
import requests

# Your Apify credentials
APIFY_TOKEN = "your_token_here"
ACTOR_ID = "your_actor_id"

# Start a run
response = requests.post(
    f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs",
    headers={"Authorization": f"Bearer {APIFY_TOKEN}"},
    json={
        "mode": "profile",
        "startingUrls": ["https://aws.amazon.com/security/"],
        "scrapingConfig": {
            "maxDepth": 3,
            "includeDownloads": True,
            "allowedDomains": ["aws.amazon.com"]
        }
    }
)

run_id = response.json()["data"]["id"]
print(f"Started run: {run_id}")

# Get results later
results = requests.get(
    f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items",
    headers={"Authorization": f"Bearer {APIFY_TOKEN}"}
)

print("Results:", results.json())
```

### 3. Scheduled Monitoring

Set up automatic runs in Apify Console:

1. Go to your actor → Schedules
2. Create new schedule (e.g., daily at 6 AM)
3. Set input configuration
4. Actor runs automatically, no backend needed

### 4. Webhook Triggers

Configure webhooks to trigger runs:

```bash
# Set up webhook in Apify Console, then trigger with:
curl -X POST "https://api.apify.com/v2/webhooks/YOUR_WEBHOOK_ID" \
  -d '{"customData": {"urgent": true}}'
```

## 📊 Input Configuration Options

### Global Mode (Monitor Everything)

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
  }
}
```

### Profile Mode (Specific Monitoring)

```json
{
  "mode": "profile",
  "profileId": "security-updates",
  "startingUrls": ["https://aws.amazon.com/security/"],
  "scrapingConfig": {
    "maxDepth": 3,
    "includeDownloads": true,
    "allowedDomains": ["aws.amazon.com"]
  },
  "exclusionRules": {
    "keywords": ["archived", "deprecated"]
  }
}
```

### Custom Mode (Advanced)

```json
{
  "mode": "custom",
  "startingUrls": [
    "https://docs.aws.amazon.com/whitepapers/",
    "https://aws.amazon.com/blogs/security/"
  ],
  "scrapingConfig": {
    "maxDepth": 1,
    "includeDownloads": false,
    "allowedDomains": ["aws.amazon.com", "docs.aws.amazon.com"],
    "fileTypes": ["pdf", "html"]
  },
  "outputConfig": {
    "generateDigest": false,
    "outputFormats": ["json", "csv"],
    "includeRawData": true
  }
}
```

## 📈 Output Data Structure

The actor outputs structured data regardless of how it's triggered:

```json
{
  "execution_summary": {
    "execution_id": "exec_20240115_143025",
    "started_at": "2024-01-15T14:30:25Z",
    "completed_at": "2024-01-15T14:45:30Z",
    "status": "completed",
    "sources_discovered": 42,
    "content_extracted": 38,
    "changes_detected": 5,
    "digest_generated": true
  },
  "sources": [...],
  "changes": [...],
  "digest": "..."
}
```

## 🔄 Integration Patterns

### Pattern 1: Standalone Monitoring

- Deploy only the Apify actor
- Set up scheduled runs
- Download results manually or via API
- **Cost**: Lowest (only Apify usage)

### Pattern 2: API Integration

- Deploy Apify actor + your own simple API
- Trigger runs programmatically
- Process results in your system
- **Cost**: Low (Apify + minimal server)

### Pattern 3: Full Application

- Deploy all three components
- Rich UI for management
- User accounts and profiles
- **Cost**: Higher (full infrastructure)

## 💡 When to Use Standalone

**Perfect for:**

- One-off monitoring projects
- Simple scheduled checks
- Integration with existing systems
- Cost-sensitive deployments
- Quick prototyping

**Not ideal for:**

- Multiple users needing different configurations
- Complex user management
- Real-time dashboards
- Frequent manual interactions

## 🚀 Quick Start (Standalone)

1. **Deploy Actor**: `./deploy-apify.sh`
2. **Test Run**: Use Apify Console with sample input
3. **Set Schedule**: Configure automatic runs
4. **Get Results**: Download from Apify or use API

**That's it! No backend or frontend needed.**

## 📞 Support & Monitoring

- **Apify Console**: Monitor all runs, logs, and results
- **API Access**: Full programmatic control
- **Webhooks**: Get notified when runs complete
- **Logs**: Detailed execution logs in Apify Console

Your actor is completely self-contained and production-ready! 🎉
