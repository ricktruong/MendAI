import React, { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
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
  content: Record<string, unknown>;
  confidence?: number;
}

const ChatPage: React.FC = () => {
  const location = useLocation();
  const patient = location.state?.patient;

  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content:
        "Hello! I'm MendAI, your AI healthcare assistant. How can I help you today? You can ask me about patient records, upload medical images for analysis, or request clinical summaries.",
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showUploadPanel, setShowUploadPanel] = useState(true);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const ctImages = [
    '/CT_head_John1.jpg',
    '/CT_head_John2.jpg',
    '/CT_head_John3.jpg',
  ];

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
      })),
    };

    setMessages([...messages, newUserMessage]);
    setInputMessage('');
    setAttachedFiles([]);
    setIsLoading(true);

    try {
      // Send messages to backend engine
      const response = await fetch('http://localhost:8000/v0/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [...messages, newUserMessage],
          patient_id: patient?.patientId || null,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Update messages with the response from backend
      if (data.messages && data.messages.length > 0) {
        setMessages(data.messages);
      }
    } catch (error) {
      console.error('Error sending message to backend:', error);
      // Fallback to mock response if backend is not available
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: "I've analyzed your query. Based on the patient's medical history and current symptoms, here are my findings...",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const removeAttachment = (index: number) => {
    setAttachedFiles(attachedFiles.filter((_, i) => i !== index));
  };

  const handlePrevImage = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCurrentImageIndex((prev) => (prev - 1 + ctImages.length) % ctImages.length);
  };

  const handleNextImage = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCurrentImageIndex((prev) => (prev + 1) % ctImages.length);
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
            📁 Patient Info
          </button>
          <button className="header-button">❓ Help</button>
        </div>
      </div>

      <div className="chat-container">
        {showUploadPanel && (
          <div className="upload-sidebar">
            {patient && (
              <div className="patient-info-card">
                <h3>Patient Information</h3>
                <p><strong>Name:</strong> {patient.patientName}</p>
                <p><strong>Gender:</strong> Male</p>
                <p><strong>Age:</strong> 54</p>
                <p><strong>ID:</strong> CT-2025001</p>
                <p><strong>CT File:</strong> {patient.fileName}</p>
                <p><strong>Date:</strong> {patient.uploadedAt}</p>

                <div className="ct-preview" style={{ marginTop: '1rem' }}>
                  <img
                    src={ctImages[currentImageIndex]}
                    alt="CT Preview"
                    style={{ width: '100%', borderRadius: '8px', cursor: 'pointer' }}
                    onClick={() => setPreviewModalOpen(true)}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {previewModalOpen && (
          <div className="modal-overlay" onClick={() => setPreviewModalOpen(false)}>
            <div className="modal-content">
              <button onClick={handlePrevImage} className="nav-button" style={{ position: 'absolute', left: '20px' }}>◀</button>
              <img
                src={ctImages[currentImageIndex]}
                alt="Full CT"
                style={{ maxWidth: '100%', maxHeight: '80vh', borderRadius: '8px' }}
              />
              <button onClick={handleNextImage} className="nav-button" style={{ position: 'absolute', right: '20px' }}>▶</button>
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
                      minute: '2-digit',
                    })}
                  </span>
                </div>
                <div className="message-content">
                  {message.content}
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
                ➤
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
