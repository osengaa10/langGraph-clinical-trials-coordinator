import React from 'react';
import { Alert, Progress, Typography } from 'antd';
import { LoadingOutlined, InfoCircleOutlined } from '@ant-design/icons';

const { Text } = Typography;

const StatusMessage = ({ currentNode, loading, numStudiesFound, customMessage, progress }) => {
  const getStatusInfo = (node) => {
    const statusMap = {
      consultant: {
        title: "Initial Consultation",
        description: "AI is analyzing your medical information and preparing personalized questions.",
        type: "info",
        estimatedTime: "30-60 seconds"
      },
      medical_report: {
        title: "Medical Report Generation",
        description: "Creating a comprehensive medical summary from your consultation or uploaded documents.",
        type: "processing",
        estimatedTime: "15-30 seconds"
      },
      search_term: {
        title: "Search Term Optimization",
        description: "Extracting key medical terms and conditions to find the most relevant clinical trials.",
        type: "processing",
        estimatedTime: "10-20 seconds"
      },
      fetch_trials: {
        title: "Finding Clinical Trials",
        description: "Searching ClinicalTrials.gov database for studies matching your condition.",
        type: "processing",
        estimatedTime: "1-2 minutes"
      },
      embed_trials: {
        title: "Processing Trial Data",
        description: `Analyzing and processing ${numStudiesFound || 'found'} clinical trials for detailed matching.`,
        type: "processing",
        estimatedTime: "2-5 minutes"
      },
      matching_trials: {
        title: "Matching Trials to Your Profile",
        description: "Using AI to identify trials that best match your medical profile and preferences.",
        type: "processing",
        estimatedTime: "1-3 minutes"
      },
      verify_eligibility: {
        title: "Verifying Eligibility",
        description: "Performing final eligibility checks and preparing personalized recommendations.",
        type: "processing",
        estimatedTime: "30-60 seconds"
      }
    };

    return statusMap[node] || {
      title: "Processing",
      description: "Working on your request...",
      type: "info",
      estimatedTime: "Please wait"
    };
  };

  if (!loading && !customMessage) {
    return null;
  }

  const statusInfo = getStatusInfo(currentNode);
  const message = customMessage || statusInfo.description;

  return (
    <div className="status-fade-in" style={{ marginTop: '16px', marginBottom: '16px' }}>
      <Alert
        message={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <LoadingOutlined className="activity-pulse" style={{ color: '#1890ff' }} />
            <Text strong className="shimmer">{customMessage ? "Status Update" : statusInfo.title}</Text>
          </div>
        }
        description={
          <div style={{ marginTop: '8px' }}>
            <Text>{message}</Text>
            {!customMessage && statusInfo.estimatedTime && (
              <div style={{ marginTop: '6px' }}>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  <InfoCircleOutlined style={{ marginRight: '4px' }} />
                  Estimated time: {statusInfo.estimatedTime}
                </Text>
              </div>
            )}
            {progress !== undefined && progress >= 0 && (
              <div style={{ marginTop: '8px' }}>
                <Progress 
                  percent={progress} 
                  size="small" 
                  status="active"
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
              </div>
            )}
            {numStudiesFound > 0 && currentNode === 'embed_trials' && (
              <div style={{ marginTop: '6px' }}>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  Processing {numStudiesFound} clinical trials found for your condition
                </Text>
              </div>
            )}
          </div>
        }
        type="info"
        showIcon={false}
        style={{ 
          border: '1px solid #e8f4fd',
          backgroundColor: '#f8fcff'
        }}
      />
    </div>
  );
};

export default StatusMessage;