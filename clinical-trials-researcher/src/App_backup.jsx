import React, { useState, useEffect, useRef } from 'react';
import { Button, Input, Typography, List, message, Spin, Divider, Card } from 'antd';
import ReactMarkdown from 'react-markdown';
import 'antd/dist/reset.css';
import { v4 as uuidv4 } from 'uuid';
import { Upload } from 'antd';
import { InboxOutlined } from '@ant-design/icons';

const { Dragger } = Upload;

const { Title, Text } = Typography;

const WebSocketClient = () => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [medicalReport, setMedicalReport] = useState('');
  const [suggestedSearchTerm, setSuggestedSearchTerm] = useState('');
  const [searchTerm, setSearchTerm] = useState(suggestedSearchTerm);
  const [showSearchTermSection, setShowSearchTermSection] = useState(false);
  const [showFinalResults, setShowFinalResults] = useState(false);
  const [researchInfo, setResearchInfo] = useState('');
  const [conversationStarted, setConversationStarted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showTrialButtons, setShowTrialButtons] = useState(false);
  const [showRetryButton, setShowRetryButton] = useState(false);
  const [retryCountdown, setRetryCountdown] = useState(60);
  const [retryCommand, setRetryCommand] = useState("")
  const [retryData, setRetryData] = useState("")
  const chatEndRef = useRef(null);
  const userInputRef = useRef(null);
  const [userUid, setUserUid] = useState(null)
  const [isUploading, setIsUploading] = useState(false);

   const websocketBaseUrl = import.meta.env.VITE_WEBSOCKET_URL
  useEffect(() => {
    const uid = uuidv4();
    setUserUid(uid)
    const ws = new WebSocket(`${websocketBaseUrl}?uid=${uid}`);
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
        setChatHistory((prev) => [...prev, { role: 'assistant', content: data.content }]);
        setConversationStarted(true);
        if (data.type === 'no_trial_found') {
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
        setShowTrialButtons(true);
      } else if (data.content === 'Clinical trials search completed') {
        message.info(`${data.state.studies_found} trials received for: ${searchTerm}`);
      } else if (data.content === 'no studies found') {
        console.log("no studies found")
        alert(`no studies found for search term '${searchTerm}'. Please try another`)
        setLoading(false);
        console.log(`loading: ${loading}`)
        setShowSearchTermSection(true);
        console.log(`showSearchTermSection: ${showSearchTermSection}`)
      } else if (data.type === 'rate_limit_error') {
        setRetryCommand(data.retry_command)
        setRetryData(data.retry_data)
        alert(data.message);
        setShowRetryButton(true);
        let countdown = 60;
        setRetryCountdown(countdown);
        const countdownInterval = setInterval(() => {
          countdown -= 1;
          setRetryCountdown(countdown);
          if (countdown === 0) {
            clearInterval(countdownInterval);
          }
        }, 1000);
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

  useEffect(() => {
    if (userInputRef.current) {
      userInputRef.current.scrollTop = 0;
    }
  }, [userInput]);

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

  const handleFileUpload = async (file) => {
    setIsUploading(true);
    const reader = new FileReader();
    reader.onload = async (e) => {
      const base64Data = e.target.result.split(',')[1];
      if (socket) {
        socket.send(JSON.stringify({ 
          command: 'upload', 
          data: base64Data,
          filename: file.name 
        }));
      }
    };
    reader.readAsDataURL(file);
    return false; // Prevent default upload behavior
  };

  const handleUserSearchTerm = () => {
    if (socket && (searchTerm.trim() || suggestedSearchTerm.trim())) {
      const termToAdd = searchTerm.trim() || suggestedSearchTerm;
      socket.send(JSON.stringify({ command: 'user_search_term', search_term: termToAdd }));
      setSearchTerm('');
      setSuggestedSearchTerm(suggestedSearchTerm);
    }
  };

  const handleUndoSearchTerm = () => {
    setSearchTerm(suggestedSearchTerm);
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
      socket.send(JSON.stringify({ command: 'cleanup', keep_searching: 'no' }));
      setShowTrialButtons(false);
    }
  };

  const handleRetry = () => {
    if (socket) {
    //   socket.send(JSON.stringify({ command: 'retry' }));
      socket.send(JSON.stringify({
        command: 'retry',
        retry_command: retryCommand,
        retry_data: retryData
    }));
      setShowRetryButton(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && userInput.trim()) {
      e.preventDefault();
      handleUserInput();
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ position: 'sticky', top: 0, background: '#fff', zIndex: 1, paddingBottom: '10px' }}>
        <Title>Clinexus</Title>
        <div style={{ marginBottom: '20px' }}>
          {connected ? (
            <Text type="success">Connected to server</Text>
          ) : (
            <Text type="danger">Not connected to server</Text>
          )}
        </div>
      </div>
      <div style={{ marginTop: '20px' }}>
        <List
          bordered
          dataSource={chatHistory}
          renderItem={(item) => (
            <List.Item style={{ backgroundColor: item.role === 'user' ? '#f0f5ff' : '#fffbe6' }}>
              <Text strong>{item.role === 'user' ? 'You:' : 'Assistant:'}</Text> {item.content}
            </List.Item>
          )}
          style={{ marginBottom: '20px', maxHeight: '400px', overflow: 'auto' }}
        >
          <div ref={chatEndRef} />
        </List>
      </div>
      {!showSearchTermSection && !showFinalResults && !conversationStarted && (
          <div style={{ marginTop: '20px' }}>
          <Dragger
            name="file"
            multiple={false}
            accept=".pdf"
            beforeUpload={handleFileUpload}
            showUploadList={false}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Click or drag clinical notes PDF here</p>
          </Dragger>
          <Divider>Or</Divider>
          <Button type="primary" onClick={handleStart} disabled={!connected}>
            Start Conversation
          </Button>
        </div>
      )}
      {isUploading && (
        <div style={{ marginTop: '20px', textAlign: 'center' }}>
            <Spin tip="Processing clinical notes..." />
        </div>
        )}
      {!showSearchTermSection && conversationStarted && (
        <>
          <Input.TextArea
            ref={userInputRef}
            rows={4}
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Enter your response"
            style={{ marginBottom: '10px' }}
          />
          <Button type="primary" onClick={handleUserInput} disabled={!userInput.trim()}>
            Send Response
          </Button>
        </>
      )}
      {showSearchTermSection && (
        <Card style={{ marginTop: '20px' }}>
          <Text strong>Suggested Search Term: </Text>
          <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ marginBottom: '10px', width: '300px' }}
            placeholder={suggestedSearchTerm}
          />
          <div style={{ marginBottom: '10px' }}>
            <Button type="primary" onClick={handleUserSearchTerm} disabled={!searchTerm.trim() && !suggestedSearchTerm.trim()} loading={loading}>
              Add Search Term
            </Button>
            <Button type="default" onClick={handleUndoSearchTerm} style={{ marginLeft: '10px' }}>
              Undo
            </Button>
          </div>
        </Card>
      )}
      {loading && (
        <div style={{ marginTop: '20px', textAlign: 'center' }}>
          <Spin tip="Loading final research information..." />
        </div>
      )}
      {medicalReport && (
        <Card style={{ marginTop: '20px' }}>
          <Divider style={{ borderColor: '#7cb305' }}>Medical Report</Divider>
          <ReactMarkdown>{medicalReport}</ReactMarkdown>
        </Card>
      )}
      {researchInfo && (
        <Card style={{ marginTop: '20px' }}>
          <Divider style={{ borderColor: '#7cb305' }}>Final Research Information</Divider>
          <ReactMarkdown>{researchInfo.toString()}</ReactMarkdown>
        </Card>
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
      {showRetryButton && (
        <div style={{ marginTop: '20px', textAlign: 'center' }}>
          <Text type="warning">Rate limit reached. Please wait {retryCountdown} seconds to retry.</Text>
          <Button type="primary" onClick={handleRetry} disabled={retryCountdown > 0} style={{ marginTop: '10px' }} id="retryButton">
            Retry
          </Button>
        </div>
      )}
    </div>
  );
};

export default WebSocketClient;
