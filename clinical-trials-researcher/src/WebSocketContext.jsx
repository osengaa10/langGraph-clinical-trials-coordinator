import React, { createContext, useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { message } from 'antd';

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

  const chatEndRef = useRef(null);
  
  const websocketBaseUrl = import.meta.env.VITE_WEBSOCKET_URL;

  useEffect(() => {
    const uid = uuidv4();
    const ws = new WebSocket(`${websocketBaseUrl}?uid=${uid}`);
    setSocket(ws);

    ws.onopen = () => {
      setConnected(true);
      message.success('Connected to server');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.current_step) {
        setCurrentNode(data.current_step);  // Update current node
      }
      
      switch (data.type) {
        case 'connected':
          message.success('WebSocket connection established');
          break;
        case 'question':
        case 'update':
        case 'studies_found':
            setNumStudiesFound(data.state.studies_found)
        case 'no_trial_found':
          setChatHistory((prev) => [...prev, { role: 'assistant', content: data.content }]);
          setConversationStarted(true);
          break;
        case 'report':
          setMedicalReport(data.content);
          setShowSearchTermSection(true);
          break;
        case 'new_search_term':
          setSuggestedSearchTerm(data.content);
          break;
        case 'research_info':
          setResearchInfo(data.state.research_info);
          setShowFinalResults(true);
          setLoading(false);
          break;
        case 'search_term_added':
          message.success(`Search term added: ${data.content}`);
          setShowSearchTermSection(false);
          setLoading(true);
          break;
        case 'search_term_exists':
          message.warning(`Search term already exists: ${data.content}`);
          break;
        case 'invalid_input':
          message.error('Invalid input. Please try again.');
          break;
        case 'workflow_complete':
          message.success('Workflow completed');
          break;
        case 'trials_found':
          break;
        case 'rate_limit_error':
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
        default:
          console.warn('Unhandled WebSocket message:', data);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      message.error('WebSocket connection closed');
    };

    return () => ws.close();
  }, []);

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
      currentNode
    }}>
      {children}
    </WebSocketContext.Provider>
  );
};