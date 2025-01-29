import React from 'react';
import { Card, Divider } from 'antd';
import ReactMarkdown from 'react-markdown';

const ReportCard = ({ title, content }) => {
  return (
    <Card style={{ marginTop: '20px' }}>
      <Divider style={{ borderColor: '#7cb305' }}>{title}</Divider>
      <ReactMarkdown>{content}</ReactMarkdown>
    </Card>
  );
};

export default ReportCard;
