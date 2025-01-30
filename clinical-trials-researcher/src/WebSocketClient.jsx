import React, { useContext } from 'react';
import {WebSocketContext} from './WebSocketContext'
import { Typography, Steps, Button } from 'antd';
import ChatList from './ChatList';
import FileUploader from './FileUploader';
import InputSection from './InputSection';
import SearchTermSection from './SearchTermSection';
import ReportCard from './ReportCard';
import RetrySection from './RetrySection';

const { Title, Text } = Typography;
const { Step } = Steps;

const WebSocketClient = () => {
    const {
        socket,
        setSocket,
        connected,
        setConnected,
        chatHistory,
        setChatHistory,
        userInput,
        setUserInput,
        medicalReport,
        setMedicalReport,
        suggestedSearchTerm,
        setSuggestedSearchTerm,
        searchTerm,
        setSearchTerm,
        showSearchTermSection,
        setShowSearchTermSection,
        showFinalResults,
        setShowFinalResults,
        researchInfo,
        setResearchInfo,
        conversationStarted,
        setConversationStarted,
        loading,
        setLoading,
        showRetryButton,
        setShowRetryButton,
        retryCountdown,
        setRetryCountdown,
        retryCommand,
        setRetryCommand,
        retryData,
        setRetryData,
        chatEndRef,
        numStudiesFound,
        currentNode,
        showTrialButtons,
        setShowTrialButtons
      } = useContext(WebSocketContext);


      const steps = [
        { title: "Consultant", key: "consultant" },
        { title: "Medical Report", key: "medical_report" },
        { title: "Search Term", key: "search_term" },
        { title: "Finding Trials", key: "fetch_trials" },
        { title: "Matching Trials", key: "matching_trials" },
        { title: "Verifying Eligibility", key: "verify_eligibility" },
      ];
 const activeStep = steps.findIndex(step => step.key === currentNode);


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


  return (
        <div style={{ padding: '20px' }}>
            <div style={{ position: 'sticky', top: 0, background: '#fff', zIndex: 1, paddingBottom: '10px', textAlign: 'center' }}>
                <Title level={2} style={{ marginBottom: '5px' }}>Clinexus</Title>
                <Text type="secondary" style={{ fontSize: '16px' }}>
                Let AI find the best clinical trial for you
                </Text>
                <div style={{ marginTop: '15px' }}>
                    {connected ? (
                        <Text type="success" strong>Connected to server</Text>
                    ) : (
                        <Text type="danger" strong>Not connected to server</Text>
                    )}
                </div>
                <Steps current={activeStep} style={{ marginTop: '20px' }}>
                {steps.map((step) => (
                <Step key={step.key} title={step.title} />
                ))}
            </Steps>

            </div>


      <ChatList chatHistory={chatHistory} chatEndRef={chatEndRef} />

      {!conversationStarted && (
        <FileUploader
          connected={connected}
          onStartConversation={() => socket.send(JSON.stringify({ command: 'start' }))}
        />
      )}

      {conversationStarted && (
        <InputSection
          userInput={userInput}
          setUserInput={setUserInput}
          onSendMessage={() => {
            setChatHistory([...chatHistory, { role: 'user', content: userInput }]);
            socket.send(JSON.stringify({ command: 'user_input', input: userInput }));
            setUserInput('');
          }}
        />
      )}

      {showSearchTermSection && (
        <SearchTermSection
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          suggestedSearchTerm={suggestedSearchTerm}
          onAddSearchTerm={() => {
            const termToAdd = searchTerm || suggestedSearchTerm;
            socket.send(JSON.stringify({ command: 'user_search_term', search_term: termToAdd }));
          }}
          loading={loading}
        />
      )}

      {medicalReport && <ReportCard title="Medical Report" content={medicalReport} />}
      {showFinalResults && <ReportCard title="Final Research Information" content={researchInfo.toString()} />}
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
        <RetrySection
          retryCountdown={retryCountdown}
          onRetry={() => {
            socket.send(JSON.stringify({ command: 'retry', retry_command: retryCommand, retry_data: retryData }));
            setShowRetryButton(false);
          }}
        />
      )}
    </div>
  );
};

export default WebSocketClient;