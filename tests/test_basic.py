"""
Basic tests for Property RAG System
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

def test_imports():
    """Test that all modules can be imported"""
    try:
        import data_ingestion
        import vector_store
        import llm_handler
        import rag_pipeline
        import query_analytics
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_data_loader():
    """Test PropertyDataLoader initialization"""
    from data_ingestion import PropertyDataLoader
    
    try:
        loader = PropertyDataLoader("test.csv")
        print("✅ PropertyDataLoader initialization successful")
        return True
    except Exception as e:
        print(f"❌ PropertyDataLoader failed: {e}")
        return False

def test_llm_handler():
    """Test LLMHandler initialization without API key"""
    from llm_handler import LLMHandler
    
    try:
        handler = LLMHandler(api_key=None)
        print("✅ LLMHandler initialization successful (fallback mode)")
        return True
    except Exception as e:
        print(f"❌ LLMHandler failed: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Running Basic Tests")
    print("="*60 + "\n")
    
    tests = [
        test_imports,
        test_data_loader,
        test_llm_handler
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        print(f"\nRunning: {test.__name__}")
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
