// API service layer for MendAI frontend
import type { BatchAnalysisResponse, SliceAnalysisResponse } from '../types/ai-analysis';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Constants
const MAX_BATCH_SIZE = 10;

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

export interface PatientFile {
  id: string;
  file_name: string;
  uploaded_at: string;
}

export interface PatientListData {
  patients: Patient[];
  recent_cases: Array<{
    id: string;
    patient_name: string;
    file_name: string;
    uploaded_at: string;
    files?: PatientFile[];
    fhirId?: string;
    birthDate?: string;
    gender?: string;
    race?: string;
    ethnicity?: string;
    maritalStatus?: string;
    managingOrganization?: string;
    language?: string;
  }>;
  total?: number;  // Total number of patients
  page?: number;   // Current page
  page_size?: number;  // Items per page
  total_pages?: number;  // Total pages
}

// Keep old name for backward compatibility
export type DashboardData = PatientListData;

// Update patient response type
export interface UpdatePatientResponse {
  success: boolean;
  case?: {
    id: string;
    patient_name: string;
    file_name: string;
    uploaded_at: string;
    files?: PatientFile[];
    fhirId?: string;
    birthDate?: string;
    gender?: string;
    race?: string;
    ethnicity?: string;
    maritalStatus?: string;
    managingOrganization?: string;
    language?: string;
  };
  message?: string;
}

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
    const url = `${this.baseURL}${endpoint}`;
    
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
      await this.makeRequest<LoginResponse>('/login/login', {
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
    return await this.makeRequest<ChatResponse>('/chat/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Patient List endpoints (formerly Dashboard endpoints)
  async getPatientListData(page: number = 1, pageSize: number = 20): Promise<PatientListData> {
    return await this.makeRequest<PatientListData>(`/dashboard?page=${page}&page_size=${pageSize}`);
  }

  // Update patient endpoint
  async updatePatient(caseId: string, formData: FormData): Promise<UpdatePatientResponse> {
    const url = `${this.baseURL}/dashboard/patients/${caseId}`;
    
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
  async deletePatient(caseId: string): Promise<{ success: boolean; message?: string }> {
    return await this.makeRequest<{ success: boolean; message?: string }>(`/dashboard/patients/${caseId}`, {
      method: 'DELETE',
    });
  }

  // Create patient endpoint
  async createPatient(formData: FormData): Promise<{ success: boolean; case?: unknown; message?: string }> {
    const url = `${this.baseURL}/dashboard/patients`;
    
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

  // Get patient files
  async getPatientFiles(caseId: string): Promise<{ success: boolean; files: PatientFile[]; message: string }> {
    return await this.makeRequest<{ success: boolean; files: PatientFile[]; message: string }>(`/dashboard/patients/${caseId}/files`);
  }

  // Delete patient file
  async deletePatientFile(caseId: string, fileId: string): Promise<{ success: boolean; message: string }> {
    return await this.makeRequest<{ success: boolean; message: string }>(`/dashboard/patients/${caseId}/files/${fileId}`, {
      method: 'DELETE',
    });
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const url = `${this.baseURL}/health`;
    const response = await fetch(url);
    return await response.json();
  }

  // AI Analysis endpoints
  async analyzeSlice(
    patientId: string,
    fileId: string,
    sliceNumber: number,
    imageData: string,
    totalSlices?: number
  ): Promise<SliceAnalysisResponse> {
    return await this.makeRequest<SliceAnalysisResponse>('/ai-analysis/slice', {
      method: 'POST',
      body: JSON.stringify({
        patient_id: patientId,
        file_id: fileId,
        slice_number: sliceNumber,
        image_data: imageData,
        ...(totalSlices && { total_slices: totalSlices })
      }),
    });
  }

  async analyzeBatch(
    patientId: string,
    fileId: string,
    sliceStart: number,
    sliceEnd: number,
    imageSlices: string[]
  ): Promise<BatchAnalysisResponse> {

    let stepSize = 1;

    // Truncate the batch size if it exceeds the max batch size
    if (sliceEnd - sliceStart > MAX_BATCH_SIZE) {
      stepSize = Math.ceil((sliceEnd - sliceStart) / MAX_BATCH_SIZE);
      imageSlices = imageSlices.filter((_, i) => i % stepSize === 0);
    }

    return await this.makeRequest<BatchAnalysisResponse>('/ai-analysis/batch', {
      method: 'POST',
      body: JSON.stringify({
        patient_id: patientId,
        file_id: fileId,
        slice_start: sliceStart,
        slice_end: sliceEnd,
        step_size: stepSize,
        image_slices: imageSlices,
      }),
    });
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;