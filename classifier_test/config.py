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
