import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './DashboardPage.css';

interface CtCase {
  id: string;
  patientName: string;
  fileName: string;
  uploadedAt: string;
}

const initialCases: CtCase[] = [
  { id: 'ct-001', patientName: 'John Doe', fileName: 'CT_Head_001.dcm', uploadedAt: '2025-07-27' },
  { id: 'ct-002', patientName: 'Jane Smith', fileName: 'CT_Chest_045.dcm', uploadedAt: '2025-07-25' },
  { id: 'ct-003', patientName: 'Maria Garcia', fileName: 'CT_Abdomen_102.dcm', uploadedAt: '2025-07-22' },
];

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [ctCases, setCtCases] = useState<CtCase[]>(initialCases);

  const handleUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const newCase: CtCase = {
        id: `ct-${Date.now()}`,
        patientName: 'New Patient', 
        fileName: file.name,
        uploadedAt: new Date().toISOString().slice(0, 10)
      };
      setCtCases([newCase, ...ctCases]);
    }
  };

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Clinical Dashboard</h1>
          <p className="header-subtitle">Real-time multimodal analysis overview</p>
        </div>
        <div className="header-actions">
          <button 
            className="nav-button"
            onClick={() => navigate('/chat')}
          >
            <span>💬</span>
            AI Assistant
          </button>
          <button className="nav-button logout">
            <span>🚪</span>
            Logout
          </button>
        </div>
      </header>

      <div className="dashboard-content">
        <div className="dashboard-card">
          <div className="card-header">
            <h2>Saved CT Cases</h2>
            <label htmlFor="ct-upload" className="upload-button">+ Upload CT File</label>
            <button className="view-all-button" onClick={() => navigate('/ct-cases')}>
               View All →
            </button>
            <input
              id="ct-upload"
              type="file"
              accept=".dcm,.zip"
              onChange={handleUpload}
              style={{ display: 'none' }}
            />
          </div>
          <div className="ct-case-list">
            {ctCases.map((ct) => (
              <div key={ct.id} className="ct-case-item">
                <div className="ct-case-info">
                  <h4>{ct.patientName}</h4>
                  <p>{ct.fileName} — {ct.uploadedAt}</p>
                </div>
                <button 
                  className="view-all-button"
                  onClick={() => navigate(`/ct-viewer/${ct.id}`)}
                >
                  View
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
