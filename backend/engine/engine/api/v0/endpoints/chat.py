from fastapi import APIRouter, HTTPException
import logging
from typing import List, Dict, Any
from pydantic import BaseModel
import httpx
import os

from ....data_models.chat import ChatRequest, ChatResponse, Message, AnalysisResult
from ....services.conversation_manager import get_conversation_manager
from datetime import datetime
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)

# Biomedical LLM service configuration
BIOMEDICAL_LLM_URL = os.getenv("BIOMEDICAL_LLM_URL", "http://biomedical_llm:8003")

# 3. Patient Dashboard Page (formerly Chat Page)
# I.User Message Request
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat with the LLM for Patient Dashboard Page - forwards to biomedical_llm service
    
    This endpoint now includes conversation memory:
    - Maintains conversation history per session
    - Automatically manages context window for LLM
    - Persists conversations across requests
    """
    try:
        logger.info(f"Received chat request with {len(request.messages)} messages, patient_id={request.patient_id}")

        # Generate session ID if not provided
        if not request.session_id:
            request.session_id = str(uuid.uuid4())
            logger.info(f"Generated new session_id: {request.session_id}")

        # Get conversation manager
        conversation_manager = get_conversation_manager()
        
        # Get the last user message from the request
        user_messages = [msg for msg in request.messages if msg.type == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found in request")
        
        last_user_message = user_messages[-1]
        
        # Add user message to conversation history
        conversation_manager.add_message(
            session_id=request.session_id,
            role="user",
            content=last_user_message.content,
            patient_id=request.patient_id
        )
        
        # Get conversation history optimized for LLM context
        conversation_history = conversation_manager.get_context_for_llm(
            session_id=request.session_id,
            max_tokens=2000  # Leave room for system prompt and response
        )
        
        logger.info(f"Using {len(conversation_history)} messages from conversation history for LLM context")

        # Forward the request to biomedical_llm service with conversation history
        try:
            # Prepare payload with conversation history
            payload = {
                "messages": conversation_history
            }
            
            # Add patient_id if provided
            if request.patient_id:
                payload["patient_id"] = request.patient_id
                logger.info(f"Including patient_id in biomedical_llm request: {request.patient_id}")

            # Call biomedical LLM service
            logger.info(f"Forwarding chat request to biomedical_llm service at {BIOMEDICAL_LLM_URL}/chat")
            async with httpx.AsyncClient(timeout=60.0) as client:  # Increased timeout for LLM processing
                llm_response = await client.post(
                    f"{BIOMEDICAL_LLM_URL}/chat",
                    json=payload
                )

                if llm_response.status_code == 200:
                    llm_data = llm_response.json()
                    ai_content = llm_data.get("response", "I apologize, but I couldn't generate a response at this time.")
                    model_used = llm_data.get("model", "unknown")
                    logger.info(f"Received response from biomedical LLM (model: {model_used})")
                else:
                    error_detail = llm_response.text
                    logger.error(f"Biomedical LLM service returned status {llm_response.status_code}: {error_detail}")
                    raise Exception(f"Biomedical LLM service returned status {llm_response.status_code}")

        except httpx.TimeoutException:
            logger.error("Timeout waiting for biomedical LLM service response")
            raise HTTPException(
                status_code=504,
                detail="The AI service is taking too long to respond. Please try again."
            )
        except httpx.ConnectError as e:
            logger.error(f"Cannot connect to biomedical LLM service at {BIOMEDICAL_LLM_URL}: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"Cannot connect to AI service at {BIOMEDICAL_LLM_URL}. Please ensure the service is running."
            )
        except Exception as llm_error:
            logger.error(f"Error calling biomedical LLM service: {str(llm_error)}")
            raise HTTPException(
                status_code=502,
                detail=f"AI service error: {str(llm_error)}"
            )

        # Add AI response to conversation history
        conversation_manager.add_message(
            session_id=request.session_id,
            role="assistant",
            content=ai_content,
            patient_id=request.patient_id
        )

        # Create AI response message
        ai_response = Message(
            id=str(uuid.uuid4()),
            type="assistant",
            content=ai_content,
            timestamp=datetime.now()
        )

        # Add the AI response to the messages
        updated_messages = request.messages + [ai_response]

        response = ChatResponse(
            session_id=request.session_id,
            messages=updated_messages,
            patient_id=request.patient_id
        )

        logger.info(f"Chat response generated successfully for session {request.session_id}")
        
        # Get session stats for monitoring
        stats = conversation_manager.get_session_stats()
        logger.info(f"Conversation stats: {stats}")
        
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Get conversation history for a session
    
    This allows the frontend to retrieve past conversations,
    useful for:
    - Restoring conversations after page refresh
    - Reviewing past interactions
    - Exporting conversation logs
    """
    try:
        conversation_manager = get_conversation_manager()
        history = conversation_manager.get_conversation_history(session_id)
        
        # Convert to Message format for frontend
        messages = [
            Message(
                id=str(uuid.uuid4()),
                type="assistant" if msg["role"] == "assistant" else "user",
                content=msg["content"],
                timestamp=datetime.fromisoformat(msg["timestamp"]) if "timestamp" in msg else datetime.now()
            )
            for msg in history
        ]
        
        return {
            "session_id": session_id,
            "messages": messages,
            "count": len(messages)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chat history: {str(e)}")


@router.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str):
    """
    Clear conversation history for a session
    
    Useful for:
    - Starting fresh conversations
    - Privacy/data cleanup
    - Resetting context
    """
    try:
        conversation_manager = get_conversation_manager()
        conversation_manager.clear_session(session_id)
        
        logger.info(f"Cleared conversation history for session {session_id}")
        return {
            "success": True,
            "message": f"Conversation history cleared for session {session_id}"
        }
        
    except Exception as e:
        logger.error(f"Error clearing chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear chat history: {str(e)}")


@router.get("/chat/stats")
async def get_conversation_stats():
    """
    Get statistics about active conversations
    
    Useful for monitoring and debugging
    """
    try:
        conversation_manager = get_conversation_manager()
        
        # Clean up expired sessions first
        conversation_manager.cleanup_expired_sessions()
        
        stats = conversation_manager.get_session_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# Frontend <- Backend Engine endpoints

# Backend Engine -> Patient Data Service endpoints

# Backend Engine <- Patient Data Service endpoints

# Backend Engine -> LLM Service endpoints

# Backend Engine <- LLM Service endpoints


