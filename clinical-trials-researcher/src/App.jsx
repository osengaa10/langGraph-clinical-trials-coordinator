import React, { useState, useEffect } from 'react';
import { Button, Input, Typography, List, message } from 'antd';
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
      } else if (data.type === 'question' || data.type === 'update' || data.type === 'trial_found' || data.type === 'no_trial_found') {
        setChatHistory((prev) => [...prev, { role: 'assistant', content: data.content }]);
      } else if (data.type === 'report') {
        setMedicalReport(data.content);
        setShowSearchTermSection(true);
      } else if (data.type === 'new_search_term') {
        setSuggestedSearchTerm(data.content);
      } else if (data.type === 'research_info') {
        setResearchInfo(data.content);
        setShowFinalResults(true);
      } else if (data.type === 'search_term_added') {
        message.success(`Search term added: ${data.content}`);
      } else if (data.type === 'search_term_exists') {
        message.warning(`Search term already exists: ${data.content}`);
      } else if (data.type === 'invalid_input') {
        message.error('Invalid input. Please try again.');
      } else if (data.type === 'workflow_complete') {
        message.success('Workflow completed');
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

  const handleSearchTermDecision = (decision) => {
    if (socket) {
      socket.send(JSON.stringify({ command: 'search_term_decision', decision }));
      if (decision === 'yes') {
        setShowSearchTermSection(false);
      }
    }
  };

  const handleUserSearchTerm = () => {
    if (socket && searchTerm.trim()) {
      socket.send(JSON.stringify({ command: 'user_search_term', search_term: searchTerm }));
      setSearchTerm('');
      setShowSearchTermSection(false);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <Title>Medical Workflow Chat</Title>
      <div style={{ marginBottom: '20px' }}>
        {connected ? (
          <Text type="success">Connected to server</Text>
        ) : (
          <Text type="danger">Not connected to server</Text>
        )}
      </div>
      {!showSearchTermSection && !showFinalResults && (
        <>
          <Button type="primary" onClick={handleStart} disabled={!connected}>
            Start Conversation
          </Button>
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
            />
          </div>
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
          <Title level={4}>Medical Report</Title>
          <ReactMarkdown>{medicalReport}</ReactMarkdown>
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
          <div style={{ marginTop: '20px' }}>
            <Button type="default" onClick={() => handleSearchTermDecision('yes')}>
              Accept Suggested Search Term
            </Button>
            <Button type="default" onClick={() => handleSearchTermDecision('no')} style={{ marginLeft: '10px' }}>
              Provide Custom Search Term
            </Button>
          </div>
        </div>
      )}
      {showFinalResults && (
        <div style={{ marginTop: '20px' }}>
          <Title level={4}>Final Research Information</Title>
          <ReactMarkdown>{researchInfo}</ReactMarkdown>
        </div>
      )}
    </div>
  );
};

export default WebSocketClient;