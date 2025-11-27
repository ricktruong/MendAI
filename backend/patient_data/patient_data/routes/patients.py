"""
patients.py

This FastAPI router defines endpoints for accessing and managing patient data
from a FHIR store, including demographic details, full clinical bundles,
normalized views, and imaging data. It also exposes routes for inspecting and
managing cache behavior used for performance optimization.

Endpoints rely on the fhir_service and openai_service modules.
"""

from fastapi import APIRouter, HTTPException
from typing import List
from patient_data.services.fhir_service import (
    get_patient_subject_ids,
    get_fhir_resource,
    get_encounter_centric_patient_bundle,
    get_all_patient_conditions,
    normalize_fhir_bundle,
    get_cache_stats,
    get_imaging_files_for_patient,
    clear_cache
)

router = APIRouter()

# -------------------------------
# Patient Endpoints
# -------------------------------
@router.get("/patients/subject_ids")
def list_patient_ids():
    """
    Retrieve all patient IDs from the FHIR store.

    Returns:
        dict: Contains a list of patient IDs and total count.
    """
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
    """
    Retrieve the basic FHIR Patient resource for a given patient ID.

    Args:
        patient_id (str): The unique FHIR patient ID.

    Returns:
        dict: FHIR Patient resource.
    """
    try:
        patient = get_fhir_resource("Patient", patient_id)
        return patient
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/patients/{patient_id}/bundle")
def get_patient_bundle(patient_id: str):
    """
    Fetch a comprehensive bundle of all FHIR resources for the patient.

    Includes patient, encounters, observations, medications, and conditions.

    Args:
        patient_id (str): The unique FHIR patient ID.

    Returns:
        dict: FHIR Bundle.
    """
    try:
        bundle = get_encounter_centric_patient_bundle(patient_id)
        return bundle
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patients/{patient_id}/normalized")
def get_normalized_patient(patient_id: str):
    """
    Return a simplified, normalized version of a patient’s clinical data.

    This view combines raw FHIR data into a cleaner structure with
    demographics, conditions, medications, and imaging.

    Args:
        patient_id (str): FHIR patient ID.

    Returns:
        dict: Normalized patient data.
    """
    try:
        bundle = get_encounter_centric_patient_bundle(patient_id)
        normalized = normalize_fhir_bundle(bundle)
        return normalized
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fhir/conditions")
def api_get_all_conditions():
    """
    Return all patient conditions across the FHIR store.

    Returns:
        list of dict: Each dict contains patient_id and condition list.
    """
    return get_all_patient_conditions()

@router.get("/patients/{patient_id}/imaging")
def get_patient_imaging_files(patient_id: str):
    """
    Retrieve all imaging files (e.g. NIfTI .nii files) for a patient from GCS.

    Args:
        patient_id (str): Patient FHIR ID.

    Returns:
        dict: Contains patient_id, file count, and list of file URLs.
    """
    try:
        files = get_imaging_files_for_patient(patient_id)

        if not files:
            raise HTTPException(status_code=404, detail="No imaging files found for this patient.")

        return {
            "patient_id": patient_id,
            "file_count": len(files),
            "files": files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------
# Cache Management Endpoints
# -------------------------------
@router.get("/cache/stats")
def get_cache_statistics():
    """
    Returns current cache statistics for both FHIR and AI subsystems.

    Useful for debugging and monitoring cache effectiveness.

    Returns:
        dict: Cache details including counts and health.
    """
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
    """
    Clears all application-level caches, including FHIR and OpenAI-related data.

    Returns:
        dict: Confirmation message.
    """
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
    """
    Clears all cache for a specific patient.

    Args:
        patient_id (str): FHIR Patient ID.

    Returns:
        dict: Confirmation of cache clearing.
    """
    clear_cache(patient_id)
    
    return {
        "message": f"Cache cleared for patient {patient_id}",
        "patient_id": patient_id
    }

@router.post("/cache/warmup")
def warmup_cache(patient_ids: List[str]):
    """
    Pre-loads cache for the provided list of patient IDs.

    Useful for demos or performance testing where initial latency should be avoided.

    Args:
        patient_ids (List[str]): List of FHIR patient IDs to warm up.

    Returns:
        dict: Summary and per-patient status of cache warming.
    """
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