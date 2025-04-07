"""
Configuration module for the educational assistant.

This module handles centralized configuration management for the application,
including environment variables, API settings, and paths.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    """Application settings."""

    # General configuration
    app_name: str = "Edu Assistant"
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # API Keys
    gemini_api_key: Optional[str] = None

    # Model configuration
    gemini_model: str = Field(default="gemini-pro")
    gemini_temperature: float = Field(default=0.7)

    # Data paths
    knowledge_base_path: Path = DATA_DIR / "knowledge_base_Caso.xlsx"

    # Router configuration
    default_agent: str = "cursos"  # Default agent if router can't determine
    router_temperature: float = 0.1  # Low temperature for more predictable routing

    class Config:
        """Pydantic configuration."""

        env_file = "/edu-assistant/.env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create a global settings object
settings = Settings()


def get_settings() -> Settings:
    """Return the settings object.

    This function is useful for dependency injection in FastAPI or similar frameworks.

    Returns:
        Settings: The application settings
    """
    return settings
