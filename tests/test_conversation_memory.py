"""
Test Script for Conversational Memory Feature
Tests the conversation management system
"""

import sys
import os
import tempfile
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from conversation_manager import ConversationManager, ConversationSession, ConversationMessage
import json
from datetime import datetime

# Use a temporary directory for persistence during tests to avoid polluting the repo
TEST_PERSIST_DIR = os.path.join(tempfile.gettempdir(), "property_rag_test_conversations")


def test_conversation_message():
    """Test ConversationMessage creation"""
    print("=" * 60)
    print("TEST 1: ConversationMessage")
    print("=" * 60)
    
    msg = ConversationMessage(
        role='user',
        content='Show me 2 bedroom apartments',
        metadata={'filters': {'bedrooms': 2}}
    )
    
    print(f"✓ Message created: {msg.role} - {msg.content[:30]}...")
    print(f"✓ Metadata: {msg.metadata}")
    print(f"✓ Timestamp: {msg.timestamp}")
    
    # Test serialization
    msg_dict = msg.to_dict()
    print(f"✓ Serialized successfully")
    
    # Test deserialization
    msg2 = ConversationMessage.from_dict(msg_dict)
    print(f"✓ Deserialized successfully")
    print()


def test_conversation_session():
    """Test ConversationSession functionality"""
    print("=" * 60)
    print("TEST 2: ConversationSession")
    print("=" * 60)
    
    session = ConversationSession("test-session-1")
    
    # Add messages
    session.add_message('user', 'Show me 2 bedroom apartments', {'filters': {'bedrooms': 2}})
    session.add_message('assistant', 'Found 5 properties matching your criteria...')
    session.add_message('user', 'What about ones under £1000?')
    session.add_message('assistant', 'Here are cheaper options...')
    
    print(f"✓ Added 4 messages to session")
    print(f"✓ Query count: {session.metadata['query_count']}")
    
    # Get history
    history = session.get_conversation_history(limit=4)
    print(f"✓ Retrieved history: {len(history)} messages")
    
    # Get context summary
    summary = session.get_context_summary()
    print(f"✓ Generated context summary ({len(summary)} chars)")
    print(f"   Preview: {summary[:100]}...")
    
    # Extract context
    context = session.extract_context_from_previous()
    print(f"✓ Extracted context:")
    print(f"   - Has history: {context['has_history']}")
    print(f"   - Previous queries: {len(context['previous_queries'])}")
    print(f"   - Mentioned filters: {context['mentioned_filters']}")
    
    # Test serialization
    session_dict = session.to_dict()
    print(f"✓ Session serialized")
    
    # Test deserialization
    session2 = ConversationSession.from_dict(session_dict)
    print(f"✓ Session deserialized")
    print(f"   - Messages preserved: {len(session2.messages)}")
    print()


def cleanup_test_data():
    """Clean up test data"""
    print("=" * 60)
    print("CLEANUP: Removing test data")
    print("=" * 60)
    
    import shutil
    test_dir = TEST_PERSIST_DIR
    
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"✓ Removed test directory: {test_dir}")
    else:
        print(f"✓ No test directory to clean")
    print()


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("CONVERSATIONAL MEMORY - TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        test_conversation_message()
        test_conversation_session()
        cleanup_test_data()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
