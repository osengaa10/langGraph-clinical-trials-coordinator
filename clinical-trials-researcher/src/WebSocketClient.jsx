import React, { useContext, useRef, useEffect, useState } from 'react';
import {WebSocketContext} from './WebSocketContext'
import { Typography, Steps, Button, Spin } from 'antd';
import ChatList from './ChatList';
import FileUploader from './FileUploader';
import InputSection from './InputSection';
import SearchTermSection from './SearchTermSection';
import ReportCard from './ReportCard';
import RetrySection from './RetrySection';
import ActivityLog from './ActivityLog';
import StatusMessage from './StatusMessage';
import SessionRecovery from './SessionRecovery';

const { Title, Text } = Typography;
const { Step } = Steps;

const WebSocketClient = () => {
    const [workflowEnded, setWorkflowEnded] = useState(false)
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
        setCurrentNode,
        showTrialButtons,
        setShowTrialButtons,
        activities,
        statusMessage,
        progress,
        customMessage,
        sessionRecovery,
        recoverSession,
        startFreshSession
      } = useContext(WebSocketContext);


    // Reference for scrolling
    const bottomRef = useRef(null);

    useEffect(() => {
    // Scroll to bottom whenever a new component is rendered or chat updates
    if (bottomRef.current) {
        bottomRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
    }, [
        chatHistory,
        medicalReport,
        showFinalResults,
        showSearchTermSection,
        showTrialButtons,
        showRetryButton,
        activities
    ]);


    const steps = [
    { title: "Consultant", key: "consultant" },
    { title: "Medical Report", key: "medical_report" },
    { title: "Search Term", key: "search_term" },
    { title: "Finding Trials", key: "fetch_trials" },
    { title: "Embedding Trials", key: "embed_trials" },
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
        setWorkflowEnded(true)
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
                        <div className="connection-pulse" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                            <div style={{ 
                                width: '8px', 
                                height: '8px', 
                                borderRadius: '50%', 
                                backgroundColor: '#52c41a' 
                            }} />
                            <Text type="success" strong>Connected to server</Text>
                        </div>
                    ) : (
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                            <div className="activity-pulse" style={{ 
                                width: '8px', 
                                height: '8px', 
                                borderRadius: '50%', 
                                backgroundColor: '#ff4d4f' 
                            }} />
                            <Text type="danger" strong>Not connected to server</Text>
                        </div>
                    )}
                </div>
                <Steps current={activeStep} style={{ marginTop: '20px' }} size="small">
                    {steps.map((step, index) => {
                      const isCompleted = index < activeStep;
                      const isActive = index === activeStep && !workflowEnded;
                      return (
                        <Step
                          key={step.key}
                          title={<span className={isActive ? 'step-breathing' : ''}>{step.title}</span>}
                          status={isCompleted ? 'finish' : (isActive ? 'process' : 'wait')}
                          icon={isActive ? <Spin size="small" className="activity-pulse" /> : null}
                        />
                      );
                    })}
                </Steps>

            </div>


      <ChatList chatHistory={chatHistory} chatEndRef={chatEndRef} />
      
      <StatusMessage 
        currentNode={currentNode} 
        loading={loading} 
        numStudiesFound={numStudiesFound}
        customMessage={customMessage}
        progress={progress}
      />
      
      <ActivityLog activities={activities} currentNode={currentNode} />

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

      {medicalReport && <ReportCard title="Medical Report" content={medicalReport} />}
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
      
      <SessionRecovery
        visible={sessionRecovery.showRecovery}
        recoveryInfo={sessionRecovery.recoveryInfo}
        onRecover={recoverSession}
        onStartFresh={startFreshSession}
        onCancel={() => startFreshSession()} // For now, treat cancel as start fresh
        loading={sessionRecovery.loading}
      />
      
      <div ref={bottomRef} />
    </div>
  );
};

export default WebSocketClient;