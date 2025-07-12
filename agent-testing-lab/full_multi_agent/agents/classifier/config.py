"""
Simple Configuration for Classifier Agent Testing
==================================================

Minimal config focused only on testing transaction classification with LLM.
"""

import os
from dataclasses import dataclass
from typing import Optional

# Load .env file if available
from dotenv import load_dotenv
# Explicitly load the .env file from the same directory as this config file.
# This ensures the agent finds its configuration regardless of the execution path.
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
else:
    load_dotenv()


@dataclass
class Config:
    """Simple configuration for classifier testing."""
    
    # Gemini settings
    google_api_key: Optional[str] = None
    model_name: str = "gemini-2.5-flash-lite-preview-06-17"
    temperature: float = 0.1
    
    # Testing modes
    debug_mode: bool = False
    max_react_iterations: int = 5
    verbose_logging: bool = True
    
    def __post_init__(self):
        """Load from environment variables."""
        self.google_api_key = os.getenv("GOOGLE_API_KEY", self.google_api_key)
        self.model_name = os.getenv("MODEL_NAME", self.model_name)
        
        temp_str = os.getenv("LLM_TEMPERATURE")
        if temp_str:
            try:
                self.temperature = float(temp_str)
            except ValueError:
                pass
        
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1", "yes")

        iterations_str = os.getenv("MAX_REACT_ITERATIONS")
        if iterations_str:
            try:
                self.max_react_iterations = int(iterations_str)
            except ValueError:
                pass
    
    def validate(self) -> list[str]:
        """Basic validation."""
        issues = []
        if not self.google_api_key:
            issues.append("GOOGLE_API_KEY required")
        return issues


# Global config
config = Config()

# Warn about issues
issues = config.validate()
if issues:
    print("⚠️  Configuration Issues:")
    for issue in issues:
        print(f"   • {issue}")
    print()
