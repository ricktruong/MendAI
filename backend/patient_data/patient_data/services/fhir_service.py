# -------------------------------------------
# Patient Data Backend - FHIR Access Layer
# -------------------------------------------

import os
import requests
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from typing import List, Dict, Any
from collections import defaultdict

# Load environment variables from .env
load_dotenv()

# -------------------------------
# Environment Config
# -------------------------------
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_LOCATION")
DATASET_ID = os.getenv("GCP_DATASET_ID")
FHIR_STORE_ID = os.getenv("GCP_FHIR_STORE_ID")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Check that all necessary config is set
if not all([PROJECT_ID, LOCATION, DATASET_ID, FHIR_STORE_ID, SERVICE_ACCOUNT_FILE]):
    raise ValueError("Missing one or more required environment variables")

# Construct base URL for Google Cloud Healthcare FHIR API
FHIR_BASE_URL = (
    f"https://healthcare.googleapis.com/v1/projects/{PROJECT_ID}"
    f"/locations/{LOCATION}/datasets/{DATASET_ID}/fhirStores/{FHIR_STORE_ID}/fhir"
)

# Global cached auth token (for reuse)
_cached_token = None


# -------------------------------
# Auth Helpers
# -------------------------------
def get_google_auth_token():
    """
    Get or refresh a Google Cloud access token for Healthcare API using the service account.
    Caches the token in memory.
    """
    global _cached_token
    if _cached_token and not _cached_token.expired:
        return _cached_token.token

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    credentials.refresh(Request())
    _cached_token = credentials
    return credentials.token


# -------------------------------
# FHIR API Wrappers
# -------------------------------
def get_fhir_resource(resource_type: str, resource_id: str):
    """Retrieve a single FHIR resource by its type and ID.""" 
    token = get_google_auth_token()
    url = f"{FHIR_BASE_URL}/{resource_type}/{resource_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/fhir+json",
    }
    response = requests.get(url, headers=headers)
    if not response.ok:
        raise Exception(f"FHIR API Error: {response.status_code} - {response.text}")
    return response.json()


def search_fhir_resource(resource_type: str, params: dict):
    """
    Perform a _search query on a resource type using POST.
    Returns a single FHIR Bundle.
    """
    token = get_google_auth_token()
    url = f"{FHIR_BASE_URL}/{resource_type}/_search"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/fhir+json;charset=utf-8",
    }
    response = requests.post(url, headers=headers, json=params or {})
    if not response.ok:
        raise Exception(f"FHIR API Error: {response.status_code} - {response.text}")
    return response.json()


def list_fhir_resources(resource_type: str, params: dict = None, max_pages: int = 5):
    """
    Retrieve paginated results of a resource type via repeated _search calls.
    Returns a flat list of entries.
    """
    token = get_google_auth_token()
    url = f"{FHIR_BASE_URL}/{resource_type}/_search"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/fhir+json;charset=utf-8",
    }

    resources = []
    page = 0
    
    while url and page < max_pages:
        if url.endswith("/_search"):
            response = requests.post(url, headers=headers, json=params or {})
        else:
            response = requests.get(url, headers=headers)
        if not response.ok:
            raise Exception(f"FHIR API Error: {response.status_code} - {response.text}")
        bundle = response.json()
        if "entry" in bundle:
            resources.extend(bundle["entry"])
        
        # Check for next page
        links = bundle.get("link", [])
        next_link = next((l["url"] for l in links if l["relation"] == "next"), None)
        url = next_link
        params = None  # Prevent re-sending params
        page += 1

    return resources


def unwrap_bundle(bundle: dict):
    """Extract flat list of `resource` objects from a FHIR Bundle."""
    return [entry["resource"] for entry in bundle.get("entry", [])]


def get_patient_subject_ids():
    """
    Retrieve all patient subject_ids (FHIR Patient.id).
    Useful for indexing or browsing the dataset.
    """
    patient_entries = list_fhir_resources("Patient", max_pages=10)
    subject_ids = []
    for entry in patient_entries:
        resource = entry.get("resource", {})
        patient_id = resource.get("id")
        if patient_id:
            subject_ids.append(patient_id)
    return subject_ids


# -------------------------------
# High-Level Patient Bundle Builder
# -------------------------------
def get_encounter_centric_patient_bundle(patient_id: str):
    """
    Construct a full FHIR bundle of all patient-related data.
    Includes:
    - Patient record
    - All Encounters
    - All encounter-scoped resources (Observations, Medications, etc.)
    - All patient-scoped resources (Conditions, Procedures, etc.)
    - Global static resources (Organization, Location, Medication)
    """
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": []
    }
    seen = set()  # Prevent duplicate resources


    def add_to_bundle(resource):
        """Helper to add resource to bundle if not already present."""
        key = f"{resource['resourceType']}/{resource['id']}"
        if key not in seen:
            seen.add(key)
            bundle["entry"].append({"resource": resource})

    # 1. Patient
    patient = get_fhir_resource("Patient", patient_id)
    add_to_bundle(patient)

    # 2. Encounters for patient
    encounter_bundle = search_fhir_resource("Encounter", {"subject": f"Patient/{patient_id}"})
    encounter_entries = encounter_bundle.get("entry", [])
    for entry in encounter_entries:
        add_to_bundle(entry["resource"])
    encounter_ids = [e["resource"]["id"] for e in encounter_entries]

    # 3. Resources linked via encounter/context (encounter-scoped)
    encounter_related_types = [
        ("Observation", "encounter"),
        ("Procedure", "encounter"),
        ("Condition", "encounter"),
        ("MedicationAdministration", "context"),
        ("MedicationDispense", "context"),
        ("MedicationStatement", "context"),
        ("MedicationRequest", "encounter"),
        ("Specimen", "encounter")
    ]

    for enc_id in encounter_ids:
        for resource_type, ref_field in encounter_related_types:
            try:
                resources = get_resources_by_encounter(enc_id, resource_type, ref_field)
                for r in resources:
                    add_to_bundle(r["resource"])
            except Exception as e:
                print(f"⚠️ Skipped {resource_type} for Encounter {enc_id}: {e}")

    # 4. Resources directly scoped to patient (e.g., Meds, Conditions)
    patient_scoped_types = [
        "Observation", "Condition", "Procedure", "Specimen",
        "MedicationStatement", "MedicationRequest", "MedicationDispense"
    ]
    for resource_type in patient_scoped_types:
        try:
            patient_resources = search_fhir_resource(resource_type, {"subject": f"Patient/{patient_id}"})
            for entry in patient_resources.get("entry", []):
                add_to_bundle(entry["resource"])
        except Exception as e:
            print(f"⚠️ Failed to fetch patient-scoped {resource_type}: {e}")

    # 5. Global shared reference resources
    for global_type in ["Medication", "Location", "Organization"]:
        try:
            resources = list_fhir_resources(global_type, max_pages=1)
            for r in resources:
                add_to_bundle(r["resource"])
        except Exception as e:
            print(f"⚠️ Skipped global resource {global_type}: {e}")

    return bundle


# -------------------------------
# Resource Helper Utilities
# -------------------------------
def get_observations_for_patient(patient_id: str, code: str = None):
    """Query Observations for a patient, optionally filtered by LOINC/SNOMED code."""
    params = {"patient": patient_id}
    if code:
        params["code"] = code
    return search_fhir_resource("Observation", params)


def get_encounters_for_patient(patient_id: str):
    """Query all Encounters for a patient."""
    params = {"patient": patient_id}
    return search_fhir_resource("Encounter", params)


def get_conditions_for_patient(patient_id: str):
    """Query all Conditions for a patient."""
    params = {"patient": patient_id}
    return search_fhir_resource("Condition", params)


def get_resources_by_encounter(encounter_id: str, resource_type: str, reference_field: str = "encounter"):
    """
    Generic method to fetch any resource linked to a specific encounter.
    The `reference_field` may be either 'encounter' or 'context' depending on resource type.
    """
    token = get_google_auth_token()
    url = f"{FHIR_BASE_URL}/{resource_type}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/fhir+json"
    }
    params = {reference_field: f"Encounter/{encounter_id}"}
    response = requests.get(url, headers=headers, params=params)
    if not response.ok:
        raise Exception(f"FHIR API Error ({resource_type}): {response.status_code} - {response.text}")
    return response.json().get("entry", [])


# -------------------------------
# Bundle Merging and Transformation
# -------------------------------
def merge_fhir_bundles(*bundles):
    """
    Merge multiple FHIR bundles into one.
    Deduplicates entries based on resourceType/id.
    """
    seen_ids = set()
    merged_entries = []

    for bundle in bundles:
        for entry in bundle.get("entry", []):
            resource = entry.get("resource")
            if not resource:
                continue
            rid = resource.get("id")
            rtype = resource.get("resourceType")
            unique_key = f"{rtype}/{rid}"
            if unique_key not in seen_ids:
                seen_ids.add(unique_key)
                merged_entries.append({"resource": resource})

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": merged_entries
    }


# -------------------------------
# Normalization of Patient Data
# -------------------------------
def normalize_fhir_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a raw FHIR bundle into an encounter-centric structure.
    
    This function takes a FHIR Bundle and organizes its resources by encounters,
    simplifying and formatting the data for frontend and LLM-friendly consumption.
    
    Returns a structure:
    {
        "patient": {...},
        "encounters": [
            {
                "id": ...,
                "status": ...,
                "start": ...,
                "end": ...,
                ...
                "observations": [...],
                "procedures": [...],
                ...
            },
            ...
        ]
    }
    """

    # Build a map of resources by type (e.g., Observation, Encounter)
    resource_map = defaultdict(list)

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        rtype = resource.get("resourceType")
        if rtype:
            resource_map[rtype].append(resource)
    
    # --- Utility to Resolve Location References ---
    def resolve_location(loc_ref: str, resource_map: Dict[str, List[dict]]) -> dict:
        """
        Look up a full Location resource by reference (e.g., 'Location/abc123').
        Extracts name and type if found.
        """
        loc_id = loc_ref.split("/")[-1].strip().lower()
        for loc in resource_map.get("Location", []):
            if loc.get("id", "").strip().lower() == loc_id:
                return {
                    "name": loc.get("name"),
                    "typeCode": loc.get("physicalType", {}).get("coding", [{}])[0].get("code"),
                    "typeDisplay": loc.get("physicalType", {}).get("coding", [{}])[0].get("display"),
                }
        return {}


    # --- Normalize Patient Demographics ---
    def extract_patient(patient, resource_map):
        """
        Extract patient-level fields and resolve managing organization, race, and ethnicity.
        """
        # Get managing organization name
        org_ref = patient.get("managingOrganization", {}).get("reference", "")
        org_id = org_ref.split("/")[-1] if org_ref else None
        org_name = next(
            (org.get("name") for org in resource_map.get("Organization", []) if org.get("id") == org_id),
            None
        )
        
        # Parse race and ethnicity from extensions
        extensions = patient.get("extension", [])
        race = None
        ethnicity = None
        if len(extensions) > 0:
            race_exts = extensions[0].get("extension", [])
            race = next((e.get("valueCoding", {}).get("display") for e in race_exts if e.get("url") == "ombCategory"), None)
        if len(extensions) > 1:
            eth_exts = extensions[1].get("extension", [])
            ethnicity = next((e.get("valueCoding", {}).get("display") for e in eth_exts if e.get("url") == "ombCategory"), None)

        # Build and return patient object
        return {
            "id": patient.get("identifier", [{}])[0].get("value"),
            "fhirId": patient.get("id"),
            "birthDate": patient.get("birthDate"),
            "gender": patient.get("gender"),
            "name": patient.get("name", [{}])[0].get("family"),
            "language": patient.get("communication", [{}])[0]
                        .get("language", {})
                        .get("coding", [{}])[0]
                        .get("code"),
            "maritalStatus": patient.get("maritalStatus", {})
                            .get("coding", [{}])[0]
                            .get("code"),
            "deceasedDateTime": patient.get("deceasedDateTime"),
            "managingOrganization": org_name,
            "race": race,
            "ethnicity": ethnicity
        }

    
    # --- Group resources by Encounter reference ---
    def group_by_encounter(resources, path="encounter"):
        """
        Groups resources that reference an Encounter using a field like `encounter` or `context`.
        Returns a dict of { encounter_id: [resource, ...] }
        """
        grouped = defaultdict(list)
        for r in resources:
            ref = r.get(path, {})
            if not isinstance(ref, dict):
                continue
            ref_val = ref.get("reference", "")
            if ref_val.startswith("Encounter/"):
                enc_id = ref_val.split("/")[1]
                grouped[enc_id].append(r)
        return grouped


    # --- Normalize each resource type ---
    # ------------------------------
    # Normalize Observations
    # ------------------------------
    def simplify_observation(obs):
        code = obs.get("code", {}).get("coding", [{}])[0]
        category = obs.get("category", [{}])[0].get("coding", [{}])[0]

        # Value can be a quantity or string
        value = None
        if "valueQuantity" in obs:
            q = obs["valueQuantity"]
            value = {
                "value": q.get("value"),
                "unit": q.get("unit"),
                "code": q.get("code")
            }
        elif "valueString" in obs:
            value = obs["valueString"]

        # Optional components (mostly for panels)
        components = []
        for comp in obs.get("component", []):
            c = comp.get("code", {}).get("coding", [{}])[0]
            v = comp.get("valueQuantity", {})
            components.append({
                "code": c.get("code"),
                "text": c.get("display"),
                "value": {
                    "value": v.get("value"),
                    "unit": v.get("unit")
                }
            })

        result = {
            "id": obs.get("id"),
            "status": obs.get("status"),
            "effectiveDateTime": obs.get("effectiveDateTime"),
            "code": {
                "code": code.get("code"),
                "text": code.get("display")
            },
            "category": {
                "code": category.get("code")
            } if category.get("code") else None,
            "value": value,
            "components": components
        }

        # Remove nulls
        return {k: v for k, v in result.items() if v is not None}


    # ------------------------------
    # Normalize MedicationAdministration 
    # ------------------------------
    def simplify_med_admin(med):
        med_code = med.get("medicationCodeableConcept", {}).get("coding", [{}])[0]
        category = med.get("category", {}).get("coding", [{}])[0]
        dose = med.get("dosage", {}).get("dose", {})
        method = med.get("dosage", {}).get("method", {}).get("coding", [{}])[0]

        result = {
            "id": med.get("id"),
            "status": med.get("status"),
            "effectiveDateTime": med.get("effectiveDateTime") or med.get("effectivePeriod", {}).get("start"),
            "medication": {
                "code": med_code.get("code"),
                "text": med_code.get("display")
            },
            "category": {
                "code": category.get("code")
            } if category.get("code") else None,
            "dose": {
                "value": dose.get("value"),
                "unit": dose.get("unit")
            } if dose.get("value") else None,
            "method": {
                "code": method.get("code")
            } if method.get("code") else None
        }

        # Remove null values
        return {k: v for k, v in result.items() if v is not None}


    # ------------------------------
    # Normalize MedicationDispense
    # ------------------------------
    def simplify_med_dispense(mdisp):
        med = mdisp.get("medicationCodeableConcept", {}).get("coding", [{}])[0]
        dosage = mdisp.get("dosageInstruction", [{}])[0] if mdisp.get("dosageInstruction") else {}
 
        route = dosage.get("route", {}).get("coding", [{}])[0].get("code")
        timing = dosage.get("timing", {}).get("code", {}).get("coding", [{}])[0].get("code")

        context_ref = mdisp.get("context", {}).get("reference", "")

        result = {
            "id": mdisp.get("id"),
            "identifier": mdisp.get("identifier", [{}])[0].get("value"),
            "status": mdisp.get("status"),
            "encounterId": context_ref.split("/")[-1] if context_ref.startswith("Encounter/") else None,
            "medication": med.get("code"),
            "route": route,
            "timing": timing,
            "whenHandedOver": mdisp.get("whenHandedOver")
        }

        # Clean nulls
        return {k: v for k, v in result.items() if v is not None}


    # ------------------------------
    # Normalize MedicationStatements
    # ------------------------------
    def simplify_med_statement(stmt):
        codings = stmt.get("medicationCodeableConcept", {}).get("coding", [])
        best_coding = next((c for c in codings if c.get("display")), codings[-1] if codings else {})
        text = stmt.get("medicationCodeableConcept", {}).get("text")

        context_ref = stmt.get("context", {}).get("reference", "")

        result = {
            "id": stmt.get("id"),
            "status": stmt.get("status"),
            "dateAsserted": stmt.get("dateAsserted"),
            "medication": {
                "code": best_coding.get("code"),
                "text": text,
                "display": best_coding.get("display")
            }
        }

        # Remove nulls and empty medication keys
        result["medication"] = {k: v for k, v in result["medication"].items() if v}
        if not result["medication"]:
            del result["medication"]

        return {k: v for k, v in result.items() if v is not None}


    # ------------------------------
    # Normalize MedicationRequests
    # ------------------------------
    def simplify_med_request(mr):
        dosage = (
            mr.get("dosageInstruction", [{}])[0]
            .get("doseAndRate", [{}])[0]
            .get("doseQuantity", {})
        )

        route = (
            mr.get("dosageInstruction", [{}])[0]
            .get("route", {}).get("coding", [{}])[0]
        )

        context_ref = mr.get("encounter", {}).get("reference", "")

        result = {
            "id": mr.get("id"),
            "identifier": mr.get("identifier", [{}])[0].get("value"),
            "status": mr.get("status"),
            "intent": mr.get("intent"),
            "authoredOn": mr.get("authoredOn"),
            "dosage": {
                "value": dosage.get("value"),
                "unit": dosage.get("unit")
            } if dosage.get("value") else None,
            "route": route.get("code"),
            "validityPeriod": {
                "start": mr.get("dispenseRequest", {}).get("validityPeriod", {}).get("start"),
                "end": mr.get("dispenseRequest", {}).get("validityPeriod", {}).get("end")
            }
        }

        # Clean out nulls and empty dicts
        result = {k: v for k, v in result.items() if v is not None}
        if "validityPeriod" in result and not any(result["validityPeriod"].values()):
            del result["validityPeriod"]

        return result


    # ------------------------------
    # Normalize Conditions
    # ------------------------------
    def simplify_condition(cond):
        code = cond.get("code", {}).get("coding", [{}])[0]
        return {
            "resourceType": cond.get("resourceType"),
            "id": cond.get("id"),
            "code": code.get("code"),
            "display": code.get("display"),
            "category": cond.get("category", [{}])[0].get("coding", [{}])[0].get("code")
        }


    # ------------------------------
    # Normalize Procedures
    # ------------------------------
    def simplify_procedure(proc):
        code = proc.get("code", {}).get("coding", [{}])[0]
        category = proc.get("category", {}).get("coding", [{}])[0]
        body_site = proc.get("bodySite", [{}])[0].get("coding", [{}])[0]
        performed_start = proc.get("performedPeriod", {}).get("start")
        performed_end = proc.get("performedPeriod", {}).get("end")

        result = {
            "id": proc.get("id"),
            "code": {
                "code": code.get("code"),
                "display": code.get("display")
            },
            "status": proc.get("status")
        }

        # Conditionally add fields only if they have data
        if category.get("code"):
            result["category"] = {
                "code": category.get("code"),
                "display": category.get("display")
            }

        if body_site.get("code"):
            result["bodySite"] = {
                "code": body_site.get("code"),
                "display": body_site.get("display"),
                "system": body_site.get("system")
            }

        if performed_start or performed_end:
            result["performedPeriod"] = {
                "start": performed_start,
                "end": performed_end
            }

        return result

    # Group each resource type by encounter
    conditions_by_enc = group_by_encounter(resource_map["Condition"])
    procedures_by_enc = group_by_encounter(resource_map["Procedure"])
    observations_by_enc = group_by_encounter(resource_map["Observation"])
    medications_by_enc = group_by_encounter(resource_map["MedicationAdministration"], path="context")
    dispenses_by_enc = group_by_encounter(resource_map["MedicationDispense"], path="context")
    medstatements_by_enc = group_by_encounter(resource_map["MedicationStatement"], path="context")
    medrequest_by_enc = group_by_encounter(resource_map["MedicationRequest"], path="encounter")


    # --- Build per-encounter view ---
    encounters_view = []
    for enc in resource_map["Encounter"]:
        enc_id = enc.get("id")

        # Normalize medications linked to this encounter
        meds = [simplify_med_admin(m) for m in medications_by_enc.get(enc_id, [])]

        # Construct normalized encounter object
        entry = {
            "id": enc_id,
            "status": enc.get("status"),
            "start": enc.get("period", {}).get("start"),
            "end": enc.get("period", {}).get("end"),
            "class": enc.get("class", {}).get("code"),
            "admitSource": enc.get("hospitalization", {}).get("admitSource", {}).get("coding", [{}])[0].get("code"),
            "dischargeDisposition": enc.get("hospitalization", {}).get("dischargeDisposition", {}).get("coding", [{}])[0].get("code"),
            "encounterTypeCode": enc.get("type", [{}])[0].get("coding", [{}])[0].get("code"),
            "encounterType": enc.get("type", [{}])[0].get("coding", [{}])[0].get("display"),
            "locations": [
                {
                    **resolve_location(loc.get("location", {}).get("reference", ""), resource_map),
                    "start": loc.get("period", {}).get("start"),
                    "end": loc.get("period", {}).get("end"),
                }
                for loc in enc.get("location", [])
            ],
            "diagnoses": [simplify_condition(c) for c in conditions_by_enc.get(enc_id, [])],
            "procedures": [simplify_procedure(p) for p in procedures_by_enc.get(enc_id, [])],
            "observations": [simplify_observation(o) for o in observations_by_enc.get(enc_id, [])],
            "medicationAdministration": meds,
            "medicationDispense": [simplify_med_dispense(d) for d in dispenses_by_enc.get(enc_id, [])],
            "medicationStatements": [simplify_med_statement(d) for d in medstatements_by_enc.get(enc_id, [])],
            "medicationRequests": [simplify_med_request(d) for d in medrequest_by_enc.get(enc_id, [])]
        }

        encounters_view.append(entry)

    # --- Final normalized output ---
    return {
        "patient": extract_patient(resource_map["Patient"][0], resource_map),
        "encounters": encounters_view
    }

