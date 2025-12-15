"""
Source Discovery Engine for AWS Content Monitor.
"""
import uuid
import hashlib
from datetime import datetime
from typing import List, Set, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
import requests
import feedparser
from bs4 import BeautifulSoup
import re

from ..models.base import ResourceProfile, ContentSource, InclusionRules, ExclusionRules, ValidationError
from ..models.enums import SourceType


class SourceDiscoveryEngine:
    """Discovers and tracks content sources from both user-defined resources and AWS feeds."""
    
    def __init__(self, request_timeout: int = 30, max_retries: int = 3):
        """Initialize the source discovery engine."""
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self._discovered_sources: Dict[str, ContentSource] = {}
        self._url_hashes: Set[str] = set()  # For duplicate detection
        
        # Default AWS RSS feeds
        self.default_aws_feeds = [
            "https://aws.amazon.com/about-aws/whats-new/recent/feed/",
            "https://aws.amazon.com/blogs/aws/feed/",
            "https://aws.amazon.com/blogs/security/feed/",
            "https://aws.amazon.com/blogs/architecture/feed/"
        ]
    
    def _make_request(self, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with retry logic."""
        headers = {
            'User-Agent': 'AWS-Content-Monitor/1.0 (https://github.com/aws-content-monitor)'
        }
        kwargs.setdefault('headers', {}).update(headers)
        kwargs.setdefault('timeout', self.request_timeout)
        
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, **kwargs)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Wait before retry (exponential backoff)
                    import time
                    time.sleep(2 ** attempt)
                continue
        
        raise last_exception
    
    def _generate_source_id(self, url: str) -> str:
        """Generate a unique ID for a content source."""
        return str(uuid.uuid5(uuid.NAMESPACE_URL, url))
    
    def _url_hash(self, url: str) -> str:
        """Generate hash for URL to detect duplicates."""
        # Normalize URL for consistent hashing
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def is_duplicate(self, source: ContentSource) -> bool:
        """Check if a source is a duplicate."""
        url_hash = self._url_hash(source.url)
        return url_hash in self._url_hashes
    
    def _add_source(self, url: str, source_type: SourceType, 
                   profile_id: Optional[str] = None, 
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[ContentSource]:
        """Add a new content source if not duplicate."""
        url_hash = self._url_hash(url)
        
        if url_hash in self._url_hashes:
            return None  # Duplicate
        
        source = ContentSource(
            id=self._generate_source_id(url),
            url=url,
            source_type=source_type,
            profile_id=profile_id,
            discovered_at=datetime.utcnow(),
            last_checked=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        self._discovered_sources[source.id] = source
        self._url_hashes.add(url_hash)
        
        return source
    
    def validate_source(self, url: str) -> bool:
        """Validate if a URL is accessible and valid."""
        try:
            response = self._make_request(url)
            return response.status_code == 200
        except Exception:
            return False
    
    def discover_from_feeds(self, feed_urls: Optional[List[str]] = None) -> List[ContentSource]:
        """Discover content sources from RSS feeds."""
        if feed_urls is None:
            feed_urls = self.default_aws_feeds
        
        discovered = []
        
        for feed_url in feed_urls:
            try:
                # Parse RSS feed
                feed = feedparser.parse(feed_url)
                
                if feed.bozo:
                    continue  # Skip malformed feeds
                
                for entry in feed.entries:
                    # Extract URL from entry
                    url = getattr(entry, 'link', None)
                    if not url:
                        continue
                    
                    # Determine source type based on URL
                    source_type = self._determine_source_type(url)
                    
                    # Create metadata from feed entry
                    metadata = {
                        'title': getattr(entry, 'title', ''),
                        'summary': getattr(entry, 'summary', ''),
                        'published': getattr(entry, 'published', ''),
                        'feed_url': feed_url,
                        'tags': [tag.term for tag in getattr(entry, 'tags', [])]
                    }
                    
                    source = self._add_source(url, source_type, metadata=metadata)
                    if source:
                        discovered.append(source)
                
            except Exception as e:
                # Log error but continue with other feeds
                print(f"Warning: Failed to process feed {feed_url}: {e}")
                continue
        
        return discovered
    
    def discover_from_profile(self, profile: ResourceProfile) -> List[ContentSource]:
        """Discover content sources from a resource profile."""
        discovered = []
        
        # Start with the profile's starting URLs
        for url in profile.starting_urls:
            sources = self._discover_from_url(
                url, 
                profile.scraping_depth, 
                profile.inclusion_rules,
                profile.exclusion_rules,
                profile.include_downloads,
                profile.id
            )
            discovered.extend(sources)
        
        return discovered
    
    def _discover_from_url(self, url: str, depth: int, 
                          inclusion_rules: InclusionRules,
                          exclusion_rules: ExclusionRules,
                          include_downloads: bool,
                          profile_id: str,
                          visited: Optional[Set[str]] = None) -> List[ContentSource]:
        """Recursively discover sources from a URL with depth control."""
        if visited is None:
            visited = set()
        
        if depth <= 0 or url in visited:
            return []
        
        visited.add(url)
        discovered = []
        
        try:
            # Check if URL should be excluded
            if exclusion_rules.excludes_domain(url) or exclusion_rules.excludes_url_pattern(url):
                return []
            
            # Check if URL matches inclusion rules
            if not (inclusion_rules.matches_domain(url) and inclusion_rules.matches_url_pattern(url)):
                return []
            
            # Determine source type
            source_type = self._determine_source_type(url)
            
            # Add the current URL as a source
            source = self._add_source(url, source_type, profile_id=profile_id)
            if source:
                discovered.append(source)
            
            # If it's an HTML page, extract links for further discovery
            if source_type == SourceType.HTML and depth > 1:
                links = self.extract_links(url, inclusion_rules, exclusion_rules, include_downloads)
                
                for link in links:
                    child_sources = self._discover_from_url(
                        link, depth - 1, inclusion_rules, exclusion_rules,
                        include_downloads, profile_id, visited
                    )
                    discovered.extend(child_sources)
        
        except Exception as e:
            print(f"Warning: Failed to discover from {url}: {e}")
        
        return discovered
    
    def extract_links(self, url: str, inclusion_rules: InclusionRules,
                     exclusion_rules: ExclusionRules, include_downloads: bool) -> List[str]:
        """Extract links from a web page."""
        try:
            response = self._make_request(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            links = []
            
            # Extract all links
            for link_tag in soup.find_all('a', href=True):
                href = link_tag['href']
                
                # Convert relative URLs to absolute
                absolute_url = urljoin(url, href)
                
                # Skip non-HTTP URLs
                if not (absolute_url.startswith('http://') or absolute_url.startswith('https://')):
                    continue
                
                # Check inclusion/exclusion rules
                if exclusion_rules.excludes_domain(absolute_url) or exclusion_rules.excludes_url_pattern(absolute_url):
                    continue
                
                if not (inclusion_rules.matches_domain(absolute_url) and inclusion_rules.matches_url_pattern(absolute_url)):
                    continue
                
                # Check file type if it's a download
                if self._is_download_link(absolute_url):
                    if not include_downloads:
                        continue
                    
                    file_ext = self._get_file_extension(absolute_url)
                    if exclusion_rules.excludes_file_type(file_ext):
                        continue
                    
                    if not inclusion_rules.matches_file_type(file_ext):
                        continue
                
                links.append(absolute_url)
            
            return links
        
        except Exception as e:
            print(f"Warning: Failed to extract links from {url}: {e}")
            return []
    
    def _determine_source_type(self, url: str) -> SourceType:
        """Determine the source type based on URL."""
        url_lower = url.lower()
        
        if url_lower.endswith('.pdf'):
            return SourceType.PDF
        elif url_lower.endswith('.docx') or url_lower.endswith('.doc'):
            return SourceType.DOCX
        elif url_lower.endswith('.txt'):
            return SourceType.TXT
        elif 'rss' in url_lower or 'feed' in url_lower or url_lower.endswith('.xml'):
            return SourceType.RSS
        else:
            return SourceType.HTML
    
    def _is_download_link(self, url: str) -> bool:
        """Check if URL points to a downloadable file."""
        download_extensions = ['.pdf', '.doc', '.docx', '.txt', '.zip', '.tar', '.gz']
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in download_extensions)
    
    def _get_file_extension(self, url: str) -> str:
        """Get file extension from URL."""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        if '.' in path:
            return path.split('.')[-1]
        return ''
    
    def get_discovered_sources(self) -> List[ContentSource]:
        """Get all discovered sources."""
        return list(self._discovered_sources.values())
    
    def get_sources_by_profile(self, profile_id: str) -> List[ContentSource]:
        """Get sources discovered for a specific profile."""
        return [source for source in self._discovered_sources.values() 
                if source.profile_id == profile_id]
    
    def clear_discovered_sources(self) -> None:
        """Clear all discovered sources (useful for testing)."""
        self._discovered_sources.clear()
        self._url_hashes.clear()