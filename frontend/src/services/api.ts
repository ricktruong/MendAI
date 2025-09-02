// API service layer for MendAI frontend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Types matching backend models
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  token?: string;
  user?: {
    id: string;
    email: string;
    name: string;
    role: string;
  };
  error?: string;
}

export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: string; // ISO string
  attachments?: Attachment[];
  analysis_results?: AnalysisResult[];
}

export interface Attachment {
  id: string;
  type: 'image' | 'document' | 'lab-result';
  name: string;
  url?: string;
}

export interface AnalysisResult {
  type: 'imaging' | 'vitals' | 'lab' | 'summary';
  title: string;
  content: Record<string, unknown>;
  confidence?: number;
}

export interface ChatRequest {
  messages: Message[];
  patient_id?: string;
  session_id?: string;
}

export interface ChatResponse {
  session_id: string;
  messages: Message[];
  patient_id?: string;
}

export interface Patient {
  id: string;
  name: string;
  email?: string;
  age?: number;
  gender?: string;
}

export interface PatientListData {
  patients: Patient[];
  recent_cases: Array<{
    id: string;
    patient_name: string;
    file_name: string;
    uploaded_at: string;
  }>;
}

// Keep old name for backward compatibility
export interface DashboardData extends PatientListData {}

// API client class
class ApiService {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}/api/v0${endpoint}`;
    
    // Add default headers
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };

    // Add auth token if available
    const token = localStorage.getItem('token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config: RequestInit = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);
      
      // Handle unauthorized responses
      if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        throw new Error('Unauthorized');
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${url}`, error);
      throw error;
    }
  }

  // Authentication endpoints
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      await this.makeRequest<any>('/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
      });

      // Map backend response to frontend expected format
      return {
        success: true,
        token: 'mock-jwt-token', // Backend doesn't return token yet
        user: {
          id: '1',
          email: credentials.email,
          name: credentials.email.split('@')[0],
          role: 'doctor',
        },
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Login failed',
      };
    }
  }

  // Chat endpoints
  async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    return await this.makeRequest<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Patient List endpoints (formerly Dashboard endpoints)
  async getPatientListData(): Promise<PatientListData> {
    try {
      return await this.makeRequest<PatientListData>('/dashboard');
    } catch (error) {
      // Return mock data for now since endpoint isn't fully implemented
      return {
        patients: [
          { id: '1', name: 'John Doe', age: 54, gender: 'Male' },
          { id: '2', name: 'Jane Smith', age: 42, gender: 'Female' },
          { id: '3', name: 'Maria Garcia', age: 37, gender: 'Female' },
        ],
        recent_cases: [
          {
            id: 'ct-001',
            patient_name: 'John Doe',
            file_name: 'CT_Head_001.dcm',
            uploaded_at: '2025-01-27',
          },
          {
            id: 'ct-002',
            patient_name: 'Jane Smith',
            file_name: 'CT_Chest_045.dcm',
            uploaded_at: '2025-01-25',
          },
          {
            id: 'ct-003',
            patient_name: 'Maria Garcia',
            file_name: 'CT_Abdomen_102.dcm',
            uploaded_at: '2025-01-22',
          },
        ],
      };
    }
  }

  // Update patient endpoint
  async updatePatient(caseId: string, formData: FormData): Promise<any> {
    const url = `${this.baseURL}/api/v0/patients/${caseId}`;
    
    // For file upload, we need to handle FormData differently
    const token = localStorage.getItem('token');
    const headers: Record<string, string> = {};
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
      const response = await fetch(url, {
        method: 'PUT',
        headers,
        body: formData,
      });

      if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        throw new Error('Unauthorized');
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Update patient request failed`, error);
      throw error;
    }
  }

  // Delete patient endpoint
  async deletePatient(caseId: string): Promise<any> {
    return await this.makeRequest<any>(`/patients/${caseId}`, {
      method: 'DELETE',
    });
  }

  // Create patient endpoint
  async createPatient(formData: FormData): Promise<any> {
    const url = `${this.baseURL}/api/v0/patients`;
    
    // For file upload, we need to handle FormData differently
    const token = localStorage.getItem('token');
    const headers: Record<string, string> = {};
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    // Don't set Content-Type for FormData - let browser set it with boundary
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
      });

      if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        throw new Error('Unauthorized');
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Create patient request failed`, error);
      throw error;
    }
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const url = `${this.baseURL}/health`;
    const response = await fetch(url);
    return await response.json();
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;