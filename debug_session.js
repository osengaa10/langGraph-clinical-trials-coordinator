// Debug session detection issue
const { SessionManager } = require('./test_session_ui_recovery.js');

console.log('=== Debug Session Detection ===\n');

// Create test state
const testState = {
  uid: 'debug-session-123',
  medicalReport: 'Test medical report',
  chatHistory: [{ role: 'user', content: 'test message' }],
  conversationStarted: true
};

console.log('1. Saving session state...');
SessionManager.saveSessionState(testState);

console.log('2. Checking session data...');
const sessionData = SessionManager.getSessionData();
console.log('Session data:', sessionData);

console.log('3. Checking session state...');
const state = SessionManager.getSessionState();
console.log('Session state keys:', state ? Object.keys(state) : 'null');
console.log('State object length:', state ? Object.keys(state).length : 0);

console.log('4. Checking session expired...');
const isExpired = SessionManager.isSessionExpired(sessionData);
console.log('Is expired:', isExpired);

console.log('5. Final hasActiveSession check...');
const hasActive = SessionManager.hasActiveSession();
console.log('Has active session:', hasActive);

console.log('6. Get recovery info...');
const recoveryInfo = SessionManager.getRecoveryInfo();
console.log('Recovery info:', recoveryInfo);

// Clean up
SessionManager.clearSession();