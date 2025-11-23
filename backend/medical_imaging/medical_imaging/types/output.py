from pydantic import BaseModel, Field
from typing import List
from common.types.ai_analysis import Finding, Recommendation, OverallSummary

class RawSliceAnalysisOutput(BaseModel):
    """Raw AI response structure for single slice analysis (without metadata)"""
    findings: List[Finding] = Field(..., description="List of clinical findings")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Image quality score")
    quality_issues: List[str] = Field(default_factory=list, description="Quality issues found")
    summary: str = Field(..., description="Brief overall summary")


class RawBatchAnalysisOutput(BaseModel):
    """Raw AI response structure for batch analysis (without metadata)"""
    overall_summary: OverallSummary = Field(..., description="Overall analysis summary")
    findings: List[Finding] = Field(..., description="List of clinical findings")
    recommendations: List[Recommendation] = Field(default_factory=list, description="Clinical recommendations")
    differential_diagnosis: List[str] = Field(default_factory=list, description="Possible diagnoses")
