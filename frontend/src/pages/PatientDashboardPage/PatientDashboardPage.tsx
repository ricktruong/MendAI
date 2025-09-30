import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './PatientDashboardPage.css';
import { apiService } from '../../services/api';
import type { Message } from '../../services/api';
import jsPDF from 'jspdf';

// Tab types for the dashboard
type TabType = 'summary' | 'ct-analysis' | 'ai-results' | 'chat';

const PatientDashboardPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const patient = location.state?.patient;

  // Debug patient data
  console.log('Dashboard received patient data:', patient);

  // Tab management
  const [activeTab, setActiveTab] = useState<TabType>('summary');

  // Chat-related state (for chat tab)
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
  const [sessionId, setSessionId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // CT Images state
  const [ctImages, setCtImages] = useState<string[]>([]);
  const [loadingImages, setLoadingImages] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [patientFiles, setPatientFiles] = useState<any[]>([]);
  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);

  // AI Analysis state
  const [aiResults, setAiResults] = useState<any[]>([]);
  const [loadingAiAnalysis, setLoadingAiAnalysis] = useState(false);
  const [aiAnalysisCompleted, setAiAnalysisCompleted] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [generatedReport, setGeneratedReport] = useState<{ name: string; url: string; size: string } | null>(null);

  // Authentication check
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }
  }, [navigate]);

  // Load CT files for the selected patient
  useEffect(() => {
    const loadPatientFiles = async () => {
      if (!patient) {
        setPatientFiles([]);
        setCtImages([]);
        return;
      }

      try {
        setLoadingImages(true);

        // Always fetch the latest files from API to ensure we have current data
        const filesResponse = await apiService.getPatientFiles(patient.id);

        if (filesResponse.success && filesResponse.files && filesResponse.files.length > 0) {
          console.log('Loaded files for patient:', filesResponse.files);
          const dcmFiles = filesResponse.files.filter(file =>
            file.file_name.toLowerCase().endsWith('.dcm')
          );
          console.log('Filtered DICOM files:', dcmFiles);
          console.log('Number of DICOM files found:', dcmFiles.length);
          setPatientFiles(dcmFiles);

          if (dcmFiles.length > 0) {
            // Fetch actual CT images from the backend
            try {
              const apiUrl = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v0/patients/${patient.id}/images`;
              console.log('Fetching images from:', apiUrl);

              const imagesResponse = await fetch(apiUrl, {
                method: 'GET',
                headers: {
                  'Authorization': `Bearer ${localStorage.getItem('token')}`,
                  'Content-Type': 'application/json',
                },
              });

              console.log('Images response status:', imagesResponse.status);
              console.log('Images response ok:', imagesResponse.ok);

              if (imagesResponse.ok) {
                const imagesData = await imagesResponse.json();
                console.log('Images API response:', imagesData);

                if (imagesData.images && imagesData.images.length > 0) {
                  console.log('Setting CT images, count:', imagesData.images.length);
                  console.log('First image preview:', imagesData.images[0].substring(0, 100) + '...');
                  setCtImages(imagesData.images);
                  setCurrentFileIndex(0);
                  setCurrentImageIndex(0);
                  console.log('CT images set successfully');
                } else {
                  console.error('No images in response:', imagesData);
                  throw new Error('No images returned from backend');
                }
              } else {
                const errorText = await imagesResponse.text();
                console.error('Images API error response:', errorText);
                throw new Error(`Images API failed: ${imagesResponse.status}`);
              }
            } catch (imageError) {
              console.error('Failed to load CT images:', imageError);
              // Fallback to placeholder
              setCtImages([
                'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400"><rect width="400" height="400" fill="%23fef2f2"/><circle cx="200" cy="200" r="80" fill="%23fecaca" stroke="%23dc2626" stroke-width="2"/><text x="200" y="190" font-family="Arial" font-size="14" fill="%23dc2626" text-anchor="middle">Image Load Failed</text><text x="200" y="210" font-family="Arial" font-size="12" fill="%23dc2626" text-anchor="middle">Check console for details</text></svg>'
              ]);
            }
          } else {
            // No DICOM files found
            setCtImages([
              'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400"><rect width="400" height="400" fill="%23fef2f2"/><circle cx="200" cy="200" r="80" fill="%23fecaca" stroke="%23dc2626" stroke-width="2"/><text x="200" y="190" font-family="Arial" font-size="14" fill="%23dc2626" text-anchor="middle">No DICOM Files</text><text x="200" y="210" font-family="Arial" font-size="12" fill="%23dc2626" text-anchor="middle">Please upload .dcm files</text></svg>'
            ]);
          }
        } else {
          // No files available
          setCtImages([
            'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400"><rect width="400" height="400" fill="%23f3f4f6"/><circle cx="200" cy="200" r="80" fill="%23d1d5db" stroke="%236b7280" stroke-width="2"/><text x="200" y="195" font-family="Arial" font-size="14" fill="%23374151" text-anchor="middle">No CT Files</text><text x="200" y="215" font-family="Arial" font-size="12" fill="%236b7280" text-anchor="middle">Upload DICOM files</text></svg>'
          ]);
        }
      } catch (error) {
        console.error('Error loading patient files:', error);
        console.error('Patient data:', patient);
        setCtImages([
          'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400"><rect width="400" height="400" fill="%23fef2f2"/><circle cx="200" cy="200" r="80" fill="%23fecaca" stroke="%23dc2626" stroke-width="2"/><text x="200" y="190" font-family="Arial" font-size="14" fill="%23dc2626" text-anchor="middle">Loading Failed</text><text x="200" y="210" font-family="Arial" font-size="12" fill="%23dc2626" text-anchor="middle">Check console for details</text></svg>'
        ]);
      } finally {
        setLoadingImages(false);
      }
    };

    loadPatientFiles();
  }, [patient]);

  // Chat functionality
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (activeTab === 'chat') {
      scrollToBottom();
    }
  }, [messages, activeTab]);

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

  // File navigation
  const handlePrevFile = () => {
    if (patientFiles.length > 0) {
      const newIndex = (currentFileIndex - 1 + patientFiles.length) % patientFiles.length;
      setCurrentFileIndex(newIndex);
      setCurrentImageIndex(newIndex);
    }
  };

  const handleNextFile = () => {
    if (patientFiles.length > 0) {
      const newIndex = (currentFileIndex + 1) % patientFiles.length;
      setCurrentFileIndex(newIndex);
      setCurrentImageIndex(newIndex);
    }
  };

  // Legacy image navigation (for backward compatibility)
  const handlePrevImage = () => {
    handlePrevFile();
  };

  const handleNextImage = () => {
    handleNextFile();
  };

  // AI Analysis function
  const triggerAiAnalysis = async () => {
    if (loadingAiAnalysis || aiAnalysisCompleted || !patient) {
      return;
    }

    setLoadingAiAnalysis(true);

    try {
      // Get all files for this patient
      const fileIds = patientFiles.map(f => f.id);
      const fileNames = patientFiles.map(f => f.file_name);

      console.log(`Analyzing ${fileIds.length} files for patient ${patient.id}`);

      // Call the comprehensive analysis API
      const apiUrl = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v0/analyze/comprehensive`;

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          patient_id: patient.id,
          file_ids: fileIds.length > 0 ? fileIds : ['default-file'],
          file_names: fileNames.length > 0 ? fileNames : [patient.fileName || 'CT_Scan.dcm']
        })
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.status}`);
      }

      const analysisData = await response.json();
      console.log('Analysis completed:', analysisData);

      // Format results for display
      const results = [
        {
          id: 1,
          priority: 'high',
          icon: '📊',
          title: 'Comprehensive Analysis Summary',
          content: analysisData.comprehensive_summary,
          details: [
            `Files Analyzed: ${analysisData.files_analyzed}`,
            `Overall Confidence: ${(analysisData.overall_confidence * 100).toFixed(0)}%`,
            `Analysis Date: ${new Date().toLocaleString()}`
          ]
        },
        {
          id: 2,
          priority: 'high',
          icon: '🔍',
          title: 'Key Findings',
          content: analysisData.key_findings.join('\n• '),
          details: analysisData.key_findings
        },
        {
          id: 3,
          priority: 'medium',
          icon: '💡',
          title: 'Clinical Recommendations',
          content: analysisData.recommendations.join('\n• '),
          details: analysisData.recommendations
        }
      ];

      // Add individual file results
      analysisData.file_results.forEach((fileResult: any, index: number) => {
        results.push({
          id: 100 + index,
          priority: 'medium',
          icon: '📄',
          title: `File Analysis: ${fileResult.file_name}`,
          content: fileResult.findings.join('\n• '),
          details: [
            `File: ${fileResult.file_name}`,
            `Confidence: ${(fileResult.confidence * 100).toFixed(0)}%`,
            ...fileResult.findings
          ]
        });
      });

      setAiResults(results);
      setAiAnalysisCompleted(true);

    } catch (error) {
      console.error('AI Analysis failed:', error);
      setAiResults([
        {
          id: 1,
          priority: 'medium',
          icon: '⚠️',
          title: 'Analysis Status',
          content: 'AI analysis service is currently unavailable. Please try again later or contact support.',
          details: [
            'Status: Service unavailable',
            'Patient ID: ' + patient.id,
            'Timestamp: ' + new Date().toLocaleString(),
            'Error: ' + (error instanceof Error ? error.message : 'Unknown error')
          ]
        }
      ]);
    } finally {
      setLoadingAiAnalysis(false);
    }
  };

  // Handle tab change with AI analysis trigger
  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
    if (tab === 'ai-results' && !aiAnalysisCompleted) {
      triggerAiAnalysis();
    }
  };

  // Generate PDF Report function
  const generatePdfReport = async () => {
    if (generatingReport || !patient || !aiAnalysisCompleted || aiResults.length === 0) {
      return;
    }

    setGeneratingReport(true);

    try {
      // Simulate API call for PDF generation
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Create PDF using jsPDF with simpler approach
      const doc = new jsPDF();
      
      // Title
      doc.setFontSize(18);
      doc.text('MendAI - AI Analysis Report', 20, 30);
      
      // Patient Information
      doc.setFontSize(14);
      doc.text('Patient Information:', 20, 50);
      
      doc.setFontSize(11);
      let y = 65;
      doc.text(`Patient Name: ${patient.patientName || patient.patient_name}`, 25, y);
      doc.text(`Patient ID: ${patient.id}`, 25, y + 10);
      doc.text(`File Name: ${patient.fileName || 'No file'}`, 25, y + 20);
      doc.text(`Upload Date: ${patient.uploadedAt}`, 25, y + 30);
      doc.text(`Report Generated: ${new Date().toLocaleString()}`, 25, y + 40);
      
      // AI Analysis Results
      y += 60;
      doc.setFontSize(14);
      doc.text('AI Analysis Results:', 20, y);
      
      y += 15;
      doc.setFontSize(11);
      aiResults.forEach((result, index) => {
        if (y > 250) {
          doc.addPage();
          y = 30;
        }
        
        doc.setFontSize(12);
        doc.text(`${index + 1}. ${result.title}`, 25, y);
        y += 10;
        
        doc.setFontSize(10);
        doc.text(`Priority: ${result.priority}`, 30, y);
        y += 8;
        
        // Split long text into multiple lines
        const maxWidth = 150;
        const contentLines = doc.splitTextToSize(result.content, maxWidth);
        doc.text(contentLines, 30, y);
        y += contentLines.length * 6 + 5;
        
        if (result.details && result.details.length > 0) {
          doc.text('Details:', 30, y);
          y += 6;
          result.details.forEach((detail: string) => {
            const detailLines = doc.splitTextToSize(`- ${detail}`, maxWidth - 10);
            doc.text(detailLines, 35, y);
            y += detailLines.length * 5;
          });
        }
        y += 10;
      });
      
      // Footer
      if (y > 250) {
        doc.addPage();
        y = 30;
      }
      doc.setFontSize(9);
      doc.text('Generated by MendAI System', 20, y + 20);
      doc.text(`Report ID: RPT-${Date.now()}`, 20, y + 30);

      // Generate blob and download info
      const pdfBlob = doc.output('blob');
      const url = window.URL.createObjectURL(pdfBlob);
      const fileName = `MendAI_Report_${patient.patientName || patient.patient_name}_${new Date().toISOString().split('T')[0]}.pdf`;
      const fileSize = `${Math.round(pdfBlob.size / 1024)} KB`;

      // Store the report info to display in UI
      setGeneratedReport({
        name: fileName,
        url: url,
        size: fileSize
      });

    } catch (error) {
      console.error('Report generation failed:', error);
      alert('Failed to generate report. Please try again.');
    } finally {
      setGeneratingReport(false);
    }
  };

  // Download report function
  const downloadReport = () => {
    if (!generatedReport) return;
    
    const link = document.createElement('a');
    link.href = generatedReport.url;
    link.download = generatedReport.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Render different tab content
  const renderTabContent = () => {
    switch (activeTab) {
      case 'summary':
        return (
          <div className="tab-content summary-tab">
            <div className="summary-header">
              <h2>Patient Summary</h2>
              <div className="last-updated">Last updated: {new Date().toLocaleDateString()}</div>
            </div>
            
            <div className="summary-grid">
              <div className="summary-card">
                <h3>Patient Demographics</h3>
                <div className="summary-items">
                  <div className="summary-item">
                    <span className="label">Patient Name:</span>
                    <span className="value">{patient?.patientName || patient?.patient_name || 'N/A'}</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Patient ID:</span>
                    <span className="value">{patient?.id || 'N/A'}</span>
                  </div>
                  {patient?.fhirId && (
                    <div className="summary-item">
                      <span className="label">FHIR ID:</span>
                      <span className="value" style={{ fontSize: '0.85rem', fontFamily: 'monospace' }}>{patient.fhirId}</span>
                    </div>
                  )}
                  <div className="summary-item">
                    <span className="label">Birth Date:</span>
                    <span className="value">
                      {patient?.birthDate
                        ? new Date(patient.birthDate).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                          })
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Gender:</span>
                    <span className="value" style={{ textTransform: 'capitalize' }}>
                      {patient?.gender || 'N/A'}
                    </span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Race:</span>
                    <span className="value">{patient?.race || 'N/A'}</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Ethnicity:</span>
                    <span className="value">{patient?.ethnicity || 'N/A'}</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Marital Status:</span>
                    <span className="value">
                      {patient?.maritalStatus === 'S' ? 'Single' :
                       patient?.maritalStatus === 'M' ? 'Married' :
                       patient?.maritalStatus === 'D' ? 'Divorced' :
                       patient?.maritalStatus === 'W' ? 'Widowed' :
                       patient?.maritalStatus === 'UNK' ? 'Unknown' :
                       patient?.maritalStatus || 'N/A'}
                    </span>
                  </div>
                  {patient?.language && (
                    <div className="summary-item">
                      <span className="label">Language:</span>
                      <span className="value" style={{ textTransform: 'uppercase' }}>{patient.language}</span>
                    </div>
                  )}
                  {patient?.managingOrganization && (
                    <div className="summary-item">
                      <span className="label">Managing Organization:</span>
                      <span className="value">{patient.managingOrganization}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="summary-card">
                <h3>Medical Records</h3>
                <div className="summary-items">
                  <div className="summary-item">
                    <span className="label">Upload Date:</span>
                    <span className="value">
                      {patient?.uploadedAt
                        ? new Date(patient.uploadedAt).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                          })
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Primary File:</span>
                    <span className="value">{patient?.fileName || 'No file attached'}</span>
                  </div>
                  {patientFiles.length > 0 && (
                    <div className="summary-item">
                      <span className="label">Total DICOM Files:</span>
                      <span className="value">{patientFiles.length} CT scan files</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        );

      case 'ct-analysis':
        return (
          <div className="tab-content ct-analysis-tab">
            <div className="ct-header">
              <h2>CT Scan Analysis</h2>
            </div>
            
            <div className="ct-viewer-container">
              <div className="ct-viewer">
                {loadingImages ? (
                  <div className="loading-spinner">
                    <div className="spinner"></div>
                    <p>Loading CT images...</p>
                  </div>
                ) : ctImages.length > 0 ? (
                  <>
                    <img
                      src={ctImages[currentImageIndex]}
                      alt={`CT Scan ${currentImageIndex + 1}`}
                      className="ct-image"
                      onClick={() => setPreviewModalOpen(true)}
                    />
                    <div className="ct-controls">
                      <button
                        onClick={handlePrevFile}
                        className="nav-btn"
                        disabled={patientFiles.length <= 1}
                      >
                        ◀ Previous File
                      </button>
                      <span className="slice-info">
                        {patientFiles.length > 0
                          ? `File ${currentFileIndex + 1} of ${patientFiles.length}: ${patientFiles[currentFileIndex]?.file_name || 'Loading...'}`
                          : `Image ${currentImageIndex + 1} of ${ctImages.length}`
                        }
                      </span>
                      <button
                        onClick={handleNextFile}
                        className="nav-btn"
                        disabled={patientFiles.length <= 1}
                      >
                        Next File ▶
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="no-images">
                    <p>No CT scan images available for this patient.</p>
                  </div>
                )}
              </div>
              
              <div className="ct-sidebar">
                <div className="ct-info-card">
                  <h4>Current File Information</h4>
                  {patientFiles.length > 0 && patientFiles[currentFileIndex] ? (
                    <>
                      <div className="info-item">
                        <span>File Name:</span>
                        <span>{patientFiles[currentFileIndex].file_name}</span>
                      </div>
                      <div className="info-item">
                        <span>Upload Date:</span>
                        <span>{new Date(patientFiles[currentFileIndex].uploaded_at).toLocaleDateString()}</span>
                      </div>
                      <div className="info-item">
                        <span>File ID:</span>
                        <span>{patientFiles[currentFileIndex].id}</span>
                      </div>
                      <div className="info-item">
                        <span>File Type:</span>
                        <span>DICOM (.dcm)</span>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="info-item">
                        <span>Study Date:</span>
                        <span>{patient?.uploadedAt}</span>
                      </div>
                      <div className="info-item">
                        <span>File Name:</span>
                        <span>{patient?.fileName || 'No file'}</span>
                      </div>
                    </>
                  )}
                </div>

                {patientFiles.length > 1 && (
                  <div className="ct-info-card">
                    <h4>All Patient Files</h4>
                    <div className="files-list-compact">
                      {patientFiles.map((file, index) => (
                        <div
                          key={file.id}
                          className={`file-item ${index === currentFileIndex ? 'active' : ''}`}
                          onClick={() => {
                            setCurrentFileIndex(index);
                            setCurrentImageIndex(index);
                          }}
                          style={{
                            padding: '8px',
                            cursor: 'pointer',
                            backgroundColor: index === currentFileIndex ? '#e5e7eb' : 'transparent',
                            borderRadius: '4px',
                            marginBottom: '4px',
                            border: index === currentFileIndex ? '2px solid #3b82f6' : '1px solid #d1d5db'
                          }}
                        >
                          <div style={{ fontWeight: '500', fontSize: '0.875rem' }}>
                            {file.file_name}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                            {new Date(file.uploaded_at).toLocaleDateString()}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        );

      case 'ai-results':
        return (
          <div className="tab-content ai-results-tab">
            <div className="ai-header">
              <h2>AI Analysis Results</h2>
              <div className="ai-header-actions">
                {aiAnalysisCompleted && (
                  <div className="confidence-indicator">
                    <span>Analysis Status: </span>
                    <span style={{ color: '#10b981', fontWeight: '600' }}>Complete</span>
                  </div>
                )}
                {aiAnalysisCompleted && aiResults.length > 0 && (
                  <button
                    className="generate-report-btn"
                    onClick={generatePdfReport}
                    disabled={generatingReport}
                  >
                    {generatingReport ? 'Generating...' : 'Generate Report'}
                  </button>
                )}
              </div>
            </div>

            {loadingAiAnalysis ? (
              <div className="ai-loading">
                <div className="loading-spinner">
                  <div className="spinner"></div>
                  <h3>Analyzing CT Scan Images...</h3>
                  <p>AI is processing the medical images and generating analysis results.</p>
                  <p>This may take a few moments.</p>
                </div>
              </div>
            ) : aiResults.length > 0 ? (
              <div className="results-grid">
                {aiResults.map((result) => (
                  <div key={result.id} className={`result-card priority-${result.priority}`}>
                    <div className="result-header">
                      <span className="result-icon">{result.icon}</span>
                      <h3>{result.title}</h3>
                      <span className={`priority-badge ${result.priority}`}>
                        {result.priority.charAt(0).toUpperCase() + result.priority.slice(1)} Priority
                      </span>
                    </div>
                    <div className="result-content">
                      <p style={{ whiteSpace: 'pre-line' }}>{result.content}</p>
                      <div className="result-details">
                        {result.details.map((detail: string, index: number) => (
                          <span key={index}>{detail}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
                
                {/* Generated Report Display */}
                {generatedReport && (
                  <div className="report-section">
                    <h3>Generated Report</h3>
                    <div className="report-file">
                      <div className="file-icon">📄</div>
                      <div className="file-info">
                        <div className="file-name">{generatedReport.name}</div>
                        <div className="file-size">{generatedReport.size}</div>
                      </div>
                      <button
                        className="download-btn"
                        onClick={downloadReport}
                      >
                        Download
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="ai-empty">
                <div className="empty-state-ai">
                  <h3>AI Analysis Ready</h3>
                  <p>Click this tab to automatically start AI analysis of the CT scan images.</p>
                  <button 
                    className="analyze-button"
                    onClick={triggerAiAnalysis}
                    disabled={!patient}
                  >
                    Start AI Analysis
                  </button>
                </div>
              </div>
            )}
          </div>
        );

      case 'chat':
        return (
          <div className="tab-content chat-tab">
            <div className="chat-header">
              <h2>AI Assistant Chat</h2>
              <span className="chat-status">
                <span className="status-dot online"></span>
                MendAI is online
              </span>
            </div>

            <div className="chat-container">
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
        );

      default:
        return <div>Tab content not found</div>;
    }
  };

  if (!patient) {
    return (
      <div className="patient-dashboard-page">
        <div className="no-patient-selected">
          <h2>No Patient Selected</h2>
          <p>Please select a patient from the Patient List to view their dashboard.</p>
          <button onClick={() => navigate('/patients')} className="back-button">
            Back to Patient List
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="patient-dashboard-page">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <h1>Patient Dashboard</h1>
          <span className="breadcrumb">
            <button onClick={() => navigate('/patients')} className="breadcrumb-link">
              Patient List
            </button>
            <span> / {patient.patientName || patient.patient_name}</span>
          </span>
        </div>
        <div className="header-right">
          <button className="header-button" onClick={() => navigate('/patients')}>
            Patient List
          </button>
        </div>
      </header>


      {/* Main Content Area */}
      <div className="dashboard-content">
        {/* Left Sidebar - Patient Info */}
        <aside className="patient-info-sidebar">
          <div className="patient-card">
            <div className="patient-avatar">
              {(patient.patientName || patient.patient_name || 'P').charAt(0).toUpperCase()}
            </div>
            <div className="patient-details">
              <h3>{patient.patientName || patient.patient_name}</h3>
              <div className="patient-meta">
                <div className="meta-item">
                  <span className="label">Patient ID:</span>
                  <span className="value">{patient.id}</span>
                </div>
                <div className="meta-item">
                  <span className="label">Upload Date:</span>
                  <span className="value">{patient.uploadedAt}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="quick-info-card">
            <h4>Current Study</h4>
            <div className="study-info">
              <div className="info-row">
                <span>File:</span>
                <span>{patient.fileName || 'No file'}</span>
              </div>
              <div className="info-row">
                <span>Date:</span>
                <span>{patient.uploadedAt}</span>
              </div>
              <div className="info-row">
                <span>Type:</span>
                <span>CT Scan</span>
              </div>
              <div className="info-row">
                <span>Status:</span>
                <span className="status-complete">Complete</span>
              </div>
            </div>
          </div>

        </aside>

        {/* Main Content */}
        <main className="main-content">
          {/* Internal Tab Navigation */}
          <nav className="internal-tab-navigation">
            <button
              className={`internal-tab-button ${activeTab === 'summary' ? 'active' : ''}`}
              onClick={() => handleTabChange('summary')}
            >
              Summary
            </button>
            <button
              className={`internal-tab-button ${activeTab === 'ct-analysis' ? 'active' : ''}`}
              onClick={() => handleTabChange('ct-analysis')}
            >
              CT Analysis
            </button>
            <button
              className={`internal-tab-button ${activeTab === 'ai-results' ? 'active' : ''}`}
              onClick={() => handleTabChange('ai-results')}
            >
              AI Results {loadingAiAnalysis && <span className="loading-indicator">●</span>}
            </button>
            <button
              className={`internal-tab-button ${activeTab === 'chat' ? 'active' : ''}`}
              onClick={() => handleTabChange('chat')}
            >
              Chat
            </button>
          </nav>
          
          {/* Tab Content */}
          <div className="internal-tab-content">
            {renderTabContent()}
          </div>
        </main>
      </div>

      {/* Image Preview Modal */}
      {previewModalOpen && (
        <div className="modal-overlay" onClick={() => setPreviewModalOpen(false)}>
          <div className="modal-content image-modal">
            <button 
              className="modal-close"
              onClick={() => setPreviewModalOpen(false)}
            >
              ×
            </button>
            <button onClick={handlePrevImage} className="nav-button left">◀</button>
            <img
              src={ctImages[currentImageIndex]}
              alt="Full CT"
              className="modal-image"
            />
            <button onClick={handleNextImage} className="nav-button right">▶</button>
            <div className="modal-info">
              Slice {currentImageIndex + 1} of {ctImages.length}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PatientDashboardPage;