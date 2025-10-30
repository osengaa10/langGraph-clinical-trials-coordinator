import React from 'react';
import { List, Typography, Card, Badge, Timeline } from 'antd';
import { CheckCircleOutlined, LoadingOutlined, ClockCircleOutlined } from '@ant-design/icons';

const { Text, Title } = Typography;

const ActivityLog = ({ activities, currentNode }) => {
  if (!activities || activities.length === 0) {
    return null;
  }

  const getActivityIcon = (activity) => {
    if (activity.status === 'completed') {
      return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
    } else if (activity.status === 'active') {
      return <LoadingOutlined style={{ color: '#1890ff' }} />;
    } else {
      return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  const getActivityColor = (activity) => {
    if (activity.status === 'completed') return '#52c41a';
    if (activity.status === 'active') return '#1890ff';
    return '#d9d9d9';
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });
  };

  return (
    <Card 
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* <LoadingOutlined style={{ color: '#1890ff' }} /> */}
          <Title level={4} style={{ margin: 0 }}>Status</Title>
        </div>
      }
      size="small" 
      style={{ 
        marginTop: '20px', 
        maxHeight: '300px', 
        overflow: 'hidden',
        border: '1px solid #e8f4fd'
      }}
    >
      <div style={{ maxHeight: '240px', overflow: 'auto' }}>
        <Timeline mode="left" style={{ paddingTop: '8px' }}>
          {activities.slice(-10).map((activity, index) => (
            <Timeline.Item
              key={activity.id || index}
              dot={getActivityIcon(activity)}
              color={getActivityColor(activity)}
            >
              <div 
                className={index === activities.length - 1 ? 'activity-slide-in timeline-item' : 'timeline-item'}
                style={{ marginBottom: '8px' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <Text 
                      strong 
                      style={{ display: 'block', marginBottom: '4px' }}
                      className={activity.status === 'active' ? 'activity-pulse' : ''}
                    >
                      {activity.title}
                    </Text>
                    {activity.description && (
                      <Text type="secondary" style={{ fontSize: '12px', display: 'block' }}>
                        {activity.description}
                      </Text>
                    )}
                    {activity.stats && (
                      <div style={{ marginTop: '4px' }}>
                        {Object.entries(activity.stats).map(([key, value]) => (
                          <Badge
                            key={key}
                            count={value}
                            className="badge-bounce"
                            style={{ 
                              backgroundColor: '#f0f5ff', 
                              color: '#1890ff',
                              marginRight: '8px',
                              fontSize: '11px'
                            }}
                            title={key}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                  <Text type="secondary" style={{ fontSize: '11px', marginLeft: '8px' }}>
                    {formatTimestamp(activity.timestamp)}
                  </Text>
                </div>
                {activity.progress !== undefined && (
                  <div 
                    className={activity.status === 'active' ? 'enhanced-progress' : ''}
                    style={{ 
                      marginTop: '4px', 
                      background: activity.status === 'active' ? 'linear-gradient(90deg, #1890ff, #52c41a)' : '#f0f5ff', 
                      borderRadius: '2px', 
                      padding: '2px 6px',
                      fontSize: '11px',
                      color: '#1890ff'
                    }}
                  >
                    {activity.progress}% complete
                  </div>
                )}
              </div>
            </Timeline.Item>
          ))}
        </Timeline>
      </div>
    </Card>
  );
};

export default ActivityLog;