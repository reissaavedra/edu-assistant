"""
Configuration module for the app.

This module loads configuration from environment variables or .env files
with special handling for Streamlit Cloud deployment.
"""

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from loguru import logger
from pydantic_settings import BaseSettings


# Determinar si estamos en Streamlit Cloud
def is_streamlit_cloud() -> bool:
    return (
        os.environ.get("STREAMLIT_SHARING", "").lower() == "true"
        or "STREAMLIT_RUNTIME" in os.environ
        or "STREAMLIT_SERVER_ADDRESS" in os.environ
    )


# Cargar variables de entorno desde diferentes fuentes según el entorno
def load_environment_variables():
    env_file = None
    root_dir = Path(__file__).parent.parent

    # Primero intentar cargar desde .env en desarrollo
    if Path(root_dir / ".env").exists():
        env_file = root_dir / ".env"
    # Alternativamente .env.streamlit para Streamlit Cloud si existe
    elif Path(root_dir / ".env.streamlit").exists():
        env_file = root_dir / ".env.streamlit"

    # Cargar las variables de entorno
    if env_file:
        logger.info(f"Loading environment from {env_file}")
        load_dotenv(env_file)
    else:
        logger.warning("No .env file found, using environment variables only")

    # En Streamlit Cloud, también podemos acceder a secretos
    if is_streamlit_cloud() and hasattr(st, "secrets"):
        logger.info("Loading secrets from Streamlit")
        # Agregar secretos de Streamlit como variables de entorno
        for key, value in st.secrets.items():
            if isinstance(value, dict):
                # Manejar secretos anidados
                for subkey, subvalue in value.items():
                    os.environ[f"{key.upper()}_{subkey.upper()}"] = str(subvalue)
            else:
                os.environ[key.upper()] = str(value)


# Cargar variables de entorno antes de definir configuraciones
load_environment_variables()


class Settings(BaseSettings):
    """Application settings."""

    # API Keys
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")

    # Model configuration
    GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro-002")
    GEMINI_TEMPERATURE: float = float(os.environ.get("GEMINI_TEMPERATURE", "0.7"))

    # Application configuration
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "development")

    # Data paths
    knowledge_base_path: Path = (
        Path(__file__).parent.parent / "data" / "knowledge_base_Caso.xlsx"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instanciar configuración
settings = Settings()


# Función para validar configuración
def validate_config() -> bool:
    """Validate that all required configuration is present."""
    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set")
        return False

    return True
