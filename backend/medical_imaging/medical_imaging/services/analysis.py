import os
import time
from typing import Optional, List
from datetime import datetime
import logging
from openai import OpenAI

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

logger = logging.getLogger(__name__)


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

    def analyze_single_slice(
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

        # Call OpenAI API
        try:
            image_format = "jpeg"  # Default to JPEG for better compression
            
            response = self.client.responses.create(
                model=self.model,
                instructions=SINGLE_SLICE_ANALYSIS_TEMPLATE,
                input=f"data:image/{image_format};base64,{image_data}"
            )
            response_text = response.output_text
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise e
        
        # Parse response into structured format
        analysis = self._parse_slice_analysis_response(
            response_text,
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
        image_slices: Optional[List[str]] = None
    ) -> BatchAnalysisResponse:
        """
        Analyze multiple CT slices

        Args:
            patient_id: Patient identifier
            file_id: File identifier
            file_name: File name
            slice_start: Starting slice number
            slice_end: Ending slice number
            image_slices: List of base64 encoded images (optional)

        Returns:
            BatchAnalysisResponse with comprehensive analysis
        """
        start_time = time.time()

        try:
            image_format = "jpeg"  # Default to JPEG for better compression
            response = self.client.responses.create(
                model=self.model,
                instructions=BATCH_ANALYSIS_TEMPLATE,
                input=image_slices
            )
            response_text = response.output_text
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise e

        analysis = self._parse_batch_analysis_response(response_text)

        processing_time = int((time.time() - start_time) * 1000)
        analysis.metadata.processing_time_ms = processing_time

        return analysis

    # ========================================================================
    # Response Parsing
    # ========================================================================

    def _parse_slice_analysis_response(
        self,
        response: str,
        slice_number: int,
        total_slices: int,
        anatomical_region: Optional[str] = None
    ) -> SliceAnalysisResponse:
        """
        Parse OpenAI response into SliceAnalysisResponse
        
        Args:
            response: JSON string response from OpenAI API
            slice_number: Current slice number
            total_slices: Total number of slices
            anatomical_region: Anatomical region name (optional, will be inferred if not provided)
            
        Returns:
            SliceAnalysisResponse with parsed findings
        """
        import json
        from datetime import datetime
        
        try:
            # Parse JSON response (handle both string and dict)
            if isinstance(response, str):
                # Try to extract JSON from markdown code blocks if present
                response_clean = response.strip()
                if response_clean.startswith("```"):
                    # Extract JSON from markdown code block
                    lines = response_clean.split("\n")
                    json_start = None
                    json_end = None
                    for i, line in enumerate(lines):
                        if line.strip().startswith("```json") or line.strip().startswith("```"):
                            json_start = i + 1
                        elif line.strip() == "```" and json_start is not None:
                            json_end = i
                            break
                    if json_start is not None and json_end is not None:
                        response_clean = "\n".join(lines[json_start:json_end])
                    elif json_start is not None:
                        response_clean = "\n".join(lines[json_start:])
                
                parsed_response = json.loads(response_clean)
            else:
                parsed_response = response
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response content: {response[:500]}")
            
            def _create_error_slice_analysis(
                slice_number: int,
                total_slices: int,
                anatomical_region: Optional[str],
                error_message: str
            ) -> SliceAnalysisResponse:
                """Create an error SliceAnalysisResponse when parsing fails"""
                from datetime import datetime
                
                if not anatomical_region:
                    position = slice_number / total_slices if total_slices > 0 else 0.5
                    if position < 0.3:
                        anatomical_region = "Upper Thorax"
                    elif position < 0.7:
                        anatomical_region = "Mid Thorax"
                    else:
                        anatomical_region = "Lower Thorax"
                
                return SliceAnalysisResponse(
                    analysis_type="single_slice",
                    metadata=SliceAnalysisMetadata(
                        slice_number=slice_number,
                        total_slices=total_slices,
                        anatomical_region=anatomical_region,
                        timestamp=datetime.utcnow().isoformat() + "Z",
                        model_version=self.model,
                        processing_time_ms=0
                    ),
                    quality_assessment=QualityAssessment(
                        score=0.0,
                        issues=[f"Parsing error: {error_message}"]
                    ),
                    findings=[],
                    summary=f"Analysis failed: {error_message}"
                )
                
            # Return a minimal error response
            return _create_error_slice_analysis(
                slice_number, total_slices, anatomical_region,
                f"Failed to parse AI response: {str(e)}"
            )
        
        # Extract data from parsed response
        findings_data = parsed_response.get("findings", [])
        quality_score = parsed_response.get("quality_score", 0.8)
        quality_issues = parsed_response.get("quality_issues", [])
        summary = parsed_response.get("summary", "Analysis completed")
        
        # Infer anatomical region if not provided
        if not anatomical_region:
            position = slice_number / total_slices if total_slices > 0 else 0.5
            if position < 0.3:
                anatomical_region = "Upper Thorax"
            elif position < 0.7:
                anatomical_region = "Mid Thorax"
            else:
                anatomical_region = "Lower Thorax"
        
        # Parse findings
        findings = []
        for idx, finding_data in enumerate(findings_data):
            try:
                # Generate ID if not provided
                finding_id = finding_data.get("id", f"finding_{slice_number}_{idx+1:03d}")
                
                # Validate and extract finding fields
                finding_type = finding_data.get("type", "normal")
                # Ensure valid type
                if finding_type not in ["normal", "abnormal", "suspicious"]:
                    finding_type = "normal"
                
                severity = finding_data.get("severity", "none")
                # Ensure valid severity
                if severity not in ["none", "mild", "moderate", "severe", "critical"]:
                    severity = "none"
                
                category = finding_data.get("category", "other")
                # Ensure valid category
                valid_categories = [
                    "lung_parenchyma", "mediastinum", "bones", "soft_tissue",
                    "airways", "cardiovascular", "other"
                ]
                if category not in valid_categories:
                    category = "other"
                
                title = finding_data.get("title", "Finding")
                description = finding_data.get("description", "")
                confidence = float(finding_data.get("confidence", 0.5))
                # Clamp confidence to [0, 1]
                confidence = max(0.0, min(1.0, confidence))
                
                supporting_evidence = finding_data.get("supporting_evidence", [])
                if not isinstance(supporting_evidence, list):
                    supporting_evidence = []
                
                # Create Finding object
                finding = Finding(
                    id=finding_id,
                    type=finding_type,
                    severity=severity,
                    category=category,
                    title=title,
                    description=description,
                    confidence=confidence,
                    supporting_evidence=supporting_evidence,
                    slice_locations=[slice_number]  # Current slice
                )
                findings.append(finding)
            except Exception as e:
                logger.warning(f"Failed to parse finding {idx}: {e}")
                continue
        
        # If no findings were parsed, create a default normal finding
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
        
        # Clamp quality score to [0, 1]
        quality_score = max(0.0, min(1.0, float(quality_score)))
        
        # Create response
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
                score=quality_score,
                issues=quality_issues if isinstance(quality_issues, list) else []
            ),
            findings=findings,
            summary=summary
        )

    def _parse_batch_analysis_response(self, response: dict) -> BatchAnalysisResponse:
        """Parse OpenAI response into BatchAnalysisResponse"""
        # TODO: Implement JSON parsing and validation
        raise NotImplementedError("Response parsing pending API integration")


# Singleton instance
_service_instance: Optional[MedicalImageAnalysisService] = None


def get_medical_image_analysis_service() -> MedicalImageAnalysisService:
    """Get singleton instance of OpenAI service"""
    global _service_instance
    if _service_instance is None:
        _service_instance = MedicalImageAnalysisService()
    return _service_instance
