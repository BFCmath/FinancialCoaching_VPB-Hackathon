import os
from pydantic import BaseSettings
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
# This is great for local development.
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables.
    """
    # --- App Info ---
    PROJECT_NAME: str = "VPBank AI Financial Coach"
    API_V1_STR: str = "/api"

    # --- Database Configuration ---
    # Example for local MongoDB: "mongodb://localhost:27017"
    # For AWS DocumentDB, this will be a different connection string.
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "vpbank_financial_coach")

    # --- Agent/LLM Configuration ---
    # This is the Google API Key required by the orchestrator's main.py
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    
    # LLM Model Configuration
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-2.5-flash-lite-preview-06-17")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    
    # Agent Configuration
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    VERBOSE_LOGGING: bool = os.getenv("VERBOSE_LOGGING", "false").lower() in ("true", "1", "yes")
    MAX_REACT_ITERATIONS: int = int(os.getenv("MAX_REACT_ITERATIONS", "5"))

    # --- JWT Authentication ---
    # A strong, randomly generated secret key is crucial for security.
    # You can generate one using: openssl rand -hex 32
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "a_very_secret_key_that_should_be_changed")
    JWT_ALGORITHM: str = "HS256"
    # Token validity period in minutes
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    class Config:
        case_sensitive = True
        # This allows Pydantic to read from a .env file if you choose to use one.
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create a single, globally accessible instance of the settings
settings = Settings()

# --- How to use this file ---
# 1. Create a file named `.env` in the root of your `/vpbank_financial_coach_backend/` directory.
# 2. Add your secret values to it, for example:
#
#    MONGO_URL="mongodb://localhost:27017"
#    DATABASE_NAME="vpbank_dev"
#    GOOGLE_API_KEY="your_google_api_key_here"
#    JWT_SECRET_KEY="your_super_strong_randomly_generated_secret_key"
#    
#    # Optional LLM Configuration
#    MODEL_NAME="gemini-2.5-flash-lite-preview-06-17"
#    LLM_TEMPERATURE="0.1"
#    DEBUG="false"
#    VERBOSE_LOGGING="false"
#    MAX_REACT_ITERATIONS="5"
#
# 3. The application will automatically load these values.
# 4. In other parts of the code, you can import and use the settings object like this:
#    from backend.core.config import settings
#    print(settings.MONGO_URL)