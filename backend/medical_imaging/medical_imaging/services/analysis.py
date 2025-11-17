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

        # Call OpenAI API
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
            # OpenAI responses.create can handle multiple images in the input
            response = self.client.responses.create(
                model=self.model,
                instructions=BATCH_ANALYSIS_TEMPLATE,
                input=formatted_images  # List of image data URIs
            )
            response_text = response.output_text
        except Exception as e:
            logger.error(f"Error calling OpenAI API for batch analysis: {e}")
            raise e
        
        # Parse response into structured format
        analysis = self._parse_batch_analysis_response(
            response_text,
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
            
            # Create an error SliceAnalysisResponse when parsing fails
            error_message = f"Failed to parse AI response: {str(e)}"
            
            # Infer anatomical region if not provided
            if not anatomical_region:
                position = slice_number / total_slices if total_slices > 0 else 0.5
                if position < 0.3:
                    anatomical_region = "Upper Thorax"
                elif position < 0.7:
                    anatomical_region = "Mid Thorax"
                else:
                    anatomical_region = "Lower Thorax"
            
            # Return a minimal error response
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

    def _parse_batch_analysis_response(
        self,
        response: str,
        patient_id: str,
        file_id: str,
        file_name: str,
        slice_start: int,
        slice_end: int,
        step_size: int,
        total_analyzed: int
    ) -> BatchAnalysisResponse:
        """
        Parse OpenAI response into BatchAnalysisResponse
        
        Args:
            response: JSON string response from OpenAI API
            patient_id: Patient identifier
            file_id: File identifier
            file_name: File name
            slice_start: Starting slice number
            slice_end: Ending slice number
            step_size: Step size used
            total_analyzed: Total number of slices analyzed
            
        Returns:
            BatchAnalysisResponse with parsed findings
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
            
            # Return a minimal error response
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
                    processing_time_ms=0
                ),
                overall_summary=OverallSummary(
                    title="Analysis Error",
                    content=f"Failed to parse AI response: {str(e)}",
                    confidence=0.0,
                    urgency="routine"
                ),
                findings=[],
                recommendations=[],
                differential_diagnosis=[]
            )
        
        # Extract overall_summary
        overall_summary_data = parsed_response.get("overall_summary", {})
        overall_summary = OverallSummary(
            title=overall_summary_data.get("title", "Analysis Summary"),
            content=overall_summary_data.get("content", "Comprehensive analysis completed"),
            confidence=max(0.0, min(1.0, float(overall_summary_data.get("confidence", 0.8)))),
            urgency=overall_summary_data.get("urgency", "routine")
        )
        
        # Parse findings
        findings_data = parsed_response.get("findings", [])
        findings = []
        for idx, finding_data in enumerate(findings_data):
            try:
                # Generate ID if not provided
                finding_id = finding_data.get("id", f"finding_batch_{idx+1:03d}")
                
                # Validate and extract finding fields
                finding_type = finding_data.get("type", "normal")
                if finding_type not in ["normal", "abnormal", "suspicious"]:
                    finding_type = "normal"
                
                severity = finding_data.get("severity", "none")
                if severity not in ["none", "mild", "moderate", "severe", "critical"]:
                    severity = "none"
                
                category = finding_data.get("category", "other")
                valid_categories = [
                    "lung_parenchyma", "mediastinum", "bones", "soft_tissue",
                    "airways", "cardiovascular", "other"
                ]
                if category not in valid_categories:
                    category = "other"
                
                title = finding_data.get("title", "Finding")
                description = finding_data.get("description", "")
                confidence = max(0.0, min(1.0, float(finding_data.get("confidence", 0.5))))
                
                # Parse slice_locations - convert to actual slice numbers based on step_size
                slice_locations_raw = finding_data.get("slice_locations", [])
                slice_locations = []
                if isinstance(slice_locations_raw, list):
                    # If slice_locations are indices (0-based), convert to actual slice numbers
                    for loc in slice_locations_raw:
                        if isinstance(loc, int):
                            # If location is within the analyzed range, use it directly
                            # Otherwise, calculate from index
                            if slice_start <= loc <= slice_end:
                                slice_locations.append(loc)
                            else:
                                # Assume it's an index, convert to slice number
                                actual_slice = slice_start + (loc * step_size)
                                if slice_start <= actual_slice <= slice_end:
                                    slice_locations.append(actual_slice)
                
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
                    slice_locations=slice_locations if slice_locations else None
                )
                findings.append(finding)
            except Exception as e:
                logger.warning(f"Failed to parse finding {idx}: {e}")
                continue
        
        # Parse recommendations
        recommendations_data = parsed_response.get("recommendations", [])
        recommendations = []
        for idx, rec_data in enumerate(recommendations_data):
            try:
                rec_id = rec_data.get("id", f"recommendation_{idx+1:03d}")
                
                priority = rec_data.get("priority", "routine")
                if priority not in ["urgent", "high", "routine", "low"]:
                    priority = "routine"
                
                category = rec_data.get("category", "monitoring")
                valid_categories = [
                    "follow_up", "intervention", "consultation", 
                    "additional_imaging", "monitoring"
                ]
                if category not in valid_categories:
                    category = "monitoring"
                
                title = rec_data.get("title", "Recommendation")
                description = rec_data.get("description", "")
                urgency = rec_data.get("urgency", "routine")
                if urgency not in ["immediate", "urgent", "routine", "elective"]:
                    urgency = "routine"
                
                timeframe = rec_data.get("timeframe")
                rationale = rec_data.get("rationale", "")
                
                recommendation = Recommendation(
                    id=rec_id,
                    priority=priority,
                    category=category,
                    title=title,
                    description=description,
                    urgency=urgency,
                    timeframe=timeframe,
                    rationale=rationale
                )
                recommendations.append(recommendation)
            except Exception as e:
                logger.warning(f"Failed to parse recommendation {idx}: {e}")
                continue
        
        # Parse differential_diagnosis
        differential_diagnosis = parsed_response.get("differential_diagnosis", [])
        if not isinstance(differential_diagnosis, list):
            differential_diagnosis = []
        
        # Create response
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
            overall_summary=overall_summary,
            findings=findings,
            recommendations=recommendations,
            differential_diagnosis=differential_diagnosis
        )

# Singleton instance
_service_instance: Optional[MedicalImageAnalysisService] = None


def get_medical_image_analysis_service() -> MedicalImageAnalysisService:
    """Get singleton instance of OpenAI service"""
    global _service_instance
    if _service_instance is None:
        _service_instance = MedicalImageAnalysisService()
    return _service_instance
