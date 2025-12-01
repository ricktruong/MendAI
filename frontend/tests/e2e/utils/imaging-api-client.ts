/**
 * Medical Imaging API Client
 * Type-safe wrapper for MendAI imaging service API calls
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import * as fs from 'fs';
import * as FormData from 'form-data';

// Type definitions
export interface UploadResponse {
  success: boolean;
  scan_id: string;
  patient_id: string;
  file_count: number;
  message?: string;
}

export interface Finding {
  type: string;
  location: string;
  size_mm: number;
  confidence: number;
  coordinates: { x: number; y: number; z?: number };
  severity?: 'low' | 'medium' | 'high' | 'critical';
  description?: string;
}

export interface SliceAnalysisResult {
  success: boolean;
  scan_id: string;
  slice_number: number;
  findings: Finding[];
  ai_confidence: number;
  summary: string;
  processing_time_ms?: number;
  model_version?: string;
}

export interface BatchAnalysisResult {
  success: boolean;
  scan_id: string;
  total_slices: number;
  analyzed_slices: number;
  overall_summary: {
    total_findings: number;
    high_risk_slices: number[];
    diagnosis: string;
    confidence: number;
  };
  slice_results?: SliceAnalysisResult[];
  processing_time_ms?: number;
}

export interface AnalysisStatus {
  analysis_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  completed: boolean;
  result?: SliceAnalysisResult | BatchAnalysisResult;
  error?: string;
  started_at?: string;
  completed_at?: string;
}

export interface ScanInfo {
  scan_id: string;
  patient_id: string;
  upload_date: string;
  slice_count: number;
  modality: string;
  body_part?: string;
}

/**
 * Medical Imaging API Client
 */
export class ImagingAPIClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor(baseURL: string, config?: AxiosRequestConfig) {
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL,
      timeout: 300000, // 5 minutes default
      headers: {
        'Content-Type': 'application/json',
      },
      ...config,
    });

    // Add request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('[API Error]', error);
        return Promise.reject(error);
      }
    );

    // Add response interceptor for logging
    this.client.interceptors.response.use(
      (response) => {
        console.log(`[API] Response ${response.status} from ${response.config.url}`);
        return response;
      },
      (error) => {
        if (error.response) {
          console.error(`[API Error] ${error.response.status} from ${error.config?.url}`);
          console.error('[API Error Data]', error.response.data);
        } else {
          console.error('[API Network Error]', error.message);
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Upload medical image file(s) to the imaging service
   */
  async uploadMedicalImages(
    filePath: string | string[],
    patientId: string
  ): Promise<UploadResponse> {
    const formData = new FormData();

    // Handle single or multiple files
    const files = Array.isArray(filePath) ? filePath : [filePath];

    files.forEach((file) => {
      if (!fs.existsSync(file)) {
        throw new Error(`File not found: ${file}`);
      }
      formData.append('files', fs.createReadStream(file));
    });

    formData.append('patient_id', patientId);

    const response = await this.client.post<UploadResponse>(
      '/api/v0/imaging/upload',
      formData,
      {
        headers: {
          ...formData.getHeaders(),
        },
        timeout: 120000, // 2 minutes for upload
      }
    );

    return response.data;
  }

  /**
   * Analyze a specific slice
   */
  async analyzeSlice(
    scanId: string,
    sliceNumber: number
  ): Promise<SliceAnalysisResult> {
    const response = await this.client.post<SliceAnalysisResult>(
      `/api/v0/imaging/analyze/slice/${scanId}`,
      { slice_number: sliceNumber },
      { timeout: 60000 } // 1 minute for slice analysis
    );

    return response.data;
  }

  /**
   * Analyze all slices in a scan (batch analysis)
   */
  async analyzeBatch(scanId: string): Promise<BatchAnalysisResult> {
    const response = await this.client.post<BatchAnalysisResult>(
      `/api/v0/imaging/analyze/batch/${scanId}`,
      {},
      { timeout: 600000 } // 10 minutes for batch analysis
    );

    return response.data;
  }

  /**
   * Get analysis status
   */
  async getAnalysisStatus(analysisId: string): Promise<AnalysisStatus> {
    const response = await this.client.get<AnalysisStatus>(
      `/api/v0/imaging/analysis/${analysisId}/status`
    );

    return response.data;
  }

  /**
   * Get scan information
   */
  async getScanInfo(scanId: string): Promise<ScanInfo> {
    const response = await this.client.get<ScanInfo>(
      `/api/v0/imaging/scans/${scanId}`
    );

    return response.data;
  }

  /**
   * List all scans for a patient
   */
  async listPatientScans(patientId: string): Promise<ScanInfo[]> {
    const response = await this.client.get<ScanInfo[]>(
      `/api/v0/imaging/patients/${patientId}/scans`
    );

    return response.data;
  }

  /**
   * Download analysis report
   */
  async downloadReport(
    analysisId: string,
    format: 'pdf' | 'json' = 'pdf'
  ): Promise<Buffer> {
    const response = await this.client.get(
      `/api/v0/imaging/analysis/${analysisId}/report`,
      {
        params: { format },
        responseType: 'arraybuffer',
      }
    );

    return Buffer.from(response.data);
  }

  /**
   * Delete a scan
   */
  async deleteScan(scanId: string): Promise<{ success: boolean }> {
    const response = await this.client.delete(
      `/api/v0/imaging/scans/${scanId}`
    );

    return response.data;
  }

  /**
   * Wait for analysis to complete with polling
   */
  async waitForAnalysisComplete(
    analysisId: string,
    options: {
      timeout?: number;
      pollInterval?: number;
      onProgress?: (status: AnalysisStatus) => void;
    } = {}
  ): Promise<SliceAnalysisResult | BatchAnalysisResult> {
    const {
      timeout = 300000, // 5 minutes default
      pollInterval = 2000, // 2 seconds
      onProgress,
    } = options;

    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      const status = await this.getAnalysisStatus(analysisId);

      // Call progress callback if provided
      if (onProgress) {
        onProgress(status);
      }

      // Check if completed
      if (status.completed) {
        if (status.status === 'failed') {
          throw new Error(`Analysis failed: ${status.error || 'Unknown error'}`);
        }

        if (!status.result) {
          throw new Error('Analysis completed but no result returned');
        }

        return status.result;
      }

      // Wait before next poll
      await this.sleep(pollInterval);
    }

    throw new Error(`Analysis timeout after ${timeout}ms`);
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string; version?: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }

  /**
   * Retry wrapper for failed requests
   */
  async withRetry<T>(
    operation: () => Promise<T>,
    options: {
      maxRetries?: number;
      retryDelay?: number;
      shouldRetry?: (error: any) => boolean;
    } = {}
  ): Promise<T> {
    const {
      maxRetries = 3,
      retryDelay = 5000,
      shouldRetry = (error) => {
        // Retry on network errors and 5xx errors
        return !error.response || error.response.status >= 500;
      },
    } = options;

    let lastError: any;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error;

        // Check if we should retry
        if (attempt < maxRetries - 1 && shouldRetry(error)) {
          console.log(`Retry attempt ${attempt + 1}/${maxRetries} after ${retryDelay}ms`);
          await this.sleep(retryDelay);
          continue;
        }

        // No more retries or shouldn't retry
        break;
      }
    }

    throw lastError;
  }

  /**
   * Helper: Sleep for specified milliseconds
   */
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

/**
 * Create a configured imaging API client
 */
export function createImagingClient(baseURL?: string): ImagingAPIClient {
  const url = baseURL || process.env.IMAGING_API_URL || 'http://localhost:8002';
  return new ImagingAPIClient(url);
}
