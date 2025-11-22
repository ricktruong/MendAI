"""
OpenAI Service for biomedical LLM inference
Handles all OpenAI API interactions with biomedical-specific prompts
"""
import logging
import re
from typing import List, Dict, Optional, Any
from functools import lru_cache
from datetime import datetime, timedelta

from openai import OpenAI

from ..config import get_settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for OpenAI LLM inference with biomedical context"""
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[OpenAI] = None
        self._response_cache: Dict[str, Dict[str, Any]] = {}
        
        # Biomedical system prompt for clinical analysis (Updated by Dan)
        self.system_prompt = """You are an advanced clinical decision support AI assisting healthcare professionals.

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
- Match response length to question complexity: brief answers for simple questions, detailed for complex ones"""

    @property
    def client(self) -> OpenAI:
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            if not self.settings.openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY not configured. Please set it in the .env file."
                )
            self._client = OpenAI(api_key=self.settings.openai_api_key)
        return self._client

    def _generate_cache_key(self, messages: List[Dict], patient_id: Optional[str]) -> str:
        """Generate cache key for response caching"""
        # Create a simple cache key from the last message and patient_id
        last_msg = messages[-1]["content"] if messages else ""
        return f"{patient_id}:{last_msg[:100]}"

    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Get cached response if available and not expired"""
        if not self.settings.enable_cache:
            return None
            
        cached = self._response_cache.get(cache_key)
        if cached:
            expires_at = cached.get("expires_at")
            if expires_at and datetime.now() < expires_at:
                logger.info(f"Cache hit for key: {cache_key[:50]}...")
                return cached.get("response")
            else:
                # Remove expired entry
                del self._response_cache[cache_key]
        return None

    def _cache_response(self, cache_key: str, response: str):
        """Cache response with expiration"""
        if self.settings.enable_cache:
            expires_at = datetime.now() + timedelta(seconds=self.settings.cache_ttl)
            self._response_cache[cache_key] = {
                "response": response,
                "expires_at": expires_at
            }
            logger.info(f"Cached response for key: {cache_key[:50]}...")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        patient_context: Optional[Dict[str, Any]] = None,
        patient_id: Optional[str] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Generate chat completion with biomedical context
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            patient_context: Optional patient data for context enrichment
            patient_id: Optional patient ID for caching
            model: Optional model override (defaults to config)
            
        Returns:
            str: Generated response
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key(messages, patient_id)
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                return cached_response

            # Build enhanced messages with patient context
            enhanced_messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add patient context if available
            if patient_context:
                context_message = self._build_patient_context_message(patient_context)
                enhanced_messages.append({
                    "role": "system",
                    "content": context_message
                })
            
            # Add conversation messages
            enhanced_messages.extend(messages)
            
            # Call OpenAI API
            model_to_use = model or self.settings.openai_model
            logger.info(f"Calling OpenAI API with model: {model_to_use}")
            
            response = self.client.chat.completions.create(
                model=model_to_use,
                messages=enhanced_messages,
                temperature=self.settings.openai_temperature,
                max_tokens=self.settings.openai_max_tokens
            )
            
            result = response.choices[0].message.content

            # Clean up duplicate content that LLM might have generated
            result = self._clean_duplicate_content(result)

            # Add disclaimer
            result = self._add_disclaimer(result)

            # Cache the response
            self._cache_response(cache_key, result)
            
            logger.info("Successfully generated response from OpenAI")
            return result
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise

    def _build_patient_context_message(self, patient_data: Dict[str, Any]) -> str:
        """
        Build a comprehensive patient context message from FHIR data
        
        Args:
            patient_data: Normalized patient data
            
        Returns:
            str: Formatted context message
        """
        context_parts = ["**Patient Medical Record Context:**"]
        
        # Basic demographics
        if "name" in patient_data:
            context_parts.append(f"Patient: {patient_data['name']}")
        
        # Calculate age from birthDate if available, otherwise use age field
        if "birthDate" in patient_data:
            from datetime import datetime
            try:
                birth_date = datetime.fromisoformat(patient_data['birthDate'].replace('Z', '+00:00'))
                today = datetime.now()
                age = today.year - birth_date.year
                # Adjust if birthday hasn't occurred this year
                if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                    age -= 1
                # Only use calculated age if it's reasonable (0-120 years)
                if 0 <= age <= 120:
                    context_parts.append(f"Age: {age} years")
                elif "age" in patient_data and 0 <= patient_data['age'] <= 120:
                    context_parts.append(f"Age: {patient_data['age']} years")
            except (ValueError, AttributeError):
                # Fallback to age field if date parsing fails
                if "age" in patient_data and 0 <= patient_data['age'] <= 120:
                    context_parts.append(f"Age: {patient_data['age']} years")
        elif "age" in patient_data and 0 <= patient_data['age'] <= 120:
            context_parts.append(f"Age: {patient_data['age']} years")
        
        if "gender" in patient_data:
            context_parts.append(f"Gender: {patient_data['gender'].capitalize()}")
        
        # Conditions
        conditions = patient_data.get("conditions", [])
        if conditions:
            context_parts.append(f"\n**Active Conditions ({len(conditions)}):**")
            for cond in conditions[:10]:  # Limit to top 10
                # Handle both string and dict formats
                if isinstance(cond, str):
                    context_parts.append(f"- {cond}")
                elif isinstance(cond, dict):
                    name = cond.get("name", "Unknown")
                    status = cond.get("status", "")
                    context_parts.append(f"- {name} ({status})")
        
        # Medications
        medications = patient_data.get("medications", [])
        if medications:
            context_parts.append(f"\n**Current Medications ({len(medications)}):**")
            for med in medications[:10]:  # Limit to top 10
                if isinstance(med, dict):
                    name = med.get("name", "Unknown")
                    dosage = med.get("dosage", "")
                    frequency = med.get("frequency", "")
                    med_str = f"- {name}"
                    if dosage:
                        med_str += f" {dosage}"
                    if frequency:
                        med_str += f" ({frequency})"
                    context_parts.append(med_str)
                elif isinstance(med, str):
                    context_parts.append(f"- {med}")
        
        # Allergies
        allergies = patient_data.get("allergies", [])
        if allergies:
            context_parts.append(f"\n**Known Allergies ({len(allergies)}):**")
            for allergy in allergies:
                if isinstance(allergy, dict):
                    allergen = allergy.get("allergen", "Unknown")
                    reaction = allergy.get("reaction", "")
                    severity = allergy.get("severity", "")
                    allergy_str = f"- {allergen}"
                    if reaction:
                        allergy_str += f": {reaction}"
                    if severity:
                        allergy_str += f" ({severity})"
                    context_parts.append(allergy_str)
                elif isinstance(allergy, str):
                    context_parts.append(f"- {allergy}")
        
        # Recent vitals/observations
        observations = patient_data.get("observations", [])
        if observations:
            context_parts.append(f"\n**Recent Vital Signs & Observations:**")
            for obs in observations[:10]:  # Limit to most recent 10
                if isinstance(obs, dict):
                    code = obs.get("code", "Unknown")
                    value = obs.get("value")
                    unit = obs.get("unit", "")
                    date = obs.get("date", "")
                    
                    obs_str = f"- {code}"
                    if value is not None:
                        obs_str += f": {value}"
                        if unit:
                            obs_str += f" {unit}"
                    if date:
                        obs_str += f" (recorded: {date})"
                    context_parts.append(obs_str)
        
        # Recent encounters
        encounters = patient_data.get("encounters", [])
        if encounters:
            recent_encounter = encounters[0] if encounters else None
            if recent_encounter:
                context_parts.append(f"\n**Most Recent Encounter:**")
                enc_type = recent_encounter.get("type", "Unknown")
                enc_date = recent_encounter.get("date", "")
                reason = recent_encounter.get("reason", "")
                context_parts.append(f"- Type: {enc_type}")
                context_parts.append(f"- Date: {enc_date}")
                if reason:
                    context_parts.append(f"- Reason: {reason}")
        
        context_parts.append(
            "\n**Note:** Use this clinical data to inform your analysis. "
            "Consider all factors including medications, allergies, and current conditions."
        )
        
        return "\n".join(context_parts)

    def _clean_duplicate_content(self, response: str) -> str:
        """
        Clean up duplicate content that the LLM might have generated.
        This handles cases where the LLM repeats disclaimers or entire sections.
        """
        # Remove duplicate disclaimer notes
        disclaimer_pattern = r"(\*?Note:\s*This analysis is generated by an AI system[^*]*(?:medical advice\.?\*?))"
        matches = list(re.finditer(disclaimer_pattern, response, re.IGNORECASE | re.DOTALL))

        if len(matches) > 1:
            # Keep only the last disclaimer, remove all others
            for match in matches[:-1]:
                response = response.replace(match.group(0), "", 1)

        # Clean up multiple consecutive newlines that might result from removal
        response = re.sub(r"\n{4,}", "\n\n\n", response)

        # Remove duplicate horizontal rules
        response = re.sub(r"(---\s*){2,}", "---\n", response)

        # Check for large block duplication (if the same paragraph appears twice)
        paragraphs = response.split("\n\n")
        seen = set()
        unique_paragraphs = []
        for para in paragraphs:
            # Normalize the paragraph for comparison (strip whitespace)
            normalized = para.strip()
            # Only filter out exact duplicates that are substantial (more than 50 chars)
            if len(normalized) < 50 or normalized not in seen:
                unique_paragraphs.append(para)
                if len(normalized) >= 50:
                    seen.add(normalized)

        response = "\n\n".join(unique_paragraphs)

        return response.strip()

    def _add_disclaimer(self, response: str) -> str:
        """Add medical disclaimer to response if not already present"""
        # More comprehensive keywords to detect existing disclaimers
        disclaimer_keywords = [
            "disclaimer",
            "AI-generated",
            "generated by an AI",
            "generated by AI",
            "not replace clinical judgment",
            "not intended to replace clinical",
            "should be reviewed by qualified",
            "reviewed by medical professionals",
            "not a substitute for professional",
        ]

        response_lower = response.lower()

        # Check if response already has a disclaimer
        has_disclaimer = any(keyword.lower() in response_lower for keyword in disclaimer_keywords)

        # Also check for duplicate "Note:" patterns that indicate existing disclaimers
        note_count = response_lower.count("note: this analysis is generated")
        if note_count > 0:
            has_disclaimer = True

        if not has_disclaimer:
            disclaimer = (
                "\n\n---\n"
                "*Note: This analysis is generated by an AI system and should be reviewed by "
                "qualified medical professionals. It is not intended to replace clinical judgment "
                "or medical advice.*"
            )
            response += disclaimer

        return response


@lru_cache()
def get_openai_service() -> OpenAIService:
    """
    Get singleton instance of OpenAI service
    
    Returns:
        OpenAIService: Cached service instance
    """
    return OpenAIService()
