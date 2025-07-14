"""
Simple Configuration for Jar Manager Prompt Testing
===================================================

Minimal config focused only on testing if prompts route correctly.
"""

import os
from dataclasses import dataclass
from typing import Optional

# Load .env file if available
from dotenv import load_dotenv  # always import this
load_dotenv()


@dataclass
class Config:
    """Simple configuration for jar manager prompt testing."""
    
    # Gemini settings
    google_api_key: Optional[str] = None
    model_name: str = "gemini-2.5-flash-lite-preview-06-17"
    temperature: float = 0.1
    
    # Testing modes
    debug_mode: bool = False
    verbose_logging: bool = True
    # Confidence thresholds
    high_confidence_threshold: int = 80
    low_confidence_threshold: int = 50
    
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
        
        # Load confidence thresholds
        high_thresh = os.getenv("HIGH_CONFIDENCE_THRESHOLD")
        if high_thresh:
            try:
                self.high_confidence_threshold = int(high_thresh)
            except ValueError:
                pass
                
        low_thresh = os.getenv("LOW_CONFIDENCE_THRESHOLD")
        if low_thresh:
            try:
                self.low_confidence_threshold = int(low_thresh)
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
