import pytest
from unittest.mock import Mock, patch
import hashlib

from app.services.scraping_service import ScrapingService
from app.models.data_source import DataSource
from app.models.raw_content import RawContent


class TestScrapingService:
    
    def test_extract_text_from_html(self):
        """Test extracting clean text from HTML"""
        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Main Title</h1>
                <p>This is a test paragraph.</p>
                <script>console.log('ignore this');</script>
                <style>.test { color: red; }</style>
            </body>
        </html>
        """
        
        service = ScrapingService()
        text = service.extract_text_from_html(html_content)
        
        assert "Main Title" in text
        assert "This is a test paragraph." in text
        assert "console.log" not in text  # Scripts should be removed
        assert ".test { color: red; }" not in text  # Styles should be removed
    
    
    def test_generate_content_hash(self):
        """Test content hash generation for deduplication"""
        service = ScrapingService()
        content = "This is test content for hashing"
        
        hash1 = service.generate_content_hash(content)
        hash2 = service.generate_content_hash(content)
        hash3 = service.generate_content_hash("Different content")
        
        assert hash1 == hash2  # Same content should produce same hash
        assert hash1 != hash3  # Different content should produce different hash
        assert len(hash1) == 64  # SHA-256 produces 64 character hex string
    
    
    @patch('app.services.scraping_service.requests.Session.get')
    def test_scrape_url_success(self, mock_get):
        """Test successful URL scraping"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><h1>Test Content</h1></body></html>"
        mock_response.headers = {'content-type': 'text/html'}
        mock_get.return_value = mock_response
        
        service = ScrapingService()
        result = service.scrape_url("https://example.com")
        
        assert result is not None
        assert result["content"] == "<html><body><h1>Test Content</h1></body></html>"
        assert result["content_type"] == "text/html"
        assert result["url"] == "https://example.com"
        assert "content_hash" in result
    
    
    @patch('app.services.scraping_service.requests.Session.get')
    def test_scrape_url_failure(self, mock_get):
        """Test URL scraping failure"""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        service = ScrapingService()
        result = service.scrape_url("https://example.com/not-found")
        
        assert result is None
    
    
    @patch('app.services.scraping_service.requests.Session.get')
    def test_scrape_url_with_timeout(self, mock_get):
        """Test URL scraping with timeout"""
        import requests
        mock_get.side_effect = requests.Timeout()
        
        service = ScrapingService()
        result = service.scrape_url("https://slow-example.com")
        
        assert result is None
    
    
    def test_clean_content(self):
        """Test content cleaning"""
        dirty_content = """
        
        
        This is content with    extra spaces.
        
        And extra newlines.
        
        
        """
        
        service = ScrapingService()
        clean = service.clean_content(dirty_content)
        
        assert clean == "This is content with extra spaces.\nAnd extra newlines."
    
    
    def test_should_scrape_content_type(self):
        """Test content type filtering"""
        service = ScrapingService()
        
        assert service.should_scrape_content_type("text/html") is True
        assert service.should_scrape_content_type("text/plain") is True
        assert service.should_scrape_content_type("application/json") is True
        assert service.should_scrape_content_type("image/jpeg") is False
        assert service.should_scrape_content_type("video/mp4") is False