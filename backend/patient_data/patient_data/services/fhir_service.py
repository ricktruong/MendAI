import os
import requests
from typing import Dict, Any, List, Optional
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime, timedelta

# Load environment variables from .env
load_dotenv()

# -------------------------------
# Environment Config
# -------------------------------
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_LOCATION")
DATASET_ID = os.getenv("GCP_DATASET_ID")
FHIR_STORE_ID = os.getenv("GCP_FHIR_STORE_ID")
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

FHIR_BASE_URL = (
    f"https://healthcare.googleapis.com/v1/projects/{PROJECT_ID}"
    f"/locations/{LOCATION}/datasets/{DATASET_ID}/fhirStores/{FHIR_STORE_ID}/fhir"
)

REQUEST_TIMEOUT = 30  # Timeout for FHIR API requests

# -------------------------------
# Cache Configuration
# -------------------------------
_patient_bundle_cache = {}  # Stores full patient bundles
_patient_list_cache = None  # Stores list of patient IDs
_cache_timestamps = {}  # Tracks when data was cached
CACHE_DURATION_MINUTES = 10  # Cache duration
_patient_list_cache_time = None

def _is_cache_valid(patient_id: str) -> bool:
    """Check if cached data for this patient is still valid."""
    if patient_id not in _cache_timestamps:
        return False
    
    cache_time = _cache_timestamps[patient_id]
    elapsed = datetime.now() - cache_time
    return elapsed < timedelta(minutes=CACHE_DURATION_MINUTES)

def _is_patient_list_cache_valid() -> bool:
    """Check if cached patient list is still valid."""
    if _patient_list_cache_time is None:
        return False
    
    elapsed = datetime.now() - _patient_list_cache_time
    return elapsed < timedelta(minutes=CACHE_DURATION_MINUTES)

def clear_cache(patient_id: Optional[str] = None):
    """Clear cache for specific patient or all patients."""
    global _patient_bundle_cache, _cache_timestamps, _patient_list_cache, _patient_list_cache_time
    
    if patient_id:
        _patient_bundle_cache.pop(patient_id, None)
        _cache_timestamps.pop(patient_id, None)
        print(f"✓ Cleared cache for patient {patient_id}")
    else:
        _patient_bundle_cache.clear()
        _cache_timestamps.clear()
        _patient_list_cache = None
        _patient_list_cache_time = None
        print("✓ Cleared all cache")

def get_cache_stats() -> Dict:
    """Get cache statistics."""
    total_cached = len(_patient_bundle_cache)
    valid_cache = sum(1 for pid in _cache_timestamps if _is_cache_valid(pid))
    
    return {
        "total_cached_patients": total_cached,
        "valid_cached_patients": valid_cache,
        "expired_cached_patients": total_cached - valid_cache,
        "cache_duration_minutes": CACHE_DURATION_MINUTES,
        "cached_patient_ids": list(_patient_bundle_cache.keys()),
        "patient_list_cached": _patient_list_cache is not None,
        "patient_list_valid": _is_patient_list_cache_valid()
    }

# -------------------------------
# Google Authentication
# -------------------------------
def get_google_auth_token():
    """Get OAuth token for Google Healthcare API."""
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=["https://www.googleapis.com/auth/cloud-healthcare"]
    )
    credentials.refresh(Request())
    return credentials.token

# -------------------------------
# Core FHIR Functions
# -------------------------------
def get_fhir_resource(resource_type: str, resource_id: str):
    """Fetch a single FHIR resource by type and ID."""
    url = f"{FHIR_BASE_URL}/{resource_type}/{resource_id}"
    
    token = get_google_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/fhir+json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise Exception(f"Request timed out after {REQUEST_TIMEOUT} seconds")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"FHIR API Error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        raise Exception(f"Error fetching {resource_type}/{resource_id}: {str(e)}")

def search_fhir_resource(resource_type: str, params: Dict[str, Any] = None):
    """Search for FHIR resources with query parameters."""
    url = f"{FHIR_BASE_URL}/{resource_type}"
    
    token = get_google_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/fhir+json"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise Exception(f"Search request timed out after {REQUEST_TIMEOUT} seconds")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"FHIR Search Error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        raise Exception(f"Error searching {resource_type}: {str(e)}")

def unwrap_bundle(bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract resources from a FHIR Bundle."""
    if not bundle or "entry" not in bundle:
        return []
    return [entry["resource"] for entry in bundle.get("entry", [])]

# -------------------------------
# Patient Data Functions (WITH CACHING)
# -------------------------------
def get_patient_subject_ids() -> List[str]:
    """
    Get all patient subject IDs from the FHIR store.
    WITH CACHING for patient list.
    """
    global _patient_list_cache, _patient_list_cache_time
    
    # Check cache
    if _is_patient_list_cache_valid():
        print(f"✓ [CACHE HIT] Returning cached patient list ({len(_patient_list_cache)} patients)")
        return _patient_list_cache
    
    print("⟳ [CACHE MISS] Fetching patient list from FHIR...")
    
    try:
        # Fetch all patients (paginate if needed)
        all_patient_ids = []
        params = {"_count": "500"}  # Increased from 100 to 500 to reduce pagination issues

        while True:
            try:
                bundle = search_fhir_resource("Patient", params)
                patient_ids = [
                    resource.get("id")
                    for resource in unwrap_bundle(bundle)
                    if resource.get("id")
                ]
                all_patient_ids.extend(patient_ids)

                # Check for next page
                next_link = None
                for link in bundle.get("link", []):
                    if link.get("relation") == "next":
                        next_link = link.get("url")
                        break

                if not next_link:
                    break

                # Extract page token for next request
                if "_page_token=" in next_link:
                    page_token = next_link.split("_page_token=")[1].split("&")[0]
                    params["_page_token"] = page_token
                else:
                    break

            except Exception as page_error:
                # If pagination fails (e.g., invalid_page_token), return what we have so far
                if "invalid_page_token" in str(page_error) or "page token" in str(page_error).lower():
                    print(f"⚠ Pagination stopped due to token error. Returning {len(all_patient_ids)} patients fetched so far.")
                    break
                else:
                    # For other errors, re-raise
                    raise

        # Cache the result
        _patient_list_cache = all_patient_ids
        _patient_list_cache_time = datetime.now()
        print(f"✓ [CACHED] Stored {len(all_patient_ids)} patient IDs (expires in {CACHE_DURATION_MINUTES} min)")

        return all_patient_ids

    except Exception as e:
        raise Exception(f"Error fetching patient IDs: {str(e)}")

def get_encounter_centric_patient_bundle(patient_id: str):
    """
    Fetch a comprehensive patient bundle including encounters and related resources.
    WITH CACHING - returns cached data if available and valid.
    """
    
    # CACHE CHECK - Return cached data if valid
    if _is_cache_valid(patient_id):
        print(f"✓ [CACHE HIT] Returning cached bundle for patient {patient_id}")
        return _patient_bundle_cache[patient_id]
    
    # CACHE MISS - Fetch fresh data
    print(f"⟳ [CACHE MISS] Fetching fresh data for patient {patient_id}...")
    
    try:
        # Get patient resource
        print(f"  [1/7] Fetching patient demographics...")
        patient = get_fhir_resource("Patient", patient_id)
        
        # Get encounters (limited to most recent)
        print(f"  [2/7] Fetching encounters...")
        encounters_bundle = search_fhir_resource("Encounter", {
            "patient": patient_id,
            "_count": "20"
        })
        encounters = unwrap_bundle(encounters_bundle)
        
        # Get observations (limited)
        print(f"  [3/7] Fetching observations...")
        observations_bundle = search_fhir_resource("Observation", {
            "patient": patient_id,
            "_count": "50",
            "_sort": "-date"
        })
        observations = unwrap_bundle(observations_bundle)
        
        # Get conditions
        print(f"  [4/7] Fetching conditions...")
        conditions_bundle = search_fhir_resource("Condition", {
            "patient": patient_id,
            "_count": "50"
        })
        conditions = unwrap_bundle(conditions_bundle)
        
        # Get medications
        print(f"  [5/7] Fetching medications...")
        medications_bundle = search_fhir_resource("MedicationRequest", {
            "patient": patient_id,
            "_count": "50"
        })
        medications = unwrap_bundle(medications_bundle)
        
        # Get allergies
        print(f"  [6/7] Fetching allergies...")
        allergies_bundle = search_fhir_resource("AllergyIntolerance", {
            "patient": patient_id
        })
        allergies = unwrap_bundle(allergies_bundle)
        
        # Get immunizations
        print(f"  [7/7] Fetching immunizations...")
        immunizations_bundle = search_fhir_resource("Immunization", {
            "patient": patient_id
        })
        immunizations = unwrap_bundle(immunizations_bundle)
        
        # Optional: Get procedures (commented out to save time)
        # procedures_bundle = search_fhir_resource("Procedure", {"patient": patient_id})
        # procedures = unwrap_bundle(procedures_bundle)
        procedures = []
        
        # Build comprehensive bundle
        all_resources = (
            [patient] + 
            encounters + 
            observations + 
            conditions + 
            medications + 
            allergies + 
            immunizations + 
            procedures
        )
        
        result = {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": len(all_resources),
            "entry": [{"resource": resource} for resource in all_resources if resource]
        }
        
        # STORE IN CACHE
        _patient_bundle_cache[patient_id] = result
        _cache_timestamps[patient_id] = datetime.now()
        print(f"✓ [CACHED] Stored bundle for patient {patient_id} ({len(all_resources)} resources, expires in {CACHE_DURATION_MINUTES} min)")
        
        return result
        
    except Exception as e:
        raise Exception(f"Error fetching patient bundle: {str(e)}")

# -------------------------------
# Normalization Functions
# -------------------------------
def normalize_fhir_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a FHIR bundle into a structured clinical data format.
    """
    resources = unwrap_bundle(bundle)
    
    # Organize resources by type
    resource_map = defaultdict(list)
    patient = None
    
    for resource in resources:
        resource_type = resource.get("resourceType")
        if resource_type == "Patient":
            patient = resource
        else:
            resource_map[resource_type].append(resource)
    
    if not patient:
        raise ValueError("No Patient resource found in bundle")
    
    # Extract patient demographics
    patient_data = {
        "id": patient.get("id"),
        "resourceType": "Patient",
        "name": extract_patient_name(patient),
        "birthDate": patient.get("birthDate"),
        "age": calculate_age(patient.get("birthDate")),
        "gender": patient.get("gender"),
        "maritalStatus": extract_codeable_concept(patient.get("maritalStatus")),
    }
    
    # Normalize clinical data
    patient_data["encounters"] = [
        normalize_encounter(enc) for enc in resource_map.get("Encounter", [])
    ]
    
    patient_data["observations"] = [
        normalize_observation(obs) for obs in resource_map.get("Observation", [])
    ]
    
    patient_data["conditions"] = [
        extract_codeable_concept(cond.get("code")) 
        for cond in resource_map.get("Condition", [])
    ]
    
    patient_data["medications"] = [
        extract_medication_info(med) 
        for med in resource_map.get("MedicationRequest", [])
    ]
    
    patient_data["allergies"] = [
        extract_codeable_concept(allergy.get("code")) 
        for allergy in resource_map.get("AllergyIntolerance", [])
    ]
    
    patient_data["immunizations"] = [
        extract_codeable_concept(imm.get("vaccineCode")) 
        for imm in resource_map.get("Immunization", [])
    ]
    
    patient_data["lastUpdated"] = datetime.now().isoformat()
    
    return patient_data

def extract_patient_name(patient: Dict) -> str:
    """Extract patient's full name."""
    names = patient.get("name", [])
    if names:
        name = names[0]
        family = name.get("family", "")
        given = " ".join(name.get("given", []))
        return f"{given} {family}".strip() or "Unknown"
    return "Unknown"

def calculate_age(birth_date: str) -> int:
    """Calculate age from birth date."""
    if not birth_date:
        return 0
    try:
        birth = datetime.strptime(birth_date, "%Y-%m-%d")
        today = datetime.now()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        return age
    except:
        return 0

def extract_codeable_concept(codeable_concept: Dict) -> str:
    """Extract display text from CodeableConcept."""
    if not codeable_concept:
        return "Unknown"
    
    if "text" in codeable_concept:
        return codeable_concept["text"]
    
    codings = codeable_concept.get("coding", [])
    if codings:
        return codings[0].get("display", "Unknown")
    
    return "Unknown"

def normalize_encounter(encounter: Dict) -> Dict:
    """Normalize encounter data."""
    return {
        "id": encounter.get("id"),
        "type": extract_codeable_concept(encounter.get("type", [{}])[0] if encounter.get("type") else {}),
        "status": encounter.get("status"),
        "date": encounter.get("period", {}).get("start"),
        "reason": extract_codeable_concept(encounter.get("reasonCode", [{}])[0] if encounter.get("reasonCode") else {})
    }

def normalize_observation(observation: Dict) -> Dict:
    """Normalize observation data."""
    value = observation.get("valueQuantity", {})
    
    return {
        "id": observation.get("id"),
        "code": extract_codeable_concept(observation.get("code")),
        "value": value.get("value"),
        "unit": value.get("unit"),
        "date": observation.get("effectiveDateTime") or observation.get("issued")
    }

def extract_medication_info(medication_request: Dict) -> Dict:
    """Extract medication information."""
    medication = medication_request.get("medicationCodeableConcept", {})
    dosage = medication_request.get("dosageInstruction", [{}])[0] if medication_request.get("dosageInstruction") else {}
    
    return {
        "name": extract_codeable_concept(medication),
        "dosage": dosage.get("text", ""),
        "frequency": dosage.get("timing", {}).get("code", {}).get("text", "")
    }

# -------------------------------
# MAIN CONVENIENCE FUNCTION - THIS WAS MISSING!
# -------------------------------
def get_patient_bundle_normalized(patient_id: str) -> Optional[Dict[str, Any]]:
    """
    Get patient data bundle and return in normalized format.
    This is a convenience function that combines fetching and normalization with caching.
    
    This is the PRIMARY function to use for getting patient data.
    
    Args:
        patient_id: FHIR patient identifier
        
    Returns:
        dict: Normalized patient data with all clinical resources
        None: If patient not found
    """
    try:
        # Check if we have normalized data cached
        normalized_cache_key = f"normalized:{patient_id}"
        
        if normalized_cache_key in _patient_bundle_cache and _is_cache_valid(patient_id):
            print(f"✓ [CACHE HIT] Returning cached normalized data for patient {patient_id}")
            return _patient_bundle_cache[normalized_cache_key]
        
        # Get raw bundle (this function has its own caching)
        bundle = get_encounter_centric_patient_bundle(patient_id)
        
        if not bundle:
            print(f"✗ Patient {patient_id} not found")
            return None
        
        # Normalize the bundle
        print(f"⟳ Normalizing bundle for patient {patient_id}...")
        normalized_data = normalize_fhir_bundle(bundle)
        
        # Cache the normalized result separately
        _patient_bundle_cache[normalized_cache_key] = normalized_data
        _cache_timestamps[patient_id] = datetime.now()
        
        print(f"✓ [CACHED] Normalized data for patient {patient_id} (expires in {CACHE_DURATION_MINUTES} min)")
        
        return normalized_data
        
    except Exception as e:
        print(f"✗ Error getting normalized patient data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# -------------------------------
# Legacy Helper Functions (for compatibility with other routes)
# -------------------------------
def get_observations_for_patient(patient_id: str):
    """Get all observations for a patient."""
    try:
        bundle = search_fhir_resource("Observation", {
            "patient": patient_id,
            "_count": "100",
            "_sort": "-date"
        })
        return unwrap_bundle(bundle)
    except Exception as e:
        raise Exception(f"Error fetching observations: {str(e)}")

def get_encounters_for_patient(patient_id: str):
    """Get all encounters for a patient."""
    try:
        bundle = search_fhir_resource("Encounter", {
            "patient": patient_id,
            "_count": "100"
        })
        return unwrap_bundle(bundle)
    except Exception as e:
        raise Exception(f"Error fetching encounters: {str(e)}")

def get_conditions_for_patient(patient_id: str):
    """Get all conditions for a patient."""
    try:
        bundle = search_fhir_resource("Condition", {
            "patient": patient_id,
            "_count": "100"
        })
        return unwrap_bundle(bundle)
    except Exception as e:
        raise Exception(f"Error fetching conditions: {str(e)}")

def get_medications_for_patient(patient_id: str):
    """Get all medication requests for a patient."""
    try:
        bundle = search_fhir_resource("MedicationRequest", {
            "patient": patient_id,
            "_count": "100"
        })
        return unwrap_bundle(bundle)
    except Exception as e:
        raise Exception(f"Error fetching medications: {str(e)}")

def get_allergies_for_patient(patient_id: str):
    """Get all allergies for a patient."""
    try:
        bundle = search_fhir_resource("AllergyIntolerance", {
            "patient": patient_id
        })
        return unwrap_bundle(bundle)
    except Exception as e:
        raise Exception(f"Error fetching allergies: {str(e)}")

def get_immunizations_for_patient(patient_id: str):
    """Get all immunizations for a patient."""
    try:
        bundle = search_fhir_resource("Immunization", {
            "patient": patient_id
        })
        return unwrap_bundle(bundle)
    except Exception as e:
        raise Exception(f"Error fetching immunizations: {str(e)}")

def get_procedures_for_patient(patient_id: str):
    """Get all procedures for a patient."""
    try:
        bundle = search_fhir_resource("Procedure", {
            "patient": patient_id
        })
        return unwrap_bundle(bundle)
    except Exception as e:
        raise Exception(f"Error fetching procedures: {str(e)}")