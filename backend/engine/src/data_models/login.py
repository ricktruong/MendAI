from typing import List
from common.src.data_model.common_response import CommonResponse

class LoginResponse(CommonResponse):
    doctor: str
    patients: List[Patient] # Another data model for patient?
