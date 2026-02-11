import os
from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    
    # App Settings
    APP_NAME: str = "Multikarnal Orchestrator"
    LOG_LEVEL: str = "INFO"
    ENABLE_BACKGROUND_WORKER: bool = True 
    X_API_KEY: Optional[str] = None

    # Dify API Configuration
    DIFY_API_BASE_URL: str
    DIFY_API_KEY: str
    
    # Database Configuration (Restored)
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASS: str

    # Feature Flags
    EMAIL_POLL_INTERVAL_SECONDS: int = 15
    MAX_INPUT_CHARS: int = 6000

    # Social Media Credentials
    INSTAGRAM_PAGE_ACCESS_TOKEN: Optional[str] = None
    INSTAGRAM_CHATBOT_ID: Optional[str] = None
    INSTAGRAM_VERIFY_TOKEN: Optional[str] = None
    INSTAGRAM_PAGE_ID: Optional[str] = None
    
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None

    # Email Settings
    EMAIL_PROVIDER: Literal["gmail", "azure_oauth2", "unknown"] = "unknown"
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USER: Optional[str] = None
    EMAIL_PASS: Optional[str] = None
    
    # Azure OAuth2
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None
    AZURE_TENANT_ID: Optional[str] = None
    AZURE_EMAIL_USER: Optional[str] = None

    BE_MAIN_URL: str = "http://localhost:9798/api/live-chat/internal/chat/bot" # Sesuaikan host
    INTERNAL_API_KEY: str = "migas-jaya-jaya-123" # Harus sama dengan BE Main

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

settings = Settings()