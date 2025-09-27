# patient_data/routes/patients.py

from fastapi import APIRouter, HTTPException
from patient_data.services.fhir_service import (
    get_fhir_resource,
    get_patient_subject_ids,
    get_encounter_centric_patient_bundle,
    normalize_fhir_bundle
)
import json

router = APIRouter()

def extract_field_summary(bundle: dict) -> dict:
    """
    Generate a dictionary summarizing the top-level fields available 
    in each resource type within a FHIR bundle.

    Useful for debugging or schema exploration.
    """
    summary = {}
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        rtype = resource.get("resourceType")
        if not rtype:
            continue
        if rtype not in summary:
            summary[rtype] = set()
        summary[rtype].update(resource.keys())

    # Convert sets to sorted lists for readability
    for rtype in summary:
        summary[rtype] = sorted(summary[rtype])
    return summary


def save_bundle_to_file(bundle, filename="debug_patient_bundle.json"):
    """
    Save a given FHIR bundle (or normalized structure) to a local JSON file.
    Used primarily for debugging purposes.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2)

# ------------------------
# Patient Data Endpoints
# ------------------------
@router.get("/patients/subject_ids")
def list_subject_ids():
    """
    List all available patient subject IDs in the FHIR store.
    
    Returns:
        dict: A dictionary containing a list of subject IDs.
    """
    try:
        ids = get_patient_subject_ids()
        return {"subject_ids": ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patients/{patient_id}")
def get_patient(patient_id: str):
    """
    Get the raw FHIR Patient resource for a given patient ID.
    
    Args:
        patient_id (str): The subject ID of the patient.
    
    Returns:
        dict: The raw Patient resource.
    """
    try:
        return get_fhir_resource("Patient", patient_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patients/{patient_id}/full")
def get_full_patient_bundle(patient_id: str):
    """
    Fetch the full encounter-centric FHIR bundle for a given patient.
    Includes all associated resources like observations, meds, encounters.

    Args:
        patient_id (str): The subject ID of the patient.
    
    Returns:
        dict: The raw FHIR Bundle.
    """
    try:
        bundle = get_encounter_centric_patient_bundle(patient_id)
        save_bundle_to_file(bundle)  # Optional debug dump
        return bundle
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patients/{patient_id}/fields")
def get_bundle_fields(patient_id: str):
    """
    Get a summary of top-level fields in each resource of the full patient bundle.

    Args:
        patient_id (str): The subject ID of the patient.
    
    Returns:
        dict: Dictionary mapping resourceType -> list of top-level fields.
    """
    try:
        full_bundle = get_encounter_centric_patient_bundle(patient_id)
        return extract_field_summary(full_bundle)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patients/{patient_id}/normalized")
def get_normalized_patient_view(patient_id: str):
    """
    Get a normalized JSON representation of a patient's data.
    Output is grouped by encounter and designed for easier consumption by frontend & LLMs.

    Args:
        patient_id (str): The subject ID of the patient.
    
    Returns:
        dict: Normalized patient data including encounters, meds, observations, etc.
    """
    try:
        bundle = get_encounter_centric_patient_bundle(patient_id)
        normalized = normalize_fhir_bundle(bundle)
        save_bundle_to_file(normalized, "normalized_patient.json") # Optional debug dump
        return normalized
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

