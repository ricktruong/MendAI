/**
 * TypeScript type definitions for AI Analysis
 * These types match the backend Python Pydantic models
 */

// ============================================================================
// Finding Types
// ============================================================================

export type FindingType = 'normal' | 'abnormal' | 'suspicious';
export type SeverityLevel = 'none' | 'mild' | 'moderate' | 'severe' | 'critical';
export type FindingCategory =
  | 'lung_parenchyma'
  | 'mediastinum'
  | 'bones'
  | 'soft_tissue'
  | 'airways'
  | 'cardiovascular'
  | 'other';

export interface Finding {
  id: string;
  type: FindingType;
  severity: SeverityLevel;
  category: FindingCategory;
  title: string;
  description: string;
  confidence: number; // 0.0 to 1.0
  slice_locations?: number[];
  supporting_evidence?: string[];
  location?: {
    region?: string;
    side?: string;
    coordinates?: any;
  };
}

// ============================================================================
// Recommendation Types
// ============================================================================

export type RecommendationPriority = 'urgent' | 'high' | 'routine' | 'low';
export type RecommendationCategory =
  | 'follow_up'
  | 'intervention'
  | 'consultation'
  | 'additional_imaging'
  | 'monitoring';
export type UrgencyLevel = 'immediate' | 'urgent' | 'routine' | 'elective';

export interface Recommendation {
  id: string;
  priority: RecommendationPriority;
  category: RecommendationCategory;
  title: string;
  description: string;
  urgency: UrgencyLevel;
  timeframe?: string;
  rationale: string;
}

// ============================================================================
// Slice Analysis (Single Slice)
// ============================================================================

export interface QualityAssessment {
  score: number; // 0.0 to 1.0
  issues: string[];
}

export interface SliceAnalysisMetadata {
  slice_number: number;
  total_slices: number;
  anatomical_region: string;
  timestamp: string; // ISO format
  model_version: string;
  processing_time_ms: number;
}

export interface SliceAnalysisResponse {
  analysis_type: 'single_slice';
  metadata: SliceAnalysisMetadata;
  quality_assessment: QualityAssessment;
  findings: Finding[];
  summary: string;
}

// ============================================================================
// Batch Analysis (Multiple Slices)
// ============================================================================

export interface SliceRange {
  start: number;
  end: number;
  total_analyzed: number;
}

export interface BatchAnalysisMetadata {
  patient_id: string;
  file_id: string;
  file_name: string;
  slice_range: SliceRange;
  timestamp: string;
  model_version: string;
  processing_time_ms: number;
}

export interface OverallSummary {
  title: string;
  content: string;
  confidence: number; // 0.0 to 1.0
  urgency: UrgencyLevel;
}

export interface BatchAnalysisResponse {
  analysis_type: 'batch_analysis';
  metadata: BatchAnalysisMetadata;
  overall_summary: OverallSummary;
  findings: Finding[];
  recommendations: Recommendation[];
  differential_diagnosis?: string[];
  measurements?: any[];
  comparison_to_prior?: any;
}

// ============================================================================
// Request Types
// ============================================================================

export interface SliceAnalysisRequest {
  patient_id: string;
  file_id: string;
  slice_number: number;
  image_data?: string; // Base64 encoded
}

export interface BatchAnalysisRequest {
  patient_id: string;
  file_id: string;
  slice_start: number;
  slice_end: number;
  step_size: number;
  image_slices: string[];
}

// ============================================================================
// UI Helper Types
// ============================================================================

export interface FindingWithUI extends Finding {
  // UI-specific additions
  icon?: string;
  color?: string;
  expanded?: boolean;
}

export interface RecommendationWithUI extends Recommendation {
  // UI-specific additions
  icon?: string;
  color?: string;
  completed?: boolean;
}

// Helper function to get finding icon based on type and severity
export function getFindingIcon(finding: Finding): string {
  if (finding.type === 'normal') return '✓';
  if (finding.severity === 'critical') return '🚨';
  if (finding.severity === 'severe') return '⚠️';
  if (finding.type === 'suspicious') return '🔍';
  return '📋';
}

// Helper function to get finding color based on severity
export function getFindingColor(finding: Finding): string {
  switch (finding.severity) {
    case 'critical': return '#dc2626'; // red-600
    case 'severe': return '#ea580c'; // orange-600
    case 'moderate': return '#f59e0b'; // amber-500
    case 'mild': return '#3b82f6'; // blue-500
    case 'none': return '#10b981'; // green-500
    default: return '#6b7280'; // gray-500
  }
}

// Helper function to get recommendation icon
export function getRecommendationIcon(rec: Recommendation): string {
  switch (rec.category) {
    case 'follow_up': return '📅';
    case 'intervention': return '🏥';
    case 'consultation': return '👨‍⚕️';
    case 'additional_imaging': return '🔬';
    case 'monitoring': return '👁️';
    default: return '💡';
  }
}

// Helper function to get recommendation color
export function getRecommendationColor(rec: Recommendation): string {
  switch (rec.priority) {
    case 'urgent': return '#dc2626';
    case 'high': return '#f59e0b';
    case 'routine': return '#3b82f6';
    case 'low': return '#10b981';
    default: return '#6b7280';
  }
}
