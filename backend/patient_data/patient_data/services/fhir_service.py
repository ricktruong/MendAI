"""
FHIR Service Module for GCP Healthcare API

This module provides a set of utilities to:
- Authenticate with Google Cloud using service accounts
- Query and retrieve FHIR resources (Patient, Condition, Encounter, etc.)
- Normalize FHIR bundles into simplified, structured Python dictionaries
- Cache data in-memory to minimize redundant API calls
- Fetch imaging data (e.g., NIfTI files) from Google Cloud Storage
"""

import os
import traceback
import requests
from typing import Dict, Any, List, Optional
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.cloud import storage
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
_gcs_imaging_cache = {}
_imaging_cache_timestamps = {}
_cache_timestamps = {}  # Tracks when data was cached
CACHE_DURATION_MINUTES = 30  # Cache duration
_patient_list_cache_time = None

def _is_cache_valid(patient_id: str) -> bool:
    """Check whether cached data for a given patient is still valid"""
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
    """Authenticate using service account credentials and return a valid OAuth token
    for Google Healthcare API requests."""
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
    """
    Fetch a single FHIR resource from the FHIR store.

    Args:
        resource_type (str): The type of FHIR resource (e.g., "Patient").
        resource_id (str): The ID of the FHIR resource.

    Returns:
        dict: JSON representation of the FHIR resource.
    """
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
    """
    Search the FHIR store for resources using query parameters.

    Args:
        resource_type (str): FHIR resource type to search.
        params (dict): Query parameters to use in search.

    Returns:
        dict: FHIR search bundle containing matched resources.
    """
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
    Retrieve all patient IDs from the FHIR store.

    Uses caching to avoid redundant requests.

    Returns:
        List[str]: List of patient FHIR resource IDs.
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
        params = {"_count": "100"}

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
                traceback.print_exc()
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
    Fetch a comprehensive FHIR bundle for a patient, including related
    encounters, observations, medications, and conditions.

    Returns:
        dict: Full FHIR bundle with patient context.
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
        
        # Get medication administrations
        print(f"  [5/7] Fetching medication administrations...")
        medications_bundle = search_fhir_resource("MedicationAdministration", {
            "patient": patient_id,
            "_count": "50"
        })
        medications = unwrap_bundle(medications_bundle)

        # Optional: Get procedures (commented out to save time)
        #procedures_bundle = search_fhir_resource("Procedure", {"subject": f"Patient/{patient_id}"})
        #procedures = unwrap_bundle(procedures_bundle)

        # Build comprehensive bundle
        all_resources = (
            [patient] + 
            encounters + 
            observations + 
            conditions + 
            medications  
            #procedures
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

def get_imaging_files_for_patient(patient_id: str) -> List[str]:
    """
    Get list of NIfTI imaging file URLs stored in GCS for a specific patient.

    Filters out directory-level blobs.

    Args:
        patient_id (str): FHIR patient ID.

    Returns:
        List[str]: List of GCS URLs for imaging files.
    """
    if patient_id in _gcs_imaging_cache and _is_cache_valid(patient_id):
        print(f"✓ [CACHE HIT] Imaging for {patient_id}")
        return _gcs_imaging_cache[patient_id]

    bucket_name = "mendai_ct_images"
    prefix = f"Patient/{patient_id}/"

    try:
        client = storage.Client.from_service_account_json(CREDENTIALS_PATH)
        bucket = client.bucket(bucket_name)
        blobs = list(bucket.list_blobs(prefix=prefix))

        imaging_files = [
            f"https://storage.googleapis.com/{bucket_name}/{blob.name}"
            for blob in blobs
            if not blob.name.endswith("/")
        ]

        _gcs_imaging_cache[patient_id] = imaging_files
        _cache_timestamps[patient_id] = datetime.now()

        return imaging_files
    except Exception as e:
        raise Exception(f"Failed to fetch imaging files: {str(e)}")

# -------------------------------
# Normalization Functions
# -------------------------------
def normalize_fhir_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a FHIR bundle into a simplified, normalized dictionary structure.
    Includes demographic data, clinical resources, and GCS imaging URLs.

    Args:
        bundle (dict): Raw FHIR Bundle.

    Returns:
        dict: Normalized patient clinical summary.
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
        "birthDate": correct_fhir_date(patient.get("birthDate")),
        "age": calculate_age(patient.get("birthDate")),
        "gender": patient.get("gender"),
        "maritalStatus": extract_marital_status(patient),
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
        normalize_medication_administration(med) 
        for med in resource_map.get("MedicationAdministration", [])
    ]

    # Add imaging files (GCS lookup)
    patient_data["imaging"] = get_imaging_files_for_patient(patient.get("id"))

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

def correct_fhir_date(date_str: str, is_datetime: bool = False) -> str:
    """
    Correct FHIR dates that are shifted by approximately 78 years into the future.
    This appears to be an issue with synthetic/test data in the FHIR store.
    
    Some dates require multiple corrections (e.g., 2118 -> 2040 -> 1962).
    We keep subtracting 78 years until the date is no longer in the future.
    
    Args:
        date_str: Date string in format "YYYY-MM-DD" or ISO datetime
        is_datetime: True if the string includes time information
    """
    if not date_str:
        return date_str
    try:
        # Handle datetime strings (e.g., "2112-10-11T21:37:35-04:00")
        if 'T' in date_str or is_datetime:
            # Parse ISO format datetime
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            # Keep subtracting 78 years until date is in the past
            while date_obj.year > datetime.now().year:
                date_obj = date_obj.replace(year=date_obj.year - 78)
            return date_obj.isoformat()
        else:
            # Handle simple date strings (e.g., "2043-02-11")
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            # Keep subtracting 78 years until date is in the past
            while date_obj.year > datetime.now().year:
                date_obj = date_obj.replace(year=date_obj.year - 78)
            return date_obj.strftime("%Y-%m-%d")
    except:
        return date_str

def calculate_age(birth_date: str) -> int:
    """Calculate age from birth date."""
    if not birth_date:
        return 0
    try:
        # Correct the date first if needed
        corrected_date = correct_fhir_date(birth_date)
        birth = datetime.strptime(corrected_date, "%Y-%m-%d")
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

def normalize_encounter(encounter: dict) -> dict:
    """Normalize Encounter data with key clinical context (minimal version)."""
    # Extract type
    type_display = "Unknown"
    if "type" in encounter and encounter["type"]:
        codings = encounter["type"][0].get("coding", [])
        if codings:
            type_display = codings[0].get("display", codings[0].get("code", "Unknown"))

    # Extract class
    encounter_class = encounter.get("class", {}).get("display", encounter.get("class", {}).get("code", "Unknown"))

    # Extract admit source
    admit_source_display = "Unknown"
    if "hospitalization" in encounter and "admitSource" in encounter["hospitalization"]:
        coding = encounter["hospitalization"]["admitSource"].get("coding", [])
        if coding:
            admit_source_display = coding[0].get("display", coding[0].get("code", "Unknown"))

    return {
        "type": type_display,
        "class": encounter_class,
        "status": encounter.get("status"),
        "admitSource": admit_source_display,
        "date": correct_fhir_date(encounter.get("period", {}).get("start"), is_datetime=True),
    }


def normalize_observation(observation: Dict) -> Dict:
    """Normalize observation data."""
    value = observation.get("valueQuantity", {})
    
    obs_date = observation.get("effectiveDateTime") or observation.get("issued")
    
    return {
        "id": observation.get("id"),
        "code": extract_codeable_concept(observation.get("code")),
        "value": value.get("value"),
        "unit": value.get("unit"),
        "date": correct_fhir_date(obs_date, is_datetime=True) if obs_date else None
    }

def normalize_procedure(proc: Dict) -> Dict:
    code = proc.get("code", {}).get("coding", [{}])[0]
    performed = proc.get("performedDateTime") or proc.get("performedPeriod", {}).get("start")
    return {
        "id": proc.get("id"),
        "code": code.get("code"),
        "description": code.get("display"),
        "status": proc.get("status"),
        "date": performed
    }

def normalize_medication_administration(med: Dict) -> Dict:
    """
    Format a MedicationAdministration FHIR resource into a simplified structure.

    Args:
        med (dict): FHIR resource of type MedicationAdministration.

    Returns:
        dict: Formatted data with name, dosage, method, and time.
    """
    medication = med.get("medicationCodeableConcept", {})
    dosage = med.get("dosage", {})
    dose_info = dosage.get("dose", {})
    method = dosage.get("method", {})

    # Format dosage as "value unit", e.g., "18.80 units"
    value = dose_info.get("value")
    unit = dose_info.get("unit", "")
    if isinstance(value, (int, float)):
        value_str = f"{value:.2f}".rstrip("0").rstrip(".")
        dosage_str = f"{value_str} {unit}".strip()
    else:
        dosage_str = unit or "Unknown"

    return {
        "id": med.get("id"),
        "name": extract_codeable_concept(medication),  # e.g., "Acetaminophen-IV"
        "dosage": dosage_str,                          # e.g., "18.8 units"
        "method": method.get("coding", [{}])[0].get("code", "Unknown"),    # e.g., "Continuous Med"
        "status": med.get("status"),
        "effectiveTime": correct_fhir_date(med.get("effectiveDateTime") or med.get("effectivePeriod", {}).get("start"))
    }

def get_all_patient_conditions() -> List[Dict[str, Any]]:
    """
    Fetch all conditions across all patients in the FHIR store.
    Returns:
        List of dicts: [{patient_id, conditions: [text]}]
    """
    all_conditions = []
    patient_ids = get_patient_subject_ids()

    print(f"⟳ Fetching conditions for {len(patient_ids)} patients...")

    for patient_id in patient_ids:
        try:
            conditions = get_conditions_for_patient(patient_id)
            condition_texts = [extract_codeable_concept(cond.get("code")) for cond in conditions]
            all_conditions.append({
                "patient_id": patient_id,
                "conditions": condition_texts
            })
        except Exception as e:
            print(f"⚠ Failed to fetch conditions for patient {patient_id}: {str(e)}")

    print(f"✓ Fetched condition data for {len(all_conditions)} patients")
    return all_conditions

# -------------------------------
# MAIN CONVENIENCE FUNCTION 
# -------------------------------
def get_patient_bundle_normalized(patient_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch and normalize a patient's data including demographics, encounters,
    observations, conditions, medications, and imaging data.

    Uses internal caching to improve performance.

    Args:
        patient_id (str): FHIR patient ID.

    Returns:
        dict or None: Normalized patient summary or None if not found.
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
        bundle = search_fhir_resource("MedicationAdministration", {
            "patient": patient_id,
            "_count": "100"
        })
        return unwrap_bundle(bundle)
    except Exception as e:
        raise Exception(f"Error fetching medications: {str(e)}")

def get_procedures_for_patient(patient_id: str):
    """Get all procedures for a patient."""
    try:
        bundle = search_fhir_resource("Procedure", {
            "subject": f"Patient/{patient_id}"   
        })
        return unwrap_bundle(bundle)
    except Exception as e:
        raise Exception(f"Error fetching procedures: {str(e)}")

def extract_marital_status(patient: dict) -> str:
    """Extract marital status from Patient resource."""
    coding_list = patient.get("maritalStatus", {}).get("coding", [])
    if coding_list:
        return coding_list[0].get("code", "Unknown")
    return "Unknown"
