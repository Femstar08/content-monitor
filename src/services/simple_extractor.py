"""
Simple content extraction service for AWS Content Monitor.
"""
from typing import Dict, Any, Optional
import aiohttp
import asyncio
from datetime import datetime
import PyPDF2
import io
import re


class SimpleContentExtractor:
    """Simple service for extracting content from PDFs and documents."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    async def extract_content(self, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract content from a source."""
        source_type = source.get("source_type", "unknown")
        url = source.get("url", "")
        
        print(f"Extracting content from {source_type}: {url}")
        
        try:
            # Handle PDF URLs specially
            if url.lower().endswith('.pdf'):
                return await self._extract_pdf_content(source)
            elif source_type in ["documentation", "webpage", "guide", "best-practice", "whitepaper"]:
                return await self._extract_web_content(source)
            else:
                print(f"Trying to extract as webpage: {source_type}")
                return await self._extract_web_content(source)
                
        except Exception as e:
            print(f"Failed to extract content from {url}: {e}")
            return None
    
    async def _extract_pdf_content(self, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract content from a PDF file."""
        url = source["url"]
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60),
                headers={'User-Agent': 'AWS-Content-Monitor/1.0'}
            ) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"Failed to download PDF: HTTP {response.status}")
                        return None
                    
                    pdf_data = await response.read()
                    
            # Extract text from PDF
            pdf_file = io.BytesIO(pdf_data)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = ""
            page_count = len(pdf_reader.pages)
            
            # Extract text from all pages (limit to first 50 pages to avoid huge files)
            max_pages = min(page_count, 50)
            for page_num in range(max_pages):
                page = pdf_reader.pages[page_num]
                text_content += page.extract_text() + "\n"
            
            # Clean up the text
            text_content = self._clean_text(text_content)
            
            # Extract key information
            title = source.get("title", "")
            if not title or title == "Untitled":
                # Try to extract title from PDF content
                title = self._extract_title_from_text(text_content)
            
            # Extract summary (first few sentences)
            summary = self._extract_summary(text_content)
            
            # Extract topics/keywords
            topics = self._extract_topics(text_content)
            
            return {
                "source_id": source.get("url", ""),
                "url": url,
                "title": title,
                "content_type": "pdf",
                "page_count": page_count,
                "file_size": len(pdf_data),
                "text_content": text_content[:10000],  # Limit content size
                "summary": summary,
                "topics": topics,
                "extracted_at": datetime.now().isoformat(),
                "_scrapedAt": datetime.now().isoformat(),
                "_source": "aws-content-monitor"
            }
            
        except Exception as e:
            print(f"Error extracting PDF content: {e}")
            return None
    
    async def _extract_web_content(self, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract content from a web page."""
        url = source["url"]
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'AWS-Content-Monitor/1.0'}
            ) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"Failed to fetch webpage: HTTP {response.status}")
                        return None
                    
                    html_content = await response.text()
            
            # Simple text extraction from HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text_content = soup.get_text()
            text_content = self._clean_text(text_content)
            
            # Extract title
            title = source.get("title", "")
            if not title or title == "Untitled":
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text(strip=True)
            
            # Extract summary
            summary = self._extract_summary(text_content)
            
            # Extract topics
            topics = self._extract_topics(text_content)
            
            return {
                "source_id": source.get("url", ""),
                "url": url,
                "title": title,
                "content_type": "webpage",
                "text_content": text_content[:10000],  # Limit content size
                "summary": summary,
                "topics": topics,
                "extracted_at": datetime.now().isoformat(),
                "_scrapedAt": datetime.now().isoformat(),
                "_source": "aws-content-monitor"
            }
            
        except Exception as e:
            print(f"Error extracting web content: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\-\(\)]', ' ', text)
        # Remove extra spaces
        text = ' '.join(text.split())
        return text.strip()
    
    def _extract_title_from_text(self, text: str) -> str:
        """Extract title from text content."""
        lines = text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if len(line) > 10 and len(line) < 200:  # Reasonable title length
                return line
        return "Untitled Document"
    
    def _extract_summary(self, text: str) -> str:
        """Extract summary from text content."""
        # Get first few sentences
        sentences = re.split(r'[.!?]+', text)
        summary_sentences = []
        char_count = 0
        
        for sentence in sentences[:10]:  # Max 10 sentences
            sentence = sentence.strip()
            if len(sentence) > 20:  # Skip very short sentences
                summary_sentences.append(sentence)
                char_count += len(sentence)
                if char_count > 500:  # Max 500 characters
                    break
        
        return '. '.join(summary_sentences) + '.' if summary_sentences else ""
    
    def _extract_topics(self, text: str) -> list:
        """Extract topics/keywords from text content."""
        # Simple keyword extraction based on AWS-related terms
        aws_keywords = [
            'aws', 'amazon', 'ec2', 's3', 'lambda', 'cloudformation', 'iam', 'vpc',
            'rds', 'dynamodb', 'cloudwatch', 'cloudfront', 'route53', 'elb',
            'security', 'compliance', 'architecture', 'best practices', 'whitepaper',
            'documentation', 'guide', 'tutorial', 'api', 'sdk', 'cli'
        ]
        
        text_lower = text.lower()
        found_topics = []
        
        for keyword in aws_keywords:
            if keyword in text_lower:
                # Count occurrences
                count = text_lower.count(keyword)
                if count >= 3:  # Only include if mentioned multiple times
                    found_topics.append({
                        "topic": keyword,
                        "mentions": count
                    })
        
        # Sort by mention count and return top 10
        found_topics.sort(key=lambda x: x["mentions"], reverse=True)
        return found_topics[:10]