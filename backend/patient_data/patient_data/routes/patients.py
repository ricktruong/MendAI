from fastapi import APIRouter, HTTPException
from typing import List
from patient_data.services.fhir_service import (
    get_patient_subject_ids,
    get_fhir_resource,
    get_encounter_centric_patient_bundle,
    normalize_fhir_bundle,
    get_cache_stats,
    clear_cache
)

router = APIRouter()

# -------------------------------
# Patient Endpoints
# -------------------------------
@router.get("/patients/subject_ids")
def list_patient_ids():
    """Get all patient IDs from FHIR store (with caching)."""
    try:
        patient_ids = get_patient_subject_ids()
        return {
            "patient_ids": patient_ids,
            "total_count": len(patient_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patients/{patient_id}")
def get_patient(patient_id: str):
    """Get basic patient demographics."""
    try:
        patient = get_fhir_resource("Patient", patient_id)
        return patient
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/patients/{patient_id}/bundle")
def get_patient_bundle(patient_id: str):
    """Get comprehensive patient bundle (with caching)."""
    try:
        bundle = get_encounter_centric_patient_bundle(patient_id)
        return bundle
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patients/{patient_id}/normalized")
def get_normalized_patient(patient_id: str):
    """Get normalized patient clinical data (with caching)."""
    try:
        bundle = get_encounter_centric_patient_bundle(patient_id)
        normalized = normalize_fhir_bundle(bundle)
        return normalized
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------
# Cache Management Endpoints
# -------------------------------
@router.get("/cache/stats")
def get_cache_statistics():
    """Get comprehensive cache statistics."""
    from patient_data.services.openai_service import get_ai_cache_stats
    
    fhir_cache = get_cache_stats()
    ai_cache = get_ai_cache_stats()
    
    return {
        "fhir_cache": fhir_cache,
        "ai_cache": ai_cache,
        "summary": {
            "total_cached_patients": fhir_cache["total_cached_patients"],
            "total_cached_ai_responses": ai_cache["total_cached_responses"],
            "cache_hit_rate": "N/A (tracking not implemented)",
            "estimated_cost_savings": "N/A"
        }
    }

@router.post("/cache/clear")
def clear_all_cache():
    """Clear all cached data (FHIR + AI)."""
    from patient_data.services.openai_service import clear_ai_cache
    
    clear_cache()  # Clear FHIR cache
    clear_ai_cache()  # Clear AI cache
    
    return {
        "message": "All caches cleared successfully",
        "fhir_cache_cleared": True,
        "ai_cache_cleared": True
    }

@router.delete("/cache/patient/{patient_id}")
def clear_patient_cache(patient_id: str):
    """Clear cache for a specific patient."""
    clear_cache(patient_id)
    
    return {
        "message": f"Cache cleared for patient {patient_id}",
        "patient_id": patient_id
    }

@router.post("/cache/warmup")
def warmup_cache(patient_ids: List[str]):
    """Pre-warm cache for multiple patients (useful before demos)."""
    results = []
    
    for patient_id in patient_ids:
        try:
            bundle = get_encounter_centric_patient_bundle(patient_id)
            results.append({
                "patient_id": patient_id,
                "status": "cached",
                "resource_count": bundle.get("total", 0)
            })
        except Exception as e:
            results.append({
                "patient_id": patient_id,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "message": f"Cache warmup completed for {len(patient_ids)} patients",
        "results": results
    }