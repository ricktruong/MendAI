import datetime
import uuid
from zoneinfo import ZoneInfo
from typing import Optional, Union, Literal

from pydantic import BaseModel, Field


class CommonResponse(BaseModel):
    status: Union[Literal["success", "error"], str] = (
        "success"  # Indicates success or failure of the request
    )
    message: Optional[str] = (
        None  # Brief message describing the result or error details
    )
    session_id: Optional[str] = (
        None  # Session ID, echoing one from request for traceability
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo("America/Los_Angeles"))
    )  # Timestamp indicating when response was generated

    def generate_session_id(self) -> None:
        self.session_id = str(uuid.uuid4())
