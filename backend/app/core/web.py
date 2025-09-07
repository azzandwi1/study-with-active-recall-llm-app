import logging
from typing import Tuple, Dict, Optional
import httpx
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from readability import Document
import re
from app.core.settings import settings

logger = logging.getLogger(__name__)


class WebScraper:
    """Handle web content extraction with sanitization and readability"""
    
    def __init__(self):
        self.blocked_patterns = settings.blocked_url_patterns
        self.timeout = 30  # seconds
        self.max_content_length = 10 * 1024 * 1024  # 10MB
    
    def extract_content(self, url: str) -> Tuple[str, Dict]:
        """
        Extract and clean content from a web URL
        
        Args:
            url: URL to extract content from
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        try:
            # Validate URL
            if not self._is_valid_url(url):
                raise ValueError(f"Invalid or blocked URL: {url}")
            
            # Fetch content
            content, response_metadata = self._fetch_url(url)
            
            # Extract and clean text
            text, extraction_metadata = self._extract_text_from_html(content, url)
            
            # Combine metadata
            metadata = {
                'source_type': 'url',
                'url': url,
                'canonical_url': self._get_canonical_url(content, url),
                'word_count': len(text.split()),
                **response_metadata,
                **extraction_metadata
            }
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"Web content extraction failed for {url}: {e}")
            raise
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL and check against blocked patterns"""
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check for blocked patterns
            url_lower = url.lower()
            for pattern in self.blocked_patterns:
                if pattern.lower() in url_lower:
                    logger.warning(f"URL blocked by pattern '{pattern}': {url}")
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _fetch_url(self, url: str) -> Tuple[str, Dict]:
        """Fetch content from URL with proper headers and error handling"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                
                # Check content length
                content_length = len(response.content)
                if content_length > self.max_content_length:
                    raise ValueError(f"Content too large: {content_length} bytes")
                
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                if not any(ct in content_type for ct in ['text/html', 'text/plain', 'application/xhtml']):
                    raise ValueError(f"Unsupported content type: {content_type}")
                
                metadata = {
                    'status_code': response.status_code,
                    'content_type': content_type,
                    'content_length': content_length,
                    'final_url': str(response.url),
                    'response_time': response.elapsed.total_seconds()
                }
                
                return response.text, metadata
                
        except httpx.TimeoutException:
            raise ValueError(f"Request timeout for URL: {url}")
        except httpx.HTTPStatusError as e:
            raise ValueError(f"HTTP error {e.response.status_code} for URL: {url}")
        except Exception as e:
            raise ValueError(f"Failed to fetch URL {url}: {e}")
    
    def _extract_text_from_html(self, html_content: str, original_url: str) -> Tuple[str, Dict]:
        """Extract clean text from HTML using readability"""
        try:
            # Use readability to extract main content
            doc = Document(html_content)
            cleaned_html = doc.summary()
            
            # Parse with BeautifulSoup for additional cleaning
            soup = BeautifulSoup(cleaned_html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text()
            
            # Clean up text
            text = self._clean_text(text)
            
            # Extract metadata
            metadata = {
                'title': doc.title() or self._extract_title(soup),
                'author': self._extract_author(soup),
                'publish_date': self._extract_publish_date(soup),
                'language': self._detect_language(text),
                'extraction_method': 'readability'
            }
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            # Fallback to simple text extraction
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text()
            text = self._clean_text(text)
            
            return text, {
                'title': 'Unknown',
                'extraction_method': 'fallback',
                'error': str(e)
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common web artifacts
        text = re.sub(r'(Share|Tweet|Like|Follow|Subscribe)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(Cookie|Privacy|Terms|Copyright)', '', text, flags=re.IGNORECASE)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        
        # Remove phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '', text)
        
        # Clean up punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
        
        return text.strip()
    
    def _get_canonical_url(self, html_content: str, original_url: str) -> str:
        """Extract canonical URL from HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            canonical_link = soup.find('link', rel='canonical')
            
            if canonical_link and canonical_link.get('href'):
                canonical_url = canonical_link['href']
                # Make absolute URL
                return urljoin(original_url, canonical_url)
            
            return original_url
            
        except Exception:
            return original_url
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from HTML"""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else 'Unknown'
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author from HTML meta tags"""
        # Try various meta tags for author
        author_selectors = [
            'meta[name="author"]',
            'meta[property="article:author"]',
            'meta[name="twitter:creator"]',
            '.author',
            '[rel="author"]'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                else:
                    return element.get_text().strip()
        
        return None
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publish date from HTML meta tags"""
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="date"]',
            'meta[name="pubdate"]',
            'time[datetime]'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                elif element.name == 'time':
                    return element.get('datetime', '').strip()
        
        return None
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection based on common words"""
        # This is a simple heuristic - in production, you might want to use a proper language detection library
        english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        indonesian_words = ['dan', 'atau', 'tetapi', 'di', 'pada', 'untuk', 'dari', 'dengan', 'oleh', 'yang', 'ini', 'itu']
        
        text_lower = text.lower()
        english_count = sum(1 for word in english_words if word in text_lower)
        indonesian_count = sum(1 for word in indonesian_words if word in text_lower)
        
        if indonesian_count > english_count:
            return 'id'
        else:
            return 'en'
