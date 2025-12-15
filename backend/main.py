"""
FastAPI backend for AWS Content Monitor UI with Apify integration
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List, Optional
import uvicorn
import os
import httpx
import asyncio
from database import ContentDatabase

app = FastAPI(title="AWS Content Monitor API", version="1.0.0")

# Configuration
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
APIFY_ACTOR_ID = os.getenv("APIFY_ACTOR_ID", "aws-content-monitor")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:3002").split(",")

# Initialize database
db = ContentDatabase()

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

@app.post("/api/apify/sync/{run_id}")
async def sync_apify_data(run_id: str, background_tasks: BackgroundTasks):
    """Sync data from Apify run to database."""
    if not APIFY_TOKEN:
        raise HTTPException(status_code=500, detail="Apify token not configured")
    
    background_tasks.add_task(db.fetch_and_store_apify_data, APIFY_TOKEN, run_id)
    
    return {
        "success": True,
        "message": f"Started syncing data from run {run_id}",
        "run_id": run_id
    }

@app.get("/api/content")
async def get_all_content(limit: Optional[int] = 50):
    """Get all extracted content from database."""
    try:
        content = db.get_all_content()
        if limit:
            content = content[:limit]
        
        return {
            "success": True,
            "data": content,
            "total": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/content/search")
async def search_content(q: str, limit: Optional[int] = 20):
    """Search content by query."""
    try:
        results = db.search_content(q)
        if limit:
            results = results[:limit]
        
        return {
            "success": True,
            "data": results,
            "total": len(results),
            "query": q
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/content/topic/{topic}")
async def get_content_by_topic(topic: str, limit: Optional[int] = 20):
    """Get content filtered by topic."""
    try:
        results = db.get_content_by_topic(topic)
        if limit:
            results = results[:limit]
        
        return {
            "success": True,
            "data": results,
            "total": len(results),
            "topic": topic
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/generate")
async def generate_content_from_data(request: dict):
    """Generate new content from extracted data."""
    try:
        topic = request.get("topic", "")
        content_type = request.get("type", "article")  # article, summary, guide
        
        # Get relevant content from database
        if topic:
            source_content = db.get_content_by_topic(topic)
        else:
            source_content = db.get_all_content()[:10]  # Get recent content
        
        if not source_content:
            raise HTTPException(status_code=404, detail="No content found for the specified topic")
        
        # Generate new content based on extracted data
        generated_content = await generate_article_from_sources(source_content, topic, content_type)
        
        return {
            "success": True,
            "data": {
                "generated_content": generated_content,
                "source_count": len(source_content),
                "topic": topic,
                "type": content_type
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def generate_article_from_sources(sources: List[dict], topic: str, content_type: str) -> dict:
    """Generate article content from source materials."""
    # Combine all text content
    combined_text = ""
    source_titles = []
    key_topics = {}
    
    for source in sources[:5]:  # Use top 5 sources
        if source.get('text_content'):
            combined_text += source['text_content'] + "\n\n"
        if source.get('title'):
            source_titles.append(source['title'])
        
        # Aggregate topics
        if source.get('topics'):
            for topic_item in source['topics']:
                topic_name = topic_item.get('topic', '')
                mentions = topic_item.get('mentions', 0)
                key_topics[topic_name] = key_topics.get(topic_name, 0) + mentions
    
    # Sort topics by mentions
    sorted_topics = sorted(key_topics.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Generate title
    if topic:
        title = f"AWS {topic.title()} Guide: Best Practices and Implementation"
    else:
        top_topic = sorted_topics[0][0] if sorted_topics else "AWS"
        title = f"AWS {top_topic.title()} Guide: Comprehensive Overview"
    
    # Generate introduction
    intro = f"This guide provides comprehensive insights into AWS {topic or 'services'} based on official AWS documentation and best practices. "
    intro += f"The information is compiled from {len(sources)} official AWS sources including whitepapers, documentation, and architectural guides."
    
    # Generate key points
    key_points = []
    for topic_name, mentions in sorted_topics[:5]:
        key_points.append(f"• {topic_name.title()}: Mentioned {mentions} times across sources")
    
    # Generate sections based on content
    sections = []
    if 'security' in [t[0] for t in sorted_topics]:
        sections.append({
            "title": "Security Best Practices",
            "content": "AWS provides comprehensive security features and best practices to protect your applications and data..."
        })
    
    if 'architecture' in [t[0] for t in sorted_topics]:
        sections.append({
            "title": "Architecture Guidelines",
            "content": "Well-architected AWS solutions follow key principles including operational excellence, security, reliability..."
        })
    
    # Generate conclusion
    conclusion = f"This guide synthesizes information from official AWS sources to provide actionable insights for {topic or 'AWS implementations'}. "
    conclusion += "Regular review of AWS documentation ensures alignment with current best practices and new service capabilities."
    
    return {
        "title": title,
        "introduction": intro,
        "key_topics": sorted_topics,
        "key_points": key_points,
        "sections": sections,
        "conclusion": conclusion,
        "sources": source_titles,
        "word_count": len(combined_text.split()),
        "generated_at": datetime.now().isoformat()
    }

@app.get("/api/system/health")
async def get_system_health():
    """Health check endpoint."""
    apify_status = "configured" if APIFY_TOKEN else "not_configured"
    
    # Check database
    try:
        content_count = len(db.get_all_content())
        db_status = "connected"
    except Exception:
        content_count = 0
        db_status = "error"
    
    return {
        "success": True, 
        "data": {
            "status": "healthy",
            "details": {
                "api_server": "running",
                "apify_integration": apify_status,
                "database": db_status,
                "content_items": content_count,
                "last_check": datetime.now().isoformat()
            }
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)