from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

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

class RecentCase(BaseModel):
    id: str
    patient_name: str
    file_name: str  # Keep for backward compatibility
    uploaded_at: str
    files: List[PatientFile] = []  # New field for multiple files

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

# In-memory storage for demo (in production, this would be a database)
stored_cases = [
    RecentCase(
        id="ct-001",
        patient_name="John Doe",
        file_name="CT_Head_001.dcm",  # Primary file for backward compatibility
        uploaded_at="2025-01-27",
        files=[
            PatientFile(id="file-001-1", file_name="CT_Head_001.dcm", uploaded_at="2025-01-27"),
            PatientFile(id="file-001-2", file_name="CT_Head_002.dcm", uploaded_at="2025-01-26"),
        ]
    ),
    RecentCase(
        id="ct-002",
        patient_name="Jane Smith",
        file_name="CT_Chest_045.dcm",
        uploaded_at="2025-01-25",
        files=[
            PatientFile(id="file-002-1", file_name="CT_Chest_045.dcm", uploaded_at="2025-01-25"),
        ]
    ),
    RecentCase(
        id="ct-003",
        patient_name="Maria Garcia",
        file_name="CT_Abdomen_102.dcm",
        uploaded_at="2025-01-22",
        files=[
            PatientFile(id="file-003-1", file_name="CT_Abdomen_102.dcm", uploaded_at="2025-01-22"),
            PatientFile(id="file-003-2", file_name="CT_Abdomen_103.dcm", uploaded_at="2025-01-21"),
            PatientFile(id="file-003-3", file_name="CT_Abdomen_104.dcm", uploaded_at="2025-01-20"),
        ]
    ),
]

# 2. Patient List Page (formerly Dashboard Page)
@router.get("/dashboard", response_model=DashboardResponse)
async def get_patient_list_data() -> DashboardResponse:
    """
    Get patient list data including patients and recent cases for Patient List Page
    
    Returns:
        DashboardResponse: Patient list data with patients and recent cases
    """
    try:
        # TODO: Implement actual data retrieval from database
        # For now, using in-memory storage
        
        patients = [
            Patient(id="1", name="John Doe", age=54, gender="Male"),
            Patient(id="2", name="Jane Smith", age=42, gender="Female"),
            Patient(id="3", name="Maria Garcia", age=37, gender="Female"),
        ]
        
        return DashboardResponse(patients=patients, recent_cases=stored_cases)
        
    except Exception as e:
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
        
        # TODO: In production, save file to storage (S3, local filesystem, etc.)
        # For now, just use the uploaded filename
        file_name = file.filename or f"uploaded_file_{new_id}"
        
        # Generate file ID
        file_id = f"file-{new_id}-1"

        # Create new case with file list
        new_case = RecentCase(
            id=new_id,
            patient_name=patient_name,
            file_name=file_name,  # Primary file for backward compatibility
            uploaded_at=uploaded_at,
            files=[PatientFile(id=file_id, file_name=file_name, uploaded_at=uploaded_at)]
        )

        # Add to in-memory storage (in production, save to database)
        stored_cases.append(new_case)
        
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
        
        if case_index is None:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Validate input
        if not patient_name.strip():
            raise HTTPException(status_code=400, detail="Patient name is required")
        
        # Update case data
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
            # TODO: In production, handle file upload to storage

            # Generate new file ID
            existing_file_count = len(updated_case.files) if updated_case.files else 0
            new_file_id = f"file-{case_id}-{existing_file_count + 1}"

            # Create new file record
            new_file = PatientFile(
                id=new_file_id,
                file_name=file.filename,
                uploaded_at=uploaded_at
            )

            # Add to files list
            if not updated_case.files:
                updated_case.files = []
            updated_case.files.append(new_file)

            # Update primary file reference to the newest file
            updated_case.file_name = file.filename
        
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

        if not case_found:
            raise HTTPException(status_code=404, detail="Patient not found")

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

        if not case_found:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Filter to only DICOM files
        dicom_files = [f for f in case_found.files if f.file_name.lower().endswith('.dcm')]

        if not dicom_files:
            # No DICOM files, return placeholder
            sample_images = [
                f"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 400 400'><rect width='400' height='400' fill='%23fef2f2'/><circle cx='200' cy='200' r='80' fill='%23fecaca' stroke='%23dc2626' stroke-width='2'/><text x='200' y='190' font-family='Arial' font-size='14' fill='%23dc2626' text-anchor='middle'>No DICOM Files</text><text x='200' y='210' font-family='Arial' font-size='12' fill='%23dc2626' text-anchor='middle'>Upload .dcm files</text></svg>"
            ]
        else:
            # Generate preview images for each DICOM file
            # In a real system, this would convert DICOM to PNG/JPEG
            # For now, create informative placeholders that look like medical images
            sample_images = []
            for i, dicom_file in enumerate(dicom_files):
                # Create a more realistic medical image placeholder
                image_svg = f"""data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 400 400'>
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
                    <text x='200' y='50' font-family='monospace' font-size='12' fill='%23f9fafb' text-anchor='middle'>{dicom_file.file_name}</text>
                    <text x='200' y='70' font-family='monospace' font-size='10' fill='%23d1d5db' text-anchor='middle'>DICOM Image {i+1} of {len(dicom_files)}</text>
                    <text x='200' y='370' font-family='monospace' font-size='10' fill='%23d1d5db' text-anchor='middle'>Uploaded: {dicom_file.uploaded_at}</text>
                    <text x='200' y='385' font-family='monospace' font-size='8' fill='%23a1a1aa' text-anchor='middle'>File ID: {dicom_file.id}</text>
                </svg>"""
                sample_images.append(image_svg)
        
        return PatientImagesResponse(
            success=True,
            images=sample_images,
            message=f"Retrieved {len(sample_images)} images for patient {case_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve patient images: {str(e)}")
