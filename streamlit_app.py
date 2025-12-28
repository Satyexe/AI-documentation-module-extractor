"""Streamlit UI for Pulse - Module Extraction AI Agent"""

import streamlit as st
import json
import logging
from typing import List

from pulse.pipeline import ExtractionPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

st.set_page_config(
    page_title="Pulse - Module Extraction AI Agent",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .log-container {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 5px;
        font-family: monospace;
        font-size: 0.85rem;
        max-height: 400px;
        overflow-y: auto;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">🔍 Pulse – Module Extraction AI Agent</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Extract structured product knowledge from documentation websites</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    max_depth = st.slider(
        "Crawl Depth",
        min_value=1,
        max_value=5,
        value=3,
        help="Maximum depth to crawl from seed URLs"
    )
    
    max_pages = st.slider(
        "Max Pages",
        min_value=10,
        max_value=200,
        value=100,
        help="Maximum number of pages to crawl"
    )
    
    crawl_delay = st.slider(
        "Crawl Delay (seconds)",
        min_value=0.0,
        max_value=2.0,
        value=0.5,
        step=0.1,
        help="Delay between requests to be respectful"
    )
    
    st.markdown("---")
    st.markdown("### 📚 Example URLs")
    example_urls = [
        "https://support.neo.space/hc/en-us",
        "https://wordpress.org/documentation/",
        "https://help.zluri.com/",
        "https://www.chargebee.com/docs/2.0/"
    ]
    for url in example_urls:
        if st.button(f"📎 {url[:50]}...", key=f"example_{url}"):
            st.session_state.example_url = url

# Main content
st.header("📥 Input URLs")

# URL input
url_input = st.text_area(
    "Enter one or more documentation URLs (one per line)",
    height=150,
    help="Enter the base URL(s) of the documentation website you want to extract modules from"
)

# Handle example URL
if 'example_url' in st.session_state:
    url_input = st.session_state.example_url
    del st.session_state.example_url

# Parse URLs
urls = []
if url_input:
    url_lines = [line.strip() for line in url_input.strip().split('\n') if line.strip()]
    urls = [url for url in url_lines if url.startswith('http://') or url.startswith('https://')]

if urls:
    st.success(f"✅ {len(urls)} URL(s) ready to process")
    with st.expander("View URLs"):
        for i, url in enumerate(urls, 1):
            st.write(f"{i}. {url}")

# Run button
run_extraction = st.button("🚀 Run Extraction", type="primary", use_container_width=True)

# Initialize session state
if 'extraction_result' not in st.session_state:
    st.session_state.extraction_result = None
if 'logs' not in st.session_state:
    st.session_state.logs = []

# Run extraction
if run_extraction:
    if not urls:
        st.error("❌ Please enter at least one valid URL")
    else:
        with st.spinner("🔄 Running extraction pipeline..."):
            # Create pipeline
            pipeline = ExtractionPipeline(
                max_depth=max_depth,
                max_pages=max_pages,
                crawl_delay=crawl_delay
            )
            
            # Run extraction
            result = pipeline.extract(urls)
            
            # Store results
            st.session_state.extraction_result = result
            st.session_state.logs = result.get('logs', [])

# Display logs
if st.session_state.logs:
    st.header("📋 Extraction Logs")
    log_text = '\n'.join(st.session_state.logs)
    st.markdown(f'<div class="log-container">{log_text}</div>', unsafe_allow_html=True)

# Display results
if st.session_state.extraction_result:
    result = st.session_state.extraction_result
    modules = result.get('modules', [])
    stats = result.get('stats', {})
    
    if modules:
        st.header("📊 Results")
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Modules Found", len(modules))
        with col2:
            st.metric("Pages Crawled", stats.get('pages_crawled', 0))
        with col3:
            st.metric("Pages Parsed", stats.get('pages_parsed', 0))
        with col4:
            total_subs = sum(len(m.get('Submodules', {})) for m in modules)
            st.metric("Submodules Found", total_subs)
        
        st.markdown("---")
        
        # Modules display
        st.subheader("📦 Extracted Modules")
        
        for i, module in enumerate(modules, 1):
            with st.expander(f"🔹 {module['module']}", expanded=(i == 1)):
                st.markdown(f"**Description:** {module.get('Description', 'N/A')}")
                
                submodules = module.get('Submodules', {})
                if submodules:
                    st.markdown("**Submodules:**")
                    for sub_name, sub_desc in submodules.items():
                        st.markdown(f"- **{sub_name}**: {sub_desc}")
                else:
                    st.info("No submodules found for this module")
        
        st.markdown("---")
        
        # JSON output
        st.subheader("📄 JSON Output")
        
        json_output = pipeline.to_json(modules, pretty=True)
        st.code(json_output, language='json')
        
        # Download button
        st.download_button(
            label="💾 Download JSON",
            data=json_output,
            file_name="extracted_modules.json",
            mime="application/json",
            use_container_width=True
        )
    else:
        st.warning("⚠️ No modules were extracted. Check the logs above for details.")

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #999;'>Pulse – Module Extraction AI Agent | "
    "Extract structured knowledge from documentation</p>",
    unsafe_allow_html=True
)

