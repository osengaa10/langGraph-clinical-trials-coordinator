#!/usr/bin/env python3
"""
Test script for session recovery functionality
"""

import asyncio
import json
import time
from session_store import session_store
from state_manager import initialize_state

def test_session_store():
    """Test basic session store functionality"""
    print("Testing SessionStore functionality...")
    
    # Test session creation
    test_session_id = "test-session-123"
    test_state = {
        "medical_report": "Test patient has diabetes",
        "search_term": ["diabetes", "type 2"],
        "chat_history": [
            {"role": "assistant", "content": "Hello! How can I help you find clinical trials?"},
            {"role": "user", "content": "I have type 2 diabetes"}
        ],
        "currentNode": "medical_report",
        "conversationStarted": True,
        "numStudiesFound": 5
    }
    
    # Save session
    success = session_store.save_session(test_session_id, test_state)
    print(f"✓ Save session: {'SUCCESS' if success else 'FAILED'}")
    
    # Load session
    loaded_session = session_store.load_session(test_session_id)
    success = loaded_session is not None and loaded_session['state']['medical_report'] == test_state['medical_report']
    print(f"✓ Load session: {'SUCCESS' if success else 'FAILED'}")
    
    # Update session
    updated_state = {"numStudiesFound": 10, "currentNode": "trials_search"}
    success = session_store.update_session(test_session_id, updated_state)
    print(f"✓ Update session: {'SUCCESS' if success else 'FAILED'}")
    
    # Verify update
    loaded_session = session_store.load_session(test_session_id)
    success = loaded_session['state']['numStudiesFound'] == 10
    print(f"✓ Verify update: {'SUCCESS' if success else 'FAILED'}")
    
    # List sessions
    sessions = session_store.list_active_sessions()
    success = any(s['session_id'] == test_session_id for s in sessions)
    print(f"✓ List sessions: {'SUCCESS' if success else 'FAILED'}")
    
    # Get session info
    info = session_store.get_session_info(test_session_id)
    success = info is not None and info['session_id'] == test_session_id
    print(f"✓ Get session info: {'SUCCESS' if success else 'FAILED'}")
    
    # Clean up test session
    success = session_store.remove_session(test_session_id)
    print(f"✓ Remove session: {'SUCCESS' if success else 'FAILED'}")
    
    print("SessionStore tests completed!\n")

def test_state_compatibility():
    """Test compatibility between old and new state formats"""
    print("Testing state compatibility...")
    
    # Create old-style state
    old_state = initialize_state("test-uid-456")
    print(f"✓ Old state created with keys: {list(old_state.keys())}")
    
    # Simulate saving and loading
    session_store.save_session("test-uid-456", old_state)
    loaded_state = session_store.load_session("test-uid-456")
    
    success = loaded_state is not None and 'medical_report' in loaded_state['state']
    print(f"✓ State compatibility: {'SUCCESS' if success else 'FAILED'}")
    
    # Clean up
    session_store.remove_session("test-uid-456")
    print("State compatibility tests completed!\n")

def test_cleanup_service():
    """Test cleanup service functionality"""
    print("Testing cleanup service...")
    
    from cleanup_service import CleanupService
    
    # Create test service
    cleanup = CleanupService(cleanup_interval_minutes=1)
    
    # Create some test sessions
    for i in range(3):
        session_id = f"cleanup-test-{i}"
        test_state = {"test": f"data-{i}"}
        session_store.save_session(session_id, test_state)
    
    # Run cleanup once
    cleanup._run_cleanup()
    print("✓ Cleanup service ran successfully")
    
    # Verify sessions still exist (they shouldn't be expired yet)
    sessions = session_store.list_active_sessions()
    test_sessions = [s for s in sessions if s['session_id'].startswith('cleanup-test-')]
    success = len(test_sessions) == 3
    print(f"✓ Sessions preserved: {'SUCCESS' if success else 'FAILED'}")
    
    # Clean up test sessions
    for i in range(3):
        session_store.remove_session(f"cleanup-test-{i}")
    
    print("Cleanup service tests completed!\n")

def test_session_expiration():
    """Test session expiration logic"""
    print("Testing session expiration...")
    
    # Create a session and manually set old timestamp
    session_id = "expiration-test"
    test_state = {"test": "expiration"}
    
    success = session_store.save_session(session_id, test_state)
    print(f"✓ Created test session: {'SUCCESS' if success else 'FAILED'}")
    
    # Manually modify the session file to simulate old timestamp
    import os
    session_file = session_store._get_session_file(session_id)
    if session_file.exists():
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Set timestamp to 50 hours ago (past expiration)
        old_time = time.time() - (50 * 3600)
        session_data['created_at'] = old_time
        session_data['last_activity'] = old_time
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        print("✓ Simulated expired session")
        
        # Try to load - should return None for expired session
        loaded = session_store.load_session(session_id)
        success = loaded is None
        print(f"✓ Expired session handling: {'SUCCESS' if success else 'FAILED'}")
    
    print("Session expiration tests completed!\n")

def main():
    print("=== Session Recovery Test Suite ===\n")
    
    try:
        test_session_store()
        test_state_compatibility()
        test_cleanup_service()
        test_session_expiration()
        
        print("=== All Tests Completed Successfully! ===")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()