from fastapi import APIRouter, HTTPException
import logging
from typing import List, Dict, Any
from pydantic import BaseModel
import httpx
import os

from ....data_models.chat import ChatRequest, ChatResponse, Message, AnalysisResult
from datetime import datetime
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)

# Biomedical LLM service configuration
BIOMEDICAL_LLM_URL = os.getenv("BIOMEDICAL_LLM_URL", "http://biomedical_llm:8003")

<<<<<<< HEAD
# AI Analysis Models
class FileAnalysisRequest(BaseModel):
    patient_id: str
    file_ids: List[str]
    file_names: List[str]

class FileAnalysisResult(BaseModel):
    file_id: str
    file_name: str
    findings: List[str]
    confidence: float

class ComprehensiveAnalysisResponse(BaseModel):
    patient_id: str
    files_analyzed: int
    file_results: List[FileAnalysisResult]
    comprehensive_summary: str
    key_findings: List[str]
    recommendations: List[str]
    overall_confidence: float

# 3. Patient Dashboard Page
=======
# 3. Patient Dashboard Page (formerly Chat Page)
>>>>>>> da8442b84b104b4d8bf63ed52cb55cccac1f5f70
# I.User Message Request
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat with the LLM for Patient Dashboard Page
    """
    try:
        logger.info(f"Received chat request with {len(request.messages)} messages")

        # Generate session ID if not provided
        if not request.session_id:
            request.session_id = str(uuid.uuid4())

        # Process the messages through the biomedical LLM service
        try:
            # Convert messages to format expected by biomedical_llm service
            llm_messages = [
                {
                    "role": "assistant" if msg.type == "assistant" else "user",
                    "content": msg.content
                }
                for msg in request.messages
            ]

            # Call biomedical LLM service
            async with httpx.AsyncClient(timeout=30.0) as client:
                llm_response = await client.post(
                    f"{BIOMEDICAL_LLM_URL}/chat",
                    json={
                        "messages": llm_messages,
                        "patient_id": request.patient_id,
                        "model": "biomedlm"
                    }
                )

                if llm_response.status_code == 200:
                    llm_data = llm_response.json()
                    ai_content = llm_data.get("response", "I apologize, but I couldn't generate a response at this time.")
                    model_used = llm_data.get("model_used", "unknown")
                    logger.info(f"Received response from biomedical LLM ({model_used})")
                else:
                    logger.warning(f"Biomedical LLM service returned status {llm_response.status_code}")
                    raise Exception("Biomedical LLM service unavailable")

        except Exception as llm_error:
            logger.warning(f"Failed to call biomedical LLM service: {str(llm_error)}. Using fallback response.")
            # Fallback to mock response if biomedical LLM is unavailable
            ai_content = "I've analyzed your query. Based on the patient's medical history and current symptoms, here are my findings...\n\n*Note: Biomedical LLM service is currently unavailable. This is a fallback response.*"

        # Create AI response message
        ai_response = Message(
            id=str(uuid.uuid4()),
            type="assistant",
            content=ai_content,
            timestamp=datetime.now(),
            analysis_results=[
                AnalysisResult(
                    type="summary",
                    title="Clinical Summary",
                    content={
                        "note": "AI-assisted analysis provided",
                        "source": "Biomedical LLM"
                    },
                    confidence=0.85
                )
            ]
        )

        # Add the AI response to the messages
        updated_messages = request.messages + [ai_response]

        response = ChatResponse(
            session_id=request.session_id,
            messages=updated_messages,
            patient_id=request.patient_id
        )

        logger.info(f"Chat response generated successfully for session {request.session_id}")
        return response

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Frontend <- Backend Engine endpoints

# Backend Engine -> Patient Data Service endpoints

# Backend Engine <- Patient Data Service endpoints

# Backend Engine -> LLM Service endpoints

# Backend Engine <- LLM Service endpoints

