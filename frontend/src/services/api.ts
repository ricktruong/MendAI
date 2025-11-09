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
        patients: [],
        recent_cases: [
          {
            id: '14889227',
            patient_name: 'Sarah Johnson',
            file_name: 'CT_Head_001.dcm',
            uploaded_at: '2025-09-28',
            fhirId: '07962bbc-98bf-5586-9988-603d6414295c',
            birthDate: '1978-01-16',
            gender: 'female',
            race: 'White',
            ethnicity: 'Not Hispanic or Latino',
            maritalStatus: 'M',
            managingOrganization: 'Beth Israel Deaconess Medical Center',
            language: 'en',
          },
          {
            id: '14889228',
            patient_name: 'Michael Chen',
            file_name: 'CT_Chest_045.dcm',
            uploaded_at: '2025-09-27',
            fhirId: 'a1b2c3d4-5678-9abc-def0-123456789abc',
            birthDate: '1965-05-22',
            gender: 'male',
            race: 'Asian',
            ethnicity: 'Not Hispanic or Latino',
            maritalStatus: 'M',
            managingOrganization: 'Massachusetts General Hospital',
            language: 'en',
          },
          {
            id: '14889229',
            patient_name: 'Maria Garcia',
            file_name: 'CT_Abdomen_102.dcm',
            uploaded_at: '2025-09-26',
            fhirId: 'b2c3d4e5-6789-0abc-def1-234567890bcd',
            birthDate: '1992-11-03',
            gender: 'female',
            race: 'Other',
            ethnicity: 'Hispanic or Latino',
            maritalStatus: 'S',
            managingOrganization: 'Boston Medical Center',
            language: 'es',
          },
          {
            id: '14889230',
            patient_name: 'James Williams',
            file_name: 'CT_Brain_Trauma_003.dcm',
            uploaded_at: '2025-09-25',
            fhirId: 'c3d4e5f6-7890-1bcd-ef12-34567890cdef',
            birthDate: '1955-07-14',
            gender: 'male',
            race: 'Black or African American',
            ethnicity: 'Not Hispanic or Latino',
            maritalStatus: 'W',
            managingOrganization: 'Brigham and Women\'s Hospital',
            language: 'en',
          },
          {
            id: '14889231',
            patient_name: 'Emily Rodriguez',
            file_name: 'CT_Spine_067.dcm',
            uploaded_at: '2025-09-24',
            fhirId: 'd4e5f6g7-8901-2cde-f123-4567890defgh',
            birthDate: '1980-03-28',
            gender: 'female',
            race: 'White',
            ethnicity: 'Hispanic or Latino',
            maritalStatus: 'D',
            managingOrganization: 'Tufts Medical Center',
            language: 'en',
          },
          {
            id: '14889232',
            patient_name: 'David Kim',
            file_name: 'CT_Thorax_089.dcm',
            uploaded_at: '2025-09-23',
            fhirId: 'e5f6g7h8-9012-3def-1234-567890efghij',
            birthDate: '1970-12-10',
            gender: 'male',
            race: 'Asian',
            ethnicity: 'Not Hispanic or Latino',
            maritalStatus: 'M',
            managingOrganization: 'Beth Israel Deaconess Medical Center',
            language: 'ko',
          },
          {
            id: '14889233',
            patient_name: 'Jennifer Washington',
            file_name: 'CT_Pelvis_045.dcm',
            uploaded_at: '2025-09-22',
            fhirId: 'f6g7h8i9-0123-4efg-2345-67890fghijk1',
            birthDate: '1988-08-19',
            gender: 'female',
            race: 'Black or African American',
            ethnicity: 'Not Hispanic or Latino',
            maritalStatus: 'S',
            managingOrganization: 'Boston Children\'s Hospital',
            language: 'en',
          },
          {
            id: '14889234',
            patient_name: 'Robert Patel',
            file_name: 'CT_Neck_034.dcm',
            uploaded_at: '2025-09-21',
            fhirId: 'g7h8i9j0-1234-5fgh-3456-7890ghijkl12',
            birthDate: '1963-04-07',
            gender: 'male',
            race: 'Asian',
            ethnicity: 'Not Hispanic or Latino',
            maritalStatus: 'M',
            managingOrganization: 'Massachusetts General Hospital',
            language: 'hi',
          },
          {
            id: '14889235',
            patient_name: 'Linda Martinez',
            file_name: 'CT_Sinus_012.dcm',
            uploaded_at: '2025-09-20',
            fhirId: 'h8i9j0k1-2345-6ghi-4567-890hijklm123',
            birthDate: '1975-09-15',
            gender: 'female',
            race: 'White',
            ethnicity: 'Hispanic or Latino',
            maritalStatus: 'M',
            managingOrganization: 'Lahey Hospital & Medical Center',
            language: 'es',
          },
          {
            id: '14889236',
            patient_name: 'Thomas Anderson',
            file_name: 'CT_Cardiac_078.dcm',
            uploaded_at: '2025-09-19',
            fhirId: 'i9j0k1l2-3456-7hij-5678-90ijklmn1234',
            birthDate: '1982-06-25',
            gender: 'male',
            race: 'White',
            ethnicity: 'Not Hispanic or Latino',
            maritalStatus: 'S',
            managingOrganization: 'Beth Israel Deaconess Medical Center',
            language: 'en',
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

  // Get patient files
  async getPatientFiles(caseId: string): Promise<{ success: boolean; files: PatientFile[]; message: string }> {
    return await this.makeRequest<{ success: boolean; files: PatientFile[]; message: string }>(`/patients/${caseId}/files`);
  }

  // Delete patient file
  async deletePatientFile(caseId: string, fileId: string): Promise<{ success: boolean; message: string }> {
    return await this.makeRequest<{ success: boolean; message: string }>(`/patients/${caseId}/files/${fileId}`, {
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
    totalSlices?: number
  ): Promise<any> {
    const params = new URLSearchParams({
      ...(totalSlices && { total_slices: totalSlices.toString() })
    });
    const queryString = params.toString();
    const endpoint = `/analysis/slice/${patientId}/${fileId}/${sliceNumber}${queryString ? '?' + queryString : ''}`;
    return await this.makeRequest<any>(endpoint);
  }

  async analyzeBatch(
    patientId: string,
    fileId: string,
    sliceStart: number,
    sliceEnd: number
  ): Promise<any> {
    const params = new URLSearchParams({
      slice_start: sliceStart.toString(),
      slice_end: sliceEnd.toString()
    });
    const endpoint = `/analysis/batch/${patientId}/${fileId}?${params.toString()}`;
    return await this.makeRequest<any>(endpoint);
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;