from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Server
    port: int = 8000
    host: str = "0.0.0.0"
    
    # Database
    database_url: str = "sqlite:///./app.db"
    
    # Security
    secret_key: str = "supersecretkey_change_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Geo providers
    geo_provider_a_url: str = "http://ip-api.com/json/"
    geo_provider_b_url: str = "https://ipapi.co/"
    geo_enabled: bool = True
    geo_timeout: int = 3
    
    # Rate limiting
    rate_limit_per_ip: str = "10/minute"
    rate_limit_per_widget: str = "5/minute"
    
    # Request limits
    max_request_size: int = 65536  # 64KB
    
    # Side effects
    side_effect_enabled: bool = True
    side_effect_fail: bool = False
    side_effect_retries: int = 3
    
    # Base URL for embed snippets
    base_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"


settings = Settings()