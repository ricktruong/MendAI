
from fastapi import APIRouter, HTTPException, Request
from ....data_models.login import LoginResponse

# Placeholder functions - these would be implemented to connect to actual services
def is_doctor_email_in_database(email: str) -> bool:
    # TODO: Implement actual database check
    return True

def is_doctor_password_correct(email: str, password: str) -> bool:
    # TODO: Implement actual password verification
    return True

def get_doctor_patients(email: str) -> list:
    # TODO: Implement actual patient retrieval
    return []

router = APIRouter()

# TODO: include all the endpoints
# Frontend -> Backend Engine endpoints
# 1. Login Page
@router.post("/login", response_model=LoginResponse)
async def login_doctor_account(request: Request) -> LoginResponse:
    """
    Login doctor account
    
    Algorithm:
        I. Doctor Authentication & Validation
        II. Patient Retrieval
    
    Args:
        request (Request): Request containing doctor's email and password

    Returns:
        LoginResponse: Response with doctor's list of patients

    Raises:
        HTTPException: 400 if doctor email is not found or password is incorrect
    """
    # TODO: Parse request body properly
    # doctor_email = request.body.doctor_email
    # For now, using placeholder data
    doctor_email = "doctor@example.com"
    
    # I. Doctor Authentication & Validation
    # # Check if doctor email is valid
    # if not is_valid_email(doctor_email):
    #     raise HTTPException(status_code=400, detail="Invalid email")
    
    # Check if doctor email is in the database
    if not is_doctor_email_in_database(doctor_email):
        raise HTTPException(status_code=400, detail="Doctor email not found")
    
    # Check if doctor password is correct
    if not is_doctor_password_correct(doctor_email, "password"):
        raise HTTPException(status_code=400, detail="Invalid password")
    
    # II. Patient Retrieval
    # Retrieve doctor's patients from Patient Data Service
    patients = get_doctor_patients(doctor_email)
    
    # Return the patients
    return LoginResponse(doctor=doctor_email, patients=patients)


