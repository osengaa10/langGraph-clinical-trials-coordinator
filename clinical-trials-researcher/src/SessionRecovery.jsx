import React, { useState } from 'react';
import { Modal, Button, Typography, Timeline, Badge, Alert, Space, Divider } from 'antd';
import { 
  ClockCircleOutlined, 
  CheckCircleOutlined, 
  FileTextOutlined, 
  SearchOutlined,
  ExperimentOutlined,
  DeleteOutlined,
  ReloadOutlined
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

const SessionRecovery = ({ 
  visible, 
  recoveryInfo, 
  onRecover, 
  onStartFresh, 
  onCancel,
  loading = false 
}) => {
  const [isStartingFresh, setIsStartingFresh] = useState(false);

  const handleRecover = () => {
    onRecover();
  };

  const handleStartFresh = () => {
    setIsStartingFresh(true);
    onStartFresh();
  };

  if (!recoveryInfo) {
    return null;
  }

  const getTimelineItems = () => {
    const items = [];

    if (recoveryInfo.hasConversation) {
      items.push({
        dot: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
        children: (
          <div>
            <Text strong>Initial Consultation</Text>
            <br />
            <Text type="secondary">AI consultation completed</Text>
          </div>
        )
      });
    }

    if (recoveryInfo.hasMedicalReport) {
      items.push({
        dot: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
        children: (
          <div>
            <Text strong>Medical Report Generated</Text>
            <br />
            <Text type="secondary">Patient profile analyzed</Text>
          </div>
        )
      });
    }

    if (recoveryInfo.studiesFound > 0) {
      items.push({
        dot: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
        children: (
          <div>
            <Text strong>Clinical Trials Found</Text>
            <br />
            <Text type="secondary">{recoveryInfo.studiesFound} potential trials identified</Text>
          </div>
        )
      });
    }

    if (recoveryInfo.hasResults) {
      items.push({
        dot: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
        children: (
          <div>
            <Text strong>Analysis Complete</Text>
            <br />
            <Text type="secondary">Trial recommendations prepared</Text>
          </div>
        )
      });
    } else if (recoveryInfo.studiesFound > 0) {
      items.push({
        dot: <ClockCircleOutlined style={{ color: '#1890ff' }} />,
        children: (
          <div>
            <Text strong>Analysis In Progress</Text>
            <br />
            <Text type="secondary">AI was analyzing trial eligibility</Text>
          </div>
        )
      });
    }

    return items;
  };

  const getCurrentStepDescription = () => {
    const stepDescriptions = {
      consultant: 'Initial consultation and medical information gathering',
      medical_report: 'Generating comprehensive medical report',
      search_term: 'Optimizing search terms for clinical trials',
      fetch_trials: 'Searching clinical trials database',
      embed_trials: 'Processing and analyzing trial documents',
      matching_trials: 'Matching trials to your medical profile',
      verify_eligibility: 'Verifying eligibility and preparing recommendations'
    };

    return stepDescriptions[recoveryInfo.lastStep] || 'Processing your request';
  };

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ReloadOutlined style={{ color: '#1890ff' }} />
          <Title level={4} style={{ margin: 0 }}>Resume Previous Search?</Title>
        </div>
      }
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={600}
      centered
    >
      <div style={{ padding: '8px 0' }}>
        <Alert
          message="Previous Session Detected"
          description={`We found an unfinished clinical trials search from ${recoveryInfo.sessionAge}. You can continue where you left off or start fresh.`}
          type="info"
          showIcon
          style={{ marginBottom: '20px' }}
        />

        <div style={{ marginBottom: '20px' }}>
          <Title level={5}>Last Activity: {getCurrentStepDescription()}</Title>
          <Space>
            {recoveryInfo.hasConversation && (
              <Badge count="✓" style={{ backgroundColor: '#52c41a' }}>
                <FileTextOutlined style={{ fontSize: '16px', color: '#666' }} />
              </Badge>
            )}
            {recoveryInfo.hasMedicalReport && (
              <Badge count="✓" style={{ backgroundColor: '#52c41a' }}>
                <SearchOutlined style={{ fontSize: '16px', color: '#666' }} />
              </Badge>
            )}
            {recoveryInfo.studiesFound > 0 && (
              <Badge count={recoveryInfo.studiesFound} style={{ backgroundColor: '#1890ff' }}>
                <ExperimentOutlined style={{ fontSize: '16px', color: '#666' }} />
              </Badge>
            )}
          </Space>
        </div>

        {getTimelineItems().length > 0 && (
          <div style={{ marginBottom: '20px' }}>
            <Paragraph strong>Progress Summary:</Paragraph>
            <Timeline 
              size="small" 
              items={getTimelineItems()}
              style={{ marginLeft: '8px' }}
            />
          </div>
        )}

        <Divider />

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <Button 
            type="primary" 
            size="large"
            icon={<ReloadOutlined />}
            loading={loading && !isStartingFresh}
            onClick={handleRecover}
            style={{ minWidth: '140px' }}
          >
            Continue Search
          </Button>
          
          <Button 
            size="large"
            icon={<DeleteOutlined />}
            loading={isStartingFresh}
            onClick={handleStartFresh}
            style={{ minWidth: '140px' }}
          >
            Start Fresh
          </Button>
        </div>

        <div style={{ textAlign: 'center', marginTop: '16px' }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            Sessions are automatically cleaned up after 48 hours of inactivity
          </Text>
        </div>
      </div>
    </Modal>
  );
};

export default SessionRecovery;