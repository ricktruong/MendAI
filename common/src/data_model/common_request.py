from abc import ABC
from typing import Optional

from pydantic import BaseModel

class CommonRequest(BaseModel, ABC):
    session_id: Optional[str] = (
        None # Field for auto-generated session ID
    )
    