#!/usr/bin/env node
/**
 * UI Session Recovery Test
 * 
 * Tests the frontend session recovery system by simulating:
 * - Page refresh scenarios
 * - Local storage state preservation
 * - Session validation logic
 * - Recovery UI data accuracy
 */

// Mock localStorage for testing
const mockLocalStorage = (() => {
  let store = {};
  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => store[key] = value.toString(),
    removeItem: (key) => delete store[key],
    clear: () => store = {},
    get length() { return Object.keys(store).length; },
    key: (index) => Object.keys(store)[index] || null,
    _getStore: () => store
  };
})();

// Mock implementation based on SessionManager.js logic
class MockSessionManager {
  static SESSION_KEY = 'clinexus_session';
  static SESSION_STATE_KEY = 'clinexus_session_state';
  static SESSION_TIMEOUT = 48 * 60 * 60 * 1000; // 48 hours in milliseconds

  static generateSessionId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  static getSessionId() {
    const sessionData = this.getSessionData();
    
    if (sessionData && !this.isSessionExpired(sessionData)) {
      return sessionData.sessionId;
    }
    
    const newSessionId = this.generateSessionId();
    this.createSession(newSessionId);
    return newSessionId;
  }

  static createSession(sessionId) {
    const sessionData = {
      sessionId,
      createdAt: Date.now(),
      lastActivity: Date.now()
    };
    
    mockLocalStorage.setItem(this.SESSION_KEY, JSON.stringify(sessionData));
    this.clearSessionState();
    return sessionData;
  }

  static getSessionData() {
    try {
      const data = mockLocalStorage.getItem(this.SESSION_KEY);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error parsing session data:', error);
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
    return sessionData && !this.isSessionExpired(sessionData) && state && Object.keys(state).length > 0;
  }

  static saveSessionState(state) {
    const essentialState = {
      uid: state.uid,
      medicalReport: state.medicalReport,
      searchTerm: state.searchTerm,
      chatHistory: state.chatHistory,
      currentNode: state.currentNode,
      conversationStarted: state.conversationStarted,
      showSearchTermSection: state.showSearchTermSection,
      suggestedSearchTerm: state.suggestedSearchTerm,
      showFinalResults: state.showFinalResults,
      researchInfo: state.researchInfo,
      numStudiesFound: state.numStudiesFound,
      activities: state.activities || [],
      loading: state.loading,
      showTrialButtons: state.showTrialButtons,
      progress: state.progress,
      customMessage: state.customMessage,
      lastSavedAt: Date.now()
    };

    mockLocalStorage.setItem(this.SESSION_STATE_KEY, JSON.stringify(essentialState));
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

  static clearSession() {
    mockLocalStorage.removeItem(this.SESSION_KEY);
    this.clearSessionState();
  }

  static clearSessionState() {
    mockLocalStorage.removeItem(this.SESSION_STATE_KEY);
  }

  static isRecoverableState(state) {
    if (!state) return false;
    
    if (!state.uid) return false;
    
    const hasProgress = (
      state.conversationStarted ||
      state.medicalReport ||
      (state.chatHistory && state.chatHistory.length > 0) ||
      (state.searchTerm && state.searchTerm.length > 0) ||
      state.numStudiesFound > 0 ||
      state.researchInfo
    );
    
    const sessionData = this.getSessionData();
    if (sessionData && this.isSessionExpired(sessionData)) {
      return false;
    }
    
    return hasProgress;
  }

  static getRecoveryInfo() {
    const sessionData = this.getSessionData();
    const state = this.getSessionState();
    
    if (!this.hasActiveSession()) {
      return null;
    }

    return {
      sessionAge: this.formatSessionAge(),
      lastStep: state.currentNode || 'consultant',
      hasResults: !!(state.researchInfo || state.numStudiesFound > 0),
      hasConversation: !!(state.chatHistory?.length > 0),
      hasMedicalReport: !!state.medicalReport,
      studiesFound: state.numStudiesFound || 0
    };
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

function runUITests() {
  console.log("🎨 Testing UI Session Recovery System");
  console.log("=" * 50);
  
  const results = [];
  
  // Test 1: Page refresh with active session
  console.log("\n1️⃣ Testing page refresh with active session...");
  
  // Simulate user starting a session
  const sessionId = MockSessionManager.getSessionId();
  console.log(`Created session: ${sessionId}`);
  
  // Simulate user progressing through workflow
  const progressiveStates = [
    {
      stage: "consultation",
      state: {
        uid: sessionId,
        conversationStarted: true,
        chatHistory: [
          { role: "user", content: "I have breast cancer" },
          { role: "assistant", content: "I'll help you find trials" }
        ],
        currentNode: "consultant"
      }
    },
    {
      stage: "medical_report",
      state: {
        uid: sessionId,
        conversationStarted: true,
        medicalReport: "Patient diagnosed with triple-negative breast cancer",
        chatHistory: [
          { role: "user", content: "I have breast cancer" },
          { role: "assistant", content: "I'll help you find trials" },
          { role: "assistant", content: "I've generated your medical report" }
        ],
        currentNode: "medical_report",
        showSearchTermSection: true
      }
    },
    {
      stage: "trials_search",
      state: {
        uid: sessionId,
        conversationStarted: true,
        medicalReport: "Patient diagnosed with triple-negative breast cancer",
        searchTerm: ["triple-negative breast cancer", "chemotherapy"],
        suggestedSearchTerm: "triple-negative breast cancer immunotherapy",
        chatHistory: [
          { role: "user", content: "I have breast cancer" },
          { role: "assistant", content: "I'll help you find trials" },
          { role: "assistant", content: "I've generated your medical report" },
          { role: "assistant", content: "Searching for trials..." }
        ],
        currentNode: "trials_search",
        showSearchTermSection: true,
        numStudiesFound: 12,
        activities: [
          { id: "1", title: "Medical Analysis", status: "completed" },
          { id: "2", title: "Trial Search", status: "active", progress: 80 }
        ],
        progress: 75
      }
    }
  ];
  
  // Test each stage
  progressiveStates.forEach(({ stage, state }) => {
    console.log(`\n  Testing ${stage} stage recovery...`);
    
    // Save state (simulating auto-save)
    MockSessionManager.saveSessionState(state);
    
    // Simulate page refresh (check if session can be recovered)
    const hasSession = MockSessionManager.hasActiveSession();
    const recoveryInfo = MockSessionManager.getRecoveryInfo();
    const savedState = MockSessionManager.getSessionState();
    
    // Verify recovery data accuracy
    const tests = [
      [`${stage} - Has active session`, hasSession],
      [`${stage} - Recovery info generated`, recoveryInfo !== null],
      [`${stage} - Chat history preserved`, savedState?.chatHistory?.length > 0],
      [`${stage} - Current node preserved`, savedState?.currentNode === state.currentNode]
    ];
    
    if (state.medicalReport) {
      tests.push([`${stage} - Medical report preserved`, savedState?.medicalReport === state.medicalReport]);
    }
    
    if (state.numStudiesFound > 0) {
      tests.push([`${stage} - Studies count preserved`, savedState?.numStudiesFound === state.numStudiesFound]);
      tests.push([`${stage} - Recovery shows studies`, recoveryInfo?.studiesFound === state.numStudiesFound]);
    }
    
    tests.forEach(([testName, result]) => {
      const status = result ? "✅ PASS" : "❌ FAIL";
      console.log(`    ${status} - ${testName}`);
      results.push({ test: testName, success: result });
    });
  });
  
  // Test 2: Session expiration handling
  console.log("\n2️⃣ Testing session expiration handling...");
  
  // Create an expired session
  const expiredSessionId = MockSessionManager.generateSessionId();
  const expiredSessionData = {
    sessionId: expiredSessionId,
    createdAt: Date.now() - (50 * 60 * 60 * 1000), // 50 hours ago
    lastActivity: Date.now() - (50 * 60 * 60 * 1000)
  };
  
  mockLocalStorage.setItem(MockSessionManager.SESSION_KEY, JSON.stringify(expiredSessionData));
  MockSessionManager.saveSessionState({
    uid: expiredSessionId,
    medicalReport: "This should be expired"
  });
  
  const expiredHasSession = MockSessionManager.hasActiveSession();
  console.log(`    ${expiredHasSession ? "❌ FAIL" : "✅ PASS"} - Expired session not recovered`);
  results.push({ test: "Expired session not recovered", success: !expiredHasSession });
  
  // Test 3: Invalid session data handling
  console.log("\n3️⃣ Testing invalid session data handling...");
  
  // Test corrupted JSON
  mockLocalStorage.setItem(MockSessionManager.SESSION_STATE_KEY, "invalid json {");
  const corruptedState = MockSessionManager.getSessionState();
  console.log(`    ${corruptedState === null ? "✅ PASS" : "❌ FAIL"} - Corrupted JSON handled`);
  results.push({ test: "Corrupted JSON handled", success: corruptedState === null });
  
  // Test missing required fields
  mockLocalStorage.setItem(MockSessionManager.SESSION_STATE_KEY, JSON.stringify({ noUid: true }));
  const invalidState = MockSessionManager.getSessionState();
  const isRecoverable = MockSessionManager.isRecoverableState(invalidState);
  console.log(`    ${!isRecoverable ? "✅ PASS" : "❌ FAIL"} - Invalid state not recoverable`);
  results.push({ test: "Invalid state not recoverable", success: !isRecoverable });
  
  // Summary
  const totalTests = results.length;
  const passedTests = results.filter(r => r.success).length;
  const successRate = (passedTests / totalTests * 100).toFixed(1);
  
  console.log("\n" + "=" * 50);
  console.log("📊 UI TEST SUMMARY");
  console.log("=" * 50);
  console.log(`Total Tests: ${totalTests}`);
  console.log(`✅ Passed: ${passedTests}`);
  console.log(`❌ Failed: ${totalTests - passedTests}`);
  console.log(`📈 Success Rate: ${successRate}%`);
  
  if (passedTests < totalTests) {
    console.log("\n❌ Failed Tests:");
    results.filter(r => !r.success).forEach(r => {
      console.log(`  - ${r.test}`);
    });
  }
  
  return passedTests === totalTests;
}

if (require.main === module) {
  const success = runUITests();
  process.exit(success ? 0 : 1);
}