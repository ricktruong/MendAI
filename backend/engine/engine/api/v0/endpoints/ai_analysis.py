"""
AI Analysis API Endpoints
Handles AI-powered analysis of CT scan images using OpenAI
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from common.types.ai_analysis import (
    SliceAnalysisRequest,
    SliceAnalysisResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
)
from engine.services.openai_service import get_openai_service

router = APIRouter()

@router.post("/analysis/slice", response_model=SliceAnalysisResponse)
async def analyze_slice(request: SliceAnalysisRequest) -> SliceAnalysisResponse:
    """
    Analyze a single CT slice

    This endpoint provides real-time analysis of a single slice,
    useful for quick assessments while navigating through scans.

    Args:
        request: SliceAnalysisRequest with patient/file info and slice number

    Returns:
        SliceAnalysisResponse with structured findings

    Raises:
        HTTPException: If analysis fails
    """
    try:
        service = get_openai_service()

        # Note: total_slices should be fetched from file metadata
        # For now, using a placeholder value
        total_slices = 150  # TODO: Get from file metadata

        result = service.analyze_single_slice(
            patient_id=request.patient_id,
            file_id=request.file_id,
            slice_number=request.slice_number,
            total_slices=total_slices,
            image_data=request.image_data
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Slice analysis failed: {str(e)}"
        )


@router.post("/analysis/batch", response_model=BatchAnalysisResponse)
async def analyze_batch(request: BatchAnalysisRequest) -> BatchAnalysisResponse:
    """
    Analyze multiple CT slices (batch analysis)

    This endpoint provides comprehensive analysis of a range of slices,
    useful for generating detailed reports and clinical recommendations.

    Args:
        request: BatchAnalysisRequest with slice range and file info

    Returns:
        BatchAnalysisResponse with comprehensive findings and recommendations

    Raises:
        HTTPException: If analysis fails
    """
    try:
        # Validate slice range
        if request.slice_start < 1:
            raise HTTPException(
                status_code=400,
                detail="slice_start must be >= 1"
            )

        if request.slice_end < request.slice_start:
            raise HTTPException(
                status_code=400,
                detail="slice_end must be >= slice_start"
            )

        # Get file information
        # TODO: Fetch actual file name from database
        file_name = f"CT_Scan_{request.file_id}.nii"

        service = get_openai_service()

        result = service.analyze_batch(
            patient_id=request.patient_id,
            file_id=request.file_id,
            file_name=file_name,
            slice_start=request.slice_start,
            slice_end=request.slice_end,
            image_slices=request.image_slices
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch analysis failed: {str(e)}"
        )


@router.get("/analysis/slice/{patient_id}/{file_id}/{slice_number}",
            response_model=SliceAnalysisResponse)
async def get_slice_analysis(
    patient_id: str,
    file_id: str,
    slice_number: int,
    total_slices: Optional[int] = Query(None, description="Total slices in scan")
) -> SliceAnalysisResponse:
    """
    Get analysis for a specific slice (GET endpoint for convenience)

    Args:
        patient_id: Patient identifier
        file_id: File identifier
        slice_number: Slice number to analyze
        total_slices: Total slices in the scan (optional)

    Returns:
        SliceAnalysisResponse with findings
    """
    try:
        print(f"Getting slice analysis for patient {patient_id}, file {file_id}, slice {slice_number}")
        service = get_openai_service()

        # Use provided total_slices or default
        if total_slices is None:
            total_slices = 150  # TODO: Get from file metadata

        result = service.analyze_single_slice(
            patient_id=patient_id,
            file_id=file_id,
            slice_number=slice_number,
            total_slices=total_slices
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Slice analysis failed: {str(e)}"
        )


@router.get("/analysis/batch/{patient_id}/{file_id}",
            response_model=BatchAnalysisResponse)
async def get_batch_analysis(
    patient_id: str,
    file_id: str,
    slice_start: int = Query(..., description="Starting slice number"),
    slice_end: int = Query(..., description="Ending slice number")
) -> BatchAnalysisResponse:
    """
    Get batch analysis for a range of slices (GET endpoint)

    Args:
        patient_id: Patient identifier
        file_id: File identifier
        slice_start: Starting slice number
        slice_end: Ending slice number

    Returns:
        BatchAnalysisResponse with comprehensive analysis
    """
    try:
        # Validate
        if slice_start < 1:
            raise HTTPException(status_code=400, detail="slice_start must be >= 1")
        if slice_end < slice_start:
            raise HTTPException(status_code=400, detail="slice_end must be >= slice_start")

        # Get file info
        file_name = f"CT_Scan_{file_id}.nii"  # TODO: Get from database

        service = get_openai_service()

        result = service.analyze_batch(
            patient_id=patient_id,
            file_id=file_id,
            file_name=file_name,
            slice_start=slice_start,
            slice_end=slice_end
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch analysis failed: {str(e)}"
        )
