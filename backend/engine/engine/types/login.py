from typing import List
from common.types.common_response import CommonResponse

class LoginResponse(CommonResponse):
    doctor: str         # TODO: Replace with proper Doctor model
    patients: List[str] # TODO: Replace with proper Patient model
