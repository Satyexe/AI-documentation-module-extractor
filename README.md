# Pulse – Module Extraction AI Agent

A production-ready Python application that extracts structured product knowledge (modules and submodules) from documentation websites using only the content present in the provided URLs.

## 🎯 Overview

Pulse crawls documentation websites recursively, extracts meaningful content, and infers a hierarchical structure of modules and submodules. The system is designed to work **entirely from extracted content** without hallucinations or external knowledge.

## ✨ Features

- **Recursive Web Crawling**: BFS-based crawler with configurable depth and page limits
- **Smart Content Extraction**: Removes boilerplate (headers, footers, navbars) and extracts meaningful documentation content
- **Module Inference**: Automatically identifies modules and submodules from documentation structure
- **Extractive Descriptions**: Generates concise, factual descriptions from extracted content
- **Streamlit UI**: Interactive web interface with real-time logs and results visualization
- **CLI Interface**: Command-line tool for batch processing
- **JSON Output**: Clean, validated JSON in the exact required format

## 🏗️ Architecture

The system is built with a modular architecture:

```
pulse/
├── __init__.py          # Package initialization
├── crawler.py           # URL crawling with BFS
├── parser.py            # HTML parsing and content extraction
├── inference.py         # Module/submodule inference
├── summarizer.py        # Description generation
└── pipeline.py          # Main orchestration pipeline

streamlit_app.py         # Streamlit web interface
cli.py                   # Command-line interface
```

### Components

1. **Crawler** (`pulse/crawler.py`): Recursively crawls documentation sites using BFS, respects robots.txt, handles redirects and errors
2. **Parser** (`pulse/parser.py`): Extracts structured content from HTML, removes boilerplate, preserves headings and text
3. **Inference** (`pulse/inference.py`): Infers module hierarchy from heading structure (H1→H2→H3)
4. **Summarizer** (`pulse/summarizer.py`): Generates concise descriptions using extractive summarization
5. **Pipeline** (`pulse/pipeline.py`): Orchestrates the complete extraction workflow

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## 🚀 Usage

### Streamlit UI (Recommended)

Launch the interactive web interface:

```bash
streamlit run streamlit_app.py
```

Then:
1. Enter one or more documentation URLs in the text area
2. Configure crawl depth, max pages, and delay
3. Click "Run Extraction"
4. View results, download JSON

### CLI Interface

Run from command line:

```bash
# Basic usage
python cli.py https://support.neo.space/hc/en-us

# With custom output file
python cli.py https://wordpress.org/documentation/ -o output.json

# With configuration options
python cli.py https://help.zluri.com/ --max-depth 2 --max-pages 50

# Multiple URLs
python cli.py url1 url2 url3 -d 4 -p 200

# Pretty-print JSON and show logs
python cli.py https://www.chargebee.com/docs/2.0/ --pretty --logs
```

#### CLI Options

- `urls`: One or more documentation URLs (required)
- `-o, --output`: Output JSON file path (default: `output.json`)
- `-d, --max-depth`: Maximum crawl depth (default: 3)
- `-p, --max-pages`: Maximum pages to crawl (default: 100)
- `--delay`: Delay between requests in seconds (default: 0.5)
- `--pretty`: Pretty-print JSON output
- `--logs`: Print extraction logs to stdout

## 📊 Output Format

The system outputs JSON in the following strict format:

```json
[
  {
    "module": "Module Name",
    "Description": "Accurate description derived from documentation",
    "Submodules": {
      "Submodule Name": "Accurate description derived from documentation",
      "Submodule Name": "Accurate description derived from documentation"
    }
  }
]
```

## 🔍 How It Works

1. **Crawling**: Starting from seed URLs, the crawler uses BFS to discover documentation pages, staying within the same domain
2. **Parsing**: HTML is parsed to extract headings (H1-H4), paragraphs, lists, and other meaningful content while removing boilerplate
3. **Inference**: Modules are inferred from top-level headings (typically H1 or dominant H2), with submodules derived from child headings
4. **Summarization**: Descriptions are generated using extractive summarization, selecting key sentences from the extracted content
5. **Output**: Results are formatted as JSON and validated

## ⚙️ Configuration

### Crawler Settings

- **Max Depth**: How many levels deep to crawl (default: 3)
- **Max Pages**: Maximum number of pages to process (default: 100)
- **Crawl Delay**: Delay between requests to be respectful (default: 0.5s)

### Filtering Rules

The crawler automatically ignores:
- Non-HTML content (PDFs, images, JS files, etc.)
- Common non-documentation paths (login, privacy, terms, etc.)
- URLs outside the seed domain
- Duplicate pages

## 🧪 Testing

The system has been tested on various documentation sites:

- https://support.neo.space/hc/en-us
- https://wordpress.org/documentation/
- https://help.zluri.com/
- https://www.chargebee.com/docs/2.0/

### Example Test

```bash
python cli.py https://support.neo.space/hc/en-us -o neo_space_modules.json --pretty --logs
```

## 📝 Assumptions

1. **Documentation Structure**: Assumes documentation uses standard HTML heading hierarchy (H1 > H2 > H3)
2. **Same Domain**: All documentation pages are on the same domain as seed URLs
3. **HTML Format**: Documentation is in HTML format (not PDF or other formats)
4. **Public Access**: Documentation pages are publicly accessible without authentication
5. **Standard Structure**: Modules correspond to major sections (H1 or frequent H2), submodules to subsections

## ⚠️ Limitations

1. **JavaScript-Rendered Content**: Cannot extract content rendered entirely via JavaScript (requires actual HTML)
2. **Authentication**: Cannot access documentation behind login walls
3. **Complex Navigation**: May miss modules if documentation uses non-standard navigation patterns
4. **Large Sites**: Very large documentation sites may hit page limits
5. **Language**: Optimized for English documentation (may work with other languages but not tested)

## 🔧 Troubleshooting

### No Modules Extracted

- Check that URLs are accessible and return HTML content
- Increase `max_depth` and `max_pages` if documentation is deep
- Check logs for crawling/parsing errors
- Verify documentation uses standard HTML heading structure

### Slow Crawling

- Reduce `max_pages` or `max_depth`
- Increase `crawl_delay` if hitting rate limits
- Check network connectivity

### Missing Submodules

- Documentation may not use clear heading hierarchy
- Try increasing `max_depth` to crawl deeper
- Check if documentation uses lists or other structures instead of headings

## 🛠️ Development

### Code Structure

The codebase follows a clean, modular architecture:

- **Separation of Concerns**: Each module handles a specific responsibility
- **Type Hints**: Functions include type annotations where appropriate
- **Logging**: Comprehensive logging for debugging
- **Error Handling**: Graceful handling of edge cases

### Extending the System

To extend functionality:

1. **Custom Crawlers**: Modify `pulse/crawler.py` for different crawling strategies
2. **Alternative Parsers**: Extend `pulse/parser.py` for different content extraction
3. **Inference Rules**: Adjust `pulse/inference.py` for different module detection strategies
4. **Summarization**: Modify `pulse/summarizer.py` for different description generation

