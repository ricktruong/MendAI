"""
Chat data models for biomedical_llm service
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Individual chat message"""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat request from engine service"""
    messages: List[ChatMessage] = Field(..., description="Conversation history")
    patient_id: Optional[str] = Field(None, description="Patient ID for context enrichment")
    model: Optional[str] = Field("biomedlm", description="Model to use (biomedlm, biomistral, openbiollm)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "user", "content": "What are the key concerns for this patient?"}
                ],
                "patient_id": "a40640b3-b1a1-51ba-bf33-10eb05b37177",
                "model": "biomedlm"
            }
        }


class ChatResponse(BaseModel):
    """Chat response to engine service"""
    response: str = Field(..., description="Generated response text")
    model_used: str = Field(..., description="Model that generated the response")
    patient_context_used: bool = Field(False, description="Whether patient context was included")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Based on the clinical information provided...",
                "model_used": "gpt-4o-mini",
                "patient_context_used": True
            }
        }
