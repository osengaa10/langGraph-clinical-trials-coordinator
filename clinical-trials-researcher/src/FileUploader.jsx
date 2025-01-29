import React, { useContext, useState } from 'react';
import { Upload, Button, Divider, Spin } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { WebSocketContext } from './WebSocketContext';

const { Dragger } = Upload;

const FileUploader = ({ connected }) => {
    const { showSearchTermSection, showFinalResults, conversationStarted, socket } = useContext(WebSocketContext);
    const [isUploading, setIsUploading] = useState(false);
    const [showUploader, setShowUploader] = useState(false);

    const handleStart = () => {
        if (socket) {
          socket.send(JSON.stringify({ command: 'start' }));
        }
    };

    const handleFileUpload = async (file) => {
        setIsUploading(true);
        const reader = new FileReader();
        reader.onload = async (e) => {
            const base64Data = e.target.result.split(',')[1];
            if (socket) {
                socket.send(JSON.stringify({ 
                    command: 'upload', 
                    data: base64Data,
                    filename: file.name 
                }));
            }
        };
        reader.readAsDataURL(file);
        return false; // Prevent default upload behavior
    };

    return (
        <>
            {!showSearchTermSection && !showFinalResults && !conversationStarted && (
                <div style={{ marginTop: '20px', textAlign: 'center' }}>
                    {/* Show two buttons initially */}
                    {!showUploader ? (
                        <>
                            <Button type="primary" onClick={handleStart} disabled={!connected} style={{ marginRight: '10px' }}>
                                Converse with agent
                            </Button>
                            <Button type="default" onClick={() => setShowUploader(true)}>
                                Upload Clinical Notes
                            </Button>
                        </>
                    ) : (
                        <>
                            <Dragger
                                name="file"
                                multiple={false}
                                accept=".pdf"
                                beforeUpload={handleFileUpload}
                                showUploadList={false}
                            >
                                <p className="ant-upload-drag-icon">
                                    <InboxOutlined />
                                </p>
                                <p className="ant-upload-text">Click or drag clinical notes PDF here</p>
                            </Dragger>
                            <Button type="default" onClick={() => setShowUploader(false)} style={{ marginTop: '10px' }}>
                                Cancel
                            </Button>
                        </>
                    )}
                </div>
            )}

            {/* {isUploading && (
                <div style={{ marginTop: '20px', textAlign: 'center' }}>
                    <Spin tip="Processing clinical notes..." />
                </div>
            )} */}
        </>
    );
};

export default FileUploader;
