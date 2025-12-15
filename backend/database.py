"""
Database integration for AWS Content Monitor
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any
import httpx


class ContentDatabase:
    """Database handler for extracted AWS content."""
    
    def __init__(self, db_path: str = "aws_content.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                source_type TEXT,
                discovered_from TEXT,
                depth INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Extracted content table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extracted_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                title TEXT,
                content_type TEXT,
                text_content TEXT,
                summary TEXT,
                topics TEXT, -- JSON string
                page_count INTEGER,
                file_size INTEGER,
                extracted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES sources (id)
            )
        """)
        
        # Execution runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT UNIQUE,
                mode TEXT,
                sources_discovered INTEGER,
                content_extracted INTEGER,
                status TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                apify_run_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def fetch_and_store_apify_data(self, apify_token: str, run_id: str):
        """Fetch data from Apify and store in database."""
        async with httpx.AsyncClient() as client:
            # Get dataset items
            response = await client.get(
                f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items",
                headers={"Authorization": f"Bearer {apify_token}"}
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch Apify data: {response.status_code}")
            
            data = response.json()
            
            # Store in database
            self.store_execution_data(data, run_id)
    
    def store_execution_data(self, data: List[Dict[str, Any]], apify_run_id: str):
        """Store execution data in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for item in data:
            if 'execution_summary' in item:
                # Store execution summary
                summary = item['execution_summary']
                cursor.execute("""
                    INSERT OR REPLACE INTO execution_runs 
                    (execution_id, mode, sources_discovered, content_extracted, status, 
                     started_at, completed_at, apify_run_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    summary.get('execution_id'),
                    'global',  # Default mode
                    summary.get('sources_discovered', 0),
                    summary.get('content_extracted', 0),
                    summary.get('status'),
                    summary.get('started_at'),
                    summary.get('completed_at'),
                    apify_run_id
                ))
            
            if 'sources' in item:
                # Store sources
                for source in item['sources']:
                    cursor.execute("""
                        INSERT OR IGNORE INTO sources 
                        (url, title, source_type, discovered_from, depth)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        source.get('url'),
                        source.get('title'),
                        source.get('source_type'),
                        source.get('discovered_from'),
                        source.get('depth', 0)
                    ))
            
            if 'extracted_content' in item:
                # Store extracted content
                for content in item['extracted_content']:
                    # Get source_id
                    cursor.execute("SELECT id FROM sources WHERE url = ?", (content.get('url'),))
                    source_row = cursor.fetchone()
                    source_id = source_row[0] if source_row else None
                    
                    cursor.execute("""
                        INSERT INTO extracted_content 
                        (source_id, title, content_type, text_content, summary, topics, 
                         page_count, file_size, extracted_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        source_id,
                        content.get('title'),
                        content.get('content_type'),
                        content.get('text_content'),
                        content.get('summary'),
                        json.dumps(content.get('topics', [])),
                        content.get('page_count'),
                        content.get('file_size'),
                        content.get('extracted_at')
                    ))
        
        conn.commit()
        conn.close()
    
    def get_all_content(self) -> List[Dict[str, Any]]:
        """Get all extracted content from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ec.*, s.url, s.source_type 
            FROM extracted_content ec
            LEFT JOIN sources s ON ec.source_id = s.id
            ORDER BY ec.created_at DESC
        """)
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            item = dict(zip(columns, row))
            if item['topics']:
                item['topics'] = json.loads(item['topics'])
            results.append(item)
        
        conn.close()
        return results
    
    def search_content(self, query: str) -> List[Dict[str, Any]]:
        """Search content by query."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ec.*, s.url, s.source_type 
            FROM extracted_content ec
            LEFT JOIN sources s ON ec.source_id = s.id
            WHERE ec.title LIKE ? OR ec.text_content LIKE ? OR ec.summary LIKE ?
            ORDER BY ec.created_at DESC
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            item = dict(zip(columns, row))
            if item['topics']:
                item['topics'] = json.loads(item['topics'])
            results.append(item)
        
        conn.close()
        return results
    
    def get_content_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """Get content filtered by topic."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ec.*, s.url, s.source_type 
            FROM extracted_content ec
            LEFT JOIN sources s ON ec.source_id = s.id
            WHERE ec.topics LIKE ?
            ORDER BY ec.created_at DESC
        """, (f"%{topic}%",))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            item = dict(zip(columns, row))
            if item['topics']:
                item['topics'] = json.loads(item['topics'])
            results.append(item)
        
        conn.close()
        return results