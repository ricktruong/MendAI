import os
import time
from typing import Optional, List
from datetime import datetime
import structlog
from openai import OpenAI
from pydantic import BaseModel, Field

from ..types.output import RawSliceAnalysisOutput, RawBatchAnalysisOutput
from ..templates.templates import SINGLE_SLICE_ANALYSIS_TEMPLATE, BATCH_ANALYSIS_TEMPLATE
from common.types.ai_analysis import (
    SliceAnalysisResponse,
    BatchAnalysisResponse,
    SliceAnalysisMetadata,
    BatchAnalysisMetadata,
    QualityAssessment,
    Finding,
    Recommendation,
    OverallSummary,
    SliceRange,
)

logger = structlog.get_logger()


class MedicalImageAnalysisService:
    """Medical image analysis service. An instance of this class is used to analyze single slices and batches of CT scans."""

    def __init__(self):
        """
        Initialize MedicalImageAnalysisService.
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.1")

    def analyze_slice(
        self,
        patient_id: str,
        file_id: str,
        slice_number: int,
        total_slices: int,
        image_data: Optional[str] = None,
        anatomical_region: Optional[str] = None
    ) -> SliceAnalysisResponse:
        """
        Analyze a single CT slice

        Args:
            patient_id: Patient identifier
            file_id: File identifier
            slice_number: Slice number to analyze
            total_slices: Total number of slices in the scan
            image_data: Base64 encoded image (optional)
            anatomical_region: Anatomical region name (optional)

        Returns:
            SliceAnalysisResponse with structured findings
        """
        print(f"Analyzing single slice {slice_number}/{total_slices} for patient {patient_id}")
        start_time = time.time()

        # Call OpenAI API with structured output
        try:
            image_format = "jpeg"  # Default to JPEG for better compression
            
            response = self.client.responses.parse(
                model=self.model,
                instructions=SINGLE_SLICE_ANALYSIS_TEMPLATE,
                input=f"data:image/{image_format};base64,{image_data}",
                text_format=RawSliceAnalysisOutput
            )
            raw_analysis = response.output_parsed
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise e
        
        # Convert raw analysis to full response with metadata
        analysis = self._convert_raw_slice_analysis(
            raw_analysis,
            slice_number=slice_number,
            total_slices=total_slices,
            anatomical_region=anatomical_region
        )

        # Add metadata
        processing_time = int((time.time() - start_time) * 1000)
        analysis.metadata.processing_time_ms = processing_time

        return analysis

    def analyze_batch(
        self,
        patient_id: str,
        file_id: str,
        file_name: str,
        slice_start: int,
        slice_end: int,
        step_size: int,
        image_slices: List[str]
    ) -> BatchAnalysisResponse:
        """
        Analyze a batch of CT slices

        Args:
            patient_id: Patient identifier
            file_id: File identifier
            file_name: File name
            slice_start: Starting slice number
            slice_end: Ending slice number
            step_size: Step size for batch analysis
            image_slices: List of Base64 encoded image slices

        Returns:
            BatchAnalysisResponse with structured findings
        """
        print(f"Analyzing batch of slices {slice_start}-{slice_end} (step={step_size}) for patient {patient_id}")
        start_time = time.time()

        # Call OpenAI API with structured output
        try:
            # Format images for OpenAI API - create a list of image data URIs
            # Since we have max 10 slices, we can send them all at once
            formatted_images = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_image", 
                            "image_url": f"data:image/jpeg;base64,{img_data}"   # Default to JPEG for better compression
                        } for img_data in image_slices
                    ]
                }
            ]
            
            # For batch analysis, we need to send multiple images
            # OpenAI responses.parse can handle multiple images in the input
            response = self.client.responses.parse(
                model=self.model,
                instructions=BATCH_ANALYSIS_TEMPLATE,
                input=formatted_images,  # List of image data URIs
                text_format=RawBatchAnalysisOutput
            )
            raw_analysis = response.output_parsed
        except Exception as e:
            logger.error(f"Error calling OpenAI API for batch analysis: {e}")
            raise e
        
        # Convert raw analysis to full response with metadata
        analysis = self._convert_raw_batch_analysis(
            raw_analysis,
            patient_id=patient_id,
            file_id=file_id,
            file_name=file_name,
            slice_start=slice_start,
            slice_end=slice_end,
            step_size=step_size,
            total_analyzed=len(image_slices)
        )

        # Add metadata
        processing_time = int((time.time() - start_time) * 1000)
        analysis.metadata.processing_time_ms = processing_time

        return analysis
        
    def _convert_raw_slice_analysis(
        self,
        raw_analysis: RawSliceAnalysisOutput,
        slice_number: int,
        total_slices: int,
        anatomical_region: Optional[str] = None
    ) -> SliceAnalysisResponse:
        """
        Convert raw AI response (already parsed by OpenAI) to SliceAnalysisResponse with metadata
        
        Args:
            raw_analysis: Parsed Pydantic model from OpenAI structured output
            slice_number: Current slice number
            total_slices: Total number of slices
            anatomical_region: Anatomical region name (optional, will be inferred if not provided)
            
        Returns:
            SliceAnalysisResponse with metadata and findings
        """
        # Infer anatomical region if not provided
        if not anatomical_region:
            position = slice_number / total_slices if total_slices > 0 else 0.5
            if position < 0.3:
                anatomical_region = "Upper Thorax"
            elif position < 0.7:
                anatomical_region = "Mid Thorax"
            else:
                anatomical_region = "Lower Thorax"
        
        # Ensure findings have IDs and slice locations
        findings = []
        for idx, finding in enumerate(raw_analysis.findings):
            # Generate ID if not provided
            if not finding.id:
                finding.id = f"finding_{slice_number}_{idx+1:03d}"
            
            # Ensure slice_locations includes current slice
            if finding.slice_locations is None:
                finding.slice_locations = [slice_number]
            elif slice_number not in finding.slice_locations:
                finding.slice_locations.append(slice_number)
            
            findings.append(finding)
        
        # If no findings, create a default normal finding
        if not findings:
            findings.append(
                Finding(
                    id=f"finding_{slice_number}_default",
                    type="normal",
                    severity="none",
                    category="other",
                    title="No Significant Findings",
                    description="No abnormalities detected in this slice.",
                    confidence=0.7,
                    supporting_evidence=[],
                    slice_locations=[slice_number]
                )
            )
        
        # Create response with metadata
        return SliceAnalysisResponse(
            analysis_type="single_slice",
            metadata=SliceAnalysisMetadata(
                slice_number=slice_number,
                total_slices=total_slices,
                anatomical_region=anatomical_region,
                timestamp=datetime.utcnow().isoformat() + "Z",
                model_version=self.model,
                processing_time_ms=0  # Will be set by caller
            ),
            quality_assessment=QualityAssessment(
                score=raw_analysis.quality_score,
                issues=raw_analysis.quality_issues
            ),
            findings=findings,
            summary=raw_analysis.summary
        )

    def _convert_raw_batch_analysis(
        self,
        raw_analysis: RawBatchAnalysisOutput,
        patient_id: str,
        file_id: str,
        file_name: str,
        slice_start: int,
        slice_end: int,
        step_size: int,
        total_analyzed: int
    ) -> BatchAnalysisResponse:
        """
        Convert raw AI response (already parsed by OpenAI) to BatchAnalysisResponse with metadata
        
        Args:
            raw_analysis: Parsed Pydantic model from OpenAI structured output
            patient_id: Patient identifier
            file_id: File identifier
            file_name: File name
            slice_start: Starting slice number
            slice_end: Ending slice number
            step_size: Step size used
            total_analyzed: Total number of slices analyzed
            
        Returns:
            BatchAnalysisResponse with metadata and findings
        """
        # Ensure findings have IDs and proper slice locations
        findings = []
        for idx, finding in enumerate(raw_analysis.findings):
            # Generate ID if not provided
            if not finding.id:
                finding.id = f"finding_batch_{idx+1:03d}"
            
            # Validate and convert slice_locations if needed
            if finding.slice_locations:
                validated_locations = []
                for loc in finding.slice_locations:
                    if isinstance(loc, int):
                        # If location is within the analyzed range, use it directly
                        if slice_start <= loc <= slice_end:
                            validated_locations.append(loc)
                        else:
                            # Assume it's an index, convert to slice number
                            actual_slice = slice_start + (loc * step_size)
                            if slice_start <= actual_slice <= slice_end:
                                validated_locations.append(actual_slice)
                finding.slice_locations = validated_locations if validated_locations else None
            
            findings.append(finding)
        
        # Ensure recommendations have IDs
        recommendations = []
        for idx, rec in enumerate(raw_analysis.recommendations):
            if not rec.id:
                rec.id = f"recommendation_{idx+1:03d}"
            recommendations.append(rec)
        
        # Create response with metadata
        return BatchAnalysisResponse(
            analysis_type="batch_analysis",
            metadata=BatchAnalysisMetadata(
                patient_id=patient_id,
                file_id=file_id,
                file_name=file_name,
                slice_range=SliceRange(
                    start=slice_start,
                    end=slice_end,
                    total_analyzed=total_analyzed
                ),
                timestamp=datetime.utcnow().isoformat() + "Z",
                model_version=self.model,
                processing_time_ms=0  # Will be set by caller
            ),
            overall_summary=raw_analysis.overall_summary,
            findings=findings,
            recommendations=recommendations,
            differential_diagnosis=raw_analysis.differential_diagnosis
        )

# Singleton instance
_service_instance: Optional[MedicalImageAnalysisService] = None


def get_medical_image_analysis_service() -> MedicalImageAnalysisService:
    """Get singleton instance of OpenAI service"""
    global _service_instance
    if _service_instance is None:
        _service_instance = MedicalImageAnalysisService()
    return _service_instance
