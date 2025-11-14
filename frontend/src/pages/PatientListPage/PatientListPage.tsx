import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './PatientListPage.css';
import { apiService } from '../../services/api';
import type { PatientListData, PatientFile } from '../../services/api';

interface CtCase {
  id: string;
  patientName: string;
  fileName: string;
  uploadedAt: string;
  files?: PatientFile[];
  // Additional fields from normalized patient format
  fhirId?: string;
  birthDate?: string;
  gender?: string;
  race?: string;
  ethnicity?: string;
  maritalStatus?: string;
  managingOrganization?: string;
  language?: string | null;
  deceasedDateTime?: string | null;
}

const PatientListPage: React.FC = () => {
  const navigate = useNavigate();
  const [ctCases, setCtCases] = useState<CtCase[]>([]);
  const [filteredCases, setFilteredCases] = useState<CtCase[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddPatientModal, setShowAddPatientModal] = useState(false);
  const [showEditPatientModal, setShowEditPatientModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showFilesModal, setShowFilesModal] = useState(false);
  const [newPatient, setNewPatient] = useState({
    patientName: '',
    fileName: '',
    uploadedAt: new Date().toISOString().split('T')[0],
    birthDate: '',
    gender: '',
    race: '',
    ethnicity: '',
    maritalStatus: '',
    managingOrganization: '',
    language: ''
  });
  const [editPatient, setEditPatient] = useState({
    id: '',
    patientName: '',
    fileName: '',
    uploadedAt: '',
    birthDate: '',
    gender: '',
    race: '',
    ethnicity: '',
    maritalStatus: '',
    managingOrganization: '',
    language: ''
  });
  const [deletePatientId, setDeletePatientId] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [deleteFile, setDeleteFile] = useState(false);
  const [currentPatientFiles, setCurrentPatientFiles] = useState<PatientFile[]>([]);
  const [viewingPatient, setViewingPatient] = useState<CtCase | null>(null);

  // Check authentication and load dashboard data
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    loadPatientListData();
  }, [navigate]);

  const loadPatientListData = async () => {
    try {
      setIsLoading(true);
      // Load first 20 patients
      const data: PatientListData = await apiService.getPatientListData();

      // Map the backend data to frontend format
      const cases: CtCase[] = data.recent_cases.map(caseData => ({
        id: caseData.id,
        patientName: caseData.patient_name,
        fileName: caseData.file_name,
        uploadedAt: caseData.uploaded_at,
        files: caseData.files || [],
        fhirId: caseData.fhirId,
        birthDate: caseData.birthDate,
        gender: caseData.gender,
        race: caseData.race,
        ethnicity: caseData.ethnicity,
        maritalStatus: caseData.maritalStatus,
        managingOrganization: caseData.managingOrganization,
        language: caseData.language,
      }));

      setCtCases(cases);
      setFilteredCases(cases);
    } catch (err) {
      console.error('Error loading patient list data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load patient list data');

      // No fallback data - show error to user
      setCtCases([]);
      setFilteredCases([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Search functionality
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredCases(ctCases);
    } else {
      const query = searchQuery.toLowerCase();
      const filtered = ctCases.filter(case_ =>
        case_.patientName.toLowerCase().includes(query) ||
        case_.fileName.toLowerCase().includes(query) ||
        case_.id.toLowerCase().includes(query) ||
        case_.fhirId?.toLowerCase().includes(query) ||
        case_.gender?.toLowerCase().includes(query) ||
        case_.race?.toLowerCase().includes(query) ||
        case_.ethnicity?.toLowerCase().includes(query) ||
        case_.managingOrganization?.toLowerCase().includes(query)
      );
      setFilteredCases(filtered);
    }
  }, [searchQuery, ctCases]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const clearSearch = () => {
    setSearchQuery('');
  };

  // Add patient functionality
  const handleAddPatient = () => {
    setShowAddPatientModal(true);
  };

  const handleCloseModal = () => {
    setShowAddPatientModal(false);
    setShowEditPatientModal(false);
    setShowDeleteConfirm(false);
    setShowFilesModal(false);
    setNewPatient({
      patientName: '',
      fileName: '',
      uploadedAt: new Date().toISOString().split('T')[0],
      birthDate: '',
      gender: '',
      race: '',
      ethnicity: '',
      maritalStatus: '',
      managingOrganization: '',
      language: ''
    });
    setEditPatient({
      id: '',
      patientName: '',
      fileName: '',
      uploadedAt: '',
      birthDate: '',
      gender: '',
      race: '',
      ethnicity: '',
      maritalStatus: '',
      managingOrganization: '',
      language: ''
    });
    setDeletePatientId('');
    setSelectedFile(null);
    setSelectedFiles([]);
    setDeleteFile(false);
    setCurrentPatientFiles([]);
    setViewingPatient(null);
  };

  const handlePatientInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setNewPatient(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setDeleteFile(false); // Reset delete file flag when new file is selected
      // Add file to selectedFiles array without replacing existing ones
      setSelectedFiles(prev => [...prev, file]);
      setNewPatient(prev => ({
        ...prev,
        fileName: file.name
      }));
    }
    // Reset the input value to allow selecting the same file again
    e.target.value = '';
  };


  const handleSubmitPatient = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newPatient.patientName.trim()) {
      alert('Please enter a patient name');
      return;
    }
    
    if (!selectedFile) {
      alert('Please select a file');
      return;
    }

    try {
      setIsLoading(true);
      
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('patient_name', newPatient.patientName);
      formData.append('uploaded_at', newPatient.uploadedAt);
      formData.append('file', selectedFile);

      // Call backend API
      const response = await apiService.createPatient(formData);

      if (response.success && response.case) {
        // Reload patient list to get updated data
        await loadPatientListData();

        // Close modal and reset form
        handleCloseModal();

        alert('Patient added successfully!');
      } else {
        throw new Error(response.message || 'Failed to add patient');
      }
    } catch (error) {
      console.error('Error adding patient:', error);
      alert(`Failed to add patient: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Edit patient functionality
  const handleEditPatient = async (patient: CtCase) => {
    try {
      setIsLoading(true);
      setEditPatient({
        id: patient.id,
        patientName: patient.patientName,
        fileName: patient.fileName,
        uploadedAt: patient.uploadedAt,
        birthDate: patient.birthDate || '',
        gender: patient.gender || '',
        race: patient.race || '',
        ethnicity: patient.ethnicity || '',
        maritalStatus: patient.maritalStatus || '',
        managingOrganization: patient.managingOrganization || '',
        language: patient.language || ''
      });
      setDeleteFile(false);
      setSelectedFile(null);
      setSelectedFiles([]);
      setViewingPatient(patient);

      // Load current files for the patient
      try {
        const response = await apiService.getPatientFiles(patient.id);
        if (response.success) {
          setCurrentPatientFiles(response.files);
        } else {
          // Fallback to files from patient data
          setCurrentPatientFiles(patient.files || []);
        }
      } catch (error) {
        console.error('Error loading patient files:', error);
        // Fallback to files from patient data
        setCurrentPatientFiles(patient.files || []);
      }

      setShowEditPatientModal(true);
    } catch (error) {
      console.error('Error opening edit modal:', error);
      alert(`Failed to open edit modal: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setEditPatient(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleUpdatePatient = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!editPatient.patientName.trim()) {
      alert('Please enter a patient name');
      return;
    }

    try {
      setIsLoading(true);

      // Create FormData for file upload
      const formData = new FormData();
      formData.append('patient_name', editPatient.patientName);
      formData.append('uploaded_at', editPatient.uploadedAt);

      if (deleteFile) {
        // Indicate to backend that file should be deleted
        formData.append('delete_file', 'true');
      } else if (selectedFiles.length > 0) {
        // Append all selected files
        selectedFiles.forEach((file) => {
          formData.append('file', file);
        });
      }

      // Call backend API
      const response = await apiService.updatePatient(editPatient.id, formData);

      if (response.success && response.case) {
        // Update the specific case in the list
        const updatedCases = ctCases.map(c =>
          c.id === editPatient.id
            ? {
                ...c,  // Keep all existing fields
                id: response.case.id,
                patientName: response.case.patient_name,
                fileName: response.case.file_name,
                uploadedAt: response.case.uploaded_at,
                files: response.case.files || [],
                // Update FHIR fields if provided
                fhirId: response.case.fhirId ?? c.fhirId,
                birthDate: response.case.birthDate ?? c.birthDate,
                gender: response.case.gender ?? c.gender,
                race: response.case.race ?? c.race,
                ethnicity: response.case.ethnicity ?? c.ethnicity,
                maritalStatus: response.case.maritalStatus ?? c.maritalStatus,
                managingOrganization: response.case.managingOrganization ?? c.managingOrganization,
                language: response.case.language ?? c.language
              }
            : c
        );

        setCtCases(updatedCases);
        setFilteredCases(updatedCases);

        // Update current patient files display
        setCurrentPatientFiles(response.case.files || []);

        // Close modal and reset form
        handleCloseModal();

        alert('Patient updated successfully!');
      } else {
        throw new Error(response.message || 'Failed to update patient');
      }
    } catch (error) {
      console.error('Error updating patient:', error);
      alert(`Failed to update patient: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Delete patient functionality
  const handleDeletePatient = (patientId: string) => {
    setDeletePatientId(patientId);
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = async () => {
    if (!deletePatientId) return;

    try {
      setIsLoading(true);
      
      const response = await apiService.deletePatient(deletePatientId);

      if (response.success) {
        // Remove the case from the current list
        const updatedCases = ctCases.filter(c => c.id !== deletePatientId);
        setCtCases(updatedCases);
        setFilteredCases(updatedCases);

        // Close modal
        handleCloseModal();

        alert('Patient deleted successfully!');
      } else {
        throw new Error(response.message || 'Failed to delete patient');
      }
    } catch (error) {
      console.error('Error deleting patient:', error);
      alert(`Failed to delete patient: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  // View patient files functionality
  const handleViewFiles = async (patient: CtCase) => {
    try {
      setIsLoading(true);
      setViewingPatient(patient);

      // Get current files from API
      const response = await apiService.getPatientFiles(patient.id);

      if (response.success) {
        setCurrentPatientFiles(response.files);
      } else {
        // Fallback to files from patient data
        setCurrentPatientFiles(patient.files || []);
      }

      setShowFilesModal(true);
    } catch (error) {
      console.error('Error loading patient files:', error);
      alert(`Failed to load patient files: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Delete individual file functionality
  const handleDeleteIndividualFile = async (fileId: string) => {
    if (!viewingPatient) return;

    if (!confirm('Are you sure you want to delete this file?')) {
      return;
    }

    try {
      setIsLoading(true);

      const response = await apiService.deletePatientFile(viewingPatient.id, fileId);

      if (response.success) {
        // Remove file from current list
        const updatedFiles = currentPatientFiles.filter(f => f.id !== fileId);
        setCurrentPatientFiles(updatedFiles);

        // Update the main patient list
        const updatedCases = ctCases.map(c =>
          c.id === viewingPatient.id
            ? {
                ...c,
                files: updatedFiles,
                fileName: updatedFiles.length > 0 ? updatedFiles[0].file_name : '',
                uploadedAt: updatedFiles.length > 0 ? updatedFiles[0].uploaded_at : c.uploadedAt
              }
            : c
        );

        setCtCases(updatedCases);
        setFilteredCases(updatedCases);

        alert('File deleted successfully!');
      } else {
        throw new Error(response.message || 'Failed to delete file');
      }
    } catch (error) {
      console.error('Error deleting file:', error);
      alert(`Failed to delete file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <div className="patient-list-page">
      <header className="patient-list-header">
        <div className="header-content">
          <h1>Patient List</h1>
          <p className="header-subtitle">Manage and view all patient cases</p>
        </div>
        
        <div className="header-search">
          <div className="search-container">
            <div className="search-input-wrapper">
              <input
                type="text"
                className="search-input"
                placeholder="Search by name, ID, gender, race, ethnicity, organization..."
                value={searchQuery}
                onChange={handleSearchChange}
              />
              <div className="search-icon">
                🔍
              </div>
              {searchQuery && (
                <button 
                  className="search-clear"
                  onClick={clearSearch}
                  aria-label="Clear search"
                >
                  ×
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="header-actions">
          <button className="logout-button" onClick={handleLogout}>
            Sign Out
          </button>
        </div>
      </header>

      <div className="patient-list-content">
        {error && (
          <div className="error-message" style={{ 
            background: '#fef2f2', 
            border: '1px solid #fecaca', 
            color: '#dc2626', 
            padding: '1rem', 
            borderRadius: '0.5rem', 
            marginBottom: '1rem' 
          }}>
            {error}
          </div>
        )}
        
        <div className="cases-section">
          <div className="section-header">
            <h2>
              {searchQuery 
                ? `Search Results (${filteredCases.length})`
                : `Patient Cases (${filteredCases.length})`
              }
            </h2>
            <div className="section-header-actions">
              {isLoading && <span className="loading-indicator">Loading...</span>}
              {searchQuery && !isLoading && (
                <span className="search-info">
                  Searching for: "{searchQuery}"
                </span>
              )}
              <button 
                className="add-patient-button"
                onClick={handleAddPatient}
                disabled={isLoading}
              >
                + Add Patient
              </button>
            </div>
          </div>
          
          {filteredCases.length === 0 && !isLoading ? (
            <div className="empty-state">
              <div className="empty-icon">
                {searchQuery ? '🔍' : '📋'}
              </div>
              <h3>
                {searchQuery ? 'No Results Found' : 'No Recent Cases'}
              </h3>
              <p>
                {searchQuery 
                  ? `No cases match "${searchQuery}". Try a different search term.`
                  : 'No patient cases available at the moment.'
                }
              </p>
              {searchQuery && (
                <button 
                  className="clear-search-button"
                  onClick={clearSearch}
                >
                  Clear Search
                </button>
              )}
            </div>
          ) : (
            <div className="patients-table-container">
              <table className="patients-table">
                <thead>
                  <tr>
                    <th>Patient ID</th>
                    <th>Patient Name</th>
                    <th>Birth Date</th>
                    <th>Gender</th>
                    <th>Race</th>
                    <th>Ethnicity</th>
                    <th>Organization</th>
                    <th>File Name</th>
                    <th>Upload Date</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCases.map((ct) => (
                    <tr key={ct.id} className="patient-row">
                      <td>
                        <div className="case-id-cell">
                          <div style={{ fontWeight: '600' }}>#{ct.id}</div>
                          {ct.fhirId && (
                            <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '2px' }} title="FHIR ID">
                              {ct.fhirId.substring(0, 8)}...
                            </div>
                          )}
                        </div>
                      </td>
                      <td>
                        <div className="patient-name-cell">{ct.patientName}</div>
                      </td>
                      <td>
                        <div className="date-cell">
                          {ct.birthDate
                            ? new Date(ct.birthDate).toLocaleDateString('en-US', {
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric'
                              })
                            : <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>N/A</span>
                          }
                        </div>
                      </td>
                      <td>
                        <div style={{ textTransform: 'capitalize' }}>
                          {ct.gender || <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>N/A</span>}
                        </div>
                      </td>
                      <td>
                        <div>{ct.race || <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>N/A</span>}</div>
                      </td>
                      <td>
                        <div>{ct.ethnicity || <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>N/A</span>}</div>
                      </td>
                      <td>
                        <div title={ct.managingOrganization}>
                          {ct.managingOrganization
                            ? (ct.managingOrganization.length > 25
                                ? ct.managingOrganization.substring(0, 25) + '...'
                                : ct.managingOrganization)
                            : <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>N/A</span>
                          }
                        </div>
                      </td>
                      <td>
                        <div className="file-name-cell">
                          {ct.files && ct.files.length > 0 ? (
                            <div>
                              <div title={ct.fileName}>
                                {ct.fileName}
                                {ct.files.length > 1 && (
                                  <span style={{
                                    color: '#3b82f6',
                                    fontSize: '0.875rem',
                                    marginLeft: '8px',
                                    fontWeight: 'bold'
                                  }}>
                                    +{ct.files.length - 1} more
                                  </span>
                                )}
                              </div>
                              <button
                                className="view-files-button"
                                onClick={() => handleViewFiles(ct)}
                                disabled={isLoading}
                                style={{
                                  fontSize: '0.75rem',
                                  padding: '2px 6px',
                                  marginTop: '4px',
                                  backgroundColor: '#e5e7eb',
                                  border: '1px solid #d1d5db',
                                  borderRadius: '3px',
                                  cursor: 'pointer'
                                }}
                              >
                                View All Files ({ct.files.length})
                              </button>
                            </div>
                          ) : (
                            <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>
                              No files attached
                            </span>
                          )}
                        </div>
                      </td>
                      <td>
                        <div className="date-cell">
                          {new Date(ct.uploadedAt).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric'
                          })}
                        </div>
                      </td>
                      <td>
                        <div className="actions-cell">
                          <button
                            className="table-edit-button"
                            onClick={() => handleEditPatient(ct)}
                            disabled={isLoading}
                            title="Edit patient"
                          >
                            Edit
                          </button>
                          <button
                            className="table-delete-button"
                            onClick={() => handleDeletePatient(ct.id)}
                            disabled={isLoading}
                            title="Delete patient"
                          >
                            Delete
                          </button>
                          <button
                            className="table-analyze-button"
                            onClick={() => navigate('/dashboard', { state: { patient: ct } })}
                            disabled={isLoading}
                          >
                            Analyze
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Add Patient Modal */}
      {showAddPatientModal && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add New Patient</h3>
              <button 
                className="modal-close-button"
                onClick={handleCloseModal}
                aria-label="Close modal"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSubmitPatient} className="add-patient-form">
              <div className="form-group">
                <label htmlFor="patientName">Patient Name *</label>
                <input
                  type="text"
                  id="patientName"
                  name="patientName"
                  value={newPatient.patientName}
                  onChange={handlePatientInputChange}
                  placeholder="Enter patient full name"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="birthDate">Birth Date</label>
                <input
                  type="date"
                  id="birthDate"
                  name="birthDate"
                  value={newPatient.birthDate}
                  onChange={handlePatientInputChange}
                />
              </div>

              <div className="form-group">
                <label htmlFor="gender">Gender</label>
                <select
                  id="gender"
                  name="gender"
                  value={newPatient.gender}
                  onChange={(e) => setNewPatient(prev => ({ ...prev, gender: e.target.value }))}
                  style={{
                    padding: '0.75rem 1rem',
                    background: '#f8fafc',
                    border: '2px solid #e2e8f0',
                    borderRadius: '8px',
                    color: '#1e293b',
                    fontSize: '1rem',
                    fontFamily: 'inherit'
                  }}
                >
                  <option value="">Select gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                  <option value="unknown">Unknown</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="race">Race</label>
                <input
                  type="text"
                  id="race"
                  name="race"
                  value={newPatient.race}
                  onChange={handlePatientInputChange}
                  placeholder="e.g., White, Asian, Black or African American"
                />
              </div>

              <div className="form-group">
                <label htmlFor="ethnicity">Ethnicity</label>
                <input
                  type="text"
                  id="ethnicity"
                  name="ethnicity"
                  value={newPatient.ethnicity}
                  onChange={handlePatientInputChange}
                  placeholder="e.g., Hispanic or Latino, Not Hispanic or Latino"
                />
              </div>

              <div className="form-group">
                <label htmlFor="maritalStatus">Marital Status</label>
                <select
                  id="maritalStatus"
                  name="maritalStatus"
                  value={newPatient.maritalStatus}
                  onChange={(e) => setNewPatient(prev => ({ ...prev, maritalStatus: e.target.value }))}
                  style={{
                    padding: '0.75rem 1rem',
                    background: '#f8fafc',
                    border: '2px solid #e2e8f0',
                    borderRadius: '8px',
                    color: '#1e293b',
                    fontSize: '1rem',
                    fontFamily: 'inherit'
                  }}
                >
                  <option value="">Select marital status</option>
                  <option value="S">Single</option>
                  <option value="M">Married</option>
                  <option value="D">Divorced</option>
                  <option value="W">Widowed</option>
                  <option value="UNK">Unknown</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="managingOrganization">Managing Organization</label>
                <input
                  type="text"
                  id="managingOrganization"
                  name="managingOrganization"
                  value={newPatient.managingOrganization}
                  onChange={handlePatientInputChange}
                  placeholder="e.g., General Hospital"
                />
              </div>

              <div className="form-group">
                <label htmlFor="language">Language</label>
                <input
                  type="text"
                  id="language"
                  name="language"
                  value={newPatient.language}
                  onChange={handlePatientInputChange}
                  placeholder="e.g., en, es, fr"
                />
              </div>

              <div className="form-group">
                <label htmlFor="uploadedAt">Upload Date *</label>
                <input
                  type="date"
                  id="uploadedAt"
                  name="uploadedAt"
                  value={newPatient.uploadedAt}
                  onChange={handlePatientInputChange}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="file">CT Scan File *</label>
                <div className="file-input-wrapper">
                  <input
                    type="file"
                    id="file"
                    onChange={handleFileSelect}
                    accept=".nii,.nii.gz"
                    style={{ display: 'none' }}
                  />
                  <button
                    type="button"
                    className="file-select-button"
                    onClick={() => document.getElementById('file')?.click()}
                  >
                    {selectedFile ? selectedFile.name : 'Select File'}
                  </button>
                  <p className="file-hint">
                    Only NIfTI (.nii or .nii.gz) files are supported for CT analysis
                  </p>
                </div>
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="cancel-button"
                  onClick={handleCloseModal}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="submit-button"
                  disabled={!newPatient.patientName.trim() || !selectedFile}
                >
                  Add Patient
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Patient Modal */}
      {showEditPatientModal && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Edit Patient</h3>
              <button 
                className="modal-close-button"
                onClick={handleCloseModal}
                aria-label="Close modal"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleUpdatePatient} className="add-patient-form">
              <div className="form-group">
                <label htmlFor="editPatientName">Patient Name *</label>
                <input
                  type="text"
                  id="editPatientName"
                  name="patientName"
                  value={editPatient.patientName}
                  onChange={handleEditInputChange}
                  placeholder="Enter patient full name"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="editBirthDate">Birth Date</label>
                <input
                  type="date"
                  id="editBirthDate"
                  name="birthDate"
                  value={editPatient.birthDate}
                  onChange={handleEditInputChange}
                />
              </div>

              <div className="form-group">
                <label htmlFor="editGender">Gender</label>
                <select
                  id="editGender"
                  name="gender"
                  value={editPatient.gender}
                  onChange={(e) => setEditPatient(prev => ({ ...prev, gender: e.target.value }))}
                  style={{
                    padding: '0.75rem 1rem',
                    background: '#f8fafc',
                    border: '2px solid #e2e8f0',
                    borderRadius: '8px',
                    color: '#1e293b',
                    fontSize: '1rem',
                    fontFamily: 'inherit'
                  }}
                >
                  <option value="">Select gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                  <option value="unknown">Unknown</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="editRace">Race</label>
                <input
                  type="text"
                  id="editRace"
                  name="race"
                  value={editPatient.race}
                  onChange={handleEditInputChange}
                  placeholder="e.g., White, Asian, Black or African American"
                />
              </div>

              <div className="form-group">
                <label htmlFor="editEthnicity">Ethnicity</label>
                <input
                  type="text"
                  id="editEthnicity"
                  name="ethnicity"
                  value={editPatient.ethnicity}
                  onChange={handleEditInputChange}
                  placeholder="e.g., Hispanic or Latino, Not Hispanic or Latino"
                />
              </div>

              <div className="form-group">
                <label htmlFor="editMaritalStatus">Marital Status</label>
                <select
                  id="editMaritalStatus"
                  name="maritalStatus"
                  value={editPatient.maritalStatus}
                  onChange={(e) => setEditPatient(prev => ({ ...prev, maritalStatus: e.target.value }))}
                  style={{
                    padding: '0.75rem 1rem',
                    background: '#f8fafc',
                    border: '2px solid #e2e8f0',
                    borderRadius: '8px',
                    color: '#1e293b',
                    fontSize: '1rem',
                    fontFamily: 'inherit'
                  }}
                >
                  <option value="">Select marital status</option>
                  <option value="S">Single</option>
                  <option value="M">Married</option>
                  <option value="D">Divorced</option>
                  <option value="W">Widowed</option>
                  <option value="UNK">Unknown</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="editManagingOrganization">Managing Organization</label>
                <input
                  type="text"
                  id="editManagingOrganization"
                  name="managingOrganization"
                  value={editPatient.managingOrganization}
                  onChange={handleEditInputChange}
                  placeholder="e.g., General Hospital"
                />
              </div>

              <div className="form-group">
                <label htmlFor="editLanguage">Language</label>
                <input
                  type="text"
                  id="editLanguage"
                  name="language"
                  value={editPatient.language}
                  onChange={handleEditInputChange}
                  placeholder="e.g., en, es, fr"
                />
              </div>

              <div className="form-group">
                <label htmlFor="editUploadedAt">Upload Date *</label>
                <input
                  type="date"
                  id="editUploadedAt"
                  name="uploadedAt"
                  value={editPatient.uploadedAt}
                  onChange={handleEditInputChange}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="editFile">Patient Files</label>
                <div className="file-input-wrapper">
                  {/* Current Files Section */}
                  <div className="current-files-section" style={{ marginBottom: '20px' }}>
                    <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', fontWeight: 'bold', color: '#374151' }}>
                      Current Files ({currentPatientFiles.length})
                    </h4>

                    {currentPatientFiles.length === 0 ? (
                      <div className="no-files" style={{
                        padding: '15px',
                        backgroundColor: '#fefce8',
                        borderRadius: '4px',
                        border: '1px solid #fde047',
                        textAlign: 'center'
                      }}>
                        <p style={{ margin: 0, color: '#a16207', fontSize: '0.875rem' }}>
                          📁 No files currently attached to this patient
                        </p>
                      </div>
                    ) : (
                      <div style={{
                        maxHeight: '200px',
                        overflowY: 'auto',
                        border: '1px solid #d1d5db',
                        borderRadius: '4px'
                      }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                          <thead>
                            <tr style={{ backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
                              <th style={{ padding: '8px', textAlign: 'left', fontWeight: 'bold' }}>File Name</th>
                              <th style={{ padding: '8px', textAlign: 'left', fontWeight: 'bold' }}>Upload Date</th>
                              <th style={{ padding: '8px', textAlign: 'center', fontWeight: 'bold', width: '80px' }}>Action</th>
                            </tr>
                          </thead>
                          <tbody>
                            {currentPatientFiles.map((file, index) => (
                              <tr
                                key={file.id}
                                style={{
                                  borderBottom: index < currentPatientFiles.length - 1 ? '1px solid #e5e7eb' : 'none',
                                  backgroundColor: 'white'
                                }}
                              >
                                <td style={{ padding: '8px' }}>
                                  <div style={{ fontWeight: '500' }}>{file.file_name}</div>
                                  <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                                    {file.id}
                                  </div>
                                </td>
                                <td style={{ padding: '8px', color: '#6b7280' }}>
                                  {new Date(file.uploaded_at).toLocaleDateString('en-US', {
                                    month: 'short',
                                    day: 'numeric',
                                    year: 'numeric'
                                  })}
                                </td>
                                <td style={{ padding: '8px', textAlign: 'center' }}>
                                  <button
                                    type="button"
                                    onClick={() => handleDeleteIndividualFile(file.id)}
                                    disabled={isLoading}
                                    style={{
                                      backgroundColor: '#dc2626',
                                      color: 'white',
                                      border: 'none',
                                      padding: '4px 8px',
                                      borderRadius: '3px',
                                      cursor: 'pointer',
                                      fontSize: '0.75rem'
                                    }}
                                  >
                                    Delete
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>

                  {/* Upload new file section */}
                  <div className="upload-section" style={{ borderTop: '1px solid #e5e7eb', paddingTop: '15px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.875rem', fontWeight: 'bold' }}>
                      Add New File
                    </label>
                    <input
                      type="file"
                      id="editFile"
                      onChange={handleFileSelect}
                      accept=".nii,.nii.gz"
                      style={{ display: 'none' }}
                    />
                    <button
                      type="button"
                      className="file-select-button"
                      onClick={() => document.getElementById('editFile')?.click()}
                      style={{
                        backgroundColor: '#3b82f6',
                        color: 'white',
                        padding: '8px 16px',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        marginBottom: '10px'
                      }}
                    >
                      Choose File
                    </button>

                    {/* Display selected files to be uploaded */}
                    {selectedFiles.length > 0 && (
                      <div style={{
                        marginTop: '10px',
                        padding: '10px',
                        backgroundColor: '#f0f9ff',
                        border: '1px solid #bfdbfe',
                        borderRadius: '4px'
                      }}>
                        <h5 style={{ margin: '0 0 8px 0', fontSize: '0.8rem', fontWeight: 'bold', color: '#1e40af' }}>
                          Files to Upload ({selectedFiles.length})
                        </h5>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                          {selectedFiles.map((file, index) => (
                            <div key={index} style={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              padding: '4px 8px',
                              backgroundColor: 'white',
                              borderRadius: '3px',
                              fontSize: '0.8rem'
                            }}>
                              <span style={{ color: '#374151' }}>📎 {file.name}</span>
                              <button
                                type="button"
                                onClick={() => setSelectedFiles(prev => prev.filter((_, i) => i !== index))}
                                style={{
                                  backgroundColor: '#ef4444',
                                  color: 'white',
                                  border: 'none',
                                  padding: '2px 6px',
                                  borderRadius: '3px',
                                  cursor: 'pointer',
                                  fontSize: '0.7rem'
                                }}
                              >
                                Remove
                              </button>
                            </div>
                          ))}
                        </div>
                        <button
                          type="button"
                          onClick={() => setSelectedFiles([])}
                          style={{
                            marginTop: '8px',
                            backgroundColor: '#6b7280',
                            color: 'white',
                            border: 'none',
                            padding: '4px 10px',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '0.75rem'
                          }}
                        >
                          Clear All
                        </button>
                      </div>
                    )}
                    <p className="file-hint" style={{ margin: '8px 0 0 0', fontSize: '0.75rem', color: '#6b7280' }}>
                      Only NIfTI (.nii or .nii.gz) files are supported for CT analysis. Click "Choose File" multiple times to add multiple files.
                    </p>
                  </div>
                </div>
              </div>

              <div className="modal-actions">
                <button 
                  type="button" 
                  className="cancel-button"
                  onClick={handleCloseModal}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="submit-button"
                  disabled={!editPatient.patientName.trim()}
                >
                  Update Patient
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content delete-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Delete Patient</h3>
              <button 
                className="modal-close-button"
                onClick={handleCloseModal}
                aria-label="Close modal"
              >
                ×
              </button>
            </div>

            <div className="delete-confirmation">
              <div className="warning-icon">⚠️</div>
              <p>Are you sure you want to delete this patient?</p>
              <p className="warning-text">
                This action cannot be undone. All patient data and files will be permanently removed.
              </p>

              <div className="modal-actions">
                <button 
                  type="button" 
                  className="cancel-button"
                  onClick={handleCloseModal}
                >
                  Cancel
                </button>
                <button 
                  type="button" 
                  className="delete-confirm-button"
                  onClick={handleConfirmDelete}
                  disabled={isLoading}
                >
                  Delete Patient
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Files View Modal */}
      {showFilesModal && viewingPatient && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content files-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Files for {viewingPatient.patientName}</h3>
              <button
                className="modal-close-button"
                onClick={handleCloseModal}
                aria-label="Close modal"
              >
                ×
              </button>
            </div>

            <div className="files-list">
              {currentPatientFiles.length === 0 ? (
                <div className="empty-state" style={{ textAlign: 'center', padding: '2rem' }}>
                  <div className="empty-icon" style={{ fontSize: '3rem', marginBottom: '1rem' }}>📁</div>
                  <h3>No Files</h3>
                  <p>This patient doesn't have any files uploaded yet.</p>
                </div>
              ) : (
                <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                        <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>File Name</th>
                        <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Upload Date</th>
                        <th style={{ padding: '12px', textAlign: 'center', fontWeight: 'bold' }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {currentPatientFiles.map((file, index) => (
                        <tr
                          key={file.id}
                          style={{
                            borderBottom: '1px solid #e5e7eb',
                            backgroundColor: index % 2 === 0 ? '#f9fafb' : 'white'
                          }}
                        >
                          <td style={{ padding: '12px' }}>
                            <div style={{ fontWeight: '500' }}>{file.file_name}</div>
                            <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                              ID: {file.id}
                            </div>
                          </td>
                          <td style={{ padding: '12px', color: '#6b7280' }}>
                            {new Date(file.uploaded_at).toLocaleDateString('en-US', {
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </td>
                          <td style={{ padding: '12px', textAlign: 'center' }}>
                            <button
                              onClick={() => handleDeleteIndividualFile(file.id)}
                              disabled={isLoading}
                              style={{
                                backgroundColor: '#dc2626',
                                color: 'white',
                                border: 'none',
                                padding: '6px 12px',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '0.875rem'
                              }}
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="modal-actions" style={{ marginTop: '1rem', borderTop: '1px solid #e5e7eb', paddingTop: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                  Total files: {currentPatientFiles.length}
                </div>
                <div>
                  <button
                    type="button"
                    className="cancel-button"
                    onClick={handleCloseModal}
                    style={{
                      marginRight: '12px',
                      backgroundColor: '#6b7280',
                      color: 'white',
                      border: 'none',
                      padding: '8px 16px',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Close
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      handleCloseModal();
                      handleEditPatient(viewingPatient);
                    }}
                    style={{
                      backgroundColor: '#3b82f6',
                      color: 'white',
                      border: 'none',
                      padding: '8px 16px',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Add More Files
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PatientListPage;
