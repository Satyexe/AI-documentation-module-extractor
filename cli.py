"""CLI Interface for Pulse - Module Extraction AI Agent"""

import argparse
import json
import sys
import logging
from pathlib import Path

from pulse.pipeline import ExtractionPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Pulse - Module Extraction AI Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py https://support.neo.space/hc/en-us
  python cli.py https://wordpress.org/documentation/ -o output.json
  python cli.py https://help.zluri.com/ --max-depth 2 --max-pages 50
  python cli.py url1 url2 url3 -d 4 -p 200
        """
    )
    
    parser.add_argument(
        'urls',
        nargs='+',
        help='One or more documentation URLs to extract from'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='output.json',
        help='Output JSON file path (default: output.json)'
    )
    
    parser.add_argument(
        '-d', '--max-depth',
        type=int,
        default=3,
        help='Maximum crawl depth (default: 3)'
    )
    
    parser.add_argument(
        '-p', '--max-pages',
        type=int,
        default=100,
        help='Maximum number of pages to crawl (default: 100)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        help='Delay between requests in seconds (default: 0.5)'
    )
    
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Pretty-print JSON output'
    )
    
    parser.add_argument(
        '--logs',
        action='store_true',
        help='Print extraction logs to stdout'
    )
    
    args = parser.parse_args()
    
    # Validate URLs
    urls = args.urls
    for url in urls:
        if not (url.startswith('http://') or url.startswith('https://')):
            logger.error(f"Invalid URL: {url}")
            sys.exit(1)
    
    print(f"🚀 Pulse - Module Extraction AI Agent")
    print(f"📥 Processing {len(urls)} URL(s)")
    print(f"⚙️  Configuration: depth={args.max_depth}, max_pages={args.max_pages}, delay={args.delay}s")
    print("-" * 60)
    
    # Create pipeline
    pipeline = ExtractionPipeline(
        max_depth=args.max_depth,
        max_pages=args.max_pages,
        crawl_delay=args.delay
    )
    
    # Run extraction
    try:
        result = pipeline.extract(urls)
        modules = result.get('modules', [])
        logs = result.get('logs', [])
        stats = result.get('stats', {})
        
        # Print logs if requested
        if args.logs:
            print("\n📋 Extraction Logs:")
            print("-" * 60)
            for log in logs:
                print(log)
            print("-" * 60)
        
        # Print statistics
        print(f"\n📊 Statistics:")
        print(f"  - Pages crawled: {stats.get('pages_crawled', 0)}")
        print(f"  - Pages parsed: {stats.get('pages_parsed', 0)}")
        print(f"  - Modules found: {len(modules)}")
        total_subs = sum(len(m.get('Submodules', {})) for m in modules)
        print(f"  - Submodules found: {total_subs}")
        
        # Save output
        json_output = pipeline.to_json(modules, pretty=args.pretty)
        output_path = Path(args.output)
        output_path.write_text(json_output, encoding='utf-8')
        
        print(f"\n✅ Extraction complete!")
        print(f"💾 Results saved to: {output_path.absolute()}")
        
        # Print summary
        if modules:
            print(f"\n📦 Extracted Modules:")
            for i, module in enumerate(modules, 1):
                sub_count = len(module.get('Submodules', {}))
                print(f"  {i}. {module['module']} ({sub_count} submodules)")
        
        # Exit code
        sys.exit(0 if modules else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Extraction interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

