/**
 * Test Environment Configuration Types
 */

export interface BackendConfig {
  base_url: string;
  patient_data_service: string;
  imaging_service: string;
  llm_service: string;
  timeout_ms: number;
}

export interface AIAnalysisConfig {
  slice_timeout_ms: number;
  batch_timeout_ms: number;
  max_retries: number;
  retry_delay_ms: number;
  poll_interval_ms: number;
}

export interface TestDataConfig {
  medical_image_dir: string;
  metadata_file: string;
}

export interface ScreenshotConfig {
  enabled: boolean;
  directory: string;
  on_failure: boolean;
  full_page: boolean;
}

export interface TestPatientsConfig {
  patient_001: string;
  patient_002: string;
}

export interface PerformanceConfig {
  upload_timeout_ms: number;
  navigation_timeout_ms: number;
  api_timeout_ms: number;
}

export interface LoggingConfig {
  level: 'debug' | 'info' | 'warn' | 'error';
  save_to_file: boolean;
  directory: string;
}

export interface TestEnvironment {
  backend: BackendConfig;
  ai_analysis: AIAnalysisConfig;
  test_data: TestDataConfig;
  screenshots: ScreenshotConfig;
  test_patients: TestPatientsConfig;
  performance: PerformanceConfig;
  logging: LoggingConfig;
}

declare const testEnv: TestEnvironment;
export default testEnv;
