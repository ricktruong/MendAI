import React, { useState, useRef, useEffect } from 'react';
import './ChatPage.css';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  attachments?: Attachment[];
  analysisResults?: AnalysisResult[];
}

interface Attachment {
  id: string;
  type: 'image' | 'document' | 'lab-result';
  name: string;
  url?: string;
}

interface AnalysisResult {
  type: 'imaging' | 'vitals' | 'lab' | 'summary';
  title: string;
  content: any;
  confidence?: number;
}

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: 'Hello! I\'m MendAI, your AI healthcare assistant. How can I help you today? You can ask me about patient records, upload medical images for analysis, or request clinical summaries.',
      timestamp: new Date(),
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showUploadPanel, setShowUploadPanel] = useState(true);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const [slope, setSlope] = useState('1.0');
  const [intercept, setIntercept] = useState('-1024.0');
  const [conversationType, setConversationType] = useState('Long Answer');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const sidebarFileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() && attachedFiles.length === 0) return;

    const newUserMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date(),
      attachments: attachedFiles.map((file, index) => ({
        id: `file-${index}`,
        type: file.type.startsWith('image/') ? 'image' : 'document',
        name: file.name,
      }))
    };

    setMessages([...messages, newUserMessage]);
    setInputMessage('');
    setAttachedFiles([]);
    setIsLoading(true);

    // Simulate AI response - in real app, this would call backend API
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'I\'ve analyzed your query. Based on the patient\'s medical history and current symptoms, here are my findings...',
        timestamp: new Date(),
        analysisResults: attachedFiles.length > 0 ? [
          {
            type: 'imaging',
            title: 'Medical Image Analysis',
            content: {
              findings: 'No significant abnormalities detected',
              confidence: 0.92
            },
            confidence: 0.92
          }
        ] : undefined
      };
      setMessages(prev => [...prev, aiResponse]);
      setIsLoading(false);
    }, 2000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleFileAttachment = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setAttachedFiles(Array.from(e.target.files));
    }
  };

  const handleSidebarFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setAttachedFiles(Array.from(e.target.files));
    }
  };

  const removeAttachment = (index: number) => {
    setAttachedFiles(attachedFiles.filter((_, i) => i !== index));
  };

  const handleSetParameters = () => {
    console.log('Parameters set:', { slope, intercept, conversationType });
  };

  return (
    <div className="chat-page">
      <div className="chat-header">
        <div className="header-left">
          <h1>MendAI Clinical Assistant</h1>
          <span className="status-indicator">
            <span className="status-dot"></span>
            Connected to EHR
          </span>
        </div>
        <div className="header-right">
          <button className="header-button" onClick={() => setShowUploadPanel(!showUploadPanel)}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M16.5 6V17.5C16.5 19.71 14.71 21.5 12.5 21.5C10.29 21.5 8.5 19.71 8.5 17.5V5C8.5 3.62 9.62 2.5 11 2.5C12.38 2.5 13.5 3.62 13.5 5V15.5C13.5 16.05 13.05 16.5 12.5 16.5C11.95 16.5 11.5 16.05 11.5 15.5V6H10V15.5C10 16.88 11.12 18 12.5 18C13.88 18 15 16.88 15 15.5V5C15 2.79 13.21 1 11 1C8.79 1 7 2.79 7 5V17.5C7 20.54 9.46 23 12.5 23C15.54 23 18 20.54 18 17.5V6H16.5Z" fill="currentColor"/>
            </svg>
            Upload File
          </button>
          <button className="header-button">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 0C4.48 0 0 4.48 0 10C0 15.52 4.48 20 10 20C15.52 20 20 15.52 20 10C20 4.48 15.52 0 10 0ZM11 15H9V13H11V15ZM11 11H9V5H11V11Z" fill="currentColor"/>
            </svg>
            Help
          </button>
        </div>
      </div>

      <div className="chat-container">
        {showUploadPanel && (
          <div className="upload-sidebar">
            <div className="upload-section">
              <h3>Upload NIfTI File</h3>
              
              <div className="parameter-group">
                <div className="parameter-row">
                  <div className="parameter-item">
                    <label>Slope</label>
                    <input
                      type="text"
                      value={slope}
                      onChange={(e) => setSlope(e.target.value)}
                      className="parameter-input"
                    />
                  </div>
                  <div className="parameter-item">
                    <label>Intercept</label>
                    <input
                      type="text"
                      value={intercept}
                      onChange={(e) => setIntercept(e.target.value)}
                      className="parameter-input"
                    />
                  </div>
                </div>
                <button className="set-button" onClick={handleSetParameters}>
                  Set
                </button>
              </div>

              <div className="file-upload-area">
                <input
                  ref={sidebarFileInputRef}
                  type="file"
                  accept=".nii,.nii.gz"
                  onChange={handleSidebarFileUpload}
                  style={{ display: 'none' }}
                />
                <div 
                  className="upload-dropzone"
                  onClick={() => sidebarFileInputRef.current?.click()}
                >
                  <div className="upload-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                      <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" fill="currentColor"/>
                    </svg>
                  </div>
                  <div className="upload-text">
                    <p><strong>Upload File Here</strong></p>
                    <p>-or-</p>
                    <p>Click to Upload</p>
                  </div>
                </div>
              </div>

              <div className="conversation-settings">
                <label>Select Conversation Type</label>
                <select 
                  value={conversationType}
                  onChange={(e) => setConversationType(e.target.value)}
                  className="conversation-select"
                >
                  <option value="Long Answer">Long Answer</option>
                  <option value="Short Answer">Short Answer</option>
                  <option value="Generate Report">Generate Report</option>
                </select>
              </div>

              <div className="parameters-section">
                <h4>Parameters</h4>
                <div className="parameters-content">
                  <p>Slope: {slope}</p>
                  <p>Intercept: {intercept}</p>
                  <p>Type: {conversationType}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="chat-main">
          <div className="messages-container">
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.type}`}>
                <div className="message-header">
                  <span className="message-author">
                    {message.type === 'user' ? 'You' : 'MendAI'}
                  </span>
                  <span className="message-time">
                    {message.timestamp.toLocaleTimeString([], { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </span>
                </div>
                <div className="message-content">
                  {message.content}
                  {message.attachments && message.attachments.length > 0 && (
                    <div className="message-attachments">
                      {message.attachments.map((attachment) => (
                        <div key={attachment.id} className="attachment-item">
                          <span className="attachment-icon">
                            {attachment.type === 'image' ? '🖼️' : '📄'}
                          </span>
                          <span className="attachment-name">{attachment.name}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {message.analysisResults && (
                    <div className="analysis-results">
                      {message.analysisResults.map((result, index) => (
                        <div key={index} className="analysis-card">
                          <h4>{result.title}</h4>
                          <div className="analysis-content">
                            {result.type === 'imaging' && (
                              <>
                                <p>Findings: {result.content.findings}</p>
                                <div className="confidence-bar">
                                  <div 
                                    className="confidence-fill" 
                                    style={{ width: `${(result.confidence || 0) * 100}%` }}
                                  ></div>
                                </div>
                                <span className="confidence-text">
                                  Confidence: {((result.confidence || 0) * 100).toFixed(0)}%
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="message assistant">
                <div className="message-header">
                  <span className="message-author">MendAI</span>
                </div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-container">
            {attachedFiles.length > 0 && (
              <div className="attached-files">
                {attachedFiles.map((file, index) => (
                  <div key={index} className="attached-file">
                    <span>{file.name}</span>
                    <button onClick={() => removeAttachment(index)}>×</button>
                  </div>
                ))}
              </div>
            )}
            <div className="chat-input">
              <button 
                className="attach-button"
                onClick={() => fileInputRef.current?.click()}
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M16.5 6V17.5C16.5 19.71 14.71 21.5 12.5 21.5C10.29 21.5 8.5 19.71 8.5 17.5V5C8.5 3.62 9.62 2.5 11 2.5C12.38 2.5 13.5 3.62 13.5 5V15.5C13.5 16.05 13.05 16.5 12.5 16.5C11.95 16.5 11.5 16.05 11.5 15.5V6H10V15.5C10 16.88 11.12 18 12.5 18C13.88 18 15 16.88 15 15.5V5C15 2.79 13.21 1 11 1C8.79 1 7 2.79 7 5V17.5C7 20.54 9.46 23 12.5 23C15.54 23 18 20.54 18 17.5V6H16.5Z" fill="currentColor"/>
                </svg>
              </button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*,.pdf,.doc,.docx,.nii,.nii.gz"
                onChange={handleFileAttachment}
                style={{ display: 'none' }}
              />
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about patient data, upload medical images, or request analysis..."
                rows={1}
              />
              <button 
                className="send-button"
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() && attachedFiles.length === 0}
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M2.01 21L23 12L2.01 3L2 10L17 12L2 14L2.01 21Z" fill="currentColor"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;