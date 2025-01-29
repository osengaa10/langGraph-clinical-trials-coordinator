import React from 'react';
import { List, Typography } from 'antd';

const { Text } = Typography;

const ChatList = ({ chatHistory, chatEndRef }) => {
  return (
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
  );
};

export default ChatList;