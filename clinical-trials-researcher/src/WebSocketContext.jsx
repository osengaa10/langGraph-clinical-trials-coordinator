import React, { createContext, useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { message } from 'antd';
import SessionManager from './SessionManager.js';

export const WebSocketContext = createContext();

export const WebSocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [medicalReport, setMedicalReport] = useState('');
  const [suggestedSearchTerm, setSuggestedSearchTerm] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showSearchTermSection, setShowSearchTermSection] = useState(false);
  const [showFinalResults, setShowFinalResults] = useState(false);
  const [researchInfo, setResearchInfo] = useState('');
  const [conversationStarted, setConversationStarted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showRetryButton, setShowRetryButton] = useState(false);
  const [retryCountdown, setRetryCountdown] = useState(60);
  const [retryCommand, setRetryCommand] = useState('');
  const [retryData, setRetryData] = useState('');
  const [numStudiesFound, setNumStudiesFound] = useState(0);
  const [currentNode, setCurrentNode] = useState("consultant"); 
  const [showTrialButtons, setShowTrialButtons] = useState(false);
  const [activities, setActivities] = useState([]);
  const [statusMessage, setStatusMessage] = useState('');
  const [progress, setProgress] = useState(0);
  const [customMessage, setCustomMessage] = useState('');
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sessionRecovery, setSessionRecovery] = useState({
    showRecovery: false,
    recoveryInfo: null,
    loading: false
  });

  const chatEndRef = useRef(null);
  
  const websocketBaseUrl = import.meta.env.VITE_WEBSOCKET_URL;

  // Helper function to add activity
  const addActivity = (title, description, status = 'active', stats = null, id = null) => {
    const newActivity = {
      id: id || uuidv4(),
      title,
      description,
      status,
      stats,
      timestamp: Date.now(),
      progress: status === 'completed' ? 100 : undefined
    };
    setActivities(prev => [...prev, newActivity]);
    return newActivity.id;
  };

  // Helper function to update activity status
  const updateActivityStatus = (activityId, status, progress) => {
    setActivities(prev => prev.map(activity => 
      activity.id === activityId 
        ? { ...activity, status, progress, timestamp: Date.now() }
        : activity
    ));
  };

  useEffect(() => {
    // Check for existing session on component mount
    const checkForExistingSession = async () => {
      try {
        // First check local storage
        let hasLocalSession = false;
        if (SessionManager.hasActiveSession()) {
          const sessionState = SessionManager.getSessionState();
          
          // Validate session before offering recovery
          if (SessionManager.isRecoverableState(sessionState)) {
            const validation = SessionManager.validateSessionIntegrity(sessionState);
            
            if (validation.isValid) {
              const recoveryInfo = SessionManager.getRecoveryInfo();
              
              if (recoveryInfo) {
                hasLocalSession = true; // Mark that we found a local session
                setSessionRecovery({
                  showRecovery: true,
                  recoveryInfo,
                  loading: false
                });
                return; // Don't connect WebSocket yet, wait for user choice
              }
            } else {
              console.warn('Session validation failed, starting fresh:', validation.errors);
              SessionManager.clearSession();
            }
          } else {
            console.log('Session not recoverable, clearing and starting fresh');
            SessionManager.clearSession();
          }
        }

        // If no local session, check backend for recoverable sessions
        if (!hasLocalSession) {
          try {
            const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/sessions/check`);
            if (response.ok) {
              const data = await response.json();
              
              if (data.hasRecoverableSession) {
                console.log('Found recoverable session on backend:', data.session);
                
                // Create local session data from backend session
                SessionManager.createSession(data.session.sessionId);
                SessionManager.saveSessionState(data.session.state);
                
                setSessionRecovery({
                  showRecovery: true,
                  recoveryInfo: data.session.recoveryInfo,
                  loading: false
                });
                return; // Don't connect WebSocket yet, wait for user choice
              }
            }
          } catch (error) {
            console.warn('Could not check backend for recoverable sessions:', error);
            // Continue with new session
          }
        }
        
        // No existing session or not recoverable, start new session
        initializeNewSession();
      } catch (error) {
        console.error('Error checking existing session:', error);
        // Clear potentially corrupted session and start fresh
        SessionManager.clearSession();
        initializeNewSession();
      }
    };
    
    checkForExistingSession();
  }, []);

  const initializeNewSession = () => {
    const uid = SessionManager.getSessionId();
    setCurrentSessionId(uid);
    const ws = new WebSocket(`${websocketBaseUrl}?uid=${uid}`);
    setSocket(ws);
    
    connectWebSocket(ws, uid);
  };

  const recoverSession = async () => {
    setSessionRecovery(prev => ({ ...prev, loading: true }));
    
    try {
      const sessionState = SessionManager.getSessionState();
      const uid = sessionState?.uid;
      
      if (!uid) {
        throw new Error('No valid session ID found');
      }

      // Validate session integrity before recovery
      const validation = SessionManager.validateSessionIntegrity(sessionState);
      if (!validation.isValid) {
        throw new Error(`Session validation failed: ${validation.errors.join(', ')}`);
      }

      // Show warnings if any
      if (validation.warnings.length > 0) {
        console.warn('Session recovery warnings:', validation.warnings);
        message.warning(`Session recovered with warnings: ${validation.warnings[0]}`);
      }
      
      // Restore state from localStorage first
      restoreSessionState(sessionState);
      
      // Connect WebSocket with recovered session
      setCurrentSessionId(uid);
      const ws = new WebSocket(`${websocketBaseUrl}?uid=${uid}&recover=true`);
      setSocket(ws);
      
      // Set up WebSocket handlers and wait for recovery confirmation
      connectWebSocket(ws, uid, true); // Pass recovery flag
      
      // Wait for connection and recovery confirmation
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Connection timeout during recovery'));
        }, 15000); // 15 second timeout for recovery
        
        let connectionReceived = false;
        let recoveryComplete = false;
        
        // Override the onmessage temporarily to wait for recovery confirmation
        const originalOnMessage = ws.onmessage;
        
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          
          if (data.type === 'connected') {
            connectionReceived = true;
            if (data.recovered) {
              console.log('Server confirmed session recovery');
            } else {
              clearTimeout(timeout);
              reject(new Error('Server could not recover session'));
              return;
            }
          }
          
          // Handle recovery messages during recovery process
          if (connectionReceived && (
            data.type === 'report' ||
            data.type === 'new_search_term' ||
            data.type === 'studies_found' ||
            data.type === 'research_info'
          )) {
            // Process recovery messages to restore UI state
            handleRecoveryMessage(data);
            
            // Set a timeout to complete recovery after processing all messages
            setTimeout(() => {
              if (!recoveryComplete) {
                recoveryComplete = true;
                clearTimeout(timeout);
                ws.onmessage = originalOnMessage;
                resolve(data);
              }
            }, 500); // Small delay to allow all recovery messages to process
            return;
          }
          
          // Check for status-only recovery completion (when no other data to restore)
          if (connectionReceived && data.type === 'status' && !data.medical_report && !data.studies_found) {
            recoveryComplete = true;
            clearTimeout(timeout);
            ws.onmessage = originalOnMessage;
            originalOnMessage(event);
            resolve(data);
            return;
          }
          
          // For other messages, pass to original handler
          if (originalOnMessage) {
            originalOnMessage(event);
          }
        };
      });
      
      setSessionRecovery({ showRecovery: false, recoveryInfo: null, loading: false });
      message.success('Session recovered successfully!');
      
    } catch (error) {
      console.error('Error recovering session:', error);
      message.error('Failed to recover session. Starting fresh.');
      startFreshSession();
    }
  };

  const restoreSessionState = (sessionState) => {
    // Restore UI state from localStorage
    if (sessionState.chatHistory) setChatHistory(sessionState.chatHistory);
    if (sessionState.medicalReport) setMedicalReport(sessionState.medicalReport);
    if (sessionState.searchTerm) setSearchTerm(sessionState.searchTerm);
    if (sessionState.suggestedSearchTerm) setSuggestedSearchTerm(sessionState.suggestedSearchTerm);
    if (sessionState.currentNode) setCurrentNode(sessionState.currentNode);
    if (sessionState.conversationStarted !== undefined) setConversationStarted(sessionState.conversationStarted);
    if (sessionState.showSearchTermSection !== undefined) setShowSearchTermSection(sessionState.showSearchTermSection);
    if (sessionState.showFinalResults !== undefined) setShowFinalResults(sessionState.showFinalResults);
    if (sessionState.researchInfo) setResearchInfo(sessionState.researchInfo);
    if (sessionState.numStudiesFound !== undefined) setNumStudiesFound(sessionState.numStudiesFound);
    if (sessionState.activities) setActivities(sessionState.activities);
    
    // Restore additional UI state
    if (sessionState.loading !== undefined) setLoading(sessionState.loading);
    if (sessionState.showTrialButtons !== undefined) setShowTrialButtons(sessionState.showTrialButtons);
    if (sessionState.progress !== undefined) setProgress(sessionState.progress);
    if (sessionState.customMessage) setCustomMessage(sessionState.customMessage);
  };

  const handleRecoveryMessage = (data) => {
    // Process WebSocket messages during recovery to update UI state
    if (data.current_node) {
      setCurrentNode(data.current_node);
    } else if (data.current_step) {
      setCurrentNode(data.current_step);
    }

    switch (data.type) {
      case 'report':
        // Restore medical report and enable search term section
        setMedicalReport(data.content);
        setShowSearchTermSection(true);
        addActivity('Medical Report Restored', 'Your medical report has been recovered', 'completed');
        break;
      case 'new_search_term':
        // Restore suggested search terms
        setSuggestedSearchTerm(data.content);
        addActivity('Search Terms Restored', `Recovered search terms: "${data.content}"`, 'completed');
        break;
      case 'studies_found':
        setNumStudiesFound(data.state?.studies_found_count || 0);
        addActivity(
          'Clinical Trials Found', 
          `Found ${data.state?.studies_found_count || 0} potential trials matching your condition`,
          'completed',
          { 'Trials Found': data.state?.studies_found_count || 0 }
        );
        break;
      case 'research_info':
        setResearchInfo(data.state?.research_info || '');
        setShowFinalResults(true);
        setLoading(false);
        addActivity('Trial Analysis Complete', 'AI has analyzed all trials and prepared personalized recommendations', 'completed');
        break;
      case 'status':
        if (data.message) {
          setCustomMessage(data.message);
          // Use specific activity info from backend if available
          if (data.activity) {
            addActivity(
              data.activity.title || 'Status Update',
              data.activity.description || data.message,
              data.activity.status || 'active',
              data.activity.stats || null,
              data.activity.id || null
            );
          } else {
            addActivity('Status Update', data.message, 'active');
          }
        }
        break;
      case 'activity_update':
        if (data.activity && data.activity.id) {
          const { id, status, description, progress } = data.activity;
          setActivities(prev => prev.map(activity => 
            activity.id === id 
              ? { 
                  ...activity, 
                  status, 
                  description: description || activity.description,
                  progress: progress !== undefined ? progress : (status === 'completed' ? 100 : activity.progress),
                  timestamp: Date.now() 
                }
              : activity
          ));
        }
        break;
      default:
        // Let the regular message handler process other message types
        break;
    }
  };

  const startFreshSession = () => {
    SessionManager.clearSession();
    setSessionRecovery({ showRecovery: false, recoveryInfo: null, loading: false });
    
    // Reset all state
    setChatHistory([]);
    setMedicalReport('');
    setSearchTerm('');
    setSuggestedSearchTerm('');
    setCurrentNode('consultant');
    setConversationStarted(false);
    setShowSearchTermSection(false);
    setShowFinalResults(false);
    setResearchInfo('');
    setNumStudiesFound(0);
    setActivities([]);
    setProgress(0);
    setCustomMessage('');
    
    initializeNewSession();
  };

  const connectWebSocket = (ws, uid, isRecovery = false) => {

    ws.onopen = () => {
      setConnected(true);
      SessionManager.updateLastActivity();
      
      // Don't show initial connection message during recovery
      if (!isRecovery) {
        // Initial connection handling
      }
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.current_node) {
        setCurrentNode(data.current_node);
      } else if (data.current_step) {
        setCurrentNode(data.current_step);
      }


      if (data.type === 'ping') {
        ws.send(JSON.stringify({ type: 'pong' })); 
        return;
      }
      switch (data.type) {
        case 'connected':
          if (data.recovered) {
            message.success('Session recovered successfully!');
          } else {
            message.success('WebSocket connection established');
          }
          // Save current state to include the new socket UID
          setTimeout(() => saveCurrentState(), 1000);
          break;
        case 'question':
          setActivities((prev) => {
            const hasConsultationStarted = prev.some(activity => activity.title === 'Consultation Started');
            if (!hasConsultationStarted) {
              return [...prev, {
                id: uuidv4(),
                title: 'Consultation Started',
                description: 'AI consultant is asking follow-up questions',
                status: 'active',
                stats: null,
                timestamp: Date.now(),
                progress: undefined
              }];
            }
            return prev;
          });
          setChatHistory((prev) => [...prev, { role: 'assistant', content: data.content }]);
          setConversationStarted(true);
          break;
        case 'update':
          addActivity('Processing Update', data.content, 'active');
          setChatHistory((prev) => [...prev, { role: 'assistant', content: data.content }]);
          setConversationStarted(true);
          break;
        case 'studies_found':
            setNumStudiesFound(data.state.studies_found_count);
            message.success(`${data.state.studies_found_count} trials found`);
            addActivity(
              'Clinical Trials Found', 
              `Found ${data.state.studies_found_count} potential trials matching your condition`,
              'completed',
              { 'Trials Found': data.state.studies_found_count }
            );
            setChatHistory((prev) => [...prev, { role: 'assistant', content: data.content }]);
            setConversationStarted(true);
            break;
        case 'no_trial_found':
          setChatHistory((prev) => [...prev, { role: 'assistant', content: data.content }]);
          setConversationStarted(true);
          addActivity('Trial Search Complete', 'No suitable trials found for current search terms', 'completed');
          break;
        case 'report':
          setMedicalReport(data.content);
          setShowSearchTermSection(true);
          addActivity('Medical Report Generated', 'Comprehensive medical summary created from your information', 'completed');
          // Save state immediately after medical report is generated with explicit state
          setTimeout(() => {
            const reportState = {
              uid: currentSessionId || SessionManager.getSessionId(),
              chatHistory: [...chatHistory, { role: 'assistant', content: 'Medical report generated' }],
              medicalReport: data.content,
              searchTerm,
              suggestedSearchTerm,
              currentNode,
              conversationStarted: true,
              showSearchTermSection: true,
              showFinalResults,
              researchInfo,
              numStudiesFound,
              activities: [...activities],
              progress,
              customMessage,
              loading: false,
              showTrialButtons
            };
            SessionManager.saveSessionState(reportState);
          }, 200);
          break;
        case 'new_search_term':
          setSuggestedSearchTerm(data.content);
          addActivity('Search Terms Generated', `Optimized search terms: "${data.content}"`, 'completed');
          // Save state immediately after search terms are generated
          setTimeout(() => saveCurrentState(), 100);
          break;
        case 'research_info':
          setResearchInfo(data.state.research_info);
          setShowFinalResults(true);
          setLoading(false);
          addActivity('Trial Analysis Complete', 'AI has analyzed all trials and prepared personalized recommendations', 'completed');
          break;
        case 'search_term_added':
          message.success(`Search term added: ${data.content}`);
          setShowSearchTermSection(false);
          setLoading(true);
          addActivity('Search Initiated', `Starting clinical trials search with term: "${data.content}"`, 'active');
          break;
        case 'search_term_exists':
          message.warning(`Search term already exists: ${data.content}`);
          break;
        case 'invalid_input':
          message.error('Invalid input. Please try again.');
          break;
        case 'trials_found':
            setShowTrialButtons(true);
            addActivity('Suitable Trials Identified', 'Found trials that match your medical profile and eligibility criteria', 'completed');
            break;
        case 'no_trials_found':
            setShowTrialButtons(true);
            addActivity('Trial Search Complete', 'Search completed - consider expanding criteria or consulting with AI for alternatives', 'completed');
            break;
        case 'need_new_term':
            console.log("no studies found")
            alert(`no studies found for search term '${searchTerm}'. Please try another`)
            setLoading(false);
            console.log(`loading: ${loading}`)
            setShowSearchTermSection(true);
            console.log(`showSearchTermSection: ${showSearchTermSection}`)
            break;
        case 'rate_limit_error': {
          setRetryCommand(data.retry_command);
          setRetryData(data.retry_data);
          alert(data.message);
          setShowRetryButton(true);
          let countdown = 60;
          setRetryCountdown(countdown);
          const countdownInterval = setInterval(() => {
            countdown -= 1;
            setRetryCountdown(countdown);
            if (countdown === 0) clearInterval(countdownInterval);
          }, 1000);
          break;
        }
        case 'status':
          if (data.message) {
            setCustomMessage(data.message);
            // Use specific activity info from backend if available
            if (data.activity) {
              addActivity(
                data.activity.title || 'Status Update',
                data.activity.description || data.message,
                data.activity.status || 'active',
                data.activity.stats || null,
                data.activity.id || null
              );
            } else {
              addActivity('Status Update', data.message, 'active');
            }
          }
          break;
        case 'activity_update':
          if (data.activity && data.activity.id) {
            const { id, status, description, progress } = data.activity;
            setActivities(prev => prev.map(activity => 
              activity.id === id 
                ? { 
                    ...activity, 
                    status, 
                    description: description || activity.description,
                    progress: progress !== undefined ? progress : (status === 'completed' ? 100 : activity.progress),
                    timestamp: Date.now() 
                  }
                : activity
            ));
          }
          break;
        case 'embedding_studies':
          addActivity('Processing Trial Data', 'Converting trial documents into searchable format for AI analysis', 'active');
          break;
        case 'cleanup_complete':
          if (data.success) {
            addActivity('Session Cleanup Complete', 'All session resources cleaned up successfully', 'completed');
            message.success('Session ended and cleaned up successfully');
            // Clear localStorage after successful cleanup
            SessionManager.clearSession();
          } else {
            addActivity('Session Cleanup', `Cleanup completed with errors: ${data.errors?.length || 0} errors`, 'completed');
            message.warning('Session cleanup completed with some errors');
            // Still clear localStorage even with errors
            SessionManager.clearSession();
          }
          break;
        case 'cleanup_error':
          addActivity('Session Cleanup Error', data.content, 'error');
          message.error('Session cleanup failed');
          break;
        case 'workflow_complete':
          if (data.content.includes('cleaned up')) {
            addActivity('Workflow Complete', 'Session ended and all resources cleaned up', 'completed');
          } else {
            addActivity('Workflow Complete', data.content, 'completed');
          }
          message.success('Workflow completed');
          break;
        default:
          console.warn('Unhandled WebSocket message:', data);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      // Save session state on disconnect
      saveCurrentState();
    };

    // Set up page visibility handlers for session persistence
    const cleanupVisibilityHandlers = SessionManager.addPageVisibilityHandlers(
      saveCurrentState, // On page hidden
      () => SessionManager.updateLastActivity() // On page visible
    );

    return () => {
      ws.close();
      cleanupVisibilityHandlers();
    };
  };

  // Save current application state to localStorage
  const saveCurrentState = () => {
    const currentState = {
      uid: currentSessionId || SessionManager.getSessionId(),
      chatHistory,
      medicalReport,
      searchTerm,
      suggestedSearchTerm,
      currentNode,
      conversationStarted,
      showSearchTermSection,
      showFinalResults,
      researchInfo,
      numStudiesFound,
      activities,
      progress,
      customMessage,
      loading,
      showTrialButtons
    };
    
    SessionManager.saveSessionState(currentState);
  };

  // Auto-save state periodically and on important changes
  useEffect(() => {
    const autoSaveInterval = setInterval(() => {
      if (connected) {
        saveCurrentState();
      }
    }, 30000); // Save every 30 seconds

    return () => clearInterval(autoSaveInterval);
  }, [connected, chatHistory, medicalReport, currentNode, conversationStarted, activities, 
      showSearchTermSection, showFinalResults, showTrialButtons, loading, currentSessionId]);


  return (
    <WebSocketContext.Provider value={{
      socket,
      connected,
      chatHistory,
      userInput,
      setUserInput,
      medicalReport,
      suggestedSearchTerm,
      setSuggestedSearchTerm,
      searchTerm,
      setSearchTerm,
      showSearchTermSection,
      showFinalResults,
      researchInfo,
      conversationStarted,
      loading,
      showRetryButton,
      retryCountdown,
      retryCommand,
      retryData,
      chatEndRef,
      numStudiesFound,
      setNumStudiesFound,
      currentNode,
      setCurrentNode,
      setShowTrialButtons,
      setChatHistory,
      showTrialButtons,
      activities,
      setActivities,
      addActivity,
      updateActivityStatus,
      statusMessage,
      setStatusMessage,
      progress,
      setProgress,
      customMessage,
      setCustomMessage,
      sessionRecovery,
      recoverSession,
      startFreshSession,
      saveCurrentState
    }}>
      {children}
    </WebSocketContext.Provider>
  );
};