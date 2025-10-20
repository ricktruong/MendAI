from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from pathlib import Path
from engine.utils.nii_processor import nii_processor

router = APIRouter()

# Persistence file path
PERSISTENCE_FILE = Path("uploaded_files/patient_data.json")

# Response models
class Patient(BaseModel):
    id: str
    name: str
    email: str = ""
    age: int = 0
    gender: str = ""

class PatientFile(BaseModel):
    id: str
    file_name: str
    uploaded_at: str
    file_path: Optional[str] = None  # Path to saved file on disk

class RecentCase(BaseModel):
    id: str
    patient_name: str
    file_name: str  # Keep for backward compatibility
    uploaded_at: str
    files: List[PatientFile] = []  # New field for multiple files
    fhirId: Optional[str] = None
    birthDate: Optional[str] = None
    gender: Optional[str] = None
    race: Optional[str] = None
    ethnicity: Optional[str] = None
    maritalStatus: Optional[str] = None
    managingOrganization: Optional[str] = None
    language: Optional[str] = None

class PatientListResponse(BaseModel):
    patients: List[Patient]
    recent_cases: List[RecentCase]

# Keep old name for backward compatibility
class DashboardResponse(PatientListResponse):
    pass

class CreatePatientRequest(BaseModel):
    patient_name: str
    uploaded_at: str

class CreatePatientResponse(BaseModel):
    success: bool
    case: Optional[RecentCase] = None
    message: str

class UpdatePatientRequest(BaseModel):
    patient_name: str
    uploaded_at: str

class UpdatePatientResponse(BaseModel):
    success: bool
    case: Optional[RecentCase] = None
    message: str

class DeletePatientResponse(BaseModel):
    success: bool
    message: str

# Persistence functions
def load_stored_cases():
    """Load stored cases from JSON file"""
    if PERSISTENCE_FILE.exists():
        try:
            with open(PERSISTENCE_FILE, 'r') as f:
                data = json.load(f)
                cases = []
                for item in data:
                    # Convert files list
                    files = [PatientFile(**f) for f in item.get('files', [])]
                    item['files'] = files
                    cases.append(RecentCase(**item))
                print(f"Loaded {len(cases)} cases from {PERSISTENCE_FILE}")
                return cases
        except Exception as e:
            print(f"Error loading cases from file: {e}")
    return []

def save_stored_cases(cases):
    """Save stored cases to JSON file"""
    try:
        # Ensure directory exists
        PERSISTENCE_FILE.parent.mkdir(exist_ok=True)

        # Convert to dict for JSON serialization
        data = []
        for case in cases:
            case_dict = case.model_dump()
            data.append(case_dict)

        with open(PERSISTENCE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(cases)} cases to {PERSISTENCE_FILE}")
    except Exception as e:
        print(f"Error saving cases to file: {e}")

# In-memory storage for demo (in production, this would be a database)
# Initialize with default cases
_default_cases = [
    RecentCase(
        id="14889227",
        patient_name="Sarah Johnson",
        file_name="CT_Head_001.nii",
        uploaded_at="2025-09-28",
        files=[PatientFile(id="file-001-1", file_name="CT_Head_001.nii", uploaded_at="2025-09-28", file_path=None)],
        fhirId="07962bbc-98bf-5586-9988-603d6414295c",
        birthDate="1978-01-16",
        gender="female",
        race="White",
        ethnicity="Not Hispanic or Latino",
        maritalStatus="M",
        managingOrganization="Beth Israel Deaconess Medical Center",
        language="en"
    ),
    RecentCase(
        id="14889228",
        patient_name="Michael Chen",
        file_name="CT_Chest_045.nii.gz",
        uploaded_at="2025-09-27",
        files=[PatientFile(id="file-002-1", file_name="CT_Chest_045.nii.gz", uploaded_at="2025-09-27", file_path=None)],
        fhirId="a1b2c3d4-5678-9abc-def0-123456789abc",
        birthDate="1965-05-22",
        gender="male",
        race="Asian",
        ethnicity="Not Hispanic or Latino",
        maritalStatus="M",
        managingOrganization="Massachusetts General Hospital",
        language="en"
    ),
    RecentCase(
        id="14889229",
        patient_name="Maria Garcia",
        file_name="CT_Abdomen_102.nii",
        uploaded_at="2025-09-26",
        files=[PatientFile(id="file-003-1", file_name="CT_Abdomen_102.nii", uploaded_at="2025-09-26", file_path=None)],
        fhirId="b2c3d4e5-6789-0abc-def1-234567890bcd",
        birthDate="1992-11-03",
        gender="female",
        race="Other",
        ethnicity="Hispanic or Latino",
        maritalStatus="S",
        managingOrganization="Boston Medical Center",
        language="es"
    ),
    RecentCase(
        id="14889230",
        patient_name="James Williams",
        file_name="CT_Brain_Trauma_003.nii",
        uploaded_at="2025-09-25",
        files=[PatientFile(id="file-004-1", file_name="CT_Brain_Trauma_003.nii", uploaded_at="2025-09-25", file_path=None)],
        fhirId="c3d4e5f6-7890-1bcd-ef12-34567890cdef",
        birthDate="1955-07-14",
        gender="male",
        race="Black or African American",
        ethnicity="Not Hispanic or Latino",
        maritalStatus="W",
        managingOrganization="Brigham and Women's Hospital",
        language="en"
    ),
    RecentCase(
        id="14889231",
        patient_name="Emily Rodriguez",
        file_name="CT_Spine_067.nii",
        uploaded_at="2025-09-24",
        files=[PatientFile(id="file-005-1", file_name="CT_Spine_067.nii", uploaded_at="2025-09-24", file_path=None)],
        fhirId="d4e5f6g7-8901-2cde-f123-4567890defgh",
        birthDate="1980-03-28",
        gender="female",
        race="White",
        ethnicity="Hispanic or Latino",
        maritalStatus="D",
        managingOrganization="Tufts Medical Center",
        language="en"
    ),
    RecentCase(
        id="14889232",
        patient_name="David Kim",
        file_name="CT_Thorax_089.nii",
        uploaded_at="2025-09-23",
        files=[PatientFile(id="file-006-1", file_name="CT_Thorax_089.nii", uploaded_at="2025-09-23", file_path=None)],
        fhirId="e5f6g7h8-9012-3def-1234-567890efghij",
        birthDate="1970-12-10",
        gender="male",
        race="Asian",
        ethnicity="Not Hispanic or Latino",
        maritalStatus="M",
        managingOrganization="Beth Israel Deaconess Medical Center",
        language="ko"
    ),
    RecentCase(
        id="14889233",
        patient_name="Jennifer Washington",
        file_name="CT_Pelvis_045.nii",
        uploaded_at="2025-09-22",
        files=[PatientFile(id="file-007-1", file_name="CT_Pelvis_045.nii", uploaded_at="2025-09-22", file_path=None)],
        fhirId="f6g7h8i9-0123-4efg-2345-67890fghijk1",
        birthDate="1988-08-19",
        gender="female",
        race="Black or African American",
        ethnicity="Not Hispanic or Latino",
        maritalStatus="S",
        managingOrganization="Boston Children's Hospital",
        language="en"
    ),
    RecentCase(
        id="14889234",
        patient_name="Robert Patel",
        file_name="CT_Neck_034.nii",
        uploaded_at="2025-09-21",
        files=[PatientFile(id="file-008-1", file_name="CT_Neck_034.nii", uploaded_at="2025-09-21", file_path=None)],
        fhirId="g7h8i9j0-1234-5fgh-3456-7890ghijkl12",
        birthDate="1963-04-07",
        gender="male",
        race="Asian",
        ethnicity="Not Hispanic or Latino",
        maritalStatus="M",
        managingOrganization="Massachusetts General Hospital",
        language="hi"
    ),
    RecentCase(
        id="14889235",
        patient_name="Linda Martinez",
        file_name="CT_Sinus_012.nii",
        uploaded_at="2025-09-20",
        files=[PatientFile(id="file-009-1", file_name="CT_Sinus_012.nii", uploaded_at="2025-09-20", file_path=None)],
        fhirId="h8i9j0k1-2345-6ghi-4567-890hijklm123",
        birthDate="1975-09-15",
        gender="female",
        race="White",
        ethnicity="Hispanic or Latino",
        maritalStatus="M",
        managingOrganization="Lahey Hospital & Medical Center",
        language="es"
    ),
    RecentCase(
        id="14889236",
        patient_name="Thomas Anderson",
        file_name="CT_Cardiac_078.nii",
        uploaded_at="2025-09-19",
        files=[PatientFile(id="file-010-1", file_name="CT_Cardiac_078.nii", uploaded_at="2025-09-19", file_path=None)],
        fhirId="i9j0k1l2-3456-7hij-5678-90ijklmn1234",
        birthDate="1982-06-25",
        gender="male",
        race="White",
        ethnicity="Not Hispanic or Latino",
        maritalStatus="S",
        managingOrganization="Beth Israel Deaconess Medical Center",
        language="en"
    ),
]

# Load persisted cases or use defaults
stored_cases = load_stored_cases() or _default_cases

# 2. Patient List Page (formerly Dashboard Page)
@router.get("/dashboard", response_model=DashboardResponse)
async def get_patient_list_data() -> DashboardResponse:
    """
    Get patient list data including patients and recent cases for Patient List Page
    Fetches real patient data from Google Healthcare FHIR API

    Returns:
        DashboardResponse: Patient list data with patients and recent cases
    """
    import httpx
    from datetime import datetime

    try:
        # Fetch patient data from patient_data service
        PATIENT_DATA_URL = os.getenv("PATIENT_DATA_SERVICE_URL", "http://patient_data:8001")

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                # Get list of patient subject IDs from FHIR
                response = await client.get(f"{PATIENT_DATA_URL}/api/patients/subject_ids")
                response.raise_for_status()
                subject_ids_data = response.json()
                subject_ids = subject_ids_data.get("subject_ids", [])

                # Fetch all patients (no limit)
                print(f"Fetching {len(subject_ids)} patients from FHIR in parallel...")

                # Helper function to extract patient data
                async def fetch_patient(subject_id: str):
                    try:
                        patient_response = await client.get(f"{PATIENT_DATA_URL}/api/patients/{subject_id}", timeout=10.0)
                        patient_response.raise_for_status()
                        patient_raw = patient_response.json()

                        # Extract patient info from raw FHIR data
                        patient_id = patient_raw.get("identifier", [{}])[0].get("value", subject_id)
                        patient_name = patient_raw.get("name", [{}])[0].get("family", f"Patient_{patient_id}")

                        # Extract race and ethnicity from extensions
                        extensions = patient_raw.get("extension", [])
                        race = None
                        ethnicity = None
                        if len(extensions) > 0:
                            race_exts = extensions[0].get("extension", [])
                            race = next((e.get("valueCoding", {}).get("display") for e in race_exts if e.get("url") == "ombCategory"), None)
                        if len(extensions) > 1:
                            eth_exts = extensions[1].get("extension", [])
                            ethnicity = next((e.get("valueCoding", {}).get("display") for e in eth_exts if e.get("url") == "ombCategory"), None)

                        # Extract managing organization
                        org_ref = patient_raw.get("managingOrganization", {}).get("reference", "")

                        # Create a case entry from patient data
                        return RecentCase(
                            id=patient_id,
                            patient_name=patient_name,
                            file_name="FHIR_Data.json",  # Placeholder for FHIR data
                            uploaded_at=datetime.now().strftime("%Y-%m-%d"),
                            files=[],
                            fhirId=subject_id,
                            birthDate=patient_raw.get("birthDate"),
                            gender=patient_raw.get("gender"),
                            race=race,
                            ethnicity=ethnicity,
                            maritalStatus=patient_raw.get("maritalStatus", {}).get("coding", [{}])[0].get("code"),
                            managingOrganization=org_ref.split("/")[-1] if org_ref else None,
                            language=patient_raw.get("communication", [{}])[0].get("language", {}).get("coding", [{}])[0].get("code")
                        )
                    except Exception as e:
                        print(f"✗ Error fetching patient {subject_id}: {type(e).__name__}")
                        return None

                # Fetch all patients in parallel using asyncio.gather
                import asyncio
                tasks = [fetch_patient(subject_id) for subject_id in subject_ids]
                results = await asyncio.gather(*tasks)

                # Filter out None results (failed requests)
                recent_cases = [case for case in results if case is not None]

                # Merge with stored_cases to include uploaded files
                # For each FHIR patient, check if there are files in stored_cases
                for fhir_case in recent_cases:
                    stored_case = next((sc for sc in stored_cases if sc.id == fhir_case.id), None)
                    if stored_case and stored_case.files:
                        # Merge file information from stored_cases
                        fhir_case.files = stored_case.files
                        fhir_case.file_name = stored_case.file_name
                        fhir_case.uploaded_at = stored_case.uploaded_at
                        print(f"Merged {len(stored_case.files)} files for patient {fhir_case.id}")

                patients = []

                print(f"Successfully loaded {len(recent_cases)} patients from FHIR")
                if len(recent_cases) == 0:
                    print("No patients loaded, falling back to stored_cases")
                    return DashboardResponse(patients=[], recent_cases=stored_cases)

                return DashboardResponse(patients=patients, recent_cases=recent_cases)

            except httpx.HTTPError as e:
                print(f"Error connecting to patient_data service: {e}")
                # Fallback to stored_cases if service is unavailable
                return DashboardResponse(patients=[], recent_cases=stored_cases)

    except Exception as e:
        print(f"Internal server error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/patients", response_model=CreatePatientResponse)
async def create_patient(
    patient_name: str = Form(...),
    uploaded_at: str = Form(...),
    file: UploadFile = File(...)
) -> CreatePatientResponse:
    """
    Create a new patient with file upload
    
    Args:
        patient_name: Name of the patient
        uploaded_at: Date of the case
        file: Uploaded CT scan file
    
    Returns:
        CreatePatientResponse: Success response with new case data
    """
    try:
        # Validate input
        if not patient_name.strip():
            raise HTTPException(status_code=400, detail="Patient name is required")
        
        if not file:
            raise HTTPException(status_code=400, detail="File is required")
        
        # Generate new case ID
        new_id = f"ct-{str(len(stored_cases) + 1).zfill(3)}"

        # Save uploaded file to disk
        file_name = file.filename or f"uploaded_file_{new_id}.nii"

        # Validate file extension
        if not (file_name.lower().endswith('.nii') or file_name.lower().endswith('.nii.gz')):
            raise HTTPException(status_code=400, detail="Only .nii or .nii.gz files are supported")

        # Read file content and save to disk
        file_content = await file.read()
        saved_file_path = nii_processor.save_uploaded_file(file_content, file_name)
        print(f"Saved uploaded NIfTI file: {saved_file_path}")

        # Generate file ID
        file_id = f"file-{new_id}-1"

        # Create new case with file list
        new_case = RecentCase(
            id=new_id,
            patient_name=patient_name,
            file_name=file_name,  # Primary file for backward compatibility
            uploaded_at=uploaded_at,
            files=[PatientFile(id=file_id, file_name=file_name, uploaded_at=uploaded_at, file_path=saved_file_path)]
        )

        # Add to in-memory storage (in production, save to database)
        stored_cases.append(new_case)

        # Persist to file
        save_stored_cases(stored_cases)

        return CreatePatientResponse(
            success=True,
            case=new_case,
            message="Patient added successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create patient: {str(e)}")

@router.put("/patients/{case_id}", response_model=UpdatePatientResponse)
async def update_patient(
    case_id: str,
    patient_name: str = Form(...),
    uploaded_at: str = Form(...),
    file: Optional[UploadFile] = File(None),
    delete_file: Optional[str] = Form(None)
) -> UpdatePatientResponse:
    """
    Update an existing patient
    
    Args:
        case_id: ID of the case to update
        patient_name: New patient name
        uploaded_at: New date
        file: Optional new file upload
        delete_file: Optional flag to delete the file (set to 'true' to delete)
    
    Returns:
        UpdatePatientResponse: Success response with updated case data
    """
    try:
        # Find the case to update
        case_index = None
        for i, case in enumerate(stored_cases):
            if case.id == case_id:
                case_index = i
                break

        # Validate input
        if not patient_name.strip():
            raise HTTPException(status_code=400, detail="Patient name is required")

        # If case not found in stored_cases (e.g., FHIR patient), create new entry
        if case_index is None:
            print(f"Patient {case_id} not found in stored_cases, creating new entry")
            updated_case = RecentCase(
                id=case_id,
                patient_name=patient_name,
                file_name="",
                uploaded_at=uploaded_at,
                files=[]
            )
            stored_cases.append(updated_case)
            case_index = len(stored_cases) - 1
        else:
            # Update existing case data
            updated_case = stored_cases[case_index]
            updated_case.patient_name = patient_name
            updated_case.uploaded_at = uploaded_at
        
        # Handle file operations
        if delete_file and delete_file.lower() == 'true':
            # Delete the primary file but keep others
            # TODO: In production, delete file from storage
            if updated_case.files:
                # Remove the primary file (first one) but keep others
                updated_case.files = updated_case.files[1:]
                # Update primary file reference
                if updated_case.files:
                    updated_case.file_name = updated_case.files[0].file_name
                    updated_case.uploaded_at = updated_case.files[0].uploaded_at
                else:
                    updated_case.file_name = ""
        elif file and file.filename:
            # Add new file to the patient's file list (preserve existing files)
            # Validate file extension
            if not (file.filename.lower().endswith('.nii') or file.filename.lower().endswith('.nii.gz')):
                raise HTTPException(status_code=400, detail="Only .nii or .nii.gz files are supported")

            # Save uploaded file to disk
            file_content = await file.read()
            saved_file_path = nii_processor.save_uploaded_file(file_content, file.filename)
            print(f"Saved updated NIfTI file: {saved_file_path}")

            # Generate new file ID
            existing_file_count = len(updated_case.files) if updated_case.files else 0
            new_file_id = f"file-{case_id}-{existing_file_count + 1}"

            # Create new file record
            new_file = PatientFile(
                id=new_file_id,
                file_name=file.filename,
                uploaded_at=uploaded_at,
                file_path=saved_file_path
            )

            # Add to files list
            if not updated_case.files:
                updated_case.files = []
            updated_case.files.append(new_file)

            # Update primary file reference to the newest file
            updated_case.file_name = file.filename

        # Persist to file
        save_stored_cases(stored_cases)

        return UpdatePatientResponse(
            success=True,
            case=updated_case,
            message="Patient updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update patient: {str(e)}")

@router.delete("/patients/{case_id}", response_model=DeletePatientResponse)
async def delete_patient(case_id: str) -> DeletePatientResponse:
    """
    Delete a patient case
    
    Args:
        case_id: ID of the case to delete
    
    Returns:
        DeletePatientResponse: Success response
    """
    try:
        # Find and remove the case
        case_found = False
        for i, case in enumerate(stored_cases):
            if case.id == case_id:
                stored_cases.pop(i)
                case_found = True
                break
        
        if not case_found:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Persist to file
        save_stored_cases(stored_cases)

        return DeletePatientResponse(
            success=True,
            message="Patient deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete patient: {str(e)}")

# Patient Files endpoints
class PatientFilesResponse(BaseModel):
    success: bool
    files: List[PatientFile]
    message: str

@router.get("/patients/{case_id}/files", response_model=PatientFilesResponse)
async def get_patient_files(case_id: str) -> PatientFilesResponse:
    """
    Get all files for a specific patient

    Args:
        case_id: ID of the patient case

    Returns:
        PatientFilesResponse: List of all files for the patient
    """
    try:
        # Find the case
        case_found = None
        for case in stored_cases:
            if case.id == case_id:
                case_found = case
                break

        # If patient not found in stored_cases (FHIR patient with no files yet), return empty list
        if not case_found:
            print(f"Patient {case_id} not found in stored_cases, returning empty file list")
            return PatientFilesResponse(
                success=True,
                files=[],
                message=f"No files found for patient {case_id}"
            )

        return PatientFilesResponse(
            success=True,
            files=case_found.files or [],
            message=f"Retrieved {len(case_found.files or [])} files for patient {case_id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve patient files: {str(e)}")

class DeleteFileResponse(BaseModel):
    success: bool
    message: str

@router.get("/patients/{fhir_id}/normalized")
async def get_patient_normalized_data(fhir_id: str):
    """
    Get normalized patient data including encounters, observations, medications, etc.
    Proxies the request to the patient_data service.

    Args:
        fhir_id: The FHIR subject ID of the patient

    Returns:
        dict: Normalized patient data
    """
    import httpx

    try:
        PATIENT_DATA_URL = os.getenv("PATIENT_DATA_SERVICE_URL", "http://patient_data:8001")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{PATIENT_DATA_URL}/api/patients/{fhir_id}/normalized")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        print(f"Error fetching normalized patient data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch patient data: {str(e)}")
    except Exception as e:
        print(f"Internal server error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/patients/{case_id}/files/{file_id}", response_model=DeleteFileResponse)
async def delete_patient_file(case_id: str, file_id: str) -> DeleteFileResponse:
    """
    Delete a specific file from a patient's record

    Args:
        case_id: ID of the patient case
        file_id: ID of the file to delete

    Returns:
        DeleteFileResponse: Success response
    """
    try:
        # Find the case
        case_found = None
        case_index = None
        for i, case in enumerate(stored_cases):
            if case.id == case_id:
                case_found = case
                case_index = i
                break

        if not case_found:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Find and remove the file
        file_found = False
        if case_found.files:
            for i, file in enumerate(case_found.files):
                if file.id == file_id:
                    case_found.files.pop(i)
                    file_found = True
                    break

        if not file_found:
            raise HTTPException(status_code=404, detail="File not found")

        # Update primary file reference if needed
        if case_found.files:
            case_found.file_name = case_found.files[0].file_name
            case_found.uploaded_at = case_found.files[0].uploaded_at
        else:
            case_found.file_name = ""
            case_found.uploaded_at = ""

        return DeleteFileResponse(
            success=True,
            message="File deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

# Patient Images endpoint
class PatientImagesResponse(BaseModel):
    success: bool
    images: List[str]
    message: str

@router.get("/patients/{case_id}/images", response_model=PatientImagesResponse)
async def get_patient_images(case_id: str) -> PatientImagesResponse:
    """
    Get CT scan images for a specific patient
    
    Args:
        case_id: ID of the patient case
    
    Returns:
        PatientImagesResponse: List of image URLs
    """
    try:
        # Find the case
        case_found = None
        for case in stored_cases:
            if case.id == case_id:
                case_found = case
                break

        # If patient not found in stored_cases (FHIR patient with no files yet), return placeholder
        if not case_found:
            print(f"Patient {case_id} not found in stored_cases, returning no files message")
            return PatientImagesResponse(
                success=True,
                images=[
                    f"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 400 400'><rect width='400' height='400' fill='%23fef2f2'/><circle cx='200' cy='200' r='80' fill='%23fecaca' stroke='%23dc2626' stroke-width='2'/><text x='200' y='190' font-family='Arial' font-size='14' fill='%23dc2626' text-anchor='middle'>No Files Uploaded</text><text x='200' y='210' font-family='Arial' font-size='12' fill='%23dc2626' text-anchor='middle'>Upload .nii files to view</text></svg>"
                ],
                message="No files uploaded for this patient yet"
            )

        # Filter to only NIfTI files
        nii_files = [f for f in case_found.files if f.file_name.lower().endswith('.nii') or f.file_name.lower().endswith('.nii.gz')]

        if not nii_files:
            # No NIfTI files, return placeholder
            sample_images = [
                f"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 400 400'><rect width='400' height='400' fill='%23fef2f2'/><circle cx='200' cy='200' r='80' fill='%23fecaca' stroke='%23dc2626' stroke-width='2'/><text x='200' y='190' font-family='Arial' font-size='14' fill='%23dc2626' text-anchor='middle'>No NIfTI Files</text><text x='200' y='210' font-family='Arial' font-size='12' fill='%23dc2626' text-anchor='middle'>Upload .nii files</text></svg>"
            ]
        else:
            # Convert NIfTI files to actual viewable images (all slices)
            sample_images = []
            for i, nii_file in enumerate(nii_files):
                if nii_file.file_path and os.path.exists(nii_file.file_path):
                    # Try to convert actual NIfTI file to multiple slices
                    print(f"Converting NIfTI file: {nii_file.file_path}")
                    converted_slices = nii_processor.convert_nii_to_base64_slices(nii_file.file_path, axis=2)

                    if converted_slices and len(converted_slices) > 0:
                        print(f"Successfully converted {nii_file.file_name} to {len(converted_slices)} slices")
                        sample_images.extend(converted_slices)  # Add all slices from this NIfTI file
                    else:
                        print(f"Failed to convert {nii_file.file_name}, using placeholder")
                        # Fallback to placeholder if conversion fails
                        placeholder_svg = f"""data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 400 400'>
                            <rect width='400' height='400' fill='%23fef2f2'/>
                            <circle cx='200' cy='200' r='80' fill='%23fecaca' stroke='%23dc2626' stroke-width='2'/>
                            <text x='200' y='180' font-family='Arial' font-size='12' fill='%23dc2626' text-anchor='middle'>NIfTI Conversion Failed</text>
                            <text x='200' y='200' font-family='Arial' font-size='10' fill='%23dc2626' text-anchor='middle'>{nii_file.file_name}</text>
                            <text x='200' y='220' font-family='Arial' font-size='10' fill='%23dc2626' text-anchor='middle'>Check server logs</text>
                        </svg>"""
                        sample_images.append(placeholder_svg)
                else:
                    print(f"No file path or file doesn't exist for {nii_file.file_name}")
                    # Create a placeholder for files without actual file data (legacy entries)
                    placeholder_svg = f"""data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 400 400'>
                        <defs>
                            <radialGradient id='grad{i}' cx='50%' cy='50%' r='50%'>
                                <stop offset='0%' style='stop-color:%23e5e7eb;stop-opacity:1' />
                                <stop offset='70%' style='stop-color:%23d1d5db;stop-opacity:1' />
                                <stop offset='100%' style='stop-color:%236b7280;stop-opacity:1' />
                            </radialGradient>
                        </defs>
                        <rect width='400' height='400' fill='%23111827'/>
                        <circle cx='200' cy='200' r='150' fill='url(%23grad{i})' opacity='0.8'/>
                        <circle cx='200' cy='200' r='120' fill='none' stroke='%23f9fafb' stroke-width='2' opacity='0.6'/>
                        <circle cx='200' cy='200' r='80' fill='none' stroke='%23f9fafb' stroke-width='1' opacity='0.4'/>
                        <circle cx='200' cy='200' r='40' fill='none' stroke='%23f9fafb' stroke-width='1' opacity='0.3'/>
                        <text x='200' y='50' font-family='monospace' font-size='12' fill='%23f9fafb' text-anchor='middle'>{nii_file.file_name}</text>
                        <text x='200' y='70' font-family='monospace' font-size='10' fill='%23d1d5db' text-anchor='middle'>Legacy File - No Data</text>
                        <text x='200' y='370' font-family='monospace' font-size='10' fill='%23d1d5db' text-anchor='middle'>Uploaded: {nii_file.uploaded_at}</text>
                        <text x='200' y='385' font-family='monospace' font-size='8' fill='%23a1a1aa' text-anchor='middle'>File ID: {nii_file.id}</text>
                    </svg>"""
                    sample_images.append(placeholder_svg)
        
        return PatientImagesResponse(
            success=True,
            images=sample_images,
            message=f"Retrieved {len(sample_images)} images for patient {case_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve patient images: {str(e)}")
