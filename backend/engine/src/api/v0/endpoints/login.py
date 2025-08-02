
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Request
from ....data_models.login import LoginResponse

router = APIRouter()

# TODO: include all the endpoints
# Frontend -> Backend Engine endpoints
# 1. Login Page
@router.post("/login", response_model=LoginResponse)
async def login_doctor_account(request: Request) -> Dict[str, Any]:
    """
    Login doctor account
    
    Algorithm:
        I. Doctor Authentication & Validation
        II. Patient Retrieval
    
    Args:
        request (Request): Request containing doctor's email and password

    Returns:
        LoginResponse: Response with doctor's list of patients
        # TODO: Or should we return a Doctor data model?

    Raises:
        HTTPException: 400 if doctor email is not found or password is incorrect
    """
    # Retrieve doctor email from LoginRequest
    doctor_email = request.email
    
    # I. Doctor Authentication & Validation
    # # Check if doctor email is valid
    # if not is_valid_email(doctor_email):
    #     raise HTTPException(status_code=400, detail="Invalid email")
    
    # Check if doctor email is in the database
    if not is_doctor_email_in_database(doctor_email):
        raise HTTPException(status_code=400, detail="Doctor email not found")
    
    # Check if doctor password is correct
    if not is_doctor_password_correct(doctor_email, request.password):
        raise HTTPException(status_code=400, detail="Invalid password")
    
    # II. Patient Retrieval
    # Retrieve doctor's patients from Patient Data Service
    patients = get_doctor_patients(doctor_email)
    
    # Return the patients
    return LoginResponse(doctor=doctor_email, patients=patients)

# 2. Dashboard Page
# I. Select Patient Request
# II. Logout Request?

# 3. Chat Page
# I.User Message Request

# Frontend <- Backend Engine endpoints

# Backend Engine -> Patient Data Service endpoints

# Backend Engine <- Patient Data Service endpoints

# Backend Engine -> LLM Service endpoints

# Backend Engine <- LLM Service endpoints

