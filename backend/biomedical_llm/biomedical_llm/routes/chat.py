"""
Chat routes for biomedical_llm service
Handles LLM inference requests from the engine service
"""
import structlog
from fastapi import APIRouter, HTTPException

from ..types.chat import ChatRequest, ChatResponse
from ..services.openai_service import get_openai_service
from ..services.patient_data_client import get_patient_data_client

router = APIRouter()
logger = structlog.get_logger()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat endpoint for biomedical LLM inference
    
    This endpoint:
    1. Receives chat request from engine service
    2. Optionally fetches patient data for context enrichment
    3. Calls OpenAI API with biomedical-specific prompts
    4. Returns AI-generated clinical insights
    
    Args:
        request: ChatRequest with messages, optional patient_id, and model
        
    Returns:
        ChatResponse with generated text and metadata
    """
    try:
        logger.info(f"Received chat request with {len(request.messages)} messages")
        
        # Extract messages as dict format
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Validate we have messages
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user messages found")
        
        # Get services
        openai_service = get_openai_service()
        patient_data_client = get_patient_data_client()
        
        # Fetch patient data if patient_id provided
        patient_context = None
        patient_context_used = False
        
        if request.patient_id:
            try:
                logger.info(f"Fetching patient data for: {request.patient_id}")
                patient_context = await patient_data_client.get_patient_data(request.patient_id)
                
                if patient_context:
                    logger.info("Successfully retrieved patient context")
                    patient_context_used = True
                else:
                    logger.warning(f"Patient data not found for {request.patient_id}, continuing without context")
            except Exception as e:
                logger.warning(f"Failed to fetch patient data: {str(e)}, continuing without context")
        
        # Generate response using OpenAI
        logger.info("Generating response with OpenAI")
        response_text = openai_service.chat_completion(
            messages=messages,
            patient_context=patient_context,
            patient_id=request.patient_id,
            model=None  # Use default from config
        )
        
        # Determine model used (for now it's always OpenAI, but can be extended)
        model_used = f"openai-{openai_service.settings.openai_model}"
        
        return ChatResponse(
            response=response_text,
            model_used=model_used,
            patient_context_used=patient_context_used
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.get("/models")
def list_models():
    """
    List available biomedical LLM models
    
    Returns:
        Dict with available models and their status
    """
    return {
        "available_models": [
            {
                "id": "biomedlm",
                "name": "OpenAI GPT-4o-mini",
                "description": "OpenAI's GPT-4o-mini with biomedical prompts",
                "status": "active",
                "provider": "openai"
            },
            {
                "id": "gpt-4",
                "name": "OpenAI GPT-4",
                "description": "OpenAI's GPT-4 with biomedical prompts (higher cost, better quality)",
                "status": "available",
                "provider": "openai"
            },
            {
                "id": "biomistral",
                "name": "BioMistral",
                "description": "Mistral-based biomedical model via Ollama",
                "status": "future",
                "provider": "ollama"
            },
            {
                "id": "openbiollm",
                "name": "OpenBioLLM",
                "description": "LLaMA3-based biomedical model via Ollama",
                "status": "future",
                "provider": "ollama"
            }
        ]
    }
