"""
Shared type definitions for AI analysis responses.
These types ensure consistency between frontend and backend.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


# ============================================================================
# Finding Types
# ============================================================================

class Finding(BaseModel):
    """A single clinical finding from AI analysis"""
    id: str = Field(..., description="Unique identifier for this finding")
    type: Literal["normal", "abnormal", "suspicious"] = Field(
        ..., description="Classification of the finding"
    )
    severity: Literal["none", "mild", "moderate", "severe", "critical"] = Field(
        ..., description="Severity level of the finding"
    )
    category: Literal[
        "lung_parenchyma",
        "mediastinum",
        "bones",
        "soft_tissue",
        "airways",
        "cardiovascular",
        "other"
    ] = Field(..., description="Anatomical category")
    title: str = Field(..., description="Short title for the finding")
    description: str = Field(..., description="Detailed description")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    slice_locations: Optional[List[int]] = Field(
        None, description="List of slice numbers where finding appears"
    )
    supporting_evidence: Optional[List[str]] = Field(
        None, description="Supporting observations"
    )
    location: Optional[dict] = Field(
        None, description="Spatial location information"
    )


# ============================================================================
# Recommendation Types
# ============================================================================

class Recommendation(BaseModel):
    """A clinical recommendation based on findings"""
    id: str = Field(..., description="Unique identifier")
    priority: Literal["urgent", "high", "routine", "low"] = Field(
        ..., description="Priority level"
    )
    category: Literal[
        "follow_up",
        "intervention",
        "consultation",
        "additional_imaging",
        "monitoring"
    ] = Field(..., description="Type of recommendation")
    title: str = Field(..., description="Short title")
    description: str = Field(..., description="Detailed description")
    urgency: Literal["immediate", "urgent", "routine", "elective"] = Field(
        ..., description="Urgency level"
    )
    timeframe: Optional[str] = Field(
        None, description="Suggested timeframe (e.g., '3_months', '1_week')"
    )
    rationale: str = Field(..., description="Reason for recommendation")


# ============================================================================
# Slice Analysis (Single Slice)
# ============================================================================

class QualityAssessment(BaseModel):
    """Image quality assessment"""
    score: float = Field(..., ge=0.0, le=1.0, description="Overall quality score")
    issues: List[str] = Field(default_factory=list, description="Quality issues found")


class SliceAnalysisMetadata(BaseModel):
    """Metadata for single slice analysis"""
    slice_number: int = Field(..., description="Current slice number")
    total_slices: int = Field(..., description="Total number of slices")
    anatomical_region: str = Field(..., description="Anatomical region name")
    timestamp: str = Field(..., description="ISO format timestamp")
    model_version: str = Field(default="mock", description="AI model version")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")


class SliceAnalysisResponse(BaseModel):
    """Response for single slice analysis"""
    analysis_type: Literal["single_slice"] = "single_slice"
    metadata: SliceAnalysisMetadata
    quality_assessment: QualityAssessment
    findings: List[Finding]
    summary: str = Field(..., description="Brief overall summary")


# ============================================================================
# Batch Analysis (Multiple Slices)
# ============================================================================

class SliceRange(BaseModel):
    """Range of slices analyzed"""
    start: int = Field(..., description="Starting slice number")
    end: int = Field(..., description="Ending slice number")
    total_analyzed: int = Field(..., description="Total slices analyzed")


class BatchAnalysisMetadata(BaseModel):
    """Metadata for batch analysis"""
    patient_id: str = Field(..., description="Patient identifier")
    file_id: str = Field(..., description="File identifier")
    file_name: str = Field(..., description="File name")
    slice_range: SliceRange
    timestamp: str = Field(..., description="ISO format timestamp")
    model_version: str = Field(default="mock", description="AI model version")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")


class OverallSummary(BaseModel):
    """Overall summary of batch analysis"""
    title: str = Field(..., description="Summary title")
    content: str = Field(..., description="Summary content")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    urgency: Literal["immediate", "urgent", "routine", "elective"] = Field(
        ..., description="Overall urgency level"
    )


class BatchAnalysisResponse(BaseModel):
    """Response for batch analysis of multiple slices"""
    analysis_type: Literal["batch_analysis"] = "batch_analysis"
    metadata: BatchAnalysisMetadata
    overall_summary: OverallSummary
    findings: List[Finding]
    recommendations: List[Recommendation]
    differential_diagnosis: Optional[List[str]] = Field(
        default_factory=list, description="Possible diagnoses"
    )
    measurements: Optional[List[dict]] = Field(
        default_factory=list, description="Quantitative measurements"
    )
    comparison_to_prior: Optional[dict] = Field(
        None, description="Comparison to prior studies if available"
    )


# ============================================================================
# Request Types
# ============================================================================

class SliceAnalysisRequest(BaseModel):
    """Request for single slice analysis"""
    patient_id: str
    file_id: str
    slice_number: int
    image_data: Optional[str] = Field(
        None, description="Base64 encoded image data (optional if using file_id)"
    )


class BatchAnalysisRequest(BaseModel):
    """Request for batch analysis"""
    patient_id: str
    file_id: str
    slice_start: int
    slice_end: int
    step_size: int
    image_slices: List[str]