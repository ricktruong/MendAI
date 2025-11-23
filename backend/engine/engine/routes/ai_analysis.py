"""
AI Analysis API Endpoints
Handles AI-powered analysis of CT scan images using OpenAI
"""
from fastapi import APIRouter, HTTPException
import httpx
import os
import structlog

from common.types.ai_analysis import (
    SliceAnalysisRequest,
    SliceAnalysisResponse,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
)

router = APIRouter(prefix="/ai-analysis", tags=["ai-analysis"])
logger = structlog.get_logger()

# Medical Imaging service configuration
MEDICAL_IMAGING_URL = os.getenv("MEDICAL_IMAGING_URL", "http://medical_imaging:8002")

@router.post("/slice", response_model=SliceAnalysisResponse)
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
        logger.info(f"Forwarding slice analysis request to medical_imaging service at {MEDICAL_IMAGING_URL}/api/v0/analysis/slice")
        
        async with httpx.AsyncClient(timeout=120.0) as client:  # Increased timeout for AI processing
            response = await client.post(
                f"{MEDICAL_IMAGING_URL}/api/v0/analysis/slice",
                json=request.model_dump()
            )
            
            if response.status_code == 200:
                return SliceAnalysisResponse(**response.json())
            else:
                error_detail = response.text
                logger.error(f"Medical imaging service returned status {response.status_code}: {error_detail}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Medical imaging service error: {error_detail}"
                )

    except httpx.TimeoutException:
        logger.error("Timeout waiting for medical imaging service response")
        raise HTTPException(
            status_code=504,
            detail="The medical imaging service is taking too long to respond. Please try again."
        )
    except httpx.ConnectError as e:
        logger.error(f"Cannot connect to medical imaging service at {MEDICAL_IMAGING_URL}: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to medical imaging service at {MEDICAL_IMAGING_URL}. Please ensure the service is running."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calling medical imaging service: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Slice analysis failed: {str(e)}"
        )


@router.post("/batch", response_model=BatchAnalysisResponse)
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

        logger.info(f"Forwarding batch analysis request to medical_imaging service at {MEDICAL_IMAGING_URL}/api/v0/analysis/batch")
                
        async with httpx.AsyncClient(timeout=300.0) as client:  # Longer timeout for batch processing
            response = await client.post(
                f"{MEDICAL_IMAGING_URL}/api/v0/analysis/batch",
                json=request.model_dump()
            )
            
            if response.status_code == 200:
                return BatchAnalysisResponse(**response.json())
            else:
                error_detail = response.text
                logger.error(f"Medical imaging service returned status {response.status_code}: {error_detail}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Medical imaging service error: {error_detail}"
                )

    except httpx.TimeoutException:
        logger.error("Timeout waiting for medical imaging service response")
        raise HTTPException(
            status_code=504,
            detail="The medical imaging service is taking too long to respond. Please try again."
        )
    except httpx.ConnectError as e:
        logger.error(f"Cannot connect to medical imaging service at {MEDICAL_IMAGING_URL}: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to medical imaging service at {MEDICAL_IMAGING_URL}. Please ensure the service is running."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calling medical imaging service: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch analysis failed: {str(e)}"
        )
