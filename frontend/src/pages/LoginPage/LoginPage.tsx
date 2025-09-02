import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './LoginPage.css';
import { apiService } from '../../services/api';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const result = await apiService.login({ email, password });

      if (result.success && result.token) {
        // Store authentication info
        localStorage.setItem('token', result.token);
        if (result.user) {
          localStorage.setItem('user', JSON.stringify(result.user));
        }
        
        console.log('Login successful, navigating to patient list');
        navigate('/patients');
      } else {
        setError(result.error || 'Login failed - invalid credentials');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError(`Login failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-left">
        <div className="login-content">
          <div className="logo-section">
            <h1 className="logo">MendAI</h1>
            <p className="tagline">Your Agentic AI Healthcare Assistant</p>
          </div>

          <div className="features-section">
            <h2>Revolutionizing Healthcare with AI</h2>
            <div className="features-grid">
              <div className="feature-item">
                <div className="feature-icon">🏥</div>
                <h3>EHR Integration</h3>
                <p>Seamlessly integrates with existing Electronic Health Record systems via SMART-on-FHIR</p>
              </div>
              <div className="feature-item">
                <div className="feature-icon">🔬</div>
                <h3>Multimodal Analysis</h3>
                <p>Analyzes medical images, vital signs, lab results, and clinical records simultaneously</p>
              </div>
              <div className="feature-item">
                <div className="feature-icon">⚡</div>
                <h3>Real-time Processing</h3>
                <p>Provides instant analysis and clinical decision support during patient visits</p>
              </div>
              <div className="feature-item">
                <div className="feature-icon">🤖</div>
                <h3>AI-Powered Insights</h3>
                <p>Advanced AI algorithms detect anomalies and generate comprehensive diagnostic insights</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="login-right">
        <div className="login-form-container">
          <form className="login-form" onSubmit={handleSubmit}>
            <h2>Welcome Back</h2>
            <p className="login-subtitle">Sign in to access your clinical dashboard</p>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="doctor@hospital.com"
                required
                disabled={isLoading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                disabled={isLoading}
              />
            </div>

            <div className="form-options">
              <label className="remember-me">
                <input type="checkbox" />
                <span>Remember me</span>
              </label>
              <a href="#" className="forgot-password">Forgot password?</a>
            </div>

            <button type="submit" className="login-button" disabled={isLoading}>
              {isLoading ? (
                <span className="loading-spinner">
                  <span className="spinner"></span>
                  Signing in...
                </span>
              ) : (
                'Sign In'
              )}
            </button>

            <div className="login-footer">
              <p>New to MendAI? <a href="/signup">Request access</a></p>
            </div>
          </form>

          <div className="security-note">
            <p>🔒 Your data is protected with end-to-end encryption and complies with HIPAA standards</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;