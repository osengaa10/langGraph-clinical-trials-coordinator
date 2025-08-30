#!/usr/bin/env node
/**
 * Debug Session Detection Issue
 * 
 * This script helps debug why the recovery modal isn't showing up
 */

console.log("🔍 Debug Session Detection Issue");
console.log("=" * 50);

// Mock localStorage to test session detection logic
const mockLocalStorage = (() => {
  let store = {};
  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => store[key] = value.toString(),
    removeItem: (key) => delete store[key],
    clear: () => store = {},
    _getStore: () => store
  };
})();

// Copy the SessionManager logic exactly as implemented
class DebugSessionManager {
  static SESSION_KEY = 'clinexus_session';
  static SESSION_STATE_KEY = 'clinexus_session_state';
  static SESSION_TIMEOUT = 48 * 60 * 60 * 1000; // 48 hours in milliseconds

  static getSessionData() {
    try {
      const data = mockLocalStorage.getItem(this.SESSION_KEY);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error parsing session data:', error);
      return null;
    }
  }

  static getSessionState() {
    try {
      const data = mockLocalStorage.getItem(this.SESSION_STATE_KEY);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error parsing session state:', error);
      return null;
    }
  }

  static isSessionExpired(sessionData) {
    if (!sessionData) return true;
    return (Date.now() - sessionData.lastActivity) > this.SESSION_TIMEOUT;
  }

  static hasActiveSession() {
    const sessionData = this.getSessionData();
    const state = this.getSessionState();
    
    console.log("🔍 hasActiveSession() debug:");
    console.log(`  - sessionData exists: ${!!sessionData}`);
    console.log(`  - sessionData expired: ${sessionData ? this.isSessionExpired(sessionData) : 'N/A'}`);
    console.log(`  - state exists: ${!!state}`);
    console.log(`  - state keys count: ${state ? Object.keys(state).length : 0}`);
    
    const hasSession = sessionData && !this.isSessionExpired(sessionData) && state && Object.keys(state).length > 0;
    console.log(`  - hasActiveSession result: ${hasSession}`);
    
    return hasSession;
  }

  static isRecoverableState(state) {
    if (!state) {
      console.log("❌ isRecoverableState: No state provided");
      return false;
    }
    
    if (!state.uid) {
      console.log("❌ isRecoverableState: Missing uid");
      return false;
    }
    
    const hasProgress = (
      state.conversationStarted ||
      state.medicalReport ||
      (state.chatHistory && state.chatHistory.length > 0) ||
      (state.searchTerm && state.searchTerm.length > 0) ||
      state.numStudiesFound > 0 ||
      state.researchInfo
    );
    
    console.log("🔍 isRecoverableState() debug:");
    console.log(`  - has uid: ${!!state.uid}`);
    console.log(`  - conversationStarted: ${!!state.conversationStarted}`);
    console.log(`  - medicalReport: ${!!state.medicalReport}`);
    console.log(`  - chatHistory length: ${state.chatHistory?.length || 0}`);
    console.log(`  - searchTerm length: ${state.searchTerm?.length || 0}`);
    console.log(`  - numStudiesFound: ${state.numStudiesFound || 0}`);
    console.log(`  - researchInfo: ${!!state.researchInfo}`);
    console.log(`  - hasProgress: ${hasProgress}`);
    
    const sessionData = this.getSessionData();
    if (sessionData && this.isSessionExpired(sessionData)) {
      console.log("❌ isRecoverableState: Session is expired");
      return false;
    }
    
    console.log(`  - isRecoverableState result: ${hasProgress}`);
    return hasProgress;
  }

  static getRecoveryInfo() {
    const sessionData = this.getSessionData();
    const state = this.getSessionState();
    
    console.log("🔍 getRecoveryInfo() debug:");
    console.log(`  - hasActiveSession: ${this.hasActiveSession()}`);
    
    if (!this.hasActiveSession()) {
      console.log("❌ getRecoveryInfo: No active session");
      return null;
    }

    const recoveryInfo = {
      sessionAge: this.formatSessionAge(),
      lastStep: state.currentNode || 'consultant',
      hasResults: !!(state.researchInfo || state.numStudiesFound > 0),
      hasConversation: !!(state.chatHistory?.length > 0),
      hasMedicalReport: !!state.medicalReport,
      studiesFound: state.numStudiesFound || 0
    };
    
    console.log("✅ Generated recovery info:", recoveryInfo);
    return recoveryInfo;
  }

  static formatSessionAge() {
    const sessionData = this.getSessionData();
    if (!sessionData) return "unknown";
    
    const ageMs = Date.now() - sessionData.createdAt;
    const minutes = Math.floor(ageMs / (1000 * 60));
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    }
  }
}

function simulateUserScenario() {
  console.log("\n👤 Simulating User Scenario: Medical Report Generated, Then Page Refresh");
  console.log("=" * 70);
  
  // Step 1: User starts session
  console.log("\n1️⃣ User starts session...");
  const sessionId = `test_${Date.now()}`;
  const sessionData = {
    sessionId: sessionId,
    createdAt: Date.now(),
    lastActivity: Date.now()
  };
  mockLocalStorage.setItem(DebugSessionManager.SESSION_KEY, JSON.stringify(sessionData));
  console.log(`✅ Session created: ${sessionId}`);
  
  // Step 2: Conversation starts
  console.log("\n2️⃣ Conversation starts...");
  const initialState = {
    uid: sessionId,
    conversationStarted: true,
    chatHistory: [
      { role: "user", content: "I have diabetes and need clinical trials" },
      { role: "assistant", content: "I'll help you find relevant trials" }
    ],
    currentNode: "consultant"
  };
  mockLocalStorage.setItem(DebugSessionManager.SESSION_STATE_KEY, JSON.stringify(initialState));
  
  // Test session detection at this point
  console.log("\n🔍 After conversation starts:");
  DebugSessionManager.hasActiveSession();
  const recoveryInfo1 = DebugSessionManager.getRecoveryInfo();
  console.log(`Modal should show: ${!!recoveryInfo1}`);
  
  // Step 3: Medical report generated (this is where the issue occurs)
  console.log("\n3️⃣ Medical report generated...");
  const reportState = {
    uid: sessionId,
    conversationStarted: true,
    chatHistory: [
      { role: "user", content: "I have diabetes and need clinical trials" },
      { role: "assistant", content: "I'll help you find relevant trials" },
      { role: "assistant", content: "I've generated your medical report" }
    ],
    medicalReport: "**Medical Report**\n\nPatient has Type 2 diabetes...",
    currentNode: "medical_report",
    showSearchTermSection: true,
    suggestedSearchTerm: "type 2 diabetes clinical trials"
  };
  mockLocalStorage.setItem(DebugSessionManager.SESSION_STATE_KEY, JSON.stringify(reportState));
  
  // Test session detection after medical report
  console.log("\n🔍 After medical report generated:");
  DebugSessionManager.hasActiveSession();
  const recoveryInfo2 = DebugSessionManager.getRecoveryInfo();
  console.log(`Modal should show: ${!!recoveryInfo2}`);
  
  if (recoveryInfo2) {
    console.log("✅ Recovery modal WOULD show with this data:");
    console.log(`  - Session age: ${recoveryInfo2.sessionAge}`);
    console.log(`  - Last step: ${recoveryInfo2.lastStep}`);
    console.log(`  - Has medical report: ${recoveryInfo2.hasMedicalReport}`);
    console.log(`  - Show search section: ${reportState.showSearchTermSection}`);
  } else {
    console.log("❌ Recovery modal WOULD NOT show - investigating why...");
    
    // Debug each condition
    const sessionData = DebugSessionManager.getSessionData();
    const state = DebugSessionManager.getSessionState();
    
    console.log("\n🔬 Detailed debugging:");
    console.log(`  - sessionData: ${JSON.stringify(sessionData, null, 2)}`);
    console.log(`  - state: ${JSON.stringify(state, null, 2)}`);
  }
  
  // Step 4: Simulate page refresh (user's problem scenario)
  console.log("\n4️⃣ User refreshes page...");
  console.log("🔄 Page refreshes - checking what recovery system sees:");
  
  // This is what happens when page loads after refresh
  DebugSessionManager.hasActiveSession();
  const finalRecoveryInfo = DebugSessionManager.getRecoveryInfo();
  
  if (finalRecoveryInfo) {
    console.log("✅ SUCCESS: Recovery modal should appear");
    console.log("✅ Medical report should be restored");
    console.log("✅ Search term section should be visible");
  } else {
    console.log("❌ PROBLEM: Recovery modal will NOT appear");
    console.log("❌ User will lose their medical report");
    console.log("❌ User will have to start over");
  }
}

function main() {
  try {
    simulateUserScenario();
    
    console.log("\n" + "=" * 70);
    console.log("🎯 CONCLUSION");
    console.log("=" * 70);
    console.log("Run this debug script to see exactly what's happening");
    console.log("with the session detection logic during the user's scenario.");
    
  } catch (error) {
    console.error("❌ Debug script failed:", error);
  }
}

if (require.main === module) {
  main();
}