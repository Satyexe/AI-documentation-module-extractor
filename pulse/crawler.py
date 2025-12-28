"""URL Crawler Module

Handles recursive crawling of documentation websites using BFS strategy.
"""

import logging
import time
from collections import deque
from typing import Set, List, Dict, Optional
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class URLCrawler:
    """Recursive crawler for documentation websites using BFS."""
    
    def __init__(
        self,
        max_depth: int = 3,
        max_pages: int = 100,
        delay: float = 0.5,
        timeout: int = 10,
        respect_robots_txt: bool = True
    ):
        """Initialize the crawler.
        
        Args:
            max_depth: Maximum crawl depth from seed URLs
            max_pages: Maximum number of pages to crawl
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            respect_robots_txt: Whether to respect robots.txt
        """
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay
        self.timeout = timeout
        self.respect_robots_txt = respect_robots_txt
        
        self.session = self._create_session()
        self.visited: Set[str] = set()
        self.robots_cache: Dict[str, RobotFileParser] = {}
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            'User-Agent': 'Pulse-Crawler/1.0 (+https://github.com/pulse-crawler)'
        })
        return session
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and trailing slashes.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL
        """
        parsed = urlparse(url)
        # Remove fragment
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path.rstrip('/') or '/',
            parsed.params,
            parsed.query,
            ''  # Remove fragment
        ))
        return normalized
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL.
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain name
        """
        return urlparse(url).netloc
    
    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs belong to the same domain.
        
        Args:
            url1: First URL
            url2: Second URL
            
        Returns:
            True if same domain
        """
        return self._get_domain(url1) == self._get_domain(url2)
    
    def _should_crawl_url(self, url: str, base_domain: str) -> bool:
        """Check if URL should be crawled.
        
        Args:
            url: URL to check
            base_domain: Base domain to restrict crawling to
            
        Returns:
            True if URL should be crawled
        """
        parsed = urlparse(url)
        
        # Check scheme
        if parsed.scheme not in ('http', 'https'):
            return False
        
        # Check domain
        if parsed.netloc != base_domain:
            return False
        
        # Ignore unsupported formats
        path_lower = parsed.path.lower()
        if any(path_lower.endswith(ext) for ext in [
            '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
            '.js', '.css', '.xml', '.zip', '.tar', '.gz'
        ]):
            return False
        
        # Ignore common non-documentation paths
        path_parts = [p.lower() for p in parsed.path.split('/') if p]
        if any(part in path_parts for part in [
            'login', 'signin', 'signup', 'register', 'logout',
            'privacy', 'terms', 'legal', 'cookie', 'contact'
        ]):
            return False
        
        # Check robots.txt if enabled
        if self.respect_robots_txt:
            if not self._can_fetch(url, base_domain):
                return False
        
        return True
    
    def _can_fetch(self, url: str, domain: str) -> bool:
        """Check if URL can be fetched according to robots.txt.
        
        Args:
            url: URL to check
            domain: Domain name
            
        Returns:
            True if can fetch
        """
        if domain not in self.robots_cache:
            robots_url = f"https://{domain}/robots.txt"
            rp = RobotFileParser()
            try:
                rp.set_url(robots_url)
                rp.read()
                self.robots_cache[domain] = rp
            except Exception as e:
                logger.debug(f"Could not fetch robots.txt for {domain}: {e}")
                self.robots_cache[domain] = None
        
        robots_parser = self.robots_cache.get(domain)
        if robots_parser is None:
            return True  # Default to allowing if robots.txt unavailable
        
        return robots_parser.can_fetch(self.session.headers['User-Agent'], url)
    
    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract links from HTML content.
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            List of absolute URLs
        """
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            absolute_url = urljoin(base_url, href)
            normalized = self._normalize_url(absolute_url)
            links.append(normalized)
        
        return links
    
    def _fetch_page(self, url: str) -> Optional[Dict]:
        """Fetch a single page.
        
        Args:
            url: URL to fetch
            
        Returns:
            Dictionary with 'url', 'html', 'status_code', or None if failed
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type:
                logger.debug(f"Skipping {url}: not HTML (Content-Type: {content_type})")
                return None
            
            return {
                'url': url,
                'html': response.text,
                'status_code': response.status_code,
                'content_type': content_type
            }
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None
    
    def crawl(self, seed_urls: List[str]) -> List[Dict]:
        """Crawl documentation website starting from seed URLs.
        
        Args:
            seed_urls: List of starting URLs
            
        Returns:
            List of page data dictionaries
        """
        # Normalize seed URLs
        seed_urls = [self._normalize_url(url) for url in seed_urls]
        
        if not seed_urls:
            return []
        
        # Validate and get base domain
        base_domain = self._get_domain(seed_urls[0])
        for url in seed_urls:
            if not self._is_same_domain(url, seed_urls[0]):
                logger.warning(f"Seed URL {url} has different domain, skipping")
                continue
        
        # BFS queue: (url, depth)
        queue = deque([(url, 0) for url in seed_urls])
        self.visited = set()
        pages = []
        
        logger.info(f"Starting crawl from {len(seed_urls)} seed URLs")
        logger.info(f"Max depth: {self.max_depth}, Max pages: {self.max_pages}")
        
        while queue and len(pages) < self.max_pages:
            url, depth = queue.popleft()
            
            # Skip if already visited
            if url in self.visited:
                continue
            
            # Skip if max depth reached
            if depth > self.max_depth:
                continue
            
            # Check if should crawl
            if not self._should_crawl_url(url, base_domain):
                logger.debug(f"Skipping {url}: filtered by rules")
                continue
            
            self.visited.add(url)
            logger.info(f"Crawling [{depth}] {url}")
            
            # Fetch page
            page_data = self._fetch_page(url)
            if page_data is None:
                continue
            
            pages.append(page_data)
            
            # Extract links for next level
            if depth < self.max_depth:
                links = self._extract_links(page_data['html'], url)
                for link in links:
                    if link not in self.visited and self._should_crawl_url(link, base_domain):
                        queue.append((link, depth + 1))
            
            # Respect delay
            if self.delay > 0:
                time.sleep(self.delay)
        
        logger.info(f"Crawl completed: {len(pages)} pages fetched")
        return pages

