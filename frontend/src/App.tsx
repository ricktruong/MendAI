import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage/LoginPage';
import PatientDashboardPage from './pages/PatientDashboardPage/PatientDashboardPage';
import PatientListPage from './pages/PatientListPage/PatientListPage';
import SignUpPage from './pages/LoginPage/SignUpPage';
import './App.css';

function App() {
  // In a real app, you would check authentication status here
  const isAuthenticated = true; // Mock authentication status

  return (
    <Router>
      <div className="app">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignUpPage />} />
          <Route 
            path="/patients" 
            element={isAuthenticated ? <PatientListPage /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/dashboard" 
            element={isAuthenticated ? <PatientDashboardPage /> : <Navigate to="/login" />} 
          />
          <Route path="/" element={<Navigate to="/login" />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
