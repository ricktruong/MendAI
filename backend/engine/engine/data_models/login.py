from typing import List
from common.data_model.common_response import CommonResponse

class LoginResponse(CommonResponse):
    doctor: str         # TODO: Replace with proper Doctor model
    patients: List[str] # TODO: Replace with proper Patient model
