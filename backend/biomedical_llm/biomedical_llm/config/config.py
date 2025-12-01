"""
Configuration settings for the biomedical_llm service
"""
import os
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Service configuration settings"""
    
    # Service settings
    service_name: str = "biomedical_llm"
    service_port: int = 8003
    debug: bool = False
    log_level: str = "INFO"
    
    # OpenAI settings
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = "gpt-4o-mini"  # Latest GPT model for better responses
    openai_temperature: float = 0.2  # Lower temperature for more consistent medical responses
    openai_max_tokens: int = 1000  # Reduced for more concise responses
    
    # Patient Data Service settings
    patient_data_url: str = Field(
        default="http://patient_data:8001",
        alias="PATIENT_DATA_URL"
    )
    patient_data_timeout: int = 30  # seconds
    
    # Cache settings
    enable_cache: bool = True
    cache_ttl: int = 600  # 10 minutes
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        populate_by_name = True
        extra = "ignore"  # Allow extra docker-compose environment variables


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    
    Returns:
        Settings: Application settings
    """
    return Settings()
