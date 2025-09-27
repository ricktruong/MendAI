from fastapi import APIRouter, HTTPException
from patient_data.services.fhir_service import get_encounters_for_patient

router = APIRouter()

@router.get("/patients/{patient_id}/encounters")
def get_encounters(patient_id: str):
    """Get all Encounters linked to a patient."""
    try:
        results = get_encounters_for_patient(patient_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
