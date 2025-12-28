"""Main Pipeline Module

Orchestrates the complete extraction pipeline.
"""

import json
import logging
from typing import List, Dict, Optional

from pulse.crawler import URLCrawler
from pulse.parser import ContentParser
from pulse.inference import ModuleInference
from pulse.summarizer import DescriptionSummarizer
from pulse.summarizer import DescriptionSummarizer

logger = logging.getLogger(__name__)


class ExtractionPipeline:
    """Main pipeline for extracting modules and submodules from documentation."""
    
    def __init__(
        self,
        max_depth: int = 3,
        max_pages: int = 100,
        crawl_delay: float = 0.5
    ):
        """Initialize the pipeline.
        
        Args:
            max_depth: Maximum crawl depth
            max_pages: Maximum pages to crawl
            crawl_delay: Delay between crawl requests
        """
        self.crawler = URLCrawler(
            max_depth=max_depth,
            max_pages=max_pages,
            delay=crawl_delay
        )
        self.parser = ContentParser()
        self.inference = ModuleInference()
        self.summarizer = DescriptionSummarizer()
        
        self.logs = []
    
    def _log(self, message: str, level: str = "INFO"):
        """Log a message.
        
        Args:
            message: Log message
            level: Log level
        """
        log_entry = f"[{level}] {message}"
        self.logs.append(log_entry)
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)
    
    def extract(self, urls: List[str]) -> Dict:
        """Run the complete extraction pipeline.
        
        Args:
            urls: List of seed URLs
            
        Returns:
            Dictionary with 'modules' (list) and 'logs' (list)
        """
        self.logs = []
        self._log(f"Starting extraction for {len(urls)} URL(s)")
        
        try:
            # Step 1: Crawl
            self._log("Step 1: Crawling URLs...")
            pages = self.crawler.crawl(urls)
            self._log(f"Crawled {len(pages)} pages")
            
            if not pages:
                self._log("No pages were crawled. Check URLs and network connectivity.", "WARNING")
                return {'modules': [], 'logs': self.logs}
            
            # Step 2: Parse
            self._log("Step 2: Parsing HTML content...")
            parsed_pages = []
            for page in pages:
                try:
                    parsed = self.parser.parse(page['html'], page['url'])
                    parsed_pages.append(parsed)
                except Exception as e:
                    self._log(f"Error parsing {page['url']}: {e}", "WARNING")
            
            self._log(f"Parsed {len(parsed_pages)} pages")
            
            if not parsed_pages:
                self._log("No pages were successfully parsed.", "WARNING")
                return {'modules': [], 'logs': self.logs}
            
            # Step 3: Infer modules
            self._log("Step 3: Inferring modules and submodules...")
            modules_dict = self.inference.infer_modules(parsed_pages)
            self._log(f"Inferred {len(modules_dict)} modules")
            
            # Step 4: Generate descriptions
            self._log("Step 4: Generating descriptions...")
            
            # Enhance modules with content from parsed pages
            for module_name, module_data in modules_dict.items():
                # Generate module description
                module_content = module_data.get('content', '')
                if not module_content:
                    # Try to find content from pages
                    for page in parsed_pages:
                        headings = page.get('headings', [])
                        for heading in headings:
                            if module_name.lower() in heading['text'].lower():
                                module_content = page.get('text', '')
                                break
                        if module_content:
                            break
                
                module_desc = self.summarizer.generate_description(module_content)
                module_data['description'] = module_desc
                
                # Generate submodule descriptions
                for sub_name in list(module_data['submodules'].keys()):
                    sub_content = module_data['submodules'][sub_name]
                    if not sub_content:
                        # Try to find content from pages
                        for page in parsed_pages:
                            headings = page.get('headings', [])
                            for heading in headings:
                                if sub_name.lower() in heading['text'].lower():
                                    sub_content = page.get('text', '')
                                    break
                            if sub_content:
                                break
                    
                    sub_desc = self.summarizer.generate_description(sub_content)
                    module_data['submodules'][sub_name] = sub_desc
            
            # Step 5: Format output
            self._log("Step 5: Formatting output...")
            output_modules = self._format_output(modules_dict)
            
            self._log(f"Extraction complete. Generated {len(output_modules)} modules")
            
            return {
                'modules': output_modules,
                'logs': self.logs,
                'stats': {
                    'pages_crawled': len(pages),
                    'pages_parsed': len(parsed_pages),
                    'modules_found': len(output_modules)
                }
            }
            
        except Exception as e:
            self._log(f"Pipeline error: {e}", "ERROR")
            import traceback
            self._log(traceback.format_exc(), "ERROR")
            return {'modules': [], 'logs': self.logs}
    
    def _format_output(self, modules_dict: Dict) -> List[Dict]:
        """Format modules into output JSON structure.
        
        Args:
            modules_dict: Dictionary of modules with submodules
            
        Returns:
            List of formatted module dictionaries
        """
        output = []
        
        for module_name, module_data in modules_dict.items():
            # Generate module description if missing
            module_desc = module_data.get('description', '')
            if not module_desc:
                module_desc = self.summarizer.generate_description(module_data.get('content', ''))
            
            # Build submodules dictionary
            submodules_dict = {}
            for sub_name, sub_desc in module_data.get('submodules', {}).items():
                if sub_desc:  # Only include submodules with descriptions
                    submodules_dict[sub_name] = sub_desc
            
            # Only include modules that have either a description or submodules
            if module_desc or submodules_dict:
                output.append({
                    'module': module_name,
                    'Description': module_desc or f"Module for {module_name}",
                    'Submodules': submodules_dict
                })
        
        return output
    
    def to_json(self, modules: List[Dict], pretty: bool = True) -> str:
        """Convert modules to JSON string.
        
        Args:
            modules: List of module dictionaries
            pretty: Whether to format JSON with indentation
            
        Returns:
            JSON string
        """
        try:
            if pretty:
                return json.dumps(modules, indent=2, ensure_ascii=False)
            else:
                return json.dumps(modules, ensure_ascii=False)
        except Exception as e:
            logger.error(f"JSON serialization error: {e}")
            return "[]"

