"""
Simple source discovery service for AWS Content Monitor.
"""
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
import logging


class SimpleSourceDiscovery:
    """Simple service for discovering AWS PDFs and documents."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_depth = config.get("maxDepth", 2)
        self.allowed_domains = config.get("allowedDomains", ["aws.amazon.com", "docs.aws.amazon.com"])
        self.include_downloads = config.get("includeDownloads", True)
        
    async def discover_sources(self, starting_urls: List[str]) -> List[Dict[str, Any]]:
        """Discover content sources from starting URLs."""
        discovered = []
        visited = set()
        
        print(f"Starting discovery from {len(starting_urls)} URLs")
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'AWS-Content-Monitor/1.0'}
        ) as session:
            for url in starting_urls:
                print(f"Crawling: {url}")
                sources = await self._crawl_url(session, url, 0, visited)
                discovered.extend(sources)
                print(f"Found {len(sources)} sources from {url}")
        
        # Remove duplicates
        unique_sources = []
        seen_urls = set()
        for source in discovered:
            if source["url"] not in seen_urls:
                unique_sources.append(source)
                seen_urls.add(source["url"])
        
        print(f"Total unique sources discovered: {len(unique_sources)}")
        return unique_sources
    
    async def _crawl_url(self, session: aiohttp.ClientSession, url: str, depth: int, visited: set) -> List[Dict[str, Any]]:
        """Crawl a URL and discover sources."""
        if depth > self.max_depth or url in visited:
            return []
        
        visited.add(url)
        sources = []
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"HTTP {response.status} for {url}")
                    return []
                
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find PDF and document links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    
                    if self._is_valid_source(full_url):
                        title = link.get_text(strip=True) or link.get('title', '') or "Untitled"
                        
                        # Try to get more context from surrounding elements
                        parent = link.parent
                        if parent and not title.strip():
                            title = parent.get_text(strip=True)[:100] or "Untitled"
                        
                        source_info = {
                            "url": full_url,
                            "title": title[:200],  # Limit title length
                            "source_type": self._get_source_type(full_url),
                            "discovered_from": url,
                            "depth": depth,
                            "file_size": None,
                            "_scrapedAt": datetime.now().isoformat(),
                            "_source": "aws-content-monitor"
                        }
                        sources.append(source_info)
                        print(f"Found source: {title[:50]}... ({full_url})")
                
                # Continue crawling if within depth limit
                if depth < self.max_depth:
                    crawl_links = []
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(url, href)
                        
                        if self._should_crawl(full_url) and full_url not in visited:
                            crawl_links.append(full_url)
                    
                    # Limit concurrent crawling to avoid overwhelming servers
                    for i in range(0, min(len(crawl_links), 10), 5):  # Max 10 links, batch of 5
                        batch = crawl_links[i:i+5]
                        tasks = [self._crawl_url(session, link_url, depth + 1, visited) for link_url in batch]
                        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        for result in batch_results:
                            if isinstance(result, list):
                                sources.extend(result)
        
        except asyncio.TimeoutError:
            print(f"Timeout crawling {url}")
        except Exception as e:
            print(f"Failed to crawl {url}: {e}")
        
        return sources
    
    def _is_valid_source(self, url: str) -> bool:
        """Check if URL is a valid source to extract."""
        parsed = urlparse(url)
        
        # Check domain
        if not any(domain in parsed.netloc for domain in self.allowed_domains):
            return False
        
        url_lower = url.lower()
        
        # Check file type
        if self.include_downloads:
            return (url_lower.endswith('.pdf') or 
                   url_lower.endswith('.docx') or 
                   url_lower.endswith('.doc') or
                   'whitepaper' in url_lower or
                   'documentation' in url_lower or
                   '/guides/' in url_lower or
                   '/best-practices/' in url_lower)
        
        return ('documentation' in url_lower or 
                'whitepaper' in url_lower or
                '/guides/' in url_lower)
    
    def _should_crawl(self, url: str) -> bool:
        """Check if URL should be crawled for more links."""
        parsed = urlparse(url)
        
        # Only crawl allowed domains
        if not any(domain in parsed.netloc for domain in self.allowed_domains):
            return False
        
        url_lower = url.lower()
        
        # Don't crawl direct file downloads
        if url_lower.endswith(('.pdf', '.docx', '.doc', '.zip', '.tar.gz', '.exe', '.dmg')):
            return False
        
        # Skip certain paths that are unlikely to contain useful content
        skip_paths = ['/search', '/login', '/signup', '/cart', '/checkout', '/account', '/contact']
        if any(skip_path in url_lower for skip_path in skip_paths):
            return False
        
        return True
    
    def _get_source_type(self, url: str) -> str:
        """Determine the type of source."""
        url_lower = url.lower()
        if url_lower.endswith('.pdf'):
            return 'pdf'
        elif url_lower.endswith(('.docx', '.doc')):
            return 'document'
        elif 'whitepaper' in url_lower:
            return 'whitepaper'
        elif 'documentation' in url_lower or '/docs/' in url_lower:
            return 'documentation'
        elif '/guides/' in url_lower:
            return 'guide'
        elif '/best-practices/' in url_lower:
            return 'best-practice'
        else:
            return 'webpage'