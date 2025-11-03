import os
import hashlib
from openai import OpenAI
from typing import List, Dict, Optional
from datetime import datetime, timedelta

# -------------------------------
# OpenAI Client Initialization
# -------------------------------
def _get_openai_client() -> OpenAI:
    """Get or initialize OpenAI client with proper error handling."""
    global _openai_client
    
    if '_openai_client' not in globals() or _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found in environment variables. "
                "Please set it in your .env file: OPENAI_API_KEY=sk-..."
            )
        _openai_client = OpenAI(api_key=api_key, timeout=30.0)
        print("✓ OpenAI client initialized successfully")
    
    return _openai_client

_openai_client = None

# -------------------------------
# AI Response Cache Configuration
# -------------------------------
_ai_response_cache = {}
_ai_cache_timestamps = {}
AI_CACHE_DURATION_MINUTES = 60  # Cache AI responses for 1 hour

def _get_question_hash(patient_id: str, question: str) -> str:
    """Create unique hash for patient + question combination."""
    combined = f"{patient_id}:{question.lower().strip()}"
    return hashlib.md5(combined.encode()).hexdigest()

def _is_ai_cache_valid(cache_key: str) -> bool:
    """Check if cached AI response is still valid."""
    if cache_key not in _ai_cache_timestamps:
        return False
    
    cache_time = _ai_cache_timestamps[cache_key]
    elapsed = datetime.now() - cache_time
    return elapsed < timedelta(minutes=AI_CACHE_DURATION_MINUTES)

def clear_ai_cache(cache_key: Optional[str] = None):
    """Clear AI response cache."""
    global _ai_response_cache, _ai_cache_timestamps
    
    if cache_key:
        _ai_response_cache.pop(cache_key, None)
        _ai_cache_timestamps.pop(cache_key, None)
        print(f"✓ Cleared AI cache for key {cache_key}")
    else:
        _ai_response_cache.clear()
        _ai_cache_timestamps.clear()
        print("✓ Cleared all AI response cache")

def get_ai_cache_stats() -> Dict:
    """Get AI cache statistics."""
    total_cached = len(_ai_response_cache)
    valid_cache = sum(1 for key in _ai_cache_timestamps if _is_ai_cache_valid(key))
    
    return {
        "total_cached_responses": total_cached,
        "valid_cached_responses": valid_cache,
        "expired_cached_responses": total_cached - valid_cache,
        "cache_duration_minutes": AI_CACHE_DURATION_MINUTES,
        "cache_keys_sample": list(_ai_response_cache.keys())[:5]
    }

# -------------------------------
# Patient Data Formatting
# -------------------------------
def format_patient_context(patient_data: dict) -> str:
    """Format patient data into a comprehensive clinical context."""
    
    context = f"""
PATIENT DEMOGRAPHICS:
- ID: {patient_data.get('id', 'Unknown')}
- Name: {patient_data.get('name', 'Unknown')}
- Age: {patient_data.get('age', 'Unknown')} years
- Gender: {patient_data.get('gender', 'Unknown')}
- Date of Birth: {patient_data.get('birthDate', 'Unknown')}

ACTIVE CONDITIONS/DIAGNOSES:
{format_clinical_list(patient_data.get('conditions', []))}

CURRENT MEDICATION REGIMEN:
{format_medications(patient_data.get('medications', []))}

RECENT VITAL SIGNS & LAB RESULTS:
{format_observations(patient_data.get('observations', []))}

RECENT CLINICAL ENCOUNTERS:
{format_encounters(patient_data.get('encounters', []))}

KNOWN ALLERGIES:
{format_clinical_list(patient_data.get('allergies', []))}

IMMUNIZATION HISTORY:
{format_clinical_list(patient_data.get('immunizations', []))}
"""
    return context.strip()

def format_clinical_list(items: List[str]) -> str:
    """Format clinical items with proper formatting."""
    if not items:
        return "• None documented"
    return "\n".join([f"• {item}" for item in items[:20]])  # Limit to 20 items

def format_medications(medications: List) -> str:
    """Format medications with dosage information if available."""
    if not medications:
        return "• No active medications documented"
    
    formatted = []
    for med in medications[:20]:  # Limit to 20 medications
        if isinstance(med, dict):
            name = med.get('name', 'Unknown medication')
            dosage = med.get('dosage', '')
            frequency = med.get('frequency', '')
            med_str = f"• {name}"
            if dosage:
                med_str += f" - {dosage}"
            if frequency:
                med_str += f" ({frequency})"
            formatted.append(med_str)
        else:
            formatted.append(f"• {med}")
    
    return "\n".join(formatted)

def format_observations(observations: List[Dict]) -> str:
    """Format clinical observations with proper medical formatting."""
    if not observations:
        return "• No recent observations documented"
    
    formatted = []
    for obs in observations[:15]:  # Last 15 observations
        if isinstance(obs, dict):
            code = obs.get('code', 'Unknown')
            value = obs.get('value', 'N/A')
            unit = obs.get('unit', '')
            date = obs.get('date', '')
            
            obs_str = f"• {code}: {value}"
            if unit:
                obs_str += f" {unit}"
            if date:
                obs_str += f" (Date: {date})"
            formatted.append(obs_str)
        else:
            formatted.append(f"• {obs}")
    
    return "\n".join(formatted)

def format_encounters(encounters: List) -> str:
    """Format clinical encounters."""
    if not encounters:
        return "• No recent encounters documented"
    
    formatted = []
    for enc in encounters[:5]:  # Last 5 encounters
        if isinstance(enc, dict):
            type_desc = enc.get('type', 'Unknown encounter')
            date = enc.get('date', '')
            reason = enc.get('reason', '')
            
            enc_str = f"• {type_desc}"
            if date:
                enc_str += f" - {date}"
            if reason:
                enc_str += f" (Reason: {reason})"
            formatted.append(enc_str)
        else:
            formatted.append(f"• {enc}")
    
    return "\n".join(formatted)

# -------------------------------
# LLM Call Function
# -------------------------------
def _call_openai(
    messages: List[Dict[str, str]], 
    temperature: float = 0.3, 
    max_tokens: int = 3000,
    model: str = "gpt-3.5-turbo"
) -> str:
    """
    Call OpenAI API with error handling and retry logic.
    """
    try:
        client = _get_openai_client()
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        error_msg = str(e)
        
        # Better error messages
        if "api_key" in error_msg.lower():
            raise Exception(
                "OpenAI API key is invalid or missing. "
                "Please check your OPENAI_API_KEY in .env file"
            )
        elif "rate_limit" in error_msg.lower():
            raise Exception(
                "OpenAI API rate limit exceeded. Please try again in a moment."
            )
        elif "timeout" in error_msg.lower():
            raise Exception(
                "OpenAI API request timed out. Please try again."
            )
        else:
            raise Exception(f"OpenAI API error: {error_msg}")

# -------------------------------
# Clinical AI Functions (WITH CACHING)
# -------------------------------
async def get_clinical_assessment(
    patient_data: dict,
    clinical_question: Optional[str] = None,
    focus_area: Optional[str] = None
) -> dict:
    """
    Get AI-powered clinical assessment WITH AI RESPONSE CACHING.
    Patient data is already cached via fhir_service.
    """
    
    try:
        # Check AI response cache for identical questions
        if clinical_question:
            cache_key = _get_question_hash(patient_data.get('id'), clinical_question)
            
            if _is_ai_cache_valid(cache_key):
                print(f"✓ [AI CACHE HIT] Returning cached AI response")
                cached_response = _ai_response_cache[cache_key].copy()
                cached_response["from_cache"] = True
                return cached_response
        
        # Generate fresh AI response
        patient_context = format_patient_context(patient_data)
        
        system_prompt = """You are an advanced clinical decision support AI assisting healthcare professionals.

Your role is to:
- Provide evidence-based clinical assessments
- Identify significant clinical findings and trends
- Suggest differential diagnoses based on presenting data
- Highlight potential drug interactions and contraindications
- Recommend appropriate diagnostic workup and management strategies
- Flag critical values and urgent clinical concerns
- Provide relevant clinical guidelines and evidence

IMPORTANT:
- You are a clinical decision support tool, not a replacement for professional judgment
- Always cite clinical reasoning and evidence when possible
- Clearly distinguish between high-confidence and low-confidence assessments
- Flag when more information is needed for accurate assessment
- Use medical terminology appropriate for healthcare professionals
- Consider all available patient data comprehensively"""

        if clinical_question:
            focus_text = f" with focus on {focus_area}" if focus_area else ""
            user_message = f"""CLINICAL CONSULTATION REQUEST{focus_text}:

{clinical_question}

PATIENT CLINICAL DATA:
{patient_context}

Please provide a comprehensive clinical assessment addressing the specific question above."""
        else:
            user_message = f"""Please provide a comprehensive clinical assessment for this patient:

PATIENT CLINICAL DATA:
{patient_context}

REQUESTED ASSESSMENT COMPONENTS:

1. CLINICAL SUMMARY
   - Brief overview of patient's current health status
   - Significant medical history highlights

2. KEY CLINICAL FINDINGS
   - Critical values or abnormal findings requiring attention
   - Significant trends in vital signs or lab results

3. DIFFERENTIAL DIAGNOSES
   - Potential diagnoses based on current presentation
   - Supporting and contradicting evidence for each

4. MEDICATION REVIEW
   - Assessment of current medication regimen
   - Potential drug interactions or contraindications
   - Medication optimization opportunities

5. RISK ASSESSMENT
   - Identify clinical risk factors
   - Stratify urgency of identified issues

6. RECOMMENDED WORKUP
   - Suggested diagnostic tests or imaging
   - Recommended specialist consultations
   - Monitoring parameters

7. MANAGEMENT RECOMMENDATIONS
   - Evidence-based treatment suggestions
   - Preventive care recommendations
   - Patient education priorities"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        print(f"⟳ Calling OpenAI API for clinical assessment...")
        ai_response = _call_openai(messages, temperature=0.3, max_tokens=3000)
        
        result = {
            "success": True,
            "patient_id": patient_data.get('id'),
            "patient_name": patient_data.get('name'),
            "patient_age": patient_data.get('age'),
            "assessment": ai_response,
            "model_used": "OpenAI GPT-3.5-Turbo",
            "clinical_question": clinical_question,
            "focus_area": focus_area,
            "timestamp": datetime.now().isoformat(),
            "from_cache": False
        }
        
        # Cache the AI response if it was a specific question
        if clinical_question:
            cache_key = _get_question_hash(patient_data.get('id'), clinical_question)
            _ai_response_cache[cache_key] = result.copy()
            _ai_cache_timestamps[cache_key] = datetime.now()
            print(f"✓ [AI CACHED] Stored AI response (expires in {AI_CACHE_DURATION_MINUTES} min)")
        
        return result
        
    except Exception as e:
        error_message = str(e)
        print(f"✗ Clinical assessment error: {error_message}")
        return {
            "success": False,
            "error": error_message,
            "patient_id": patient_data.get('id'),
            "from_cache": False
        }

async def clinical_chat(
    patient_data: dict,
    conversation_history: List[Dict[str, str]],
    new_question: str
) -> dict:
    """
    Continue a clinical consultation conversation about a patient.
    Note: Conversation history is NOT cached as context changes with each message.
    """
    
    try:
        patient_context = format_patient_context(patient_data)
        
        system_prompt = f"""You are a clinical decision support AI assisting a healthcare professional with patient care.

CURRENT PATIENT CONTEXT:
{patient_context}

Provide evidence-based, clinically relevant responses to the healthcare provider's questions.
Maintain professional medical terminology and cite clinical reasoning when appropriate.
Always consider the complete patient context in your responses."""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history[-10:])  # Last 5 Q&A pairs (10 messages)
        messages.append({"role": "user", "content": new_question})
        
        print(f"⟳ Calling OpenAI API for chat response...")
        ai_response = _call_openai(messages, temperature=0.3, max_tokens=1500)
        
        return {
            "success": True,
            "response": ai_response,
            "patient_id": patient_data.get('id'),
            "patient_name": patient_data.get('name'),
            "from_cache": False
        }
        
    except Exception as e:
        error_message = str(e)
        print(f"✗ Chat error: {error_message}")
        return {
            "success": False,
            "error": error_message,
            "from_cache": False
        }

async def get_medication_interaction_check(patient_data: dict, new_medication: str) -> dict:
    """
    Check for potential interactions with a new medication.
    """
    
    try:
        current_meds = patient_data.get('medications', [])
        conditions = patient_data.get('conditions', [])
        allergies = patient_data.get('allergies', [])
        
        # Check cache for this specific medication interaction
        cache_key = _get_question_hash(patient_data.get('id'), f"medication_check:{new_medication}")
        
        if _is_ai_cache_valid(cache_key):
            print(f"✓ [AI CACHE HIT] Returning cached medication interaction analysis")
            cached_response = _ai_response_cache[cache_key].copy()
            cached_response["from_cache"] = True
            return cached_response
        
        prompt = f"""Please analyze potential interactions for adding this medication:

PROPOSED MEDICATION: {new_medication}

CURRENT MEDICATIONS:
{format_medications(current_meds)}

ACTIVE CONDITIONS:
{format_clinical_list(conditions)}

KNOWN ALLERGIES:
{format_clinical_list(allergies)}

Please provide:
1. Potential drug-drug interactions
2. Drug-disease contraindications
3. Allergy concerns
4. Dosing considerations based on patient conditions
5. Monitoring recommendations"""

        system_prompt = """You are a clinical pharmacology expert providing drug interaction analysis.
Be thorough and evidence-based. Cite specific interaction mechanisms when relevant."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        print(f"⟳ Calling OpenAI API for medication interaction check...")
        ai_response = _call_openai(messages, temperature=0.2, max_tokens=1500)
        
        result = {
            "success": True,
            "patient_id": patient_data.get('id'),
            "proposed_medication": new_medication,
            "interaction_analysis": ai_response,
            "from_cache": False
        }
        
        # Cache the medication interaction analysis
        _ai_response_cache[cache_key] = result.copy()
        _ai_cache_timestamps[cache_key] = datetime.now()
        print(f"✓ [AI CACHED] Stored medication interaction analysis (expires in {AI_CACHE_DURATION_MINUTES} min)")
        
        return result
        
    except Exception as e:
        error_message = str(e)
        print(f"✗ Medication interaction check error: {error_message}")
        return {
            "success": False,
            "error": error_message,
            "from_cache": False
        }