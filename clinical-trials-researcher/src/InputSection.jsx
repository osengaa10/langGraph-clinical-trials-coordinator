import React from 'react';
import { Input, Button } from 'antd';

const InputSection = ({ userInput, setUserInput, onSendMessage }) => {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && userInput.trim()) {
      e.preventDefault();
      onSendMessage();
    }
  };

  return (
    <div style={{ marginTop: '20px' }}>
      <Input.TextArea
        rows={4}
        value={userInput}
        onChange={(e) => setUserInput(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Enter your response"
        style={{ marginBottom: '10px' }}
      />
      <Button type="primary" onClick={onSendMessage} disabled={!userInput.trim()}>
        Send Response
      </Button>
    </div>
  );
};

export default InputSection;