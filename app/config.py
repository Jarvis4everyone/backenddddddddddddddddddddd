from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # MongoDB Configuration
    mongodb_url: str
    database_name: str = "saas_subscription_db"

    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Razorpay Configuration
    razorpay_key_id: str
    razorpay_key_secret: str
    razorpay_webhook_secret: str

    # Application Configuration
    app_name: str = "Jarvis4Everyone Backend"
    debug: bool = False
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    
    # Download Configuration
    download_file_path: str = "./.downloads/jarvis4everyone.zip"

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins list, handling wildcard case"""
        # When using credentials, we can't use wildcard "*"
        # Convert "*" to common development origins
        if self.cors_origins.strip() == "*":
            return [
                "http://localhost:3000",
                "http://localhost:5173", 
                "http://localhost:8080",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173"
            ]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

