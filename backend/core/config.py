import os
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
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
    # Default Google API Key - agents can override with their own
    GOOGLE_API_KEY: str = Field(default="", description="Default Google API Key for Gemini models")
    
    # Agent-specific Google API Keys
    CLASSIFIER_GOOGLE_API_KEY: str = os.getenv("CLASSIFIER_GOOGLE_API_KEY", "")
    JAR_GOOGLE_API_KEY: str = os.getenv("JAR_GOOGLE_API_KEY", "")
    FEE_GOOGLE_API_KEY: str = os.getenv("FEE_GOOGLE_API_KEY", "")
    PLAN_GOOGLE_API_KEY: str = os.getenv("PLAN_GOOGLE_API_KEY", "")
    FETCHER_GOOGLE_API_KEY: str = os.getenv("FETCHER_GOOGLE_API_KEY", "")
    KNOWLEDGE_GOOGLE_API_KEY: str = os.getenv("KNOWLEDGE_GOOGLE_API_KEY", "")
    ORCHESTRATOR_GOOGLE_API_KEY: str = os.getenv("ORCHESTRATOR_GOOGLE_API_KEY", "")
    
    # LLM Model Configuration (shared across all agents)
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-2.5-flash-lite-preview-06-17")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    MAX_MEMORY_TURNS: int = int(os.getenv("MAX_MEMORY_TURNS", "10"))
    # Agent Configuration (shared across all agents)
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "true").lower() in ("true", "1", "yes")
    VERBOSE_LOGGING: bool = os.getenv("VERBOSE_LOGGING", "true").lower() in ("true", "1", "yes")
    MAX_REACT_ITERATIONS: int = int(os.getenv("MAX_REACT_ITERATIONS", "5"))
    
    @field_validator('GOOGLE_API_KEY')
    @classmethod
    def validate_google_api_key(cls, v):
        """Validate that Google API Key is provided when needed."""
        # Only validate in production or when explicitly required
        if not v and os.getenv("REQUIRE_GOOGLE_API_KEY", "false").lower() in ("true", "1", "yes"):
            raise ValueError("GOOGLE_API_KEY is required when REQUIRE_GOOGLE_API_KEY is set")
        return v
    
    def __init__(self, **kwargs):
        # Load environment variables for this instance
        super().__init__(**kwargs)
        # Set default GOOGLE_API_KEY if not provided
        if not self.GOOGLE_API_KEY:
            self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    
    def get_agent_api_key(self, agent_name: str) -> str:
        """Get the Google API key for a specific agent, falling back to default."""
        agent_key_mapping = {
            "classifier": self.CLASSIFIER_GOOGLE_API_KEY,
            "jar": self.JAR_GOOGLE_API_KEY,
            "fee": self.FEE_GOOGLE_API_KEY,
            "plan": self.PLAN_GOOGLE_API_KEY,
            "fetcher": self.FETCHER_GOOGLE_API_KEY,
            "knowledge": self.KNOWLEDGE_GOOGLE_API_KEY,
            "orchestrator": self.ORCHESTRATOR_GOOGLE_API_KEY,
        }
        
        # Return agent-specific key if available, otherwise fall back to default
        agent_key = agent_key_mapping.get(agent_name.lower(), "")
        return agent_key if agent_key else self.GOOGLE_API_KEY

    # --- JWT Authentication ---
    # A strong, randomly generated secret key is crucial for security.
    # You can generate one using: openssl rand -hex 32
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
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