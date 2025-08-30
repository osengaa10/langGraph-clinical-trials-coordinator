// Debug session detection issue - with fix
const { SessionManager } = require('./test_session_ui_recovery.js');

console.log('=== Debug Session Detection - Fixed ===\n');

console.log('1. Creating a new session...');
const sessionId = SessionManager.getSessionId(); // This creates the session
console.log('Created session ID:', sessionId);

// Create test state with the session ID
const testState = {
  uid: sessionId,
  medicalReport: 'Test medical report',
  chatHistory: [{ role: 'user', content: 'test message' }],
  conversationStarted: true,
  currentNode: 'search_term',
  showSearchTermSection: true,
  activities: [{ id: '1', title: 'Test activity', status: 'completed' }]
};

console.log('2. Saving session state...');
SessionManager.saveSessionState(testState);

console.log('3. Checking session data...');
const sessionData = SessionManager.getSessionData();
console.log('Session data exists:', !!sessionData);
console.log('Session ID matches:', sessionData?.sessionId === sessionId);

console.log('4. Checking session state...');
const state = SessionManager.getSessionState();
console.log('Session state keys:', state ? Object.keys(state) : 'null');

console.log('5. Checking session expired...');
const isExpired = SessionManager.isSessionExpired(sessionData);
console.log('Is expired:', isExpired);

console.log('6. Final hasActiveSession check...');
const hasActive = SessionManager.hasActiveSession();
console.log('Has active session:', hasActive);

console.log('7. Get recovery info...');
const recoveryInfo = SessionManager.getRecoveryInfo();
console.log('Recovery info:', JSON.stringify(recoveryInfo, null, 2));

// Clean up
SessionManager.clearSession();