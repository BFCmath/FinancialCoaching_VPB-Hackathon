"""
Configuration for Budget Advisor Agent
======================================

Configuration for LLM-powered financial advisory services.
"""

import os
from dataclasses import dataclass
from typing import Optional

# Load .env file if available
from dotenv import load_dotenv
load_dotenv()

@dataclass
class Config:
    """Configuration for Budget Advisor agent."""
    
    # LLM settings
    google_api_key: Optional[str] = None
    model_name: str = "gemini-2.5-flash-lite-preview-06-17"
    temperature: float = 0.1
    
    # ReAct framework settings
    max_react_iterations: int = 6
    
    # Advisory settings
    default_confidence_threshold: int = 70
    enable_proposal_system: bool = True
    enable_multi_agent_integration: bool = True
    
    # Memory settings (for interactive mode only)
    enable_memory: bool = True
    max_memory_turns: int = 10
    
    # Testing and debug
    debug_mode: bool = True
    verbose_logging: bool = True
    
    def __post_init__(self):
        """Load from environment variables."""
        self.google_api_key = os.getenv("GOOGLE_API_KEY", self.google_api_key)
        self.model_name = os.getenv("PLAN_MODEL_NAME", self.model_name)
        
        # Temperature setting
        temp_str = os.getenv("LLM_TEMPERATURE")
        if temp_str:
            try:
                self.temperature = float(temp_str)
            except ValueError:
                pass
        
        # ReAct iterations
        iterations_str = os.getenv("MAX_REACT_ITERATIONS")
        if iterations_str:
            try:
                self.max_react_iterations = int(iterations_str)
            except ValueError:
                pass
        
        # Confidence threshold
        confidence_str = os.getenv("CONFIDENCE_THRESHOLD")
        if confidence_str:
            try:
                self.default_confidence_threshold = int(confidence_str)
            except ValueError:
                pass
        
        # Memory turns
        memory_turns_str = os.getenv("MAX_MEMORY_TURNS")
        if memory_turns_str:
            try:
                self.max_memory_turns = int(memory_turns_str)
            except ValueError:
                pass
        
        # Boolean settings
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1", "yes")
        self.verbose_logging = os.getenv("VERBOSE_LOGGING", "false").lower() in ("true", "1", "yes")
        self.enable_proposal_system = os.getenv("ENABLE_PROPOSALS", "true").lower() in ("true", "1", "yes")
        self.enable_multi_agent_integration = os.getenv("ENABLE_MULTI_AGENT", "true").lower() in ("true", "1", "yes")
        self.enable_memory = os.getenv("ENABLE_MEMORY", "true").lower() in ("true", "1", "yes")
    
    def validate(self) -> list[str]:
        """Validate configuration."""
        issues = []
        
        if not self.google_api_key:
            issues.append("GOOGLE_API_KEY required for LLM operations")
        
        if self.temperature < 0 or self.temperature > 1:
            issues.append("LLM_TEMPERATURE must be between 0 and 1")
        
        if self.max_react_iterations <= 0:
            issues.append("MAX_REACT_ITERATIONS must be positive")
        
        if self.default_confidence_threshold < 0 or self.default_confidence_threshold > 100:
            issues.append("CONFIDENCE_THRESHOLD must be between 0 and 100")
        
        if self.max_memory_turns <= 0:
            issues.append("MAX_MEMORY_TURNS must be positive")
        
        return issues

# Global config instance
config = Config()

# Validate and warn about issues
issues = config.validate()
if issues:
    print("⚠️  Budget Advisor Configuration Issues:")
    for issue in issues:
        print(f"   • {issue}")
    print()

# Success message for valid config
if not issues and config.debug_mode:
    print("✅ Budget Advisor configuration loaded successfully")
    print(f"   • Model: {config.model_name}")
    print(f"   • Temperature: {config.temperature}")
    print(f"   • Max iterations: {config.max_react_iterations}")
    print(f"   • Proposal system: {config.enable_proposal_system}")
    print(f"   • Multi-agent integration: {config.enable_multi_agent_integration}")
    print(f"   • Memory enabled: {config.enable_memory}")
    print(f"   • Max memory turns: {config.max_memory_turns}")
    print()
