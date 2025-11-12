import React, { useContext, useState, useEffect } from 'react';
import { Upload, Button, Divider, Spin, Space, Row, Col } from 'antd';
import { InboxOutlined, DownloadOutlined } from '@ant-design/icons';
import { WebSocketContext } from './WebSocketContext';

const { Dragger } = Upload;

const FileUploader = ({ connected }) => {
    const { showSearchTermSection, showFinalResults, conversationStarted, socket, addActivity } = useContext(WebSocketContext);
    const [isUploading, setIsUploading] = useState(false);
    const [showUploader, setShowUploader] = useState(false);

    // Clear uploading state when medical report is generated
    useEffect(() => {
        if (showSearchTermSection || showFinalResults || conversationStarted) {
            setIsUploading(false);
        }
    }, [showSearchTermSection, showFinalResults, conversationStarted]);

    const handleStart = () => {
        if (socket) {
          socket.send(JSON.stringify({ command: 'start' }));
        }
    };

    const handleFileUpload = async (file) => {
        setIsUploading(true);
        addActivity('File Upload Started', `Processing ${file.name}...`, 'active');
        
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

                            {/* Sample data download section */}
                            <Divider style={{ margin: '20px 0' }}>Or try with sample data</Divider>
                            <Space wrap>
                                <a href="/samples/breast_cancer_chart.pdf" download="breast_cancer_chart.pdf">
                                    <Button
                                        icon={<DownloadOutlined />}
                                        size="small"
                                    >
                                        Breast Cancer (35F)
                                    </Button>
                                </a>
                                <a href="/samples/sarcoma_cancer_chart.pdf" download="sarcoma_cancer_chart.pdf">
                                    <Button
                                        icon={<DownloadOutlined />}
                                        size="small"
                                    >
                                        Soft Tissue Sarcoma (52F)
                                    </Button>
                                </a>
                                <a href="/samples/bladder_cancer_chart.pdf" download="bladder_cancer_chart.pdf">
                                    <Button
                                        icon={<DownloadOutlined />}
                                        size="small"
                                    >
                                        Bladder Cancer (67M)
                                    </Button>
                                </a>
                            </Space>
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

            {isUploading && (
                <div style={{ marginTop: '20px', textAlign: 'center' }}>
                    <Spin tip="Processing clinical notes..." />
                    <div style={{ marginTop: '10px', fontSize: '14px', color: '#666' }}>
                        This may take a few moments while we extract and analyze your medical information...
                    </div>
                </div>
            )}
        </>
    );
};

export default FileUploader;
