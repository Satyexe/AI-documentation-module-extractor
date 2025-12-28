"""Simple import test to verify all modules can be imported correctly."""

import sys

def test_imports():
    """Test that all modules can be imported."""
    try:
        print("Testing imports...")
        
        print("  - pulse package...")
        import pulse
        
        print("  - pulse.crawler...")
        from pulse.crawler import URLCrawler
        
        print("  - pulse.parser...")
        from pulse.parser import ContentParser
        
        print("  - pulse.inference...")
        from pulse.inference import ModuleInference
        
        print("  - pulse.summarizer...")
        from pulse.summarizer import DescriptionSummarizer
        
        print("  - pulse.pipeline...")
        from pulse.pipeline import ExtractionPipeline
        
        print("\n✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_imports()
    sys.exit(0 if success else 1)

