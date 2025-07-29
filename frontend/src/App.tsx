import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage/LoginPage';
import ChatPage from './pages/ChatPage/ChatPage';
import DashboardPage from './pages/DashboardPage/DashboardPage';
import CtCaseListPage from './pages/DashboardPage/CtCaseListPage'; // ✅ 已引入
import './App.css';

function App() {
  // In a real app, you would check authentication status here
  const isAuthenticated = true; // Mock authentication status

  return (
    <Router>
      <div className="app">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route 
            path="/chat" 
            element={isAuthenticated ? <ChatPage /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/dashboard" 
            element={isAuthenticated ? <DashboardPage /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/ct-cases" 
            element={isAuthenticated ? <CtCaseListPage /> : <Navigate to="/login" />} 
          />
          <Route path="/" element={<Navigate to="/login" />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
