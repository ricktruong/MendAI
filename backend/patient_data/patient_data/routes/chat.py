from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from patient_data.services.fhir_service import (
    get_patient_bundle_normalized,
    get_patient_subject_ids
)
from patient_data.services.openai_service import (
    get_clinical_assessment,
    clinical_chat,
    get_medication_interaction_check
)

router = APIRouter(tags=["Clinical Decision Support"])

# ========================================
# REQUEST/RESPONSE MODELS
# ========================================

class ClinicalMessage(BaseModel):
    """Represents a single message in the conversation."""
    role: str = Field(..., description="'user' for healthcare provider or 'assistant' for AI")
    content: str = Field(..., description="Message content")

class ClinicalChatRequest(BaseModel):
    """Request for interactive clinical chat - accepts ANY user input."""
    patient_id: str = Field(..., description="Patient identifier")
    message: str = Field(..., description="User's message, question, statement, or follow-up")
    conversation_history: Optional[List[ClinicalMessage]] = Field(
        default=[],
        description="Previous conversation messages for context (keeps conversation flowing)"
    )

class ClinicalAssessmentRequest(BaseModel):
    """Request for structured clinical assessment."""
    patient_id: str = Field(..., description="Patient identifier")
    clinical_question: Optional[str] = Field(
        None,
        description="Specific clinical question (optional for general assessment)"
    )
    focus_area: Optional[str] = Field(
        None,
        description="Specific clinical area to focus on (e.g., 'cardiovascular', 'medications')"
    )

class MedicationCheckRequest(BaseModel):
    """Request to check medication interactions."""
    patient_id: str = Field(..., description="Patient identifier")
    new_medication: str = Field(..., description="Proposed medication to check for interactions")

# ========================================
# INTERACTIVE CHAT ENDPOINT (Main Feature)
# ========================================

@router.post("/chat")
async def clinical_chat_endpoint(request: ClinicalChatRequest):
    """
    Interactive clinical chat - handles ANY user input:
    - Questions: "What are the vital signs?"
    - Statements: "I'm concerned about the blood pressure"
    - Follow-ups: "What about the other medications?"
    - Clarifications: "Can you explain that in simpler terms?"
    - Commands: "Show me the lab results"
    - Conversational: "Thanks, that helps"
    
    The AI maintains context and responds naturally to all inputs.
    """
    try:
        print(f"💬 Chat Request:")
        print(f"   Patient: {request.patient_id}")
        print(f"   Message: '{request.message}'")
        print(f"   History: {len(request.conversation_history)} previous messages")
        
        # Get patient data (cached for performance)
        patient_data = get_patient_bundle_normalized(request.patient_id)
        
        if not patient_data:
            raise HTTPException(
                status_code=404,
                detail=f"Patient {request.patient_id} not found in system"
            )
        
        print(f"✓ Patient data loaded: {patient_data.get('name')} (Age: {patient_data.get('age')})")
        
        # Convert Pydantic models to dict format for OpenAI service
        history = [{"role": msg.role, "content": msg.content} 
                   for msg in request.conversation_history]
        
        # Call the AI chat service (handles context, reasoning, responses)
        result = await clinical_chat(
            patient_data=patient_data,
            conversation_history=history,
            new_question=request.message  # Works for ANY user input, not just questions
        )
        
        if not result.get("success"):
            error_detail = result.get('error', 'Unknown error occurred')
            print(f"✗ Chat failed: {error_detail}")
            raise HTTPException(
                status_code=500,
                detail=f"Clinical chat failed: {error_detail}"
            )
        
        response_preview = result.get('response', '')[:100]
        print(f"✓ Chat response generated: {len(result.get('response', ''))} chars")
        print(f"   Preview: '{response_preview}...'")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Unexpected error in chat endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error in clinical chat: {str(e)}"
        )

# ========================================
# STRUCTURED ASSESSMENT ENDPOINT
# ========================================

@router.post("/assessment")
async def clinical_assessment_endpoint(request: ClinicalAssessmentRequest):
    """
    Get a comprehensive structured clinical assessment.
    More formal than chat - provides organized clinical sections.
    """
    try:
        print(f"📋 Assessment Request:")
        print(f"   Patient: {request.patient_id}")
        print(f"   Question: {request.clinical_question or 'General assessment'}")
        print(f"   Focus: {request.focus_area or 'All areas'}")
        
        patient_data = get_patient_bundle_normalized(request.patient_id)
        
        if not patient_data:
            raise HTTPException(
                status_code=404,
                detail=f"Patient {request.patient_id} not found in system"
            )
        
        result = await get_clinical_assessment(
            patient_data=patient_data,
            clinical_question=request.clinical_question,
            focus_area=request.focus_area
        )
        
        if not result.get("success"):
            error_detail = result.get('error', 'Unknown error')
            print(f"✗ Assessment failed: {error_detail}")
            raise HTTPException(
                status_code=500,
                detail=f"Clinical assessment failed: {error_detail}"
            )
        
        print(f"✓ Assessment generated: {len(result.get('assessment', ''))} chars")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Error in assessment endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating clinical assessment: {str(e)}"
        )

# ========================================
# QUICK SUMMARY ENDPOINT
# ========================================

@router.get("/summary/{patient_id}")
async def get_quick_clinical_summary(patient_id: str):
    """
    Get a quick 3-4 sentence clinical summary.
    Perfect for morning rounds, handoffs, or quick reviews.
    """
    try:
        print(f"📝 Summary requested for patient: {patient_id}")
        
        patient_data = get_patient_bundle_normalized(patient_id)
        
        if not patient_data:
            raise HTTPException(
                status_code=404,
                detail=f"Patient {patient_id} not found"
            )
        
        # Request a concise summary from the AI
        result = await get_clinical_assessment(
            patient_data=patient_data,
            clinical_question=(
                "Provide a concise clinical summary in 3-4 sentences suitable for "
                "morning rounds or handoffs. Include: current diagnosis, active issues, "
                "and any immediate clinical concerns."
            )
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Summary generation failed: {result.get('error')}"
            )
        
        print(f"✓ Summary generated for {patient_data.get('name')}")
        
        return {
            "success": True,
            "patient_id": patient_id,
            "patient_name": patient_data.get('name'),
            "age": patient_data.get('age'),
            "gender": patient_data.get('gender'),
            "summary": result.get('assessment'),
            "from_cache": result.get('from_cache', False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Error generating summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating summary: {str(e)}"
        )

# ========================================
# MEDICATION INTERACTION CHECK
# ========================================

@router.post("/medication-interaction")
async def check_medication_interactions(request: MedicationCheckRequest):
    """
    Check for potential drug interactions before prescribing.
    Analyzes against current medications, conditions, and allergies.
    """
    try:
        print(f"💊 Medication check:")
        print(f"   Patient: {request.patient_id}")
        print(f"   New medication: {request.new_medication}")
        
        patient_data = get_patient_bundle_normalized(request.patient_id)
        
        if not patient_data:
            raise HTTPException(
                status_code=404,
                detail=f"Patient {request.patient_id} not found"
            )
        
        result = await get_medication_interaction_check(
            patient_data=patient_data,
            new_medication=request.new_medication
        )
        
        if not result.get("success"):
            error_detail = result.get('error', 'Unknown error')
            print(f"✗ Medication check failed: {error_detail}")
            raise HTTPException(
                status_code=500,
                detail=f"Medication interaction check failed: {error_detail}"
            )
        
        print(f"✓ Interaction analysis completed")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Error checking medication: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error checking medication interactions: {str(e)}"
        )

# ========================================
# PATIENT LIST ENDPOINT
# ========================================

@router.get("/patients")
async def list_available_patients():
    """
    Get list of all patients available for clinical review.
    Useful for browsing or selecting a patient to review.
    """
    try:
        print(f"👥 Fetching patient list...")
        
        patient_ids = get_patient_subject_ids()
        
        print(f"✓ Found {len(patient_ids)} patients")
        
        return {
            "success": True,
            "total_patients": len(patient_ids),
            "patient_ids": patient_ids
        }
        
    except Exception as e:
        print(f"✗ Error retrieving patient list: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving patient list: {str(e)}"
        )

# ========================================
# CONVERSATION STARTER SUGGESTIONS
# ========================================

@router.get("/chat/suggestions/{patient_id}")
async def get_conversation_starters(patient_id: str):
    """
    Get suggested conversation starters based on patient data.
    Helps users know what to ask about.
    """
    try:
        patient_data = get_patient_bundle_normalized(patient_id)
        
        if not patient_data:
            raise HTTPException(
                status_code=404,
                detail=f"Patient {patient_id} not found"
            )
        
        # Generate smart suggestions based on what data is available
        suggestions = []
        
        if patient_data.get('conditions'):
            suggestions.append("What are the active conditions?")
            suggestions.append("How are we managing the chronic conditions?")
        
        if patient_data.get('medications'):
            suggestions.append("Review current medications")
            suggestions.append("Are there any drug interactions?")
        
        if patient_data.get('observations'):
            suggestions.append("What are the recent vital signs?")
            suggestions.append("Any concerning lab values?")
        
        if patient_data.get('encounters'):
            suggestions.append("Summarize recent encounters")
        
        # Always include general ones
        suggestions.extend([
            "Give me a clinical overview",
            "What are the immediate concerns?",
            "What should I monitor?"
        ])
        
        return {
            "success": True,
            "patient_id": patient_id,
            "patient_name": patient_data.get('name'),
            "suggestions": suggestions[:6]  # Top 6 suggestions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating suggestions: {str(e)}"
        )



# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel, Field
# from typing import List, Optional
# from patient_data.services.fhir_service import (
#     get_encounter_centric_patient_bundle,
#     normalize_fhir_bundle,
#     get_patient_subject_ids
# )
# from patient_data.services.openai_service import (
#     get_clinical_assessment,
#     clinical_chat,
#     get_medication_interaction_check
# )

# router = APIRouter(tags=["Clinical Decision Support"])

# def get_patient_data(patient_id: str):
#     """Helper function to get normalized patient data."""
#     bundle = get_encounter_centric_patient_bundle(patient_id)
#     if not bundle:
#         return None
#     return normalize_fhir_bundle(bundle)

# class ClinicalMessage(BaseModel):
#     role: str = Field(..., description="'user' for provider or 'assistant' for AI")
#     content: str = Field(..., description="Message content")

# class ClinicalChatRequest(BaseModel):
#     patient_id: str = Field(..., description="Patient identifier")
#     question: str = Field(..., description="Clinical question from healthcare provider")
#     conversation_history: Optional[List[ClinicalMessage]] = Field(
#         default=[],
#         description="Previous conversation messages for context"
#     )

# class ClinicalAssessmentRequest(BaseModel):
#     patient_id: str = Field(..., description="Patient identifier")
#     clinical_question: Optional[str] = Field(
#         None,
#         description="Specific clinical question (optional for general assessment)"
#     )
#     focus_area: Optional[str] = Field(
#         None,
#         description="Specific clinical area to focus on"
#     )

# class MedicationCheckRequest(BaseModel):
#     patient_id: str = Field(..., description="Patient identifier")
#     new_medication: str = Field(..., description="Proposed medication to check for interactions")

# @router.post("/clinical/assessment")
# async def get_patient_assessment(request: ClinicalAssessmentRequest):
#     """Get comprehensive clinical assessment for a patient."""
#     try:
#         patient_data = get_patient_data(request.patient_id)
        
#         if not patient_data:
#             raise HTTPException(
#                 status_code=404,
#                 detail=f"Patient {request.patient_id} not found in system"
#             )
        
#         result = await get_clinical_assessment(
#             patient_data=patient_data,
#             clinical_question=request.clinical_question,
#             focus_area=request.focus_area
#         )
        
#         if not result.get("success"):
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Clinical assessment failed: {result.get('error')}"
#             )
        
#         return result
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error generating clinical assessment: {str(e)}"
#         )

# @router.post("/clinical/chat")
# async def clinical_consultation(request: ClinicalChatRequest):
#     """Continue clinical consultation conversation about a patient."""
#     try:
#         patient_data = get_patient_data(request.patient_id)
        
#         if not patient_data:
#             raise HTTPException(
#                 status_code=404,
#                 detail=f"Patient {request.patient_id} not found"
#             )
        
#         history = [{"role": msg.role, "content": msg.content} 
#                    for msg in request.conversation_history]
        
#         result = await clinical_chat(
#             patient_data=patient_data,
#             conversation_history=history,
#             new_question=request.question
#         )
        
#         if not result.get("success"):
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Clinical consultation failed: {result.get('error')}"
#             )
        
#         return result
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error in clinical consultation: {str(e)}"
#         )

# @router.get("/clinical/summary/{patient_id}")
# async def get_clinical_summary(patient_id: str):
#     """Get quick clinical summary for rounds or handoffs."""
#     try:
#         patient_data = get_patient_data(patient_id)
        
#         if not patient_data:
#             raise HTTPException(
#                 status_code=404,
#                 detail=f"Patient {patient_id} not found"
#             )
        
#         result = await get_clinical_assessment(
#             patient_data=patient_data,
#             clinical_question="Provide a concise clinical summary suitable for morning rounds. Include: current diagnosis, active issues, and immediate clinical concerns. Keep to 3-4 sentences."
#         )
        
#         if not result.get("success"):
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Summary generation failed: {result.get('error')}"
#             )
        
#         return {
#             "patient_id": patient_id,
#             "patient_name": patient_data.get('name'),
#             "age": patient_data.get('age'),
#             "summary": result.get('assessment')
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error generating summary: {str(e)}"
#         )

# @router.post("/clinical/medication-check")
# async def check_medication_interaction(request: MedicationCheckRequest):
#     """Check for interactions before prescribing new medication."""
#     try:
#         patient_data = get_patient_data(request.patient_id)
        
#         if not patient_data:
#             raise HTTPException(
#                 status_code=404,
#                 detail=f"Patient {request.patient_id} not found"
#             )
        
#         result = await get_medication_interaction_check(
#             patient_data=patient_data,
#             new_medication=request.new_medication
#         )
        
#         if not result.get("success"):
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Medication check failed: {result.get('error')}"
#             )
        
#         return result
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error checking medication: {str(e)}"
#         )

# @router.get("/clinical/patients")
# async def list_patients_for_review():
#     """Get list of patients available for clinical review."""
#     try:
#         patient_ids = get_patient_subject_ids()
        
#         return {
#             "total_patients": len(patient_ids),
#             "patient_ids": patient_ids
#         }
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error retrieving patient list: {str(e)}"
#         )