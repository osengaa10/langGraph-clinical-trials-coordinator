#!/usr/bin/env python3
"""
Test for Medical Report Recovery Issue

This test verifies that after refresh:
1. Medical report is visible
2. Search term section is shown
3. User can submit search terms
"""

import asyncio
import json
from session_store import session_store
from websocket_routes import send_recovery_status, validate_recovery_state

def test_medical_report_recovery():
    print("🏥 Testing Medical Report Recovery Issue")
    print("=" * 50)
    
    # Create a session state that matches the user's scenario:
    # "After a medical report is generated and before submitting a search term"
    
    session_id = "recovery_test_medical_report"
    medical_report_state = {
        "uid": session_id,
        "medical_report": """**Comprehensive Medical Report**

**Patient Information:**
* Age: 45 years old  
* Condition: Type 2 Diabetes Mellitus
* Current medications: Metformin, Insulin

**Medical History:**
The patient was diagnosed with Type 2 diabetes 5 years ago. Currently managing with Metformin 1000mg twice daily and insulin as needed. Recent HbA1c level is 8.2%, indicating suboptimal glycemic control.

**Treatment Goals:**
- Achieve HbA1c < 7%
- Explore newer diabetes medications
- Consider clinical trials for innovative therapies""",
        
        "search_term": [],  # Empty - user hasn't submitted search terms yet
        "chat_history": [
            {"role": "assistant", "content": "Hello! I'll help you find clinical trials."},
            {"role": "user", "content": "I have type 2 diabetes and need better treatment options"},
            {"role": "assistant", "content": "I understand. Let me analyze your medical information and generate a comprehensive report."},
            {"role": "assistant", "content": "I've generated your medical report based on your information."}
        ],
        "next_step": "prompt_distiller",  # Waiting for search terms
        "current_node": "medical_report",
        "conversationStarted": True,
        "showSearchTermSection": True,  # This should be visible after recovery
        "suggestedSearchTerm": "type 2 diabetes metformin insulin glycemic control",
        "showFinalResults": False,
        "researchInfo": "",
        "numStudiesFound": 0,
        "activities": [
            {"id": "1", "title": "Medical Consultation", "status": "completed"},
            {"id": "2", "title": "Medical Report Generated", "status": "completed"}
        ],
        "loading": False,
        "showTrialButtons": False,
        "progress": 40
    }
    
    # Save the session state
    success = session_store.save_session(session_id, medical_report_state)
    print(f"✅ Created test session: {'SUCCESS' if success else 'FAILED'}")
    
    # Test recovery validation
    is_recoverable = validate_recovery_state(medical_report_state)
    print(f"✅ Session is recoverable: {'SUCCESS' if is_recoverable else 'FAILED'}")
    
    # Load the session (simulating server recovery)
    loaded_session = session_store.load_session(session_id)
    if loaded_session:
        state = loaded_session['state']
        
        # Verify critical state for medical report recovery
        tests = [
            ("Medical report exists", bool(state.get('medical_report'))),
            ("Show search term section", state.get('showSearchTermSection') == True),
            ("Conversation started", state.get('conversationStarted') == True),
            ("Current node is medical_report", state.get('current_node') == 'medical_report'),
            ("Has suggested search term", bool(state.get('suggestedSearchTerm'))),
            ("Chat history preserved", len(state.get('chat_history', [])) == 4),
            ("Not in final results", state.get('showFinalResults') == False),
            ("No studies found yet", state.get('numStudiesFound') == 0)
        ]
        
        print(f"\n📊 Recovery State Verification:")
        for test_name, result in tests:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} - {test_name}")
        
        # Test what messages would be sent during recovery
        print(f"\n📡 Recovery Messages That Would Be Sent:")
        
        # Check medical report message
        if state.get('medical_report'):
            print(f"  ✅ 'report' message: Medical report ({len(state['medical_report'])} chars)")
        
        # Check search term message
        if state.get('search_term') and len(state.get('search_term', [])) > 0:
            print(f"  ✅ 'new_search_term' message: {state['search_term']}")
        elif state.get('suggestedSearchTerm'):
            print(f"  ✅ Should restore suggested term: {state['suggestedSearchTerm']}")
        
        # Check studies found message
        if state.get('studies_found', 0) > 0:
            print(f"  ✅ 'studies_found' message: {state['studies_found']} trials")
        else:
            print(f"  ℹ️  No studies message (none found yet)")
        
        # Check research info message
        if state.get('research_info'):
            print(f"  ✅ 'research_info' message: Research data available")
        else:
            print(f"  ℹ️  No research info message (analysis not complete)")
        
        print(f"\n🎯 Expected UI State After Recovery:")
        print(f"  - Medical report visible: {'YES' if state.get('medical_report') else 'NO'}")
        print(f"  - Search term section visible: {'YES' if state.get('showSearchTermSection') else 'NO'}")
        print(f"  - Can submit search terms: {'YES' if state.get('showSearchTermSection') and not state.get('showFinalResults') else 'NO'}")
        print(f"  - Workflow stage: {state.get('current_node', 'unknown')}")
        
    else:
        print("❌ FAILED - Could not load test session")
    
    # Cleanup
    session_store.remove_session(session_id)
    print(f"\n🧹 Cleaned up test session")

def test_different_recovery_scenarios():
    """Test recovery at different workflow stages"""
    print(f"\n🔄 Testing Different Recovery Scenarios")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "Before Medical Report",
            "state": {
                "uid": "test-before-report",
                "conversationStarted": True,
                "chatHistory": [{"role": "user", "content": "I need help"}],
                "next_step": "consultant",
                "showSearchTermSection": False,
                "medicalReport": ""
            },
            "expected_report_visible": False,
            "expected_search_visible": False
        },
        {
            "name": "After Medical Report, Before Search Terms",
            "state": {
                "uid": "test-after-report",
                "conversationStarted": True,
                "medicalReport": "Patient has diabetes...",
                "showSearchTermSection": True,
                "suggestedSearchTerm": "diabetes treatment",
                "next_step": "prompt_distiller",
                "searchTerm": []
            },
            "expected_report_visible": True,
            "expected_search_visible": True
        },
        {
            "name": "After Search Terms Submitted",
            "state": {
                "uid": "test-after-search",
                "conversationStarted": True,
                "medicalReport": "Patient has diabetes...",
                "showSearchTermSection": False,
                "searchTerm": ["diabetes", "metformin"],
                "next_step": "trials_search",
                "numStudiesFound": 0
            },
            "expected_report_visible": True,
            "expected_search_visible": False
        },
        {
            "name": "After Trials Found",
            "state": {
                "uid": "test-trials-found",
                "conversationStarted": True,
                "medicalReport": "Patient has diabetes...",
                "showSearchTermSection": False,
                "searchTerm": ["diabetes"],
                "numStudiesFound": 8,
                "next_step": "research_info_search"
            },
            "expected_report_visible": True,
            "expected_search_visible": False
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        
        session_id = scenario['state']['uid']
        
        # Save scenario state
        session_store.save_session(session_id, scenario['state'])
        
        # Load and verify
        loaded = session_store.load_session(session_id)
        if loaded:
            state = loaded['state']
            
            # Check expected UI visibility
            report_visible = bool(state.get('medicalReport'))
            search_visible = bool(state.get('showSearchTermSection'))
            
            report_test = report_visible == scenario['expected_report_visible']
            search_test = search_visible == scenario['expected_search_visible']
            
            print(f"  Medical report visible: {'✅' if report_test else '❌'} "
                  f"Expected: {scenario['expected_report_visible']}, Got: {report_visible}")
            print(f"  Search section visible: {'✅' if search_test else '❌'} "
                  f"Expected: {scenario['expected_search_visible']}, Got: {search_visible}")
            
        # Cleanup
        session_store.remove_session(session_id)

def main():
    try:
        test_medical_report_recovery()
        test_different_recovery_scenarios()
        
        print(f"\n🎉 Medical Report Recovery Tests Complete!")
        print(f"\nℹ️  To test manually:")
        print(f"1. Start the application")
        print(f"2. Upload medical info and generate report")
        print(f"3. Refresh the page before submitting search terms")
        print(f"4. Choose 'Continue Search' in the recovery modal")
        print(f"5. Verify medical report is visible and search terms can be submitted")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()