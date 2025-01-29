import React from 'react';
import { Card, Input, Button, Typography } from 'antd';

const { Text } = Typography;

const SearchTermSection = ({
  searchTerm,
  setSearchTerm,
  suggestedSearchTerm,
  onAddSearchTerm,
  loading,
}) => {
  const handleUndo = () => {
    setSearchTerm(suggestedSearchTerm);
  };

  return (
    <Card style={{ marginTop: '20px' }}>
      <Text strong>Suggested Search Term: </Text>
      <Input
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        style={{ marginBottom: '10px', width: '300px' }}
        placeholder={suggestedSearchTerm}
      />
      <div style={{ marginBottom: '10px' }}>
        <Button
          type="primary"
          onClick={onAddSearchTerm}
          disabled={!searchTerm.trim() && !suggestedSearchTerm.trim()}
          loading={loading}
        >
          Add Search Term
        </Button>
        <Button type="default" onClick={handleUndo} style={{ marginLeft: '10px' }}>
          Undo
        </Button>
      </div>
    </Card>
  );
};

export default SearchTermSection;
