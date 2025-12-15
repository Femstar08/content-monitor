#!/usr/bin/env python3
"""
Script to sync data from Apify to local database
"""
import asyncio
import os
import sys
from database import ContentDatabase
from content_generator import ContentGenerator

async def main():
    """Main sync function."""
    if len(sys.argv) < 2:
        print("Usage: python sync_apify_data.py <apify_run_id>")
        print("Example: python sync_apify_data.py abc123def456")
        sys.exit(1)
    
    run_id = sys.argv[1]
    apify_token = os.getenv("APIFY_TOKEN")
    
    if not apify_token:
        print("Error: APIFY_TOKEN environment variable not set")
        print("Set it with: export APIFY_TOKEN=your_token_here")
        sys.exit(1)
    
    print(f"🔄 Syncing data from Apify run: {run_id}")
    
    # Initialize database
    db = ContentDatabase()
    
    try:
        # Fetch and store data
        await db.fetch_and_store_apify_data(apify_token, run_id)
        print("✅ Data synced successfully!")
        
        # Show summary
        content = db.get_all_content()
        print(f"📊 Total content items in database: {len(content)}")
        
        if content:
            print("\n📝 Recent content:")
            for item in content[:5]:
                print(f"  • {item.get('title', 'Untitled')[:60]}...")
        
        # Generate sample content
        print("\n🎯 Generating sample blog post...")
        generator = ContentGenerator()
        
        if len(content) >= 3:
            blog_post = generator.generate_blog_post(content[:5], "security")
            print(f"✅ Generated: {blog_post['title']}")
            print(f"📖 Word count: {blog_post['word_count']}")
            print(f"⏱️ Reading time: {blog_post['reading_time']} minutes")
        
    except Exception as e:
        print(f"❌ Error syncing data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())