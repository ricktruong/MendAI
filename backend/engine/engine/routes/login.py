
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..types.login import LoginResponse

# Request model for login
class LoginRequest(BaseModel):
    email: str
    password: str

# Placeholder functions - these would be implemented to connect to actual services
def is_doctor_email_in_database(email: str) -> bool:
    # TODO: Implement actual database check
    # For now, accept any email
    return True

def is_doctor_password_correct(email: str, password: str) -> bool:
    # TODO: Implement actual password verification
    # For now, accept any password
    return True

def get_doctor_patients(email: str) -> list:
    # TODO: Implement actual patient retrieval
    return [
        "John Doe",
        "Jane Smith", 
        "Maria Garcia"
    ]

router = APIRouter(prefix="/login", tags=["login"])

# Frontend -> Backend Engine endpoints
# 1. Login Page
@router.post("/login", response_model=LoginResponse)
async def login_doctor_account(request: LoginRequest) -> LoginResponse:
    """
    Login doctor account
    
    Algorithm:
        I. Doctor Authentication & Validation
        II. Patient Retrieval
    
    Args:
        request (LoginRequest): Request containing doctor's email and password

    Returns:
        LoginResponse: Response with doctor's list of patients

    Raises:
        HTTPException: 400 if doctor email is not found or password is incorrect
    """
    
    # I. Doctor Authentication & Validation
    # Check if doctor email is in the database
    if not is_doctor_email_in_database(request.email):
        raise HTTPException(status_code=400, detail="Doctor email not found")
    
    # Check if doctor password is correct
    if not is_doctor_password_correct(request.email, request.password):
        raise HTTPException(status_code=400, detail="Invalid password")
    
    # II. Patient Retrieval
    # Retrieve doctor's patients from Patient Data Service
    patients = get_doctor_patients(request.email)
    
    # Return the patients
    return LoginResponse(doctor=request.email, patients=patients)


