import React, { useState, useEffect, useRef } from 'react';
import { Button, Input, Typography, List, message, Spin, Divider } from 'antd';
import ReactMarkdown from 'react-markdown';
import 'antd/dist/reset.css';

const { Title, Text } = Typography;

const WebSocketClient = () => {
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
  const [showTrialButtons, setShowTrialButtons] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    setSocket(ws);

    ws.onopen = () => {
      setConnected(true);
      message.success('Connected to server');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'connected') {
        message.success('WebSocket connection established');
      } else if (data.type === 'question' || data.type === 'update' || data.type === 'no_trial_found') {
        console.log("data.type", data.type)
        setChatHistory((prev) => [...prev, { role: 'assistant', content: data.content }]);
        setConversationStarted(true);
        if (data.type === 'no_trial_found') {
          console.log("NO TRIAL FOUND")
          setShowTrialButtons(false);
        }
      } else if (data.type === 'report') {
        setMedicalReport(data.content);
        setShowSearchTermSection(true);
      } else if (data.type === 'new_search_term') {
        setSuggestedSearchTerm(data.content);
      } else if (data.type === 'research_info') {
        setResearchInfo(data.state.research_info);
        setShowFinalResults(true);
        setLoading(false);
      } else if (data.type === 'search_term_added') {
        console.log("Search term added received:", data);
        message.success(`Search term added: ${data.content}`);
        setShowSearchTermSection(false);
        setLoading(true);
      } else if (data.type === 'search_term_exists') {
        message.warning(`Search term already exists: ${data.content}`);
      } else if (data.type === 'invalid_input') {
        message.error('Invalid input. Please try again.');
      } else if (data.type === 'workflow_complete') {
        message.success('Workflow completed');
      } else if (data.type === 'trials_found') {
        console.log("TRIALS FOUND")
        setShowTrialButtons(true);
      } else if (data.content === 'Clinical trials search completed') {
        message.info(`${data.state.studies_found} trials received for: ${searchTerm}`);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      message.error('WebSocket connection closed');
    };

    return () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory]);

  const handleStart = () => {
    if (socket) {
      socket.send(JSON.stringify({ command: 'start' }));
    }
  };

  const handleUserInput = () => {
    if (socket && userInput.trim()) {
      setChatHistory((prev) => [...prev, { role: 'user', content: userInput }]);
      socket.send(JSON.stringify({ command: 'user_input', input: userInput }));
      setUserInput('');
    }
  };

  const handleUserSearchTerm = () => {
    if (socket && (searchTerm.trim() || suggestedSearchTerm.trim())) {
      const termToAdd = searchTerm.trim() || suggestedSearchTerm;
      socket.send(JSON.stringify({ command: 'user_search_term', search_term: termToAdd }));
      setSearchTerm('');
    }
  };

  const handleContinueSearch = () => {
    if (socket) {
      socket.send(JSON.stringify({ command: 'continue_search', keep_searching: 'yes' }));
      setShowTrialButtons(false);
      setConversationStarted(true);
    }
  };

  const handleEndSearch = () => {
    if (socket) {
      socket.send(JSON.stringify({ command: 'continue_search', keep_searching: 'no' }));
      setShowTrialButtons(false);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <Title>Clinexus</Title>
      <div style={{ marginBottom: '20px' }}>
        {connected ? (
          <Text type="success">Connected to server</Text>
        ) : (
          <Text type="danger">Not connected to server</Text>
        )}
      </div>
      <div style={{ marginTop: '20px' }}>
      <List
        bordered
        dataSource={chatHistory}
        renderItem={(item) => (
            <List.Item>
            <Text strong>{item.role === 'user' ? 'You:' : 'Assistant:'}</Text> {item.content}
            </List.Item>
        )}
        style={{ marginBottom: '20px', maxHeight: '400px', overflow: 'auto' }}
        >
        <div ref={chatEndRef} />
        </List>
      </div>
      {!showSearchTermSection && !showFinalResults && !conversationStarted && (
        <Button type="primary" onClick={handleStart} disabled={!connected}>
          Start Conversation
        </Button>
      )}
      {!showSearchTermSection && conversationStarted && (
        <>
          <Input.TextArea
            rows={4}
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="Enter your response"
            style={{ marginBottom: '10px' }}
          />
          <Button type="primary" onClick={handleUserInput} disabled={!userInput.trim()}>
            Send Response
          </Button>
        </>
      )}
      {showSearchTermSection && (
        <div style={{ marginTop: '20px' }}>
          <Text strong>Suggested Search Term: </Text>
          <Input
            value={searchTerm || suggestedSearchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ marginBottom: '10px', width: '300px' }}
          />
          <Button type="primary" onClick={handleUserSearchTerm} disabled={!searchTerm.trim() && !suggestedSearchTerm.trim()}>
            Add Search Term
          </Button>
        </div>
      )}
      {loading && (
        <div style={{ marginTop: '20px', textAlign: 'center' }}>
          <Spin tip="Loading final research information..." />
        </div>
      )}
      {medicalReport && (
        <div style={{ marginTop: '20px' }}>
        <Divider style={{  borderColor: '#7cb305' }}>Medical Report</Divider>
          <ReactMarkdown>{medicalReport}</ReactMarkdown>
        </div>
      )}
      {researchInfo && (
        <div style={{ marginTop: '20px' }}>
          <Divider style={{  borderColor: '#7cb305' }}>Final Research Information</Divider>
          <ReactMarkdown>{researchInfo.toString()}</ReactMarkdown>
        </div>
      )}

      {showTrialButtons && (
        <div style={{ marginTop: '20px', textAlign: 'center' }}>
          <Button type="primary" onClick={handleContinueSearch} style={{ marginRight: '10px' }}>
            Continue Searching
          </Button>
          <Button type="default" onClick={handleEndSearch}>
            End Search
          </Button>
        </div>
      )}
    </div>
  );
};

export default WebSocketClient;
