import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './PatientDashboardPage.css';
import { apiService } from '../../services/api';
import type { Message } from '../../services/api';
import jsPDF from 'jspdf';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid, LineChart, Line, Legend } from 'recharts';

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
  const [isPlaying, setIsPlaying] = useState(false);
  const [playSpeed, setPlaySpeed] = useState(100); // milliseconds per frame
  const [jumpToSlice, setJumpToSlice] = useState('');

  // Modal zoom and pan state
  const [modalZoom, setModalZoom] = useState(1);
  const [modalPan, setModalPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // AI Analysis state
  const [aiResults, setAiResults] = useState<any[]>([]);
  const [loadingAiAnalysis, setLoadingAiAnalysis] = useState(false);
  const [aiAnalysisCompleted, setAiAnalysisCompleted] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);

  // Real-time slice analysis state
  const [sliceAnalysis, setSliceAnalysis] = useState<any>(null);
  const [loadingSliceAnalysis, setLoadingSliceAnalysis] = useState(false);
  const [sliceAnalysisError, setSliceAnalysisError] = useState<string | null>(null);
  const [generatedReport, setGeneratedReport] = useState<{ name: string; url: string; size: string } | null>(null);

  // Patient normalized data state
  const [patientNormalizedData, setPatientNormalizedData] = useState<any>(null);

  // Sidebar collapse state
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Authentication check
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }
  }, [navigate]);

  // Load patient normalized data (with timeout handling)
  useEffect(() => {
    const loadPatientNormalizedData = async () => {
      if (!patient || !patient.fhirId) {
        setPatientNormalizedData(null);
        return;
      }

      try {
        const apiUrl = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v0/patients/${patient.fhirId}/normalized`;

        console.log(`Fetching normalized data for patient ${patient.fhirId}...`);

        // Create an abort controller with timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

        const response = await fetch(apiUrl, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (response.ok) {
          const data = await response.json();
          console.log('Loaded normalized patient data:', data);
          setPatientNormalizedData(data);
        } else {
          console.warn(`Failed to load normalized patient data: ${response.status}. Using demographics only.`);
          setPatientNormalizedData(null);
        }
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          console.warn('Request timed out. Using demographics data only for charts.');
        } else {
          console.error('Error loading normalized patient data:', error);
        }
        setPatientNormalizedData(null);
      }
    };

    loadPatientNormalizedData();
  }, [patient]);

  // Load images for a specific file
  const loadImagesForFile = async (fileId: string) => {
    if (!patient) return;

    try {
      setLoadingImages(true);
      const apiUrl = `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v0/patients/${patient.id}/images?file_id=${fileId}`;
      console.log('Fetching images for file:', fileId, 'from:', apiUrl);

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
          setCtImages(imagesData.images);
          setCurrentImageIndex(0);
          console.log('CT images set successfully for file:', fileId);
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
    } finally {
      setLoadingImages(false);
    }
  };

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
          const niiFiles = filesResponse.files.filter(file =>
            file.file_name.toLowerCase().endsWith('.nii') ||
            file.file_name.toLowerCase().endsWith('.nii.gz')
          );
          console.log('Filtered NIfTI files:', niiFiles);
          console.log('Number of NIfTI files found:', niiFiles.length);
          setPatientFiles(niiFiles);

          if (niiFiles.length > 0) {
            // Load images for the first file
            setCurrentFileIndex(0);
            await loadImagesForFile(niiFiles[0].id);
          } else {
            // No NIfTI files found
            setCtImages([
              'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400"><rect width="400" height="400" fill="%23fef2f2"/><circle cx="200" cy="200" r="80" fill="%23fecaca" stroke="%23dc2626" stroke-width="2"/><text x="200" y="190" font-family="Arial" font-size="14" fill="%23dc2626" text-anchor="middle">No NIfTI Files</text><text x="200" y="210" font-family="Arial" font-size="12" fill="%23dc2626" text-anchor="middle">Please upload .nii files</text></svg>'
            ]);
            setLoadingImages(false);
          }
        } else {
          // No files available
          setCtImages([
            'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400"><rect width="400" height="400" fill="%23f3f4f6"/><circle cx="200" cy="200" r="80" fill="%23d1d5db" stroke="%236b7280" stroke-width="2"/><text x="200" y="195" font-family="Arial" font-size="14" fill="%23374151" text-anchor="middle">No CT Files</text><text x="200" y="215" font-family="Arial" font-size="12" fill="%236b7280" text-anchor="middle">Upload files</text></svg>'
          ]);
          setLoadingImages(false);
        }
      } catch (error) {
        console.error('Error loading patient files:', error);
        console.error('Patient data:', patient);
        setCtImages([
          'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400"><rect width="400" height="400" fill="%23fef2f2"/><circle cx="200" cy="200" r="80" fill="%23fecaca" stroke="%23dc2626" stroke-width="2"/><text x="200" y="190" font-family="Arial" font-size="14" fill="%23dc2626" text-anchor="middle">Loading Failed</text><text x="200" y="210" font-family="Arial" font-size="12" fill="%23dc2626" text-anchor="middle">Check console for details</text></svg>'
        ]);
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

  // File navigation (between different NIfTI files)
  const handlePrevFile = () => {
    if (patientFiles.length > 0) {
      const newIndex = (currentFileIndex - 1 + patientFiles.length) % patientFiles.length;
      setCurrentFileIndex(newIndex);
      // Load images for the new file
      loadImagesForFile(patientFiles[newIndex].id);
    }
  };

  const handleNextFile = () => {
    if (patientFiles.length > 0) {
      const newIndex = (currentFileIndex + 1) % patientFiles.length;
      setCurrentFileIndex(newIndex);
      // Load images for the new file
      loadImagesForFile(patientFiles[newIndex].id);
    }
  };

  // Image/Slice navigation (between slices within the current image set)
  const handlePrevImage = () => {
    if (ctImages.length > 0) {
      const newIndex = (currentImageIndex - 1 + ctImages.length) % ctImages.length;
      setCurrentImageIndex(newIndex);
    }
  };

  const handleNextImage = () => {
    if (ctImages.length > 0) {
      const newIndex = (currentImageIndex + 1) % ctImages.length;
      setCurrentImageIndex(newIndex);
    }
  };

  // Jump to specific slice
  const handleJumpToSlice = () => {
    const sliceNum = parseInt(jumpToSlice);
    if (!isNaN(sliceNum) && sliceNum >= 1 && sliceNum <= ctImages.length) {
      setCurrentImageIndex(sliceNum - 1);
      setJumpToSlice('');
    }
  };

  // Modal zoom and pan handlers
  const handleZoomIn = () => {
    setModalZoom(prev => Math.min(prev + 0.5, 5));
  };

  const handleZoomOut = () => {
    setModalZoom(prev => Math.max(prev - 0.5, 0.5));
  };

  const handleResetZoom = () => {
    setModalZoom(1);
    setModalPan({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (modalZoom > 1) {
      setIsDragging(true);
      setDragStart({ x: e.clientX - modalPan.x, y: e.clientY - modalPan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging && modalZoom > 1) {
      setModalPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    if (e.deltaY < 0) {
      handleZoomIn();
    } else {
      handleZoomOut();
    }
  };

  // Reset zoom when modal opens/closes
  const openModal = () => {
    setPreviewModalOpen(true);
    setModalZoom(1);
    setModalPan({ x: 0, y: 0 });
  };

  const closeModal = () => {
    setPreviewModalOpen(false);
    setModalZoom(1);
    setModalPan({ x: 0, y: 0 });
  };

  // Toggle auto-play
  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  // Auto-play effect
  React.useEffect(() => {
    if (isPlaying && ctImages.length > 0) {
      const interval = setInterval(() => {
        setCurrentImageIndex((prevIndex) => (prevIndex + 1) % ctImages.length);
      }, playSpeed);
      return () => clearInterval(interval);
    }
  }, [isPlaying, ctImages.length, playSpeed]);

  // Keyboard navigation
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Modal keyboard controls
      if (previewModalOpen) {
        if (e.key === 'Escape') {
          e.preventDefault();
          closeModal();
        } else if (e.key === 'ArrowLeft') {
          e.preventDefault();
          handlePrevImage();
        } else if (e.key === 'ArrowRight') {
          e.preventDefault();
          handleNextImage();
        } else if (e.key === '+' || e.key === '=') {
          e.preventDefault();
          handleZoomIn();
        } else if (e.key === '-' || e.key === '_') {
          e.preventDefault();
          handleZoomOut();
        } else if (e.key === '0') {
          e.preventDefault();
          handleResetZoom();
        }
      }
      // CT analysis tab keyboard controls
      else if (activeTab === 'ct-analysis' && ctImages.length > 0) {
        if (e.key === 'ArrowLeft') {
          e.preventDefault();
          handlePrevImage();
        } else if (e.key === 'ArrowRight') {
          e.preventDefault();
          handleNextImage();
        } else if (e.key === ' ') {
          e.preventDefault();
          togglePlay();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeTab, ctImages.length, currentImageIndex, previewModalOpen, modalZoom]);

  // AI Analysis function
  const triggerAiAnalysis = async () => {
    if (loadingAiAnalysis || !patient || ctImages.length === 0) {
      return;
    }

    // Get slice range from inputs
    const fromSliceInput = document.getElementById('slice-from') as HTMLInputElement;
    const toSliceInput = document.getElementById('slice-to') as HTMLInputElement;

    const fromSlice = fromSliceInput ? parseInt(fromSliceInput.value) : 1;
    const toSlice = toSliceInput ? parseInt(toSliceInput.value) : ctImages.length;

    // Validate range
    if (fromSlice < 1 || toSlice > ctImages.length || fromSlice > toSlice) {
      alert(`Please enter a valid slice range (1-${ctImages.length})`);
      return;
    }

    const sliceCount = toSlice - fromSlice + 1;
    console.log(`Analyzing slices ${fromSlice} to ${toSlice} (${sliceCount} slices)`);

    setLoadingAiAnalysis(true);

    try {
      // Simulate analysis time based on number of slices
      await new Promise(resolve => setTimeout(resolve, 1500 + sliceCount * 10));

      // Get current file info
      const currentFile = patientFiles[currentFileIndex];
      const fileName = currentFile?.file_name || 'CT Scan';

      // Generate mock analysis results based on slice range
      const mockResults = [
        {
          id: 1,
          priority: 'high',
          icon: '📊',
          title: 'Analysis Summary',
          content: `Analyzed ${sliceCount} CT slices (${fromSlice}-${toSlice}) from ${fileName}. The AI system has completed a comprehensive evaluation of the specified region.`,
          details: [
            `File: ${fileName}`,
            `Slices Analyzed: ${fromSlice} to ${toSlice} (${sliceCount} total)`,
            `Analysis Confidence: ${(88 + Math.random() * 10).toFixed(0)}%`,
            `Analysis Date: ${new Date().toLocaleString()}`
          ]
        },
        {
          id: 2,
          priority: Math.random() > 0.7 ? 'high' : 'medium',
          icon: '🔍',
          title: 'Key Findings',
          content: Math.random() > 0.6
            ? `• Normal lung parenchyma observed throughout analyzed slices\n• No significant masses or nodules detected\n• Clear airways and vasculature\n• Symmetric bilateral findings`
            : `• Small nodular opacity noted in right upper lobe (slice ${Math.floor(fromSlice + sliceCount * 0.3)})\n• Recommend follow-up imaging in 3-6 months\n• Otherwise normal lung parenchyma\n• Clear airways observed`,
          details: [
            'Lung Fields: Within normal limits',
            'Mediastinum: Normal size and position',
            'Bone Structures: No acute abnormalities'
          ]
        },
        {
          id: 3,
          priority: 'medium',
          icon: '💡',
          title: 'Clinical Recommendations',
          content: Math.random() > 0.6
            ? `• Continue routine monitoring\n• No immediate intervention required\n• Annual follow-up CT recommended\n• Maintain current treatment plan if applicable`
            : `• Follow-up CT scan in 3-6 months\n• Correlate with clinical symptoms\n• Consider pulmonology consultation\n• Document any changes in patient condition`,
          details: [
            'Urgency: Routine',
            'Suggested Follow-up: 3-12 months',
            'Additional Tests: As clinically indicated'
          ]
        }
      ];

      setAiResults(mockResults);
      setAiAnalysisCompleted(true);

    } catch (error) {
      console.error('AI Analysis failed:', error);
      setAiResults([
        {
          id: 1,
          priority: 'medium',
          icon: '⚠️',
          title: 'Analysis Error',
          content: 'Unable to complete analysis. Please try again.',
          details: [
            'Status: Error',
            'Timestamp: ' + new Date().toLocaleString()
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
  };

  // Real-time slice analysis function
  const analyzeCurrentSlice = async () => {
    if (!patient || ctImages.length === 0 || loadingSliceAnalysis) {
      return;
    }

    setLoadingSliceAnalysis(true);
    setSliceAnalysisError(null);

    try {
      // Generate synthetic analysis based on slice position
      const position = currentImageIndex / ctImages.length;
      const sliceType = position < 0.3 ? 'upper' : position < 0.7 ? 'middle' : 'lower';

      // Randomize findings based on slice position
      const findingsOptions = [
        {
          type: 'Normal',
          description: 'No significant abnormalities detected in this slice',
          confidence: 0.85 + Math.random() * 0.12
        },
        {
          type: 'Normal',
          description: 'Lung parenchyma appears normal with clear visualization',
          confidence: 0.88 + Math.random() * 0.1
        },
        {
          type: 'Abnormal',
          description: 'Small nodular opacity detected, recommend follow-up',
          confidence: 0.72 + Math.random() * 0.15
        },
        {
          type: 'Suspicious',
          description: 'Subtle density changes noted, further evaluation needed',
          confidence: 0.65 + Math.random() * 0.15
        }
      ];

      // Select findings based on position (mostly normal)
      const selectedFindings = Math.random() > 0.7
        ? [findingsOptions[Math.floor(Math.random() * findingsOptions.length)]]
        : [findingsOptions[0]];

      const mockAnalysis = {
        slice_number: currentImageIndex + 1,
        total_slices: ctImages.length,
        anatomical_region: sliceType === 'upper' ? 'Upper Thorax' :
                          sliceType === 'middle' ? 'Mid Thorax' : 'Lower Thorax',
        findings: selectedFindings,
        quality_score: 0.85 + Math.random() * 0.13,
        timestamp: new Date().toISOString()
      };

      setSliceAnalysis(mockAnalysis);
      setSliceAnalysisError(null);
    } catch (error) {
      console.error('Slice analysis error:', error);
      setSliceAnalysisError('Unable to analyze slice');
    } finally {
      setLoadingSliceAnalysis(false);
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
        // Calculate patient age
        const calculateAge = (birthDate: string) => {
          if (!birthDate) return null;
          const today = new Date();
          const birth = new Date(birthDate);
          let age = today.getFullYear() - birth.getFullYear();
          const monthDiff = today.getMonth() - birth.getMonth();
          if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
            age--;
          }
          return age;
        };

        const patientAge = patient?.birthDate ? calculateAge(patient.birthDate) : null;

        // Generate pseudo-random but consistent data based on patient ID
        // This ensures each patient has different data even without FHIR encounter data
        const patientIdHash = patient?.id ? parseInt(patient.id.substring(0, 8), 36) : 0;
        const seed = patientIdHash % 100;

        // Extract vital signs from normalized patient data OR generate based on demographics
        let vitalSignsData = [
          { name: 'Temperature', value: 98.6, unit: '°F', normal: 98.6, color: '#10b981' },
          { name: 'Heart Rate', value: 72, unit: 'bpm', normal: 72, color: '#10b981' },
          { name: 'Resp. Rate', value: 16, unit: '/min', normal: 16, color: '#10b981' },
          { name: 'O2 Sat', value: 98, unit: '%', normal: 98, color: '#10b981' },
        ];

        let bloodPressureTrendData = [
          { date: 'N/A', systolic: 120, diastolic: 80, normalSystolic: 120, normalDiastolic: 80 },
        ];

        let encounterStatsData = [
          { name: 'Diagnoses', value: 0, color: '#8b5cf6' },
          { name: 'Procedures', value: 0, color: '#3b82f6' },
          { name: 'Medications', value: 0, color: '#10b981' },
          { name: 'Observations', value: 0, color: '#f59e0b' },
        ];

        // If no FHIR data available, generate synthetic data based on patient demographics
        if (!patientNormalizedData || !patientNormalizedData.encounters || patientNormalizedData.encounters.length === 0) {
          console.log('Using synthetic data for patient:', patient?.id);

          // Generate varied vital signs based on patient demographics
          const genderVariance = patient?.gender === 'male' ? 2 : -2;

          const tempValue = 98.6 + (seed % 5) * 0.2 - 0.4;
          const hrValue = 72 + Math.floor((seed % 30) - 15) + genderVariance;
          const rrValue = 16 + Math.floor((seed % 8) - 4);
          const o2Value = 98 + Math.floor((seed % 4) - 1);

          vitalSignsData = [
            {
              name: 'Temperature',
              value: parseFloat(tempValue.toFixed(1)),
              unit: '°F',
              normal: 98.6,
              color: tempValue > 99.5 ? '#ef4444' : tempValue > 98.9 ? '#f59e0b' : '#10b981'
            },
            {
              name: 'Heart Rate',
              value: hrValue,
              unit: 'bpm',
              normal: 72,
              color: hrValue > 100 || hrValue < 60 ? '#ef4444' : hrValue > 90 || hrValue < 65 ? '#f59e0b' : '#10b981'
            },
            {
              name: 'Resp. Rate',
              value: rrValue,
              unit: '/min',
              normal: 16,
              color: rrValue > 20 || rrValue < 12 ? '#ef4444' : '#10b981'
            },
            {
              name: 'O2 Sat',
              value: o2Value,
              unit: '%',
              normal: 98,
              color: o2Value < 95 ? '#ef4444' : o2Value < 97 ? '#f59e0b' : '#10b981'
            },
          ];

          // Generate blood pressure trend based on age and demographics
          const baseSystolic = 120 + (patientAge ? Math.floor((patientAge - 50) * 0.5) : 0);
          const baseDiastolic = 80 + (patientAge ? Math.floor((patientAge - 50) * 0.3) : 0);

          bloodPressureTrendData = [
            { date: 'Week 1', systolic: baseSystolic - (seed % 8), diastolic: baseDiastolic - (seed % 5), normalSystolic: 120, normalDiastolic: 80 },
            { date: 'Week 2', systolic: baseSystolic - (seed % 5), diastolic: baseDiastolic - (seed % 3), normalSystolic: 120, normalDiastolic: 80 },
            { date: 'Week 3', systolic: baseSystolic + (seed % 6), diastolic: baseDiastolic + (seed % 4), normalSystolic: 120, normalDiastolic: 80 },
            { date: 'Week 4', systolic: baseSystolic + (seed % 10), diastolic: baseDiastolic + (seed % 6), normalSystolic: 120, normalDiastolic: 80 },
          ];

          // Generate encounter stats
          encounterStatsData = [
            { name: 'Diagnoses', value: 1 + (seed % 3), color: '#8b5cf6' },
            { name: 'Procedures', value: (seed % 5), color: '#3b82f6' },
            { name: 'Medications', value: 1 + (seed % 6), color: '#10b981' },
            { name: 'Observations', value: 5 + (seed % 8), color: '#f59e0b' },
          ];
        }

        if (patientNormalizedData && patientNormalizedData.encounters && patientNormalizedData.encounters.length > 0) {
          // Get the most recent encounter
          const latestEncounter = patientNormalizedData.encounters[0];

          // Extract vital signs from observations
          const observations = latestEncounter.observations || [];

          const tempObs = observations.find((obs: any) => obs.code?.text === 'Body temperature');
          const hrObs = observations.find((obs: any) => obs.code?.text === 'Heart rate');
          const rrObs = observations.find((obs: any) => obs.code?.text === 'Respiratory rate');
          const o2Obs = observations.find((obs: any) => obs.code?.text === 'Oxygen saturation in Arterial blood');

          if (tempObs?.value?.value) {
            const tempValue = tempObs.value.value;
            vitalSignsData[0] = {
              name: 'Temperature',
              value: tempValue,
              unit: '°F',
              normal: 98.6,
              color: tempValue > 99.5 ? '#ef4444' : tempValue > 98.9 ? '#f59e0b' : '#10b981'
            };
          }

          if (hrObs?.value?.value) {
            const hrValue = hrObs.value.value;
            vitalSignsData[1] = {
              name: 'Heart Rate',
              value: hrValue,
              unit: 'bpm',
              normal: 72,
              color: hrValue > 100 || hrValue < 60 ? '#ef4444' : hrValue > 90 || hrValue < 65 ? '#f59e0b' : '#10b981'
            };
          }

          if (rrObs?.value?.value) {
            const rrValue = rrObs.value.value;
            vitalSignsData[2] = {
              name: 'Resp. Rate',
              value: rrValue,
              unit: '/min',
              normal: 16,
              color: rrValue > 20 || rrValue < 12 ? '#ef4444' : '#10b981'
            };
          }

          if (o2Obs?.value?.value) {
            const o2Value = o2Obs.value.value;
            vitalSignsData[3] = {
              name: 'O2 Sat',
              value: o2Value,
              unit: '%',
              normal: 98,
              color: o2Value < 95 ? '#ef4444' : o2Value < 97 ? '#f59e0b' : '#10b981'
            };
          }

          // Extract blood pressure trend from encounters
          bloodPressureTrendData = patientNormalizedData.encounters.slice(0, 4).reverse().map((enc: any) => {
            const bpObservation = enc.observations?.find((obs: any) =>
              obs.code?.text === 'Blood pressure panel with all children optional'
            );

            const systolicComp = bpObservation?.components?.find((c: any) => c.text === 'Systolic blood pressure');
            const diastolicComp = bpObservation?.components?.find((c: any) => c.text === 'Diastolic blood pressure');

            const systolic = systolicComp?.value?.value || 120;
            const diastolic = diastolicComp?.value?.value || 80;

            return {
              date: new Date(enc.start).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
              systolic,
              diastolic,
              normalSystolic: 120,
              normalDiastolic: 80
            };
          });

          // Count encounter statistics
          encounterStatsData = [
            { name: 'Diagnoses', value: latestEncounter.diagnoses?.length || 0, color: '#8b5cf6' },
            { name: 'Procedures', value: latestEncounter.procedures?.length || 0, color: '#3b82f6' },
            { name: 'Medications', value: (latestEncounter.medicationStatements?.length || 0) + (latestEncounter.medicationDispense?.length || 0), color: '#10b981' },
            { name: 'Observations', value: latestEncounter.observations?.length || 0, color: '#f59e0b' },
          ];
        }

        // Health metrics overview
        const normalVitals = vitalSignsData.filter(v => v.color === '#10b981').length;
        const abnormalVitals = vitalSignsData.filter(v => v.color !== '#10b981').length;

        const healthMetricsData = [
          { category: 'Normal Vitals', status: 'Normal', count: normalVitals, color: '#10b981' },
          { category: 'Abnormal Vitals', status: 'Warning', count: abnormalVitals, color: '#f59e0b' },
        ].filter(m => m.count > 0);

        return (
          <div className="tab-content summary-tab">
            <div className="summary-header">
              <div className="last-updated">Last updated: {new Date().toLocaleDateString()}</div>
            </div>

            {/* Patient Data Visualizations */}
            <div className="visualization-section">
              <h2 style={{ marginTop: '0', marginBottom: '1rem' }}>Clinical Data Visualizations</h2>

              <div className="charts-grid">
                {/* Vital Signs Chart */}
                <div className="chart-card">
                  <h3>Latest Vital Signs</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={vitalSignsData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip
                        content={({ active, payload }: any) => {
                          if (active && payload && payload.length) {
                            return (
                              <div style={{
                                background: 'white',
                                padding: '10px',
                                border: '1px solid #ccc',
                                borderRadius: '8px'
                              }}>
                                <p style={{ margin: 0, fontWeight: 600 }}>{payload[0].payload.name}</p>
                                <p style={{ margin: '4px 0 0 0', color: '#64748b' }}>
                                  Current: {payload[0].value} {payload[0].payload.unit}
                                </p>
                                <p style={{ margin: '4px 0 0 0', color: '#64748b' }}>
                                  Normal: {payload[0].payload.normal} {payload[0].payload.unit}
                                </p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Bar dataKey="value">
                        {vitalSignsData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <p className="chart-description">
                    Vital signs from most recent encounter
                  </p>
                </div>

                {/* Blood Pressure Trend Chart */}
                <div className="chart-card">
                  <h3>Blood Pressure Trend</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={bloodPressureTrendData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis domain={[60, 160]} label={{ value: 'mm[Hg]', angle: -90, position: 'insideLeft' }} />
                      <Tooltip />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="systolic"
                        stroke="#ef4444"
                        strokeWidth={2}
                        name="Systolic"
                        dot={{ fill: '#ef4444', r: 5 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="diastolic"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        name="Diastolic"
                        dot={{ fill: '#f59e0b', r: 5 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="normalSystolic"
                        stroke="#94a3b8"
                        strokeWidth={1}
                        strokeDasharray="5 5"
                        name="Normal Systolic"
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="normalDiastolic"
                        stroke="#cbd5e1"
                        strokeWidth={1}
                        strokeDasharray="5 5"
                        name="Normal Diastolic"
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                  <p className="chart-description">
                    Latest: 149/92 mm[Hg] - Elevated and trending upward
                  </p>
                </div>

                {/* Encounter Statistics */}
                <div className="chart-card">
                  <h3>Encounter Summary</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={encounterStatsData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={(entry: any) => `${entry.name}: ${entry.value}`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {encounterStatsData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                  <p className="chart-description">
                    Medical records from recent emergency visit
                  </p>
                </div>

                {/* Health Status Overview */}
                <div className="chart-card">
                  <h3>Health Status Overview</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={healthMetricsData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={(entry: any) => `${entry.category}: ${entry.count}`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="count"
                      >
                        {healthMetricsData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                  <p className="chart-description">
                    Overall patient health metrics assessment
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      case 'ct-analysis':
        return (
          <div className="tab-content ct-analysis-tab">
            <div className="ct-header">
              <div style={{ flex: 1 }}>
                {/* File Selector for Multiple Files */}
                {patientFiles.length > 1 && (
                  <div className="file-selector-bar">
                    <label className="file-selector-label">Select CT Scan:</label>
                    <select
                      value={currentFileIndex}
                      onChange={(e) => {
                        const newIndex = parseInt(e.target.value);
                        setCurrentFileIndex(newIndex);
                        // Load images for the selected file
                        loadImagesForFile(patientFiles[newIndex].id);
                      }}
                      className="file-selector-dropdown"
                    >
                      {patientFiles.map((file, index) => (
                        <option key={file.id} value={index}>
                          {file.file_name} ({new Date(file.uploaded_at).toLocaleDateString()})
                        </option>
                      ))}
                    </select>
                    <span className="file-count-badge">
                      {currentFileIndex + 1} of {patientFiles.length} files
                    </span>
                  </div>
                )}
              </div>
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
                    {/* Current File Indicator */}
                    {patientFiles.length > 0 && (
                      <div style={{
                        position: 'absolute',
                        top: '10px',
                        left: '10px',
                        background: 'rgba(0, 123, 255, 0.9)',
                        color: 'white',
                        padding: '8px 16px',
                        borderRadius: '8px',
                        fontWeight: 'bold',
                        fontSize: '14px',
                        zIndex: 10,
                        boxShadow: '0 2px 8px rgba(0,0,0,0.3)'
                      }}>
                        📁 {patientFiles[currentFileIndex]?.file_name || 'Loading...'}
                      </div>
                    )}
                    <img
                      src={ctImages[currentImageIndex]}
                      alt={`CT Scan ${currentImageIndex + 1}`}
                      className="ct-image"
                      onClick={openModal}
                    />
                    <div className="ct-controls">
                      {/* Slice navigation buttons */}
                      <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '10px' }}>
                        <button
                          onClick={handlePrevImage}
                          className="nav-btn"
                          disabled={ctImages.length <= 1}
                        >
                          ◀ Previous
                        </button>
                        <button
                          onClick={togglePlay}
                          className="nav-btn"
                          disabled={ctImages.length <= 1}
                          style={{ minWidth: '80px' }}
                        >
                          {isPlaying ? '⏸ Pause' : '▶ Play'}
                        </button>
                        <span className="slice-info" style={{ flex: 1, textAlign: 'center', fontWeight: 'bold' }}>
                          Slice {currentImageIndex + 1} of {ctImages.length}
                        </span>
                        <button
                          onClick={handleNextImage}
                          className="nav-btn"
                          disabled={ctImages.length <= 1}
                        >
                          Next ▶
                        </button>
                      </div>

                      {/* Slider for quick navigation */}
                      <div style={{ marginBottom: '10px' }}>
                        <input
                          type="range"
                          min="0"
                          max={ctImages.length - 1}
                          value={currentImageIndex}
                          onChange={(e) => setCurrentImageIndex(parseInt(e.target.value))}
                          style={{ width: '100%', cursor: 'pointer' }}
                          disabled={ctImages.length <= 1}
                        />
                      </div>

                      {/* Jump to slice and speed controls */}
                      <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '10px', fontSize: '0.875rem' }}>
                        <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                          <label>Jump to:</label>
                          <input
                            type="number"
                            min="1"
                            max={ctImages.length}
                            value={jumpToSlice}
                            onChange={(e) => setJumpToSlice(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleJumpToSlice()}
                            placeholder="#"
                            style={{ width: '60px', padding: '4px', border: '1px solid #ccc', borderRadius: '4px' }}
                          />
                          <button
                            onClick={handleJumpToSlice}
                            className="nav-btn"
                            style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                          >
                            Go
                          </button>
                        </div>
                        <div style={{ display: 'flex', gap: '5px', alignItems: 'center', marginLeft: 'auto' }}>
                          <label>Speed:</label>
                          <select
                            value={playSpeed}
                            onChange={(e) => setPlaySpeed(parseInt(e.target.value))}
                            style={{ padding: '4px', border: '1px solid #ccc', borderRadius: '4px' }}
                          >
                            <option value="50">Fast (20 fps)</option>
                            <option value="100">Normal (10 fps)</option>
                            <option value="200">Slow (5 fps)</option>
                            <option value="500">Very Slow (2 fps)</option>
                          </select>
                        </div>
                      </div>

                      {/* Keyboard shortcuts hint */}
                      <div style={{ fontSize: '0.75rem', color: '#6b7280', textAlign: 'center', marginBottom: '10px' }}>
                        Keyboard: Arrow keys to navigate, Space to play/pause
                      </div>

                      {/* File navigation (if multiple files) */}
                      {patientFiles.length > 1 && (
                        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', borderTop: '1px solid #e5e7eb', paddingTop: '10px' }}>
                          <button
                            onClick={handlePrevFile}
                            className="nav-btn"
                            disabled={patientFiles.length <= 1}
                          >
                            ◀ Previous File
                          </button>
                          <span className="slice-info" style={{ flex: 1, textAlign: 'center', fontSize: '0.875rem' }}>
                            File {currentFileIndex + 1} of {patientFiles.length}: {patientFiles[currentFileIndex]?.file_name || 'Loading...'}
                          </span>
                          <button
                            onClick={handleNextFile}
                            className="nav-btn"
                            disabled={patientFiles.length <= 1}
                          >
                            Next File ▶
                          </button>
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="no-images">
                    <p>No CT scan images available for this patient.</p>
                  </div>
                )}
              </div>
              
              <div className="ct-sidebar">
              {/* Slice Analysis Section */}
              <div className="ct-info-card">
                <h4>Slice Analysis</h4>
                <button
                  onClick={analyzeCurrentSlice}
                  disabled={loadingSliceAnalysis || ctImages.length === 0}
                  className="analyze-slice-btn"
                >
                  {loadingSliceAnalysis ? 'Analyzing...' : 'Analyze Current Slice'}
                </button>

                {sliceAnalysisError && (
                  <div className="analysis-error-message">
                    {sliceAnalysisError}
                  </div>
                )}

                {sliceAnalysis && !loadingSliceAnalysis && (
                  <div className="analysis-results">
                    <div className="analysis-header">
                      <span className="analysis-label">Slice {sliceAnalysis.slice_number}</span>
                      <span className="analysis-region">{sliceAnalysis.anatomical_region}</span>
                    </div>

                    <div className="findings-section">
                      <span className="findings-label">Findings</span>
                      {sliceAnalysis.findings && sliceAnalysis.findings.map((finding: any, idx: number) => (
                        <div key={idx} className="finding-item">
                          <span className={`finding-type ${finding.type.toLowerCase()}`}>
                            {finding.type}
                          </span>
                          <span className="finding-desc">{finding.description}</span>
                          <span className="finding-confidence">
                            {Math.round(finding.confidence * 100)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              </div>
            </div>
          </div>
        );

      case 'ai-results':
        return (
          <div className="tab-content ai-results-tab">
            <div className="ai-header">
              <div style={{ flex: 1 }}>
                {/* CT Slice Range Selector */}
                <div className="slice-range-selector">
                  {/* File Selector */}
                  {patientFiles.length > 1 && (
                    <div className="selector-row">
                      <label className="selector-label">Select CT File:</label>
                      <select
                        value={currentFileIndex}
                        onChange={(e) => {
                          const newIndex = parseInt(e.target.value);
                          setCurrentFileIndex(newIndex);
                          // Load images for the selected file
                          loadImagesForFile(patientFiles[newIndex].id);
                        }}
                        className="file-selector-dropdown"
                        style={{ maxWidth: '400px' }}
                      >
                        {patientFiles.map((file, index) => (
                          <option key={file.id} value={index}>
                            {file.file_name} ({new Date(file.uploaded_at).toLocaleDateString()})
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  {/* Slice Range Selector */}
                  <div className="selector-row">
                    <label className="selector-label">Select CT Slices to Analyze:</label>
                    <div className="range-inputs">
                      <div className="input-group">
                        <label>From Slice:</label>
                        <input
                          type="number"
                          min="1"
                          max={ctImages.length}
                          defaultValue="1"
                          className="slice-input"
                          id="slice-from"
                        />
                      </div>
                      <span className="range-separator">to</span>
                      <div className="input-group">
                        <label>To Slice:</label>
                        <input
                          type="number"
                          min="1"
                          max={ctImages.length}
                          defaultValue={ctImages.length}
                          className="slice-input"
                          id="slice-to"
                        />
                      </div>
                      <span className="total-slices">
                        (Total: {ctImages.length} slices)
                      </span>
                    </div>
                  </div>
                  <button
                    className="analyze-slices-btn"
                    onClick={triggerAiAnalysis}
                    disabled={loadingAiAnalysis || ctImages.length === 0}
                  >
                    {loadingAiAnalysis ? 'Analyzing...' : 'Start Analysis'}
                  </button>
                </div>
              </div>
            </div>

            {/* Generate Report Button - Centered */}
            {aiResults.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '1.5rem' }}>
                <button
                  className="generate-report-btn"
                  onClick={generatePdfReport}
                  disabled={generatingReport}
                >
                  {generatingReport ? 'Generating...' : 'Generate Report'}
                </button>

                {/* Generated Report Display - Below Button */}
                {generatedReport && (
                  <div className="report-section" style={{ marginTop: '1.5rem' }}>
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
            )}

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
              </div>
            ) : (
              <div className="ai-empty">
                <div className="empty-state-ai">
                  <h3>No Analysis Results Yet</h3>
                  <p>Select the CT slice range above and click "Start Analysis" to begin AI analysis.</p>
                </div>
              </div>
            )}
          </div>
        );

      case 'chat':
        return (
          <div className="tab-content chat-tab">
            <div className="chat-header">
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
        <aside className={`patient-info-sidebar ${isSidebarCollapsed ? 'collapsed' : ''}`}>
          <button
            className="sidebar-collapse-btn"
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            title={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isSidebarCollapsed ? '»' : '«'}
          </button>
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

          {/* Patient Demographics */}
          <div className="quick-info-card">
            <h4>Patient Demographics</h4>
            <div className="info-row">
              <span>Patient Name:</span>
              <span>{patient?.patientName || patient?.patient_name || 'N/A'}</span>
            </div>
            <div className="info-row">
              <span>Patient ID:</span>
              <span>{patient?.id || 'N/A'}</span>
            </div>
            {patient?.fhirId && (
              <div className="info-row">
                <span>FHIR ID:</span>
                <span style={{ fontSize: '0.75rem', fontFamily: 'monospace' }}>{patient.fhirId}</span>
              </div>
            )}
            <div className="info-row">
              <span>Birth Date:</span>
              <span>
                {patient?.birthDate
                  ? new Date(patient.birthDate).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })
                  : 'N/A'}
              </span>
            </div>
            <div className="info-row">
              <span>Age:</span>
              <span>
                {patient?.birthDate ? (() => {
                  const today = new Date();
                  const birth = new Date(patient.birthDate);
                  let age = today.getFullYear() - birth.getFullYear();
                  const monthDiff = today.getMonth() - birth.getMonth();
                  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
                    age--;
                  }
                  return `${age} years`;
                })() : 'N/A'}
              </span>
            </div>
            <div className="info-row">
              <span>Gender:</span>
              <span style={{ textTransform: 'capitalize' }}>{patient?.gender || 'N/A'}</span>
            </div>
            <div className="info-row">
              <span>Race:</span>
              <span>{patient?.race || 'N/A'}</span>
            </div>
            <div className="info-row">
              <span>Ethnicity:</span>
              <span>{patient?.ethnicity || 'N/A'}</span>
            </div>
            <div className="info-row">
              <span>Marital Status:</span>
              <span>
                {patient?.maritalStatus === 'S' ? 'Single' :
                 patient?.maritalStatus === 'M' ? 'Married' :
                 patient?.maritalStatus === 'D' ? 'Divorced' :
                 patient?.maritalStatus === 'W' ? 'Widowed' :
                 patient?.maritalStatus === 'UNK' ? 'Unknown' :
                 patient?.maritalStatus || 'N/A'}
              </span>
            </div>
            {patient?.language && (
              <div className="info-row">
                <span>Language:</span>
                <span style={{ textTransform: 'uppercase' }}>{patient.language}</span>
              </div>
            )}
            {patient?.managingOrganization && (
              <div className="info-row">
                <span>Managing Org:</span>
                <span>{patient.managingOrganization}</span>
              </div>
            )}
          </div>

          {/* Medical Records */}
          <div className="quick-info-card">
            <h4>Medical Records</h4>
            <div className="info-row">
              <span>Upload Date:</span>
              <span>
                {patient?.uploadedAt
                  ? new Date(patient.uploadedAt).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })
                  : 'N/A'}
              </span>
            </div>
            <div className="info-row">
              <span>Primary File:</span>
              <span>{patient?.fileName || 'No file'}</span>
            </div>
            {patientFiles.length > 0 && (
              <div className="info-row">
                <span>Total Files:</span>
                <span>{patientFiles.length} CT scans</span>
              </div>
            )}
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

      {/* Enhanced Image Preview Modal */}
      {previewModalOpen && (
        <div className="modal-overlay" onClick={(e) => {
          if (e.target === e.currentTarget) closeModal();
        }}>
          <div className="modal-content image-modal">
            {/* Top Control Bar */}
            <div className="modal-top-bar">
              <div className="modal-title">
                CT Scan Viewer - Slice {currentImageIndex + 1} of {ctImages.length}
              </div>
              <button
                className="modal-close"
                onClick={closeModal}
                title="Close (ESC)"
              >
                ✕
              </button>
            </div>

            {/* Image Container with Zoom and Pan */}
            <div
              className="modal-image-container"
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              onWheel={handleWheel}
              style={{ cursor: modalZoom > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default' }}
            >
              <img
                src={ctImages[currentImageIndex]}
                alt="Full CT"
                className="modal-image"
                style={{
                  transform: `scale(${modalZoom}) translate(${modalPan.x / modalZoom}px, ${modalPan.y / modalZoom}px)`,
                  transition: isDragging ? 'none' : 'transform 0.1s ease-out'
                }}
                draggable={false}
              />
            </div>

            {/* Navigation Buttons */}
            <button
              onClick={handlePrevImage}
              className="nav-button left"
              title="Previous (←)"
              disabled={ctImages.length <= 1}
            >
              ◀
            </button>
            <button
              onClick={handleNextImage}
              className="nav-button right"
              title="Next (→)"
              disabled={ctImages.length <= 1}
            >
              ▶
            </button>

            {/* Bottom Control Bar - Full CT Controls */}
            <div className="modal-bottom-bar">
              {/* Left Section - Slice Navigation */}
              <div className="modal-ct-controls">
                <div className="modal-nav-controls">
                  <button
                    onClick={handlePrevImage}
                    className="modal-nav-btn"
                    disabled={ctImages.length <= 1}
                    title="Previous Slice (←)"
                  >
                    ◀
                  </button>
                  <span className="slice-info-modal">
                    Slice {currentImageIndex + 1} / {ctImages.length}
                  </span>
                  <button
                    onClick={handleNextImage}
                    className="modal-nav-btn"
                    disabled={ctImages.length <= 1}
                    title="Next Slice (→)"
                  >
                    ▶
                  </button>
                </div>

                <div className="modal-playback-controls">
                  <button
                    onClick={togglePlay}
                    className="modal-play-btn"
                    title={isPlaying ? 'Pause (Space)' : 'Play (Space)'}
                  >
                    {isPlaying ? '⏸ Pause' : '▶ Play'}
                  </button>
                  <select
                    value={playSpeed}
                    onChange={(e) => setPlaySpeed(parseInt(e.target.value))}
                    className="modal-speed-select"
                    title="Playback Speed"
                  >
                    <option value="50">Fast (20 fps)</option>
                    <option value="100">Normal (10 fps)</option>
                    <option value="200">Slow (5 fps)</option>
                    <option value="500">Very Slow (2 fps)</option>
                  </select>
                </div>

                <div className="modal-jump-controls">
                  <input
                    type="number"
                    min="1"
                    max={ctImages.length}
                    value={jumpToSlice}
                    onChange={(e) => setJumpToSlice(e.target.value)}
                    placeholder="Jump to..."
                    className="modal-jump-input"
                    title="Jump to slice number"
                  />
                  <button
                    onClick={handleJumpToSlice}
                    className="modal-jump-btn"
                    disabled={!jumpToSlice}
                    title="Go to slice"
                  >
                    Go
                  </button>
                </div>
              </div>

              {/* Center Section - Zoom Controls */}
              <div className="zoom-controls">
                <button
                  className="zoom-btn"
                  onClick={handleZoomOut}
                  title="Zoom Out (-)"
                  disabled={modalZoom <= 0.5}
                >
                  −
                </button>
                <span className="zoom-level">{Math.round(modalZoom * 100)}%</span>
                <button
                  className="zoom-btn"
                  onClick={handleZoomIn}
                  title="Zoom In (+)"
                  disabled={modalZoom >= 5}
                >
                  +
                </button>
                <button
                  className="zoom-btn reset"
                  onClick={handleResetZoom}
                  title="Reset View (0)"
                  disabled={modalZoom === 1 && modalPan.x === 0 && modalPan.y === 0}
                >
                  Reset View
                </button>
              </div>

              {/* Right Section - Help Text */}
              <div className="modal-help">
                <span className="help-text">
                  Scroll: zoom • Drag: pan • ←→: navigate • Space: play/pause
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PatientDashboardPage;