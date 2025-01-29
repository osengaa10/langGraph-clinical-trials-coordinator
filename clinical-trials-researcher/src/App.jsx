import React from 'react';
import WebSocketClient from './WebSocketClient';
import { WebSocketProvider } from './WebSocketContext';

const App = () => {
  return (
    <WebSocketProvider>
      <WebSocketClient />
    </WebSocketProvider>
  );
};

export default App;