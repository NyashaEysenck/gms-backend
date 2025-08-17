import os
from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name: str = os.getenv("DATABASE_NAME", "grants_management")
    secret_key: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:8080")
    
    # CORS settings
    allowed_origins: list = ["*"
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add the frontend_url from environment to allowed_origins if not already present
        if self.frontend_url not in self.allowed_origins:
            self.allowed_origins.append(self.frontend_url)

    class Config:
        env_file = ".env"

settings = Settings()
