# 🗄️ Database Integration Guide

## Overview

This guide shows you how to extract your Apify data into a database and create content from it.

## 🚀 Quick Start

### 1. Set Up Environment Variables

```bash
# In your backend directory
export APIFY_TOKEN="your_apify_token_here"
export APIFY_ACTOR_ID="your_actor_id"
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Sync Your Apify Data

```bash
# Replace 'your_run_id' with your actual Apify run ID
python sync_apify_data.py your_run_id
```

### 4. Start the Backend

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📊 Available API Endpoints

### **Content Management**

#### Get All Content

```bash
GET /api/content?limit=50
```

Returns all extracted content from database.

#### Search Content

```bash
GET /api/content/search?q=security&limit=20
```

Search content by keywords.

#### Get Content by Topic

```bash
GET /api/content/topic/security?limit=20
```

Filter content by specific AWS topics.

### **Content Generation**

#### Generate Blog Post

```bash
POST /api/content/generate
Content-Type: application/json

{
  "topic": "security",
  "type": "blog_post"
}
```

#### Generate Technical Guide

```bash
POST /api/content/generate
Content-Type: application/json

{
  "topic": "lambda",
  "type": "technical_guide"
}
```

#### Generate Summary Report

```bash
POST /api/content/generate
Content-Type: application/json

{
  "topic": "architecture",
  "type": "summary_report"
}
```

### **Data Synchronization**

#### Sync Apify Data

```bash
POST /api/apify/sync/{run_id}
```

Automatically sync data from an Apify run to your database.

## 🎯 Content Generation Examples

### Example 1: Generate Security Blog Post

```python
import requests

response = requests.post("http://localhost:8000/api/content/generate", json={
    "topic": "security",
    "type": "blog_post"
})

blog_post = response.json()["data"]
print(f"Title: {blog_post['title']}")
print(f"Reading time: {blog_post['reading_time']} minutes")
print(f"Sections: {len(blog_post['sections'])}")
```

### Example 2: Search and Generate Content

```python
import requests

# Search for Lambda content
search_response = requests.get("http://localhost:8000/api/content/search?q=lambda")
lambda_content = search_response.json()["data"]

# Generate technical guide
guide_response = requests.post("http://localhost:8000/api/content/generate", json={
    "topic": "lambda",
    "type": "technical_guide"
})

guide = guide_response.json()["data"]
print(f"Guide: {guide['title']}")
print(f"Difficulty: {guide['difficulty']}")
print(f"Estimated time: {guide['estimated_time']}")
```

## 🔄 Automated Workflow

### Set Up Automatic Data Sync

1. **Run Apify Actor** (manually or scheduled)
2. **Get Run ID** from Apify Console
3. **Sync to Database**:
   ```bash
   python sync_apify_data.py <run_id>
   ```
4. **Generate Content** via API calls

### Frontend Integration

Update your frontend to use the new endpoints:

```typescript
// Get all content
const getContent = async () => {
  const response = await fetch("/api/content?limit=20");
  const data = await response.json();
  return data.data;
};

// Search content
const searchContent = async (query: string) => {
  const response = await fetch(`/api/content/search?q=${query}`);
  const data = await response.json();
  return data.data;
};

// Generate blog post
const generateBlogPost = async (topic: string) => {
  const response = await fetch("/api/content/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic, type: "blog_post" }),
  });
  const data = await response.json();
  return data.data;
};
```

## 📈 Content Types You Can Generate

### 1. **Blog Posts**

- SEO-optimized titles and meta descriptions
- Multiple sections with structured content
- Reading time estimates
- Related tags and topics

### 2. **Technical Guides**

- Step-by-step implementation instructions
- Prerequisites and requirements
- Best practices and troubleshooting
- Difficulty assessment and time estimates

### 3. **Summary Reports**

- Executive summaries
- Key findings and recommendations
- Metrics and analytics
- Source attribution

## 🎨 Customization Options

### Custom Content Templates

You can modify `content_generator.py` to create custom content types:

```python
def generate_custom_content(self, sources, topic):
    # Your custom content generation logic
    return {
        "type": "custom",
        "title": "Custom Content Title",
        "content": "Generated content...",
        # Add your custom fields
    }
```

### Database Schema Extensions

Extend the database schema in `database.py`:

```python
# Add new table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS custom_content (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
```

## 🔍 Database Structure

### Tables Created:

1. **sources** - Discovered URLs and metadata
2. **extracted_content** - Processed content with summaries and topics
3. **execution_runs** - Apify run tracking and statistics

### Sample Queries:

```sql
-- Get most mentioned topics
SELECT json_extract(topics, '$[0].topic') as topic,
       COUNT(*) as frequency
FROM extracted_content
GROUP BY topic
ORDER BY frequency DESC;

-- Find security-related content
SELECT title, summary
FROM extracted_content
WHERE topics LIKE '%security%';

-- Get content by source type
SELECT source_type, COUNT(*) as count
FROM sources
GROUP BY source_type;
```

## 🚀 Production Deployment

### Environment Variables for Production:

```bash
# .env file
APIFY_TOKEN=your_production_token
APIFY_ACTOR_ID=your_actor_id
DATABASE_URL=postgresql://user:pass@host:port/dbname  # For PostgreSQL
CORS_ORIGINS=https://your-frontend-domain.com
```

### Database Migration to PostgreSQL:

For production, consider migrating from SQLite to PostgreSQL:

```python
# Update database.py to use PostgreSQL
import psycopg2
from psycopg2.extras import RealDictCursor

class ContentDatabase:
    def __init__(self, db_url: str):
        self.db_url = db_url
        # PostgreSQL connection logic
```

## ✅ Success Metrics

After setup, you should be able to:

- ✅ Sync Apify data to your database
- ✅ Search and filter extracted content
- ✅ Generate blog posts from AWS documentation
- ✅ Create technical guides and reports
- ✅ Access content via REST API
- ✅ Integrate with your frontend application

## 🆘 Troubleshooting

### Common Issues:

1. **Database not found**: Run the sync script to initialize
2. **No content generated**: Ensure you have synced Apify data first
3. **API errors**: Check that the backend is running on port 8000
4. **Empty results**: Verify your Apify run contains extracted content

### Debug Commands:

```bash
# Check database content
python -c "from database import ContentDatabase; db = ContentDatabase(); print(len(db.get_all_content()))"

# Test content generation
python -c "from content_generator import ContentGenerator; print('Generator loaded successfully')"

# Check API health
curl http://localhost:8000/api/system/health
```

Your AWS content is now ready to be transformed into valuable, structured content! 🎯
