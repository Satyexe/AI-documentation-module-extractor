"""HTML Parser Module

Extracts meaningful content from HTML pages, removing boilerplate.
"""

import logging
import re
from typing import Dict, List, Optional

from bs4 import BeautifulSoup, Tag, NavigableString

logger = logging.getLogger(__name__)


class ContentParser:
    """Parser for extracting structured content from HTML."""
    
    # Common selectors for boilerplate removal
    BOILERPLATE_SELECTORS = [
        'header', 'footer', 'nav', 'aside',
        '.header', '.footer', '.navbar', '.sidebar', '.menu',
        '.navigation', '.nav-menu', '.site-header', '.site-footer',
        'script', 'style', 'noscript', 'iframe',
        '.advertisement', '.ads', '.ad-banner',
        '.cookie-banner', '.cookie-consent',
        '.social-share', '.share-buttons'
    ]
    
    def __init__(self):
        """Initialize the parser."""
        pass
    
    def parse(self, html: str, url: str) -> Dict:
        """Parse HTML and extract structured content.
        
        Args:
            html: HTML content
            url: Source URL
            
        Returns:
            Dictionary with 'url', 'title', 'headings', 'content', 'text'
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove boilerplate
        self._remove_boilerplate(soup)
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract headings with hierarchy
        headings = self._extract_headings(soup)
        
        # Extract main content
        content_blocks = self._extract_content_blocks(soup)
        
        # Extract plain text
        text = self._extract_text(soup)
        
        return {
            'url': url,
            'title': title,
            'headings': headings,
            'content_blocks': content_blocks,
            'text': text
        }
    
    def _remove_boilerplate(self, soup: BeautifulSoup) -> None:
        """Remove boilerplate elements from soup.
        
        Args:
            soup: BeautifulSoup object to modify in-place
        """
        for selector in self.BOILERPLATE_SELECTORS:
            for element in soup.select(selector):
                element.decompose()
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Page title
        """
        # Try title tag first
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            if title:
                return title
        
        # Try h1 as fallback
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        return ""
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract headings with their hierarchy.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of heading dictionaries with 'level', 'text', 'id'
        """
        headings = []
        for level in range(1, 5):
            for tag in soup.find_all(f'h{level}'):
                text = tag.get_text(strip=True)
                if text:
                    headings.append({
                        'level': level,
                        'text': text,
                        'id': tag.get('id', ''),
                        'tag': f'h{level}'
                    })
        return headings
    
    def _extract_content_blocks(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract structured content blocks.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of content block dictionaries
        """
        blocks = []
        
        # Find main content area (common patterns)
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('div', class_=re.compile(r'content|main|body|documentation', re.I)) or
            soup.find('body')
        )
        
        if not main_content:
            main_content = soup
        
        # Extract structured content
        for element in main_content.descendants:
            if isinstance(element, Tag):
                if element.name in ('p', 'li', 'td', 'th'):
                    text = element.get_text(strip=True)
                    if text and len(text) > 20:  # Filter very short texts
                        blocks.append({
                            'type': element.name,
                            'text': text,
                            'tag': element.name
                        })
        
        return blocks
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract clean plain text from soup.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Plain text content
        """
        # Find main content area
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('div', class_=re.compile(r'content|main|body|documentation', re.I)) or
            soup.find('body')
        )
        
        if not main_content:
            main_content = soup
        
        # Get text and clean it
        text = main_content.get_text(separator=' ', strip=True)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def extract_section_content(self, heading: Tag, soup: BeautifulSoup, max_depth: int = 3) -> str:
        """Extract content associated with a heading.
        
        Args:
            heading: Heading tag element
            soup: BeautifulSoup object
            max_depth: Maximum depth to extract content
            
        Returns:
            Extracted text content
        """
        content_parts = []
        current = heading.next_sibling
        
        heading_level = int(heading.name[1]) if heading.name.startswith('h') else 1
        
        depth = 0
        while current and depth < max_depth:
            if isinstance(current, Tag):
                # Stop at next heading of same or higher level
                if current.name.startswith('h'):
                    next_level = int(current.name[1])
                    if next_level <= heading_level:
                        break
                
                # Collect text from paragraphs, lists, etc.
                if current.name in ('p', 'li', 'div', 'ul', 'ol'):
                    text = current.get_text(strip=True)
                    if text:
                        content_parts.append(text)
            
            current = current.next_sibling
            depth += 1
        
        return ' '.join(content_parts)

