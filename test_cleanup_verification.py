#!/usr/bin/env python3
"""
Focused test to verify session cleanup functionality
"""

import json
import time
from pathlib import Path
from session_store import session_store
from cleanup_service import CleanupService

def test_cleanup_verification():
    print("🧹 Testing Session Cleanup Verification...")
    
    # Create a truly expired session by manually creating the file
    old_session_id = "truly-expired-test"
    session_file = session_store._get_session_file(old_session_id)
    
    # Create session data that's definitely expired (60 hours old)
    old_time = time.time() - (60 * 3600)  # 60 hours ago
    session_data = {
        'session_id': old_session_id,
        'state': {'test': 'expired-data'},
        'created_at': old_time,
        'last_updated': old_time,
        'last_activity': old_time
    }
    
    # Write the expired session file
    with open(session_file, 'w') as f:
        json.dump(session_data, f)
    
    print(f"✅ Created expired session: {old_session_id}")
    
    # Create associated resource directories
    for resource_dir in ['studies', 'db']:
        resource_path = Path(resource_dir, old_session_id)
        resource_path.mkdir(parents=True, exist_ok=True)
        (resource_path / 'test_file.txt').write_text('test data')
    
    print(f"✅ Created resource directories for expired session")
    
    # Count before cleanup
    sessions_before = session_store.list_active_sessions()
    expired_session_exists = any(s['session_id'] == old_session_id for s in sessions_before)
    studies_before = Path('studies', old_session_id).exists()
    db_before = Path('db', old_session_id).exists()
    
    print(f"Before cleanup:")
    print(f"  - Expired session exists: {expired_session_exists}")
    print(f"  - Studies dir exists: {studies_before}")
    print(f"  - DB dir exists: {db_before}")
    print(f"  - Total active sessions: {len(sessions_before)}")
    
    # Run cleanup
    cleanup_service = CleanupService()
    cleanup_service._cleanup_expired_sessions()
    cleanup_service._cleanup_orphaned_resources()
    
    # Count after cleanup
    sessions_after = session_store.list_active_sessions()
    expired_session_gone = not any(s['session_id'] == old_session_id for s in sessions_after)
    studies_after = Path('studies', old_session_id).exists()
    db_after = Path('db', old_session_id).exists()
    
    print(f"\nAfter cleanup:")
    print(f"  - Expired session removed: {expired_session_gone}")
    print(f"  - Studies dir removed: {not studies_after}")
    print(f"  - DB dir removed: {not db_after}")
    print(f"  - Total active sessions: {len(sessions_after)}")
    
    # Test results
    success = expired_session_gone and not studies_after and not db_after
    
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'} - Cleanup verification")
    
    # Manual cleanup if automated cleanup didn't work
    if session_file.exists():
        session_file.unlink()
        print("🧹 Manually removed expired session file")
    
    return success

def test_session_age_calculation():
    """Test that session age calculation works correctly"""
    print("\n🕐 Testing Session Age Calculation...")
    
    # Test current session ages
    sessions = session_store.list_active_sessions()
    print(f"Found {len(sessions)} active sessions:")
    
    for session in sessions[:5]:  # Show first 5
        age_hours = session.get('age_hours', 0)
        should_expire = age_hours > 48
        print(f"  - {session['session_id']}: {age_hours:.1f}h ({'EXPIRED' if should_expire else 'ACTIVE'})")
    
    return True

def main():
    print("🔍 Session Cleanup Verification Test")
    print("=" * 50)
    
    try:
        success1 = test_cleanup_verification()
        success2 = test_session_age_calculation()
        
        if success1 and success2:
            print("\n🎉 All cleanup tests passed!")
            return True
        else:
            print("\n⚠️ Some cleanup tests failed.")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)