from fastapi import APIRouter, HTTPException
from patient_data.services.fhir_service import get_conditions_for_patient

router = APIRouter()

@router.get("/patients/{patient_id}/conditions")
def get_conditions(patient_id: str):
    """Get all Conditions linked to a patient."""
    try:
        results = get_conditions_for_patient(patient_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
