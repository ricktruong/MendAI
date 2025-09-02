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

class RecentCase(BaseModel):
    id: str
    patient_name: str
    file_name: str
    uploaded_at: str

class DashboardResponse(BaseModel):
    patients: List[Patient]
    recent_cases: List[RecentCase]

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
        file_name="CT_Head_001.dcm",
        uploaded_at="2025-01-27"
    ),
    RecentCase(
        id="ct-002", 
        patient_name="Jane Smith",
        file_name="CT_Chest_045.dcm",
        uploaded_at="2025-01-25"
    ),
    RecentCase(
        id="ct-003",
        patient_name="Maria Garcia", 
        file_name="CT_Abdomen_102.dcm",
        uploaded_at="2025-01-22"
    ),
]

# 2. Dashboard Page
@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_data() -> DashboardResponse:
    """
    Get dashboard data including patients and recent cases
    
    Returns:
        DashboardResponse: Dashboard data with patients and recent cases
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
        
        # Create new case
        new_case = RecentCase(
            id=new_id,
            patient_name=patient_name,
            file_name=file_name,
            uploaded_at=uploaded_at
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
            # Delete the file
            # TODO: In production, delete file from storage
            updated_case.file_name = ""  # Clear filename
        elif file and file.filename:
            # If new file provided, update filename
            # TODO: In production, handle file upload to storage
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
        case_found = False
        for case in stored_cases:
            if case.id == case_id:
                case_found = True
                break
        
        if not case_found:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # In a real system, these would be fetched from a medical imaging server (PACS)
        # or from file storage based on the patient's actual uploaded DICOM files
        # For now, return placeholder image URLs that the frontend can display
        sample_images = [
            f"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 400 400'><rect width='400' height='400' fill='%23f3f4f6'/><circle cx='200' cy='200' r='120' fill='%23d1d5db' stroke='%236b7280' stroke-width='3'/><text x='200' y='190' font-family='Arial' font-size='16' fill='%23374151' text-anchor='middle'>Patient: {case_id}</text><text x='200' y='210' font-family='Arial' font-size='14' fill='%236b7280' text-anchor='middle'>CT Scan - Axial View</text><text x='200' y='230' font-family='Arial' font-size='12' fill='%239ca3af' text-anchor='middle'>Slice 1 of 3</text></svg>",
            f"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 400 400'><rect width='400' height='400' fill='%23f3f4f6'/><ellipse cx='200' cy='200' rx='80' ry='120' fill='%23d1d5db' stroke='%236b7280' stroke-width='3'/><text x='200' y='190' font-family='Arial' font-size='16' fill='%23374151' text-anchor='middle'>Patient: {case_id}</text><text x='200' y='210' font-family='Arial' font-size='14' fill='%236b7280' text-anchor='middle'>CT Scan - Sagittal View</text><text x='200' y='230' font-family='Arial' font-size='12' fill='%239ca3af' text-anchor='middle'>Slice 2 of 3</text></svg>",
            f"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 400 400'><rect width='400' height='400' fill='%23f3f4f6'/><ellipse cx='200' cy='200' rx='120' ry='80' fill='%23d1d5db' stroke='%236b7280' stroke-width='3'/><text x='200' y='190' font-family='Arial' font-size='16' fill='%23374151' text-anchor='middle'>Patient: {case_id}</text><text x='200' y='210' font-family='Arial' font-size='14' fill='%236b7280' text-anchor='middle'>CT Scan - Coronal View</text><text x='200' y='230' font-family='Arial' font-size='12' fill='%239ca3af' text-anchor='middle'>Slice 3 of 3</text></svg>"
        ]
        
        return PatientImagesResponse(
            success=True,
            images=sample_images,
            message=f"Retrieved {len(sample_images)} images for patient {case_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve patient images: {str(e)}")
