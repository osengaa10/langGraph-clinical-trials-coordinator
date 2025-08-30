class SessionManager {
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
    
    // Create new session if none exists or expired
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
    
    localStorage.setItem(this.SESSION_KEY, JSON.stringify(sessionData));
    this.clearSessionState(); // Clear any old state
    return sessionData;
  }

  static getSessionData() {
    try {
      const data = localStorage.getItem(this.SESSION_KEY);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error parsing session data:', error);
      return null;
    }
  }

  static updateLastActivity() {
    const sessionData = this.getSessionData();
    if (sessionData) {
      sessionData.lastActivity = Date.now();
      localStorage.setItem(this.SESSION_KEY, JSON.stringify(sessionData));
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
    try {
      // Only save essential state that should survive page refresh
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

      localStorage.setItem(this.SESSION_STATE_KEY, JSON.stringify(essentialState));
      this.updateLastActivity();
    } catch (error) {
      console.error('Error saving session state:', error);
    }
  }

  static getSessionState() {
    try {
      const data = localStorage.getItem(this.SESSION_STATE_KEY);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error parsing session state:', error);
      return null;
    }
  }

  static clearSession() {
    localStorage.removeItem(this.SESSION_KEY);
    this.clearSessionState();
  }

  static clearSessionState() {
    localStorage.removeItem(this.SESSION_STATE_KEY);
  }

  static getSessionAge() {
    const sessionData = this.getSessionData();
    if (!sessionData) return 0;
    return Date.now() - sessionData.createdAt;
  }

  static formatSessionAge() {
    const ageMs = this.getSessionAge();
    const minutes = Math.floor(ageMs / (1000 * 60));
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) {
      return `${days} day${days > 1 ? 's' : ''} ago`;
    } else if (hours > 0) {
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    }
  }

  static addPageVisibilityHandlers(onPageHidden, onPageVisible) {
    const handleVisibilityChange = () => {
      if (document.hidden && onPageHidden) {
        onPageHidden();
      } else if (!document.hidden && onPageVisible) {
        onPageVisible();
      }
    };

    const handleBeforeUnload = (event) => {
      if (onPageHidden) {
        onPageHidden();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('beforeunload', handleBeforeUnload);

    // Return cleanup function
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }

  static isRecoverableState(state) {
    if (!state) return false;
    
    // Check for required fields
    if (!state.uid) return false;
    
    // Check if we have enough meaningful progress to recover
    const hasProgress = (
      state.conversationStarted ||
      state.medicalReport ||
      (state.chatHistory && state.chatHistory.length > 0) ||
      (state.searchTerm && state.searchTerm.length > 0) ||
      state.numStudiesFound > 0 ||
      state.researchInfo
    );
    
    // Check if session isn't too old (older than 48 hours)
    const sessionData = this.getSessionData();
    if (sessionData && this.isSessionExpired(sessionData)) {
      return false;
    }
    
    return hasProgress;
  }

  static validateSessionIntegrity(state) {
    const validation = {
      isValid: true,
      errors: [],
      warnings: []
    };

    if (!state) {
      validation.isValid = false;
      validation.errors.push('No session state found');
      return validation;
    }

    // Check essential fields
    if (!state.uid) {
      validation.isValid = false;
      validation.errors.push('Missing session ID');
    }

    // Check for data consistency
    if (state.numStudiesFound > 0 && !state.searchTerm) {
      validation.warnings.push('Studies found but no search term recorded');
    }

    if (state.researchInfo && state.numStudiesFound === 0) {
      validation.warnings.push('Research info exists but no studies recorded');
    }

    if (state.showFinalResults && !state.researchInfo) {
      validation.warnings.push('Final results shown but no research info available');
    }

    // Check for corrupted data
    try {
      if (state.chatHistory && !Array.isArray(state.chatHistory)) {
        validation.isValid = false;
        validation.errors.push('Chat history is corrupted');
      }

      if (state.activities && !Array.isArray(state.activities)) {
        validation.warnings.push('Activities data is corrupted');
      }
    } catch (e) {
      validation.isValid = false;
      validation.errors.push('Session data is corrupted');
    }

    return validation;
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
}

export default SessionManager;