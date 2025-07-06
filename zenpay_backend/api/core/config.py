# zenpay_backend/core/config.py
import os
from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings
from pydantic import validator, PostgresDsn, AnyHttpUrl


class Settings(BaseSettings):
    PROJECT_NAME: str = "ZenPay"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./zenpay.db")
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost", "http://localhost:3000", "http://localhost:8000"]
    
    # Stripe
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    # API Keys
    API_KEY_PREFIX: str = "zp_"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()