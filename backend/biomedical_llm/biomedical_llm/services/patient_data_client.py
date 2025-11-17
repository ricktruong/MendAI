"""
Patient Data Client Service
Handles communication with the patient_data service to fetch FHIR data
"""
import logging
from typing import Optional, Dict, Any
from functools import lru_cache
from datetime import datetime, timedelta

import httpx

from ..config import get_settings

logger = logging.getLogger(__name__)


class PatientDataClient:
    """Client for interacting with the patient_data service"""
    
    def __init__(self):
        self.settings = get_settings()
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def _generate_cache_key(self, patient_id: str) -> str:
        """Generate cache key for patient data"""
        return f"patient_data:{patient_id}"
    
    def _get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached patient data if available and not expired"""
        if not self.settings.enable_cache:
            return None
            
        cached = self._cache.get(cache_key)
        if cached:
            expires_at = cached.get("expires_at")
            if expires_at and datetime.now() < expires_at:
                logger.info(f"Cache hit for patient data: {cache_key}")
                return cached.get("data")
            else:
                # Remove expired entry
                del self._cache[cache_key]
        return None
    
    def _cache_data(self, cache_key: str, data: Dict[str, Any]):
        """Cache patient data with expiration"""
        if self.settings.enable_cache:
            expires_at = datetime.now() + timedelta(seconds=self.settings.cache_ttl)
            self._cache[cache_key] = {
                "data": data,
                "expires_at": expires_at
            }
            logger.info(f"Cached patient data: {cache_key}")
    
    async def get_patient_data(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch normalized patient data from patient_data service
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            Dict with patient data or None if not found
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key(patient_id)
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data
            
            # Fetch from patient_data service
            url = f"{self.settings.patient_data_url}/api/patients/{patient_id}/normalized"
            logger.info(f"Fetching patient data from: {url}")
            
            async with httpx.AsyncClient(timeout=self.settings.patient_data_timeout) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Successfully fetched patient data for {patient_id}")
                    
                    # Cache the data
                    self._cache_data(cache_key, data)
                    
                    return data
                elif response.status_code == 404:
                    logger.warning(f"Patient {patient_id} not found")
                    return None
                else:
                    logger.error(
                        f"Failed to fetch patient data: {response.status_code} - {response.text}"
                    )
                    return None
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching patient data for {patient_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching patient data: {str(e)}")
            return None
    
    async def check_patient_data_health(self) -> bool:
        """
        Check if patient_data service is healthy
        
        Returns:
            bool: True if service is healthy
        """
        try:
            url = f"{self.settings.patient_data_url}/health"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Patient data service health check failed: {str(e)}")
            return False


@lru_cache()
def get_patient_data_client() -> PatientDataClient:
    """
    Get singleton instance of patient data client
    
    Returns:
        PatientDataClient: Cached client instance
    """
    return PatientDataClient()
