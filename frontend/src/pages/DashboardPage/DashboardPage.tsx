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
  const [ctCases] = useState<CtCase[]>(initialCases);

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Clinical Dashboard</h1>
          <p className="header-subtitle">Real-time multimodal analysis overview</p>
        </div>
        <div className="header-actions">
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
                  onClick={() => navigate('/chat', { state: { patient: ct } })}
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
