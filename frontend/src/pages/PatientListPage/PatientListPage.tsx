import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './PatientListPage.css';
import { apiService } from '../../services/api';
import type { DashboardData } from '../../services/api';

interface CtCase {
  id: string;
  patientName: string;
  fileName: string;
  uploadedAt: string;
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
  const [newPatient, setNewPatient] = useState({
    patientName: '',
    fileName: '',
    uploadedAt: new Date().toISOString().split('T')[0]
  });
  const [editPatient, setEditPatient] = useState({
    id: '',
    patientName: '',
    fileName: '',
    uploadedAt: ''
  });
  const [deletePatientId, setDeletePatientId] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [deleteFile, setDeleteFile] = useState(false);

  // Check authentication and load dashboard data
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    loadDashboardData();
  }, [navigate]);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      const data: DashboardData = await apiService.getDashboardData();
      
      // Map the backend data to frontend format
      const cases: CtCase[] = data.recent_cases.map(caseData => ({
        id: caseData.id,
        patientName: caseData.patient_name,
        fileName: caseData.file_name,
        uploadedAt: caseData.uploaded_at,
      }));
      
      setCtCases(cases);
      setFilteredCases(cases);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
      
      // Fallback to mock data
      const fallbackCases = [
        { id: 'ct-001', patientName: 'John Doe', fileName: 'CT_Head_001.dcm', uploadedAt: '2025-01-27' },
        { id: 'ct-002', patientName: 'Jane Smith', fileName: 'CT_Chest_045.dcm', uploadedAt: '2025-01-25' },
        { id: 'ct-003', patientName: 'Maria Garcia', fileName: 'CT_Abdomen_102.dcm', uploadedAt: '2025-01-22' },
      ];
      setCtCases(fallbackCases);
      setFilteredCases(fallbackCases);
    } finally {
      setIsLoading(false);
    }
  };

  // Search functionality
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredCases(ctCases);
    } else {
      const filtered = ctCases.filter(case_ =>
        case_.patientName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        case_.fileName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        case_.id.toLowerCase().includes(searchQuery.toLowerCase())
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
    setNewPatient({
      patientName: '',
      fileName: '',
      uploadedAt: new Date().toISOString().split('T')[0]
    });
    setEditPatient({
      id: '',
      patientName: '',
      fileName: '',
      uploadedAt: ''
    });
    setDeletePatientId('');
    setSelectedFile(null);
    setDeleteFile(false);
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
      setNewPatient(prev => ({
        ...prev,
        fileName: file.name
      }));
    }
  };

  const handleDeleteFile = () => {
    setDeleteFile(true);
    setSelectedFile(null);
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
        // Map backend response to frontend format
        const newCase: CtCase = {
          id: response.case.id,
          patientName: response.case.patient_name,
          fileName: response.case.file_name,
          uploadedAt: response.case.uploaded_at
        };

        // Add to cases list
        const updatedCases = [...ctCases, newCase];
        setCtCases(updatedCases);
        setFilteredCases(updatedCases);

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
  const handleEditPatient = (patient: CtCase) => {
    setEditPatient({
      id: patient.id,
      patientName: patient.patientName,
      fileName: patient.fileName,
      uploadedAt: patient.uploadedAt
    });
    setDeleteFile(false);
    setSelectedFile(null);
    setShowEditPatientModal(true);
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
      } else if (selectedFile) {
        formData.append('file', selectedFile);
      }

      // Call backend API
      const response = await apiService.updatePatient(editPatient.id, formData);
      
      if (response.success && response.case) {
        // Update the case in the list
        const updatedCases = ctCases.map(c => 
          c.id === editPatient.id 
            ? {
                id: response.case.id,
                patientName: response.case.patient_name,
                fileName: deleteFile ? '' : response.case.file_name, // Clear filename if deleted
                uploadedAt: response.case.uploaded_at
              }
            : c
        );
        
        setCtCases(updatedCases);
        setFilteredCases(updatedCases);

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
        // Remove the case from the list
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

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
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
                placeholder="Search patients, case IDs, or file names..."
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

      <div className="dashboard-content">
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
                    <th>Case ID</th>
                    <th>Patient Name</th>
                    <th>Study Type</th>
                    <th>File Name</th>
                    <th>Upload Date</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCases.map((ct) => (
                    <tr key={ct.id} className="patient-row">
                      <td>
                        <div className="case-id-cell">#{ct.id}</div>
                      </td>
                      <td>
                        <div className="patient-name-cell">{ct.patientName}</div>
                      </td>
                      <td>
                        <div className="study-type-cell">CT Scan</div>
                      </td>
                      <td>
                        <div className="file-name-cell" title={ct.fileName}>
                          {ct.fileName ? ct.fileName : (
                            <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>
                              No file attached
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
                <label htmlFor="uploadedAt">Date *</label>
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
                    accept=".dcm,.jpg,.jpeg,.png,.pdf"
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
                    Supported formats: DICOM (.dcm), Images, PDF
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
                <label htmlFor="editUploadedAt">Date *</label>
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
                  {/* Show existing file */}
                  {editPatient.fileName && !deleteFile && (
                    <div className="existing-file" style={{ 
                      padding: '10px', 
                      backgroundColor: '#f3f4f6', 
                      borderRadius: '4px', 
                      marginBottom: '10px',
                      border: '1px solid #d1d5db'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <strong> {editPatient.fileName}</strong>
                          <p style={{ margin: '4px 0 0 0', fontSize: '0.875rem', color: '#6b7280' }}>
                            Currently attached file
                          </p>
                        </div>
                        <button 
                          type="button"
                          className="file-delete-button"
                          onClick={handleDeleteFile}
                          style={{ 
                            backgroundColor: '#dc2626', 
                            color: 'white', 
                            padding: '6px 12px',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '0.875rem'
                          }}
                        >
                           Delete
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Show file marked for deletion */}
                  {editPatient.fileName && deleteFile && (
                    <div className="deleted-file" style={{ 
                      padding: '10px', 
                      backgroundColor: '#fef2f2', 
                      borderRadius: '4px', 
                      marginBottom: '10px',
                      border: '1px solid #fecaca'
                    }}>
                      <div style={{ color: '#dc2626' }}>
                        <strong> {editPatient.fileName}</strong>
                        <p style={{ margin: '4px 0 0 0', fontSize: '0.875rem' }}>
                          This file will be deleted when you save changes
                        </p>
                      </div>
                      <button 
                        type="button"
                        onClick={() => setDeleteFile(false)}
                        style={{ 
                          backgroundColor: '#6b7280', 
                          color: 'white', 
                          padding: '4px 8px',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '0.75rem',
                          marginTop: '6px'
                        }}
                      >
                        Cancel Delete
                      </button>
                    </div>
                  )}

                  {/* Show no file message */}
                  {!editPatient.fileName && (
                    <div className="no-file" style={{ 
                      padding: '10px', 
                      backgroundColor: '#fefce8', 
                      borderRadius: '4px', 
                      marginBottom: '10px',
                      border: '1px solid #fde047'
                    }}>
                      <p style={{ margin: 0, color: '#a16207', fontSize: '0.875rem' }}>
                        📝 No file currently attached to this patient
                      </p>
                    </div>
                  )}

                  {/* Upload new file section */}
                  <div className="upload-section" style={{ marginTop: '15px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.875rem', fontWeight: 'bold' }}>
                      Upload New File (Optional)
                    </label>
                    <input
                      type="file"
                      id="editFile"
                      onChange={handleFileSelect}
                      accept=".dcm,.jpg,.jpeg,.png,.pdf"
                      style={{ display: 'none' }}
                    />
                    <button 
                      type="button"
                      className="file-select-button"
                      onClick={() => document.getElementById('editFile')?.click()}
                      disabled={deleteFile}
                      style={{ 
                        backgroundColor: '#3b82f6', 
                        color: 'white', 
                        padding: '8px 16px',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer'
                      }}
                    >
                      {selectedFile ? `📎 ${selectedFile.name}` : ' Choose New File'}
                    </button>
                    <p className="file-hint" style={{ margin: '8px 0 0 0', fontSize: '0.75rem', color: '#6b7280' }}>
                      Supported formats: DICOM (.dcm), Images, PDF
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
    </div>
  );
};

export default PatientListPage;
