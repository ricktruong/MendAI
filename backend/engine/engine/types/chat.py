from typing import List, Optional, Union, Literal
from datetime import datetime
from pydantic import BaseModel

from common.types.common_request import CommonRequest
from common.types.common_response import CommonResponse


class Attachment(BaseModel):
    id: str
    type: Literal['image', 'document', 'lab-result']
    name: str
    url: Optional[str] = None


class AnalysisResult(BaseModel):
    type: Literal['imaging', 'vitals', 'lab', 'summary']
    title: str
    content: dict  # Changed from 'any' to 'dict' to fix linter error
    confidence: Optional[float] = None


class Message(BaseModel):
    id: str
    type: Literal['user', 'assistant']
    content: str
    timestamp: datetime
    attachments: Optional[List[Attachment]] = None
    analysis_results: Optional[List[AnalysisResult]] = None


class ChatRequest(CommonRequest):
    messages: List[Message]
    patient_id: Optional[str] = None


class ChatResponse(CommonResponse):
    messages: List[Message]
    patient_id: Optional[str] = None
