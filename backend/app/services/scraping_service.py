import requests
import hashlib
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)



class ScrapingService:
    """Service for web scraping and content extraction"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; AI-CompetitiveIntel/1.0)'
        })
    
    def scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape content from a URL"""
        logger.info(f"Scraping URL: {url}")
        try:
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code != 200:
                logger.warning(f"Scraping failed: {url} | Status: {response.status_code}")
                return None
            
            content_type = response.headers.get('content-type', '').split(';')[0]
            
            if not self.should_scrape_content_type(content_type):
                return None
            
            content = response.text
            content_hash = self.generate_content_hash(content)
            
            return {
                "content": content,
                "content_type": content_type,
                "url": url,
                "content_hash": content_hash
            }
            
        except (requests.RequestException, requests.Timeout):
            return None
    
    def extract_text_from_html(self, html_content: str) -> str:
        """Extract clean text from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean it
        text = soup.get_text()
        return self.clean_content(text)
    
    def clean_content(self, content: str) -> str:
        """Clean and normalize content without regex"""
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Strip whitespace and replace multiple spaces
            cleaned_line = ' '.join(line.split())
            if cleaned_line:  # Only add non-empty lines
                cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)
    
    def generate_content_hash(self, content: str) -> str:
        """Generate SHA-256 hash of content for deduplication"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def should_scrape_content_type(self, content_type: str) -> bool:
        """Check if content type should be scraped"""
        allowed_types = [
            'text/html',
            'text/plain',
            'application/json',
            'text/xml',
            'application/xml'
        ]
        return content_type in allowed_types