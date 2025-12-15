"""
FastAPI backend for AWS Content Monitor UI with Apify integration
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List, Optional
import uvicorn
import os
import httpx
import asyncio

app = FastAPI(title="AWS Content Monitor API", version="1.0.0")

# Configuration
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
APIFY_ACTOR_ID = os.getenv("APIFY_ACTOR_ID", "aws-content-monitor")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:3002").split(",")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
mock_data = {
    "dashboard_metrics": {
        "total_profiles": 5,
        "active_profiles": 3,
        "total_sources": 42,
        "recent_changes": 12,
        "last_execution": datetime.now().isoformat(),
        "system_health": "healthy"
    },
    "profiles": [
        {
            "id": "1",
            "name": "AWS Security Updates",
            "starting_urls": ["https://aws.amazon.com/security/"],
            "inclusion_rules": {
                "domains": ["aws.amazon.com"],
                "url_patterns": [],
                "file_types": [],
                "content_types": []
            },
            "exclusion_rules": {
                "domains": [],
                "url_patterns": [],
                "file_types": [],
                "keywords": []
            },
            "scraping_depth": 2,
            "include_downloads": True,
            "track_changes": True,
            "check_frequency": "0 0 * * *",
            "generate_digest": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": "2",
            "name": "AWS Documentation",
            "starting_urls": ["https://docs.aws.amazon.com/"],
            "inclusion_rules": {
                "domains": ["docs.aws.amazon.com"],
                "url_patterns": [],
                "file_types": ["pdf"],
                "content_types": []
            },
            "exclusion_rules": {
                "domains": [],
                "url_patterns": [],
                "file_types": [],
                "keywords": []
            },
            "scraping_depth": 3,
            "include_downloads": True,
            "track_changes": True,
            "check_frequency": "0 6 * * *",
            "generate_digest": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ],
    "changes": [
        {
            "id": "1",
            "source_id": "src1",
            "change_type": "modified",
            "section_id": "Security Best Practices",
            "old_content": "Previous security guidelines for IAM policies...",
            "new_content": "Updated security guidelines with new IAM policy recommendations...",
            "detected_at": datetime.now().isoformat(),
            "impact_score": 0.8,
            "classification": "security",
            "confidence_score": 0.9
        },
        {
            "id": "2",
            "source_id": "src2",
            "change_type": "added",
            "section_id": "New AWS Service Launch",
            "old_content": None,
            "new_content": "AWS announces new machine learning service for document analysis...",
            "detected_at": datetime.now().isoformat(),
            "impact_score": 0.6,
            "classification": "feature",
            "confidence_score": 0.85
        },
        {
            "id": "3",
            "source_id": "src1",
            "change_type": "removed",
            "section_id": "Deprecated API Methods",
            "old_content": "Legacy API methods that will be discontinued...",
            "new_content": None,
            "detected_at": datetime.now().isoformat(),
            "impact_score": 0.7,
            "classification": "deprecation",
            "confidence_score": 0.95
        }
    ]
}

@app.get("/")
async def root():
    return {"message": "AWS Content Monitor API", "status": "running"}

@app.get("/api/dashboard/metrics")
async def get_dashboard_metrics():
    return {"success": True, "data": mock_data["dashboard_metrics"]}

@app.get("/api/profiles")
async def get_profiles():
    return {"success": True, "data": mock_data["profiles"]}

@app.get("/api/profiles/{profile_id}")
async def get_profile(profile_id: str):
    profile = next((p for p in mock_data["profiles"] if p["id"] == profile_id), None)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"success": True, "data": profile}

@app.post("/api/profiles")
async def create_profile(profile_data: dict):
    # In a real implementation, you'd validate and save the profile
    new_profile = {
        "id": str(len(mock_data["profiles"]) + 1),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        **profile_data
    }
    mock_data["profiles"].append(new_profile)
    return {"success": True, "data": new_profile}

@app.get("/api/changes")
async def get_changes(
    profile_id: Optional[str] = None,
    classification: Optional[str] = None,
    limit: Optional[int] = None
):
    changes = mock_data["changes"]
    
    # Apply filters
    if classification:
        changes = [c for c in changes if c["classification"] == classification]
    
    if limit:
        changes = changes[:limit]
    
    return {"success": True, "data": changes}

@app.get("/api/changes/recent")
async def get_recent_changes(limit: int = 10):
    return {"success": True, "data": mock_data["changes"][:limit]}

@app.post("/api/profiles/{profile_id}/run")
async def run_profile_monitoring(profile_id: str):
    """Trigger Apify actor run for a specific profile."""
    profile = next((p for p in mock_data["profiles"] if p["id"] == profile_id), None)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    if not APIFY_TOKEN:
        raise HTTPException(status_code=500, detail="Apify token not configured")
    
    # Prepare input for Apify actor
    actor_input = {
        "mode": "profile",
        "profileId": profile_id,
        "startingUrls": profile["starting_urls"],
        "scrapingConfig": {
            "maxDepth": profile["scraping_depth"],
            "includeDownloads": profile["include_downloads"],
            "allowedDomains": profile["inclusion_rules"]["domains"]
        },
        "outputConfig": {
            "generateDigest": profile["generate_digest"],
            "outputFormats": ["json"],
            "includeRawData": False
        }
    }
    
    # Call Apify API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"https://api.apify.com/v2/acts/{APIFY_ACTOR_ID}/runs",
                headers={"Authorization": f"Bearer {APIFY_TOKEN}"},
                json=actor_input,
                timeout=30.0
            )
            response.raise_for_status()
            run_data = response.json()
            
            return {
                "success": True,
                "data": {
                    "run_id": run_data["data"]["id"],
                    "status": run_data["data"]["status"],
                    "started_at": run_data["data"]["startedAt"],
                    "profile_id": profile_id
                }
            }
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Failed to start Apify run: {str(e)}")

@app.get("/api/runs/{run_id}/status")
async def get_run_status(run_id: str):
    """Get status of an Apify actor run."""
    if not APIFY_TOKEN:
        raise HTTPException(status_code=500, detail="Apify token not configured")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://api.apify.com/v2/actor-runs/{run_id}",
                headers={"Authorization": f"Bearer {APIFY_TOKEN}"},
                timeout=30.0
            )
            response.raise_for_status()
            run_data = response.json()
            
            return {
                "success": True,
                "data": {
                    "run_id": run_id,
                    "status": run_data["data"]["status"],
                    "started_at": run_data["data"]["startedAt"],
                    "finished_at": run_data["data"].get("finishedAt"),
                    "stats": run_data["data"].get("stats", {})
                }
            }
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Failed to get run status: {str(e)}")

@app.get("/api/runs/{run_id}/results")
async def get_run_results(run_id: str):
    """Get results from an Apify actor run."""
    if not APIFY_TOKEN:
        raise HTTPException(status_code=500, detail="Apify token not configured")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items",
                headers={"Authorization": f"Bearer {APIFY_TOKEN}"},
                timeout=30.0
            )
            response.raise_for_status()
            results = response.json()
            
            return {
                "success": True,
                "data": results
            }
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Failed to get run results: {str(e)}")

@app.get("/api/system/health")
async def get_system_health():
    """Health check endpoint."""
    apify_status = "configured" if APIFY_TOKEN else "not_configured"
    
    return {
        "success": True, 
        "data": {
            "status": "healthy",
            "details": {
                "api_server": "running",
                "apify_integration": apify_status,
                "last_check": datetime.now().isoformat()
            }
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)