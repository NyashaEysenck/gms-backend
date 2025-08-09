import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name: str = os.getenv("DATABASE_NAME", "grants_management")
    secret_key: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:8080")
    
    # CORS settings
    allowed_origins: list = [
        "http://localhost:8080",  # Frontend development server
        "http://127.0.0.1:8080",
        "http://localhost:3000",  # Alternative frontend port
        "http://127.0.0.1:3000"
    ]

    class Config:
        env_file = ".env"

settings = Settings()