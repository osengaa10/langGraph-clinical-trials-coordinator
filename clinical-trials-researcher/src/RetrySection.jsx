import React from 'react';
import { Button, Typography } from 'antd';

const { Text } = Typography;

const RetrySection = ({ retryCountdown, onRetry }) => {
  return (
    <div style={{ marginTop: '20px', textAlign: 'center' }}>
      <Text type="warning">Rate limit reached. Please wait {retryCountdown} seconds to retry.</Text>
      <Button
        type="primary"
        onClick={onRetry}
        disabled={retryCountdown > 0}
        style={{ marginTop: '10px' }}
      >
        Retry
      </Button>
    </div>
  );
};

export default RetrySection;
