from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from common.types.ai_analysis import (
    SliceAnalysisRequest,
    SliceAnalysisResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
)
from ..services.analysis import get_medical_image_analysis_service

router = APIRouter(prefix="/v0")


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
        service = get_medical_image_analysis_service()

        # Note: total_slices should be fetched from file metadata
        # For now, using a placeholder value
        total_slices = 150  # TODO: Get from file metadata

        result = service.analyze_slice(
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

        service = get_medical_image_analysis_service()

        result = service.analyze_batch(
            patient_id=request.patient_id,
            file_id=request.file_id,
            file_name=file_name,
            slice_start=request.slice_start,
            slice_end=request.slice_end,
            step_size=request.step_size,
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
