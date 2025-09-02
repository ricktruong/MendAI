import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './PatientDashboardPage.css';
import { apiService } from '../../services/api';
import type { Message } from '../../services/api';

const PatientDashboardPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const patient = location.state?.patient;

  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: patient
        ? `Hello! I'm MendAI, your AI healthcare assistant. I can see you're viewing ${patient.patientName || patient.patient_name}'s medical records. I have access to their CT scan images and can help analyze them. What would you like to know about this patient?`
        : "Hello! I'm MendAI, your AI healthcare assistant. How can I help you today?",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPatientPanel, setShowPatientPanel] = useState(true);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [sessionId, setSessionId] = useState<string>('');
  const [ctImages, setCtImages] = useState<string[]>([]);
  const [loadingImages, setLoadingImages] = useState(false);

  // Check authentication status
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }
  }, [navigate]);

  // Load CT images for the selected patient
  useEffect(() => {
    const loadPatientImages = async () => {
      if (!patient) {
        setCtImages([]);
        return;
      }

      try {
        setLoadingImages(true);
        
        // Call backend API to get patient's CT images
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v0/patients/${patient.id}/images`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          if (data.images && data.images.length > 0) {
            setCtImages(data.images);
          } else {
            // Fallback to placeholder images if no images available
            setCtImages([
              'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect width="300" height="300" fill="%23f3f4f6"/><circle cx="150" cy="150" r="80" fill="%23d1d5db" stroke="%236b7280" stroke-width="2"/><text x="150" y="155" font-family="Arial" font-size="14" fill="%23374151" text-anchor="middle">CT Scan</text><text x="150" y="175" font-family="Arial" font-size="12" fill="%236b7280" text-anchor="middle">No Images Available</text></svg>'
            ]);
          }
        } else {
          // Backend doesn't have the endpoint yet, use placeholder
          setCtImages([
            'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect width="300" height="300" fill="%23f3f4f6"/><circle cx="150" cy="150" r="80" fill="%23d1d5db" stroke="%236b7280" stroke-width="2"/><text x="150" y="155" font-family="Arial" font-size="14" fill="%23374151" text-anchor="middle">CT Scan 1</text><text x="150" y="175" font-family="Arial" font-size="12" fill="%236b7280" text-anchor="middle">Head Axial</text></svg>',
            'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect width="300" height="300" fill="%23f3f4f6"/><circle cx="150" cy="150" r="80" fill="%23d1d5db" stroke="%236b7280" stroke-width="2"/><text x="150" y="155" font-family="Arial" font-size="14" fill="%23374151" text-anchor="middle">CT Scan 2</text><text x="150" y="175" font-family="Arial" font-size="12" fill="%236b7280" text-anchor="middle">Head Sagittal</text></svg>',
            'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect width="300" height="300" fill="%23f3f4f6"/><circle cx="150" cy="150" r="80" fill="%23d1d5db" stroke="%236b7280" stroke-width="2"/><text x="150" y="155" font-family="Arial" font-size="14" fill="%23374151" text-anchor="middle">CT Scan 3</text><text x="150" y="175" font-family="Arial" font-size="12" fill="%236b7280" text-anchor="middle">Head Coronal</text></svg>'
          ]);
        }
      } catch (error) {
        console.error('Error loading patient images:', error);
        // Fallback to placeholder images on error
        setCtImages([
          'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect width="300" height="300" fill="%23f3f4f6"/><circle cx="150" cy="150" r="80" fill="%23d1d5db" stroke="%236b7280" stroke-width="2"/><text x="150" y="155" font-family="Arial" font-size="14" fill="%23374151" text-anchor="middle">CT Scan</text><text x="150" y="175" font-family="Arial" font-size="12" fill="%236b7280" text-anchor="middle">Loading Failed</text></svg>'
        ]);
      } finally {
        setLoadingImages(false);
      }
    };

    loadPatientImages();
  }, [patient]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);


  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const newUserMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString(),
    };

    const currentMessages = [...messages, newUserMessage];
    setMessages(currentMessages);
    const currentInputMessage = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    try {
      const chatRequest = {
        messages: currentMessages,
        patient_id: patient?.id || patient?.patientId,
        session_id: sessionId,
      };

      const response = await apiService.sendChatMessage(chatRequest);
      
      if (response.session_id && !sessionId) {
        setSessionId(response.session_id);
      }
      
      setMessages(response.messages);
    } catch (error) {
      console.error('Error sending message to backend:', error);
      
      // Fallback response for development
      const fallbackResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `I've received your message: "${currentInputMessage}". ${patient ? `Based on ${patient.patientName || patient.patient_name}'s CT scan data, ` : ''}I can provide clinical insights and analysis. However, I'm currently experiencing connectivity issues with the backend services.`,
        timestamp: new Date().toISOString(),
      };
      
      setMessages(prev => [...prev, fallbackResponse]);
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
          <h1>Patient Dashboard</h1>
          <span className="status-indicator">
            <span className="status-dot"></span>
            Connected to EHR
          </span>
        </div>
        <div className="header-right">
          <button className="header-button" onClick={() => setShowPatientPanel(!showPatientPanel)}>
            Patient Info
          </button>
          <button className="header-button" onClick={() => navigate('/patients')}>
            Patient List
          </button>
        </div>
      </div>

      <div className="chat-container">
        {showPatientPanel && patient && (
          <div className="upload-sidebar">
            <div className="patient-info-card">
              <h3>Patient Information</h3>
              <p><strong>Name:</strong> {patient.patientName || patient.patient_name}</p>
              <p><strong>Gender:</strong> Male</p>
              <p><strong>Age:</strong> 54</p>
              <p><strong>ID:</strong> {patient.id}</p>
              <p><strong>CT File:</strong> {patient.fileName || patient.file_name}</p>
              <p><strong>Date:</strong> {patient.uploadedAt || patient.uploaded_at}</p>

              <div className="ct-images-section">
                <h4>CT Scan Images</h4>
                {loadingImages ? (
                  <div className="loading-images">
                    <div className="loading-placeholder">
                      <div className="loading-spinner"></div>
                      <p>Loading CT images...</p>
                    </div>
                  </div>
                ) : ctImages.length > 0 ? (
                  <div className="ct-preview">
                    <img
                      src={ctImages[currentImageIndex]}
                      alt={`CT Scan ${currentImageIndex + 1}`}
                      onClick={() => setPreviewModalOpen(true)}
                    />
                    <div className="image-navigation">
                      <button onClick={(e) => handlePrevImage(e)}>
                        ◀
                      </button>
                      <span className="image-counter">
                        {currentImageIndex + 1} of {ctImages.length}
                      </span>
                      <button onClick={(e) => handleNextImage(e)}>
                        ▶
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="no-images">
                    <p>No CT scan images available for this patient.</p>
                  </div>
                )}
              </div>
            </div>
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
                    {new Date(message.timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
                <div className="message-content">
                  {message.content}
                  

                  {message.analysis_results && message.analysis_results.length > 0 && (
                    <div className="analysis-results">
                      {message.analysis_results.map((result, index) => (
                        <div key={index} className="analysis-card">
                          <h4>{result.title}</h4>
                          <div className="analysis-content">
                            {typeof result.content === 'string' 
                              ? result.content 
                              : JSON.stringify(result.content, null, 2)
                            }
                          </div>
                          {result.confidence && (
                            <div>
                              <div className="confidence-bar">
                                <div 
                                  className="confidence-fill" 
                                  style={{ width: `${result.confidence * 100}%` }}
                                ></div>
                              </div>
                              <div className="confidence-text">
                                Confidence: {(result.confidence * 100).toFixed(1)}%
                              </div>
                            </div>
                          )}
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
            <div className="chat-input">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={patient 
                  ? `Ask me about ${patient.patientName || patient.patient_name}'s CT scan or medical condition...`
                  : "Ask me about medical analysis or patient data..."
                }
                rows={1}
                disabled={isLoading}
              />
              <button
                className="send-button"
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading}
              >
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatientDashboardPage;