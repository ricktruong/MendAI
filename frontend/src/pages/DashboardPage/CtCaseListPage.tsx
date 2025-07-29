import React from 'react';
import { useNavigate } from 'react-router-dom';
import './DashboardPage.css'; // 可复用样式

const allCtCases = [
  { id: 'ct-001', patientName: 'John Doe', fileName: 'CT_Head_001.dcm', uploadedAt: '2025-07-27' },
  { id: 'ct-002', patientName: 'Jane Smith', fileName: 'CT_Chest_045.dcm', uploadedAt: '2025-07-25' },
  { id: 'ct-003', patientName: 'Maria Garcia', fileName: 'CT_Abdomen_102.dcm', uploadedAt: '2025-07-22' },
  { id: 'ct-004', patientName: 'Robert Johnson', fileName: 'CT_Lung_089.dcm', uploadedAt: '2025-07-20' },
  // 更多数据……
];

const CtCaseListPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>All CT Cases</h1>
          <p className="header-subtitle">Browse all uploaded CT files</p>
        </div>
        <div className="header-actions">
          <button className="nav-button logout" onClick={() => navigate('/')}>
            ← Back to Dashboard
          </button>
        </div>
      </header>

      <div className="dashboard-content">
        <div className="dashboard-card">
          <div className="ct-case-list">
            {allCtCases.map((ct) => (
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

export default CtCaseListPage;
