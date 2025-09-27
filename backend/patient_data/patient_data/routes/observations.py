from fastapi import APIRouter, HTTPException
from patient_data.services.fhir_service import get_observations_for_patient

router = APIRouter()

@router.get("/patients/{patient_id}/observations")
def get_observations(patient_id: str, code: str = None):
    """
    Get all Observations for a patient.
    Optionally filter by LOINC/SNOMED code (e.g., 8310-5 for body temperature).
    """
    try:
        results = get_observations_for_patient(patient_id, code)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
