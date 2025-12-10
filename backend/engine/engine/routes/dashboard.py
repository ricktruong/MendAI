from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import asyncio
import httpx
from pathlib import Path
from engine.utils.nii_processor import nii_processor

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

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
    age: Optional[int] = None  # Patient age calculated from corrected birthDate
    gender: Optional[str] = None
    race: Optional[str] = None
    ethnicity: Optional[str] = None
    maritalStatus: Optional[str] = None
    managingOrganization: Optional[str] = None
    language: Optional[str] = None

class PatientListResponse(BaseModel):
    patients: List[Patient]
    recent_cases: List[RecentCase]
    total: int = 0  # Total number of patients
    page: int = 1   # Current page
    page_size: int = 20  # Items per page
    total_pages: int = 1  # Total number of pages

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
# Initialize with default cases using REAL FHIR patient IDs with actual medical data
_default_cases = [
    RecentCase(
        id="14889227",
        patient_name="Patient_19621044",
        file_name="CT_Head_001.nii",
        uploaded_at="2025-09-28",
        files=[PatientFile(id="file-001-1", file_name="CT_Head_001.nii", uploaded_at="2025-09-28", file_path=None)],
        fhirId="a40640b3-b1a1-51ba-bf33-10eb05b37177",  # REAL - Has 15 conditions, 50 medications
        birthDate="2104-03-04",
        gender="male",
        race="Unknown",
        ethnicity="Unknown",
        maritalStatus="Unknown",
        managingOrganization="Healthcare Facility",
        language="en"
    ),
    RecentCase(
        id="14889228",
        patient_name="Patient_14987745",
        file_name="CT_Chest_045.nii",
        uploaded_at="2025-09-27",
        files=[PatientFile(id="file-002-1", file_name="CT_Chest_045.nii", uploaded_at="2025-09-27", file_path=None)],
        fhirId="157b5ca8-1a12-57d1-ade6-5e311fcd2312",  # REAL - Has 41 conditions, 50 medications
        birthDate="1965-05-22",
        gender="male",
        race="Unknown",
        ethnicity="Unknown",
        maritalStatus="Unknown",
        managingOrganization="Healthcare Facility",
        language="en"
    ),
    RecentCase(
        id="14889229",
        patient_name="Patient_19852995",
        file_name="CT_Abdomen_102.nii",
        uploaded_at="2025-09-26",
        files=[PatientFile(id="file-003-1", file_name="CT_Abdomen_102.nii", uploaded_at="2025-09-26", file_path=None)],
        fhirId="bd380b2e-3b4a-5225-b692-55d035cec534",  # REAL - Has 24 conditions, 50 medications
        birthDate="1992-11-03",
        gender="female",
        race="Unknown",
        ethnicity="Unknown",
        maritalStatus="Unknown",
        managingOrganization="Healthcare Facility",
        language="en"
    ),
    RecentCase(
        id="14889230",
        patient_name="Patient_19794709",
        file_name="CT_Brain_Trauma_003.nii",
        uploaded_at="2025-09-25",
        files=[PatientFile(id="file-004-1", file_name="CT_Brain_Trauma_003.nii", uploaded_at="2025-09-25", file_path=None)],
        fhirId="4b8344ae-1dbd-53e2-803c-d9912bbe0a8b",  # REAL - Has 12 conditions, 38 medications
        birthDate="1955-07-14",
        gender="male",
        race="Unknown",
        ethnicity="Unknown",
        maritalStatus="Unknown",
        managingOrganization="Healthcare Facility",
        language="en"
    ),
    RecentCase(
        id="14889231",
        patient_name="Patient_19674707",
        file_name="CT_Spine_067.nii",
        uploaded_at="2025-09-24",
        files=[PatientFile(id="file-005-1", file_name="CT_Spine_067.nii", uploaded_at="2025-09-24", file_path=None)],
        fhirId="ebcb8e92-a469-5637-a3e1-5808b0d0d206",  # REAL - Has 50 conditions, 50 medications
        birthDate="1980-03-28",
        gender="female",
        race="Unknown",
        ethnicity="Unknown",
        maritalStatus="Unknown",
        managingOrganization="Healthcare Facility",
        language="en"
    ),
    RecentCase(
        id="14889232",
        patient_name="Patient_19580789",
        file_name="CT_Thorax_089.nii",
        uploaded_at="2025-09-23",
        files=[PatientFile(id="file-006-1", file_name="CT_Thorax_089.nii", uploaded_at="2025-09-23", file_path=None)],
        fhirId="adc104ea-ad67-5fcb-bbc6-3f010a5489fd",  # REAL - Has 50 conditions, 50 medications
        birthDate="1970-12-10",
        gender="male",
        race="Unknown",
        ethnicity="Unknown",
        maritalStatus="Unknown",
        managingOrganization="Healthcare Facility",
        language="en"
    ),
    RecentCase(
        id="14889233",
        patient_name="Patient_19519554",
        file_name="CT_Pelvis_045.nii",
        uploaded_at="2025-09-22",
        files=[PatientFile(id="file-007-1", file_name="CT_Pelvis_045.nii", uploaded_at="2025-09-22", file_path=None)],
        fhirId="b78c7cf9-5806-5add-8de6-dc96ad039263",  # REAL - Has 44 conditions, 50 medications
        birthDate="1988-08-19",
        gender="female",
        race="Unknown",
        ethnicity="Unknown",
        maritalStatus="Unknown",
        managingOrganization="Healthcare Facility",
        language="en"
    ),
    RecentCase(
        id="14889234",
        patient_name="Patient_19950252",
        file_name="CT_Neck_034.nii",
        uploaded_at="2025-09-21",
        files=[PatientFile(id="file-008-1", file_name="CT_Neck_034.nii", uploaded_at="2025-09-21", file_path=None)],
        fhirId="167fb11d-cdb0-5df0-b31d-d6849bc86f9c",  # REAL - Has 9 conditions, 0 medications
        birthDate="1963-04-07",
        gender="male",
        race="Unknown",
        ethnicity="Unknown",
        maritalStatus="Unknown",
        managingOrganization="Healthcare Facility",
        language="en"
    ),
]

# Load persisted cases or use defaults
stored_cases = load_stored_cases() or _default_cases

# 2. Patient List Page (formerly Dashboard Page)
@router.get("/", response_model=DashboardResponse)
async def get_patient_list_data(
    page: int = 1,
    page_size: int = 20
) -> DashboardResponse:
    """
    Get patient list data with pagination
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of patients per page (default: 20, max: 100)
    
    Returns:
        DashboardResponse: Paginated patient list data
    """
    from datetime import datetime
    import math

    try:
        # Validate pagination parameters
        page = max(1, page)  # Ensure page >= 1
        page_size = min(max(1, page_size), 100)  # Limit between 1 and 100

        # Fetch patient data from patient_data service
        PATIENT_DATA_URL = os.getenv("PATIENT_DATA_SERVICE_URL", "http://patient_data:8001")

        async def fetch_with_retry(url: str, max_retries: int = 3, initial_delay: float = 2.0):
            """
            Fetch with retry logic for handling sleeping services (502 errors).
            Render free tier services sleep after 15min inactivity and take ~10-30s to wake up.
            """
            async with httpx.AsyncClient(timeout=120.0) as client:
                for attempt in range(max_retries):
                    try:
                        response = await client.get(url)
                        if response.status_code == 502:
                            # Service is likely sleeping, wait and retry
                            if attempt < max_retries - 1:
                                delay = initial_delay * (2 ** attempt)  # Exponential backoff
                                print(f"⚠ Service returned 502 (likely sleeping). Retrying in {delay}s (attempt {attempt + 1}/{max_retries})...")
                                await asyncio.sleep(delay)
                                continue
                        response.raise_for_status()
                        return response
                    except httpx.HTTPStatusError as e:
                        if e.response.status_code == 502 and attempt < max_retries - 1:
                            delay = initial_delay * (2 ** attempt)
                            print(f"⚠ HTTP {e.response.status_code} error. Retrying in {delay}s (attempt {attempt + 1}/{max_retries})...")
                            await asyncio.sleep(delay)
                            continue
                        raise
                raise Exception(f"Failed after {max_retries} attempts")

        try:
            # Get list of patient subject IDs from FHIR (with retry for sleeping services)
            response = await fetch_with_retry(f"{PATIENT_DATA_URL}/api/patients/subject_ids")
                subject_ids_data = response.json()
                # Fix: API returns 'patient_ids' not 'subject_ids'
                all_subject_ids = subject_ids_data.get("patient_ids", subject_ids_data.get("subject_ids", []))

                total_patients = len(all_subject_ids)
                total_pages = math.ceil(total_patients / page_size)
                
                # Calculate pagination indices
                start_idx = (page - 1) * page_size
                end_idx = min(start_idx + page_size, total_patients)
                
                # Get paginated subset
                subject_ids = all_subject_ids[start_idx:end_idx]

                print(f"Fetching page {page}/{total_pages}: patients {start_idx+1}-{end_idx} of {total_patients}")

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

                        # Get birthDate and correct it if needed (subtract 78 years if in future)
                        birth_date_str = patient_raw.get("birthDate")
                        corrected_birth_date = birth_date_str
                        age = None
                        
                        if birth_date_str:
                            try:
                                birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
                                
                                # If date is in the future, keep subtracting 78 years until it's not
                                while birth_date.year > datetime.now().year:
                                    birth_date = birth_date.replace(year=birth_date.year - 78)
                                
                                corrected_birth_date = birth_date.strftime("%Y-%m-%d")
                                
                                # Calculate age from corrected birthdate
                                today = datetime.now()
                                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                            except Exception as e:
                                print(f"Error calculating age for {subject_id}: {e}")
                                age = None

                        # Create a case entry from patient data
                        return RecentCase(
                            id=patient_id,
                            patient_name=patient_name,
                            file_name="FHIR_Data.json",  # Placeholder for FHIR data
                            uploaded_at=datetime.now().strftime("%Y-%m-%d"),
                            files=[],
                            fhirId=subject_id,
                            birthDate=corrected_birth_date,
                            age=age,
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

                # Fetch patients for current page in parallel using asyncio.gather
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

                print(f"Successfully loaded {len(recent_cases)} patients from FHIR (page {page}/{total_pages})")
                if len(recent_cases) == 0 and page == 1:
                    print("No patients loaded, falling back to stored_cases")
                    return DashboardResponse(
                        patients=[], 
                        recent_cases=stored_cases,
                        total=len(stored_cases),
                        page=1,
                        page_size=page_size,
                        total_pages=1
                    )

                return DashboardResponse(
                    patients=patients,
                    recent_cases=recent_cases,
                    total=total_patients,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages
                )

            except httpx.HTTPError as e:
                print(f"Error connecting to patient_data service: {e}")
                # Fallback to stored_cases if service is unavailable
                return DashboardResponse(
                    patients=[],
                    recent_cases=stored_cases,
                    total=len(stored_cases),
                    page=1,
                    page_size=page_size,
                    total_pages=1
                )

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

        # Stream file directly to disk (memory-efficient for large files)
        # Max file size: 500MB (adjustable based on Render free tier limits)
        try:
            saved_file_path = await nii_processor.save_uploaded_file_streaming(
                file, 
                file_name, 
                max_size_mb=500
            )
            print(f"Saved uploaded NIfTI file: {saved_file_path}")
        except ValueError as e:
            raise HTTPException(status_code=413, detail=str(e))

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
    file: Optional[List[UploadFile]] = File(None),
    delete_file: Optional[str] = Form(None)
) -> UpdatePatientResponse:
    """
    Update an existing patient

    Args:
        case_id: ID of the case to update
        patient_name: New patient name
        uploaded_at: New date
        file: Optional list of new file uploads (supports multiple files)
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
        elif file and len(file) > 0:
            # Add new files to the patient's file list (preserve existing files)
            # Initialize files list if it doesn't exist
            if not updated_case.files:
                updated_case.files = []

            existing_file_count = len(updated_case.files)

            # Process each uploaded file
            for upload_file in file:
                if upload_file.filename:
                    # Validate file extension
                    if not (upload_file.filename.lower().endswith('.nii') or upload_file.filename.lower().endswith('.nii.gz')):
                        raise HTTPException(status_code=400, detail=f"Only .nii or .nii.gz files are supported. Got: {upload_file.filename}")

                    # Stream file directly to disk (memory-efficient for large files)
                    # Max file size: 500MB (adjustable based on Render free tier limits)
                    try:
                        saved_file_path = await nii_processor.save_uploaded_file_streaming(
                            upload_file,
                            upload_file.filename,
                            max_size_mb=500
                        )
                        print(f"Saved updated NIfTI file: {saved_file_path}")
                    except ValueError as e:
                        raise HTTPException(status_code=413, detail=str(e))

                    # Generate new file ID
                    existing_file_count += 1
                    new_file_id = f"file-{case_id}-{existing_file_count}"

                    # Create new file record
                    new_file = PatientFile(
                        id=new_file_id,
                        file_name=upload_file.filename,
                        uploaded_at=uploaded_at,
                        file_path=saved_file_path
                    )

                    # Add to files list
                    updated_case.files.append(new_file)

                    # Update primary file reference to the newest file
                    updated_case.file_name = upload_file.filename

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
    async def fetch_with_retry(url: str, max_retries: int = 3, initial_delay: float = 2.0):
        """
        Fetch with retry logic for handling sleeping services (502 errors).
        Render free tier services sleep after 15min inactivity and take ~10-30s to wake up.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(max_retries):
                try:
                    response = await client.get(url)
                    if response.status_code == 502:
                        # Service is likely sleeping, wait and retry
                        if attempt < max_retries - 1:
                            delay = initial_delay * (2 ** attempt)  # Exponential backoff
                            print(f"⚠ Service returned 502 (likely sleeping). Retrying in {delay}s (attempt {attempt + 1}/{max_retries})...")
                            await asyncio.sleep(delay)
                            continue
                    response.raise_for_status()
                    return response
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 502 and attempt < max_retries - 1:
                        delay = initial_delay * (2 ** attempt)
                        print(f"⚠ HTTP {e.response.status_code} error. Retrying in {delay}s (attempt {attempt + 1}/{max_retries})...")
                        await asyncio.sleep(delay)
                        continue
                    raise
            raise Exception(f"Failed after {max_retries} attempts")

    try:
        PATIENT_DATA_URL = os.getenv("PATIENT_DATA_SERVICE_URL", "http://patient_data:8001")

        response = await fetch_with_retry(f"{PATIENT_DATA_URL}/api/patients/{fhir_id}/normalized")
        return response.json()
    except httpx.HTTPError as e:
        error_msg = str(e)
        if "502" in error_msg:
            error_msg += " (Service may be sleeping on free tier. It should wake up automatically, but may take 10-30 seconds.)"
        print(f"Error fetching normalized patient data: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch patient data: {error_msg}")
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
async def get_patient_images(case_id: str, file_id: Optional[str] = None) -> PatientImagesResponse:
    """
    Get CT scan images for a specific patient

    Args:
        case_id: ID of the patient case
        file_id: Optional file ID to get images from a specific file only

    Returns:
        PatientImagesResponse: List of image URLs
    """
    print(f"[DEBUG] get_patient_images called with case_id={case_id}, file_id={file_id}")
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

        # If file_id is specified, filter to only that file
        if file_id:
            nii_files = [f for f in nii_files if f.id == file_id]
            if not nii_files:
                print(f"File {file_id} not found for patient {case_id}")
                return PatientImagesResponse(
                    success=False,
                    images=[
                        f"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 400 400'><rect width='400' height='400' fill='%23fef2f2'/><circle cx='200' cy='200' r='80' fill='%23fecaca' stroke='%23dc2626' stroke-width='2'/><text x='200' y='190' font-family='Arial' font-size='14' fill='%23dc2626' text-anchor='middle'>File Not Found</text><text x='200' y='210' font-family='Arial' font-size='12' fill='%23dc2626' text-anchor='middle'>File ID: {file_id}</text></svg>"
                    ],
                    message=f"File {file_id} not found"
                )

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
                    print(f"Converting NIfTI file: {nii_file.file_path} (file_id: {nii_file.id})")
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
