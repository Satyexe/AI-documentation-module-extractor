"""Module and Submodule Inference

Extracts modules and submodules from parsed documentation content.
"""

import logging
import re
from typing import List, Dict, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class ModuleInference:
    """Infers modules and submodules from documentation structure."""
    
    def __init__(self):
        """Initialize the inference engine."""
        pass
    
    def infer_modules(self, parsed_pages: List[Dict]) -> Dict:
        """Infer modules and submodules from parsed pages.
        
        Args:
            parsed_pages: List of parsed page dictionaries
            
        Returns:
            Dictionary with modules and their submodules
        """
        # Collect all headings across pages with content association
        all_headings = []
        heading_content_map = {}
        page_content_map = {}
        
        for page in parsed_pages:
            url = page['url']
            headings = page.get('headings', [])
            text = page.get('text', '')
            content_blocks = page.get('content_blocks', [])
            
            page_content_map[url] = {
                'text': text,
                'headings': headings,
                'content_blocks': content_blocks
            }
            
            for heading in headings:
                level = heading['level']
                text_content = heading['text']
                heading_key = f"{url}::{text_content}"  # Make unique per page
                
                all_headings.append({
                    'level': level,
                    'text': text_content,
                    'url': url,
                    'id': heading.get('id', '')
                })
                
                # Extract content specific to this heading (content after heading until next heading)
                heading_content = self._extract_content_for_heading(heading, headings, text, content_blocks)
                heading_content_map[heading_key] = heading_content
                # Also store by text only for fallback
                if text_content not in heading_content_map:
                    heading_content_map[text_content] = heading_content
        
        # Infer module hierarchy
        modules = self._build_hierarchy(all_headings, heading_content_map, page_content_map)
        
        return modules
    
    def _extract_content_for_heading(
        self,
        heading: Dict,
        all_page_headings: List[Dict],
        page_text: str,
        content_blocks: List[Dict]
    ) -> str:
        """Extract content associated with a specific heading.
        
        Args:
            heading: Heading dictionary
            all_page_headings: All headings on the page
            page_text: Full page text
            content_blocks: Structured content blocks
            
        Returns:
            Extracted content text
        """
        heading_level = heading['level']
        heading_text = heading['text']
        
        # Find heading index
        heading_index = -1
        for i, h in enumerate(all_page_headings):
            if h['text'] == heading_text and h['level'] == heading_level:
                heading_index = i
                break
        
        if heading_index == -1:
            return page_text[:500]  # Fallback: first 500 chars
        
        # Extract content until next heading of same or higher level
        content_parts = []
        for i in range(heading_index + 1, len(all_page_headings)):
            next_heading = all_page_headings[i]
            if next_heading['level'] <= heading_level:
                break
            
            # Get content between headings (simplified: use text chunks)
            if i == heading_index + 1:
                # Use page text, extract relevant portion
                content_parts.append(page_text[:1000])  # Use substantial portion
        
        # If we have content blocks, try to extract more specifically
        if content_blocks:
            # Use first few content blocks as representative
            block_texts = [block.get('text', '') for block in content_blocks[:5]]
            content_parts.extend(block_texts)
        
        result = ' '.join(content_parts).strip()
        return result if result else page_text[:500]
    
    def _build_hierarchy(self, headings: List[Dict], content_map: Dict[str, str], page_content_map: Dict = None) -> Dict:
        """Build module-submodule hierarchy from headings.
        
        Args:
            headings: List of heading dictionaries
            content_map: Map of heading text to page content
            page_content_map: Map of URLs to page content
            
        Returns:
            Dictionary of modules with submodules
        """
        if page_content_map is None:
            page_content_map = {}
        # Group headings by level
        h1_headings = [h for h in headings if h['level'] == 1]
        h2_headings = [h for h in headings if h['level'] == 2]
        h3_headings = [h for h in headings if h['level'] == 3]
        
        modules = {}
        
        # Strategy 1: H1 headings as modules
        if h1_headings:
            for h1 in h1_headings:
                module_name = self._clean_heading(h1['text'])
                if not module_name or len(module_name) < 3:
                    continue
                
                # Find associated H2/H3 as submodules
                submodules = self._find_submodules_for_module(
                    h1, h2_headings, h3_headings, headings
                )
                
                if module_name not in modules:
                    # Get content for this heading
                    heading_key = f"{h1['url']}::{h1['text']}"
                    module_content = content_map.get(heading_key, content_map.get(h1['text'], ''))
                    if not module_content and h1['url'] in page_content_map:
                        module_content = page_content_map[h1['url']].get('text', '')
                    
                    modules[module_name] = {
                        'submodules': {},
                        'content': module_content,
                        'url': h1['url']
                    }
                
                # Add submodules with content
                for sub_name, sub_content in submodules.items():
                    if sub_name not in modules[module_name]['submodules']:
                        modules[module_name]['submodules'][sub_name] = sub_content
        
        # Strategy 2: If no H1, use dominant H2 as modules
        if not modules and h2_headings:
            # Group H2 headings that appear frequently or early in pages
            h2_counts = defaultdict(int)
            for h2 in h2_headings:
                h2_counts[h2['text']] += 1
            
            # Use top H2 headings as modules
            top_h2s = sorted(h2_counts.items(), key=lambda x: x[1], reverse=True)[:15]
            
            for h2_text, count in top_h2s:
                module_name = self._clean_heading(h2_text)
                if not module_name or len(module_name) < 3:
                    continue
                
                # Find the H2 heading object
                h2_obj = next((h for h in h2_headings if h['text'] == h2_text), None)
                if not h2_obj:
                    continue
                
                # Find associated H3 as submodules
                submodules = self._find_submodules_for_module(
                    h2_obj, h3_headings, [], headings
                )
                
                if module_name not in modules:
                    # Get content for this heading
                    heading_key = f"{h2_obj['url']}::{h2_text}"
                    module_content = content_map.get(heading_key, content_map.get(h2_text, ''))
                    if not module_content and h2_obj['url'] in page_content_map:
                        module_content = page_content_map[h2_obj['url']].get('text', '')
                    
                    modules[module_name] = {
                        'submodules': {},
                        'content': module_content,
                        'url': h2_obj['url']
                    }
                
                for sub_name, sub_content in submodules.items():
                    if sub_name not in modules[module_name]['submodules']:
                        modules[module_name]['submodules'][sub_name] = sub_content
        
        # Strategy 3: Use navigation/common patterns if still no modules
        if not modules:
            # Extract from page titles or URL patterns
            modules = self._infer_from_urls_and_titles(headings, content_map, page_content_map)
        
        return modules
    
    def _find_submodules_for_module(
        self,
        module_heading: Dict,
        candidate_submodules: List[Dict],
        candidate_submodules2: List[Dict],
        all_headings: List[Dict]
    ) -> Dict[str, str]:
        """Find submodules for a given module heading.
        
        Args:
            module_heading: The module heading dictionary
            candidate_submodules: Primary candidates (typically H2 if module is H1)
            candidate_submodules2: Secondary candidates (typically H3)
            all_headings: All headings for context
            
        Returns:
            Dictionary mapping submodule names to content
        """
        submodules = {}
        module_level = module_heading['level']
        module_url = module_heading['url']
        
        # Find headings that come after this module heading and are at next level
        module_index = -1
        for i, h in enumerate(all_headings):
            if h['text'] == module_heading['text'] and h['url'] == module_url:
                module_index = i
                break
        
        if module_index == -1:
            return submodules
        
        # Look for next-level headings after this module
        target_level = module_level + 1
        collected_sub_headings = []
        
        for i in range(module_index + 1, len(all_headings)):
            heading = all_headings[i]
            
            # Stop if we hit a heading at same or higher level (different module)
            if heading['level'] <= module_level:
                break
            
            # Collect headings at target level
            if heading['level'] == target_level:
                sub_name = self._clean_heading(heading['text'])
                if sub_name and len(sub_name) >= 3:
                    collected_sub_headings.append(heading)
        
        # Build submodules with content
        for sub_heading in collected_sub_headings:
            sub_name = self._clean_heading(sub_heading['text'])
            # Content will be filled later in pipeline
            submodules[sub_name] = ''
        
        return submodules
    
    def _infer_from_urls_and_titles(self, headings: List[Dict], content_map: Dict[str, str], page_content_map: Dict = None) -> Dict:
        """Infer modules from URL patterns and page titles when headings are insufficient.
        
        Args:
            headings: List of headings
            content_map: Content mapping
            page_content_map: Map of URLs to page content
            
        Returns:
            Dictionary of inferred modules
        """
        if page_content_map is None:
            page_content_map = {}
        modules = {}
        
        # Group by URL path segments
        url_groups = defaultdict(list)
        for heading in headings:
            url = heading['url']
            from urllib.parse import urlparse
            path = urlparse(url).path
            segments = [s for s in path.split('/') if s and s not in ('', 'docs', 'documentation', 'help', 'support')]
            
            if segments:
                # Use first meaningful segment as module
                module_segment = segments[0].replace('-', ' ').replace('_', ' ').title()
                if module_segment and len(module_segment) >= 3:
                    url_groups[module_segment].append(heading)
        
        # Create modules from URL groups
        for module_name, heading_list in url_groups.items():
            if len(heading_list) >= 2:  # Require at least 2 headings for a module
                modules[module_name] = {
                    'submodules': {},
                    'content': '',
                    'url': heading_list[0]['url']
                }
                
                # Use H2/H3 from these pages as submodules
                for heading in heading_list:
                    if heading['level'] >= 2:
                        sub_name = self._clean_heading(heading['text'])
                        if sub_name and len(sub_name) >= 3:
                            modules[module_name]['submodules'][sub_name] = ''
        
        return modules
    
    def _clean_heading(self, text: str) -> str:
        """Clean and normalize heading text.
        
        Args:
            text: Raw heading text
            
        Returns:
            Cleaned heading text
        """
        # Remove common prefixes/suffixes
        text = text.strip()
        
        # Remove section numbers (e.g., "1.2.3 Module Name")
        text = re.sub(r'^\d+\.?\d*\.?\d*\s*', '', text)
        
        # Remove common documentation markers
        markers = ['#', '*', '→', '►', '▼']
        for marker in markers:
            text = text.replace(marker, '').strip()
        
        # Limit length
        if len(text) > 100:
            text = text[:100].strip()
        
        return text.strip()
    
    def _extract_content_for_module(self, module_name: str, pages: List[Dict]) -> str:
        """Extract content relevant to a module from pages.
        
        Args:
            module_name: Module name
            pages: List of parsed pages
            
        Returns:
            Extracted content text
        """
        content_parts = []
        
        for page in pages:
            headings = page.get('headings', [])
            text = page.get('text', '')
            
            # Check if page mentions this module
            for heading in headings:
                if module_name.lower() in heading['text'].lower():
                    content_parts.append(text)
                    break
        
        return ' '.join(content_parts)

