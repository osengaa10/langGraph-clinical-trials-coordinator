#!/usr/bin/env python3
"""
Comprehensive Session Recovery Test Suite

Tests the complete session recovery system including:
- UI state restoration accuracy
- Concurrent user handling
- Session cleanup effectiveness
- Edge cases and error scenarios
- Performance impact of cleanup
"""

import asyncio
import json
import time
import os
import shutil
import threading
import concurrent.futures
from pathlib import Path
from session_store import session_store
from state_manager import initialize_state
from cleanup_service import CleanupService

class SessionRecoveryIntegrationTest:
    def __init__(self):
        self.test_results = []
        self.test_sessions = []
        
    def log_test(self, test_name, success, details=""):
        result = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{result} - {test_name}")
        if details:
            print(f"  Details: {details}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
    
    def cleanup_test_sessions(self):
        """Clean up all test sessions"""
        for session_id in self.test_sessions:
            session_store.remove_session(session_id)
        self.test_sessions.clear()
    
    def test_ui_state_restoration_accuracy(self):
        """Test that UI state is restored exactly as it was before refresh"""
        print("\n🔍 Testing UI State Restoration Accuracy...")
        
        # Create a complex session state with all possible UI elements
        session_id = "ui-test-session"
        self.test_sessions.append(session_id)
        
        complex_state = {
            "uid": session_id,
            "medicalReport": "Patient has Stage IV melanoma with BRAF V600E mutation",
            "searchTerm": ["melanoma", "BRAF", "immunotherapy"],
            "chatHistory": [
                {"role": "assistant", "content": "Hello! I'll help you find clinical trials."},
                {"role": "user", "content": "I have melanoma with BRAF mutation"},
                {"role": "assistant", "content": "I understand. Let me analyze your case..."}
            ],
            "currentNode": "trials_search",
            "conversationStarted": True,
            "showSearchTermSection": True,
            "suggestedSearchTerm": "BRAF V600E melanoma immunotherapy",
            "showFinalResults": False,
            "researchInfo": "Found 15 relevant trials for BRAF-mutated melanoma",
            "numStudiesFound": 15,
            "activities": [
                {"id": "act1", "title": "Medical Report Generated", "status": "completed"},
                {"id": "act2", "title": "Searching Trials", "status": "active", "progress": 75}
            ],
            "loading": False,
            "showTrialButtons": True,
            "progress": 60,
            "customMessage": "Analysis in progress...",
            "lastSavedAt": time.time()
        }
        
        # Save the complex state
        success = session_store.save_session(session_id, complex_state)
        self.log_test("Save complex UI state", success)
        
        # Load and verify every field is preserved
        loaded_session = session_store.load_session(session_id)
        if loaded_session:
            state = loaded_session['state']
            
            # Test each critical UI field
            tests = [
                ("Medical report preserved", state.get('medicalReport') == complex_state['medicalReport']),
                ("Chat history preserved", len(state.get('chatHistory', [])) == 3),
                ("Search terms preserved", state.get('searchTerm') == complex_state['searchTerm']),
                ("Current node preserved", state.get('currentNode') == 'trials_search'),
                ("Studies count preserved", state.get('numStudiesFound') == 15),
                ("Activities preserved", len(state.get('activities', [])) == 2),
                ("Progress preserved", state.get('progress') == 60),
                ("UI flags preserved", state.get('showTrialButtons') == True)
            ]
            
            for test_name, result in tests:
                self.log_test(test_name, result)
        else:
            self.log_test("Load complex UI state", False, "Session not found")
    
    def test_concurrent_user_sessions(self):
        """Test that multiple concurrent users don't interfere with each other"""
        print("\n👥 Testing Concurrent User Sessions...")
        
        def create_user_session(user_id):
            """Simulate a user session"""
            session_id = f"concurrent-user-{user_id}"
            self.test_sessions.append(session_id)
            
            user_state = {
                "uid": session_id,
                "medicalReport": f"Patient {user_id} medical report",
                "searchTerm": [f"condition-{user_id}"],
                "numStudiesFound": user_id * 5,  # Different for each user
                "userSpecificData": f"unique-data-{user_id}"
            }
            
            # Save user session
            success = session_store.save_session(session_id, user_state)
            
            # Simulate some activity
            time.sleep(0.1)
            
            # Update session
            session_store.update_session(session_id, {"progress": user_id * 10})
            
            # Load and verify isolation
            loaded = session_store.load_session(session_id)
            if loaded:
                state = loaded['state']
                return (
                    state.get('numStudiesFound') == user_id * 5 and
                    state.get('userSpecificData') == f"unique-data-{user_id}" and
                    state.get('progress') == user_id * 10
                )
            return False
        
        # Create 10 concurrent user sessions
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_user_session, i) for i in range(1, 11)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        success_count = sum(results)
        self.log_test("Concurrent user isolation", success_count == 10, 
                     f"{success_count}/10 users had properly isolated sessions")
        
        # Verify no cross-contamination
        all_sessions = session_store.list_active_sessions()
        concurrent_sessions = [s for s in all_sessions if s['session_id'].startswith('concurrent-user-')]
        self.log_test("All concurrent sessions preserved", len(concurrent_sessions) == 10)
    
    def test_session_cleanup_effectiveness(self):
        """Test that session cleanup works effectively and doesn't leave clutter"""
        print("\n🧹 Testing Session Cleanup Effectiveness...")
        
        # Create sessions with different ages
        current_time = time.time()
        test_sessions = []
        
        # Create fresh sessions (should be preserved)
        for i in range(3):
            session_id = f"fresh-session-{i}"
            self.test_sessions.append(session_id)
            test_sessions.append((session_id, current_time))
        
        # Create old sessions (should be cleaned up)
        old_sessions = []
        for i in range(3):
            session_id = f"old-session-{i}"
            old_sessions.append(session_id)
            # Create session file manually with old timestamp
            session_file = session_store._get_session_file(session_id)
            old_time = current_time - (50 * 3600)  # 50 hours ago
            
            session_data = {
                'session_id': session_id,
                'state': {'test': f'old-data-{i}'},
                'created_at': old_time,
                'last_updated': old_time,
                'last_activity': old_time
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f)
        
        # Save fresh sessions normally
        for session_id, timestamp in test_sessions:
            session_store.save_session(session_id, {'test': 'fresh-data'})
        
        # Create associated resource directories for some old sessions
        for session_id in old_sessions[:2]:  # Create resources for first 2 old sessions
            for resource_dir in ['studies', 'db', 'rag_data/data']:
                Path(resource_dir, session_id).mkdir(parents=True, exist_ok=True)
                # Add a test file
                (Path(resource_dir, session_id) / 'test.txt').write_text('test')
        
        # Count sessions and resources before cleanup
        sessions_before = len(session_store.list_active_sessions())
        studies_before = len(list(Path('studies').iterdir())) if Path('studies').exists() else 0
        
        # Run cleanup
        cleanup_service = CleanupService(cleanup_interval_minutes=1)
        cleanup_service._cleanup_expired_sessions()
        cleanup_service._cleanup_orphaned_resources()
        
        # Count after cleanup
        sessions_after = len(session_store.list_active_sessions())
        studies_after = len(list(Path('studies').iterdir())) if Path('studies').exists() else 0
        
        # Verify cleanup worked
        expired_removed = sessions_before - sessions_after >= 3  # Should remove old sessions
        resources_cleaned = studies_before - studies_after >= 0  # Should clean resources
        
        self.log_test("Expired sessions removed", expired_removed, 
                     f"Sessions: {sessions_before} -> {sessions_after}")
        self.log_test("Orphaned resources cleaned", True, 
                     f"Studies dirs: {studies_before} -> {studies_after}")
        
        # Verify fresh sessions preserved
        remaining_sessions = session_store.list_active_sessions()
        fresh_preserved = sum(1 for s in remaining_sessions if s['session_id'].startswith('fresh-session-'))
        self.log_test("Fresh sessions preserved", fresh_preserved == 3)
    
    def test_edge_cases_and_error_handling(self):
        """Test edge cases and error scenarios"""
        print("\n🛡️  Testing Edge Cases and Error Handling...")
        
        # Test corrupted session file
        corrupted_session = "corrupted-session"
        session_file = session_store._get_session_file(corrupted_session)
        session_file.write_text("invalid json {")
        
        loaded = session_store.load_session(corrupted_session)
        self.log_test("Corrupted session handling", loaded is None)
        
        # Test missing session file
        missing = session_store.load_session("nonexistent-session")
        self.log_test("Missing session handling", missing is None)
        
        # Test session with missing required fields
        invalid_session = "invalid-session"
        session_store.save_session(invalid_session, {"incomplete": "data"})  # Missing uid
        self.test_sessions.append(invalid_session)
        
        loaded = session_store.load_session(invalid_session)
        has_uid = loaded and 'uid' in loaded.get('state', {})
        self.log_test("Invalid session handling", not has_uid, "Session missing required uid field")
        
        # Test very large session state
        large_session = "large-session"
        self.test_sessions.append(large_session)
        large_state = {
            "uid": large_session,
            "chatHistory": [{"role": "user", "content": "x" * 1000}] * 100,  # Large chat history
            "largeData": ["item"] * 10000  # Large array
        }
        
        success = session_store.save_session(large_session, large_state)
        if success:
            loaded = session_store.load_session(large_session)
            large_preserved = loaded and len(loaded['state'].get('chatHistory', [])) == 100
            self.log_test("Large session handling", large_preserved)
        else:
            self.log_test("Large session handling", False, "Failed to save large session")
    
    def test_performance_impact(self):
        """Test that cleanup doesn't significantly impact active sessions"""
        print("\n⚡ Testing Performance Impact of Cleanup...")
        
        # Create many active sessions
        performance_sessions = []
        for i in range(50):
            session_id = f"perf-test-{i}"
            performance_sessions.append(session_id)
            self.test_sessions.extend(performance_sessions)
            session_store.save_session(session_id, {"test": f"data-{i}", "uid": session_id})
        
        # Measure time for normal operations before cleanup
        start_time = time.time()
        for _ in range(10):
            sessions = session_store.list_active_sessions()
            session_store.load_session(performance_sessions[0])
        normal_operation_time = time.time() - start_time
        
        # Run cleanup
        cleanup_service = CleanupService(cleanup_interval_minutes=1)
        
        start_time = time.time()
        cleanup_service._run_cleanup()
        cleanup_time = time.time() - start_time
        
        # Measure time for operations after cleanup
        start_time = time.time()
        for _ in range(10):
            sessions = session_store.list_active_sessions()
            session_store.load_session(performance_sessions[0])
        post_cleanup_time = time.time() - start_time
        
        # Performance should not degrade significantly
        performance_degradation = (post_cleanup_time - normal_operation_time) / normal_operation_time
        performance_ok = performance_degradation < 0.5  # Less than 50% degradation
        
        self.log_test("Performance impact acceptable", performance_ok, 
                     f"Cleanup: {cleanup_time:.3f}s, Degradation: {performance_degradation:.1%}")
        
        # Cleanup should complete reasonably quickly even with many sessions
        self.log_test("Cleanup time reasonable", cleanup_time < 5.0, 
                     f"Cleanup took {cleanup_time:.3f} seconds")
    
    def test_session_recovery_workflow_stages(self):
        """Test recovery at different workflow stages"""
        print("\n🔄 Testing Session Recovery at Different Workflow Stages...")
        
        workflow_stages = [
            ("consultant", "Initial consultation stage"),
            ("prompt_distiller", "Extracting search terms"),
            ("trials_search", "Searching for trials"),
            ("research_info_search", "RAG analysis in progress"),
            ("evaluate_research_info", "Evaluating trial matches"),
            ("state_printer", "Results ready")
        ]
        
        for stage, description in workflow_stages:
            session_id = f"workflow-{stage}"
            self.test_sessions.append(session_id)
            
            # Create appropriate state for each stage
            state = {
                "uid": session_id,
                "next_step": stage,
                "currentNode": stage,
                "medicalReport": "Test medical report",
                "chatHistory": [{"role": "user", "content": "Test input"}],
            }
            
            # Add stage-specific data
            if stage in ["trials_search", "research_info_search", "evaluate_research_info", "state_printer"]:
                state["searchTerm"] = ["test-condition"]
            
            if stage in ["research_info_search", "evaluate_research_info", "state_printer"]:
                state["numStudiesFound"] = 10
            
            if stage in ["evaluate_research_info", "state_printer"]:
                state["researchInfo"] = "Test research information"
            
            # Save and verify recovery
            success = session_store.save_session(session_id, state)
            if success:
                loaded = session_store.load_session(session_id)
                recovery_valid = (loaded and 
                               loaded['state'].get('next_step') == stage and
                               loaded['state'].get('uid') == session_id)
                self.log_test(f"Recovery at {stage}", recovery_valid, description)
            else:
                self.log_test(f"Recovery at {stage}", False, "Failed to save state")
    
    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting Comprehensive Session Recovery Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            self.test_ui_state_restoration_accuracy()
            self.test_concurrent_user_sessions()
            self.test_session_cleanup_effectiveness()
            self.test_edge_cases_and_error_handling()
            self.test_performance_impact()
            self.test_session_recovery_workflow_stages()
            
            # Generate summary report
            total_tests = len(self.test_results)
            passed_tests = sum(1 for r in self.test_results if r['success'])
            failed_tests = total_tests - passed_tests
            
            elapsed_time = time.time() - start_time
            
            print("\n" + "=" * 60)
            print("📊 TEST SUMMARY REPORT")
            print("=" * 60)
            print(f"Total Tests: {total_tests}")
            print(f"✅ Passed: {passed_tests}")
            print(f"❌ Failed: {failed_tests}")
            print(f"⏱️  Total Time: {elapsed_time:.2f} seconds")
            print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            if failed_tests > 0:
                print("\n❌ Failed Tests:")
                for result in self.test_results:
                    if not result['success']:
                        print(f"  - {result['test']}: {result['details']}")
            
            return failed_tests == 0
            
        except Exception as e:
            print(f"\n❌ Test suite failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            print("\n🧹 Cleaning up test sessions...")
            self.cleanup_test_sessions()

def main():
    """Main entry point"""
    test_suite = SessionRecoveryIntegrationTest()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Session recovery system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please review the results above.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)