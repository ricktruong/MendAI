from fastapi import APIRouter, HTTPException
from patient_data.services.fhir_service import search_fhir_resource

router = APIRouter()

@router.get("/patients/{patient_id}/medications")
def get_medications(patient_id: str):
    """
    Get all MedicationAdministrations for a patient.
    """
    try:
        results = search_fhir_resource("MedicationAdministration", {"patient": patient_id})
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
