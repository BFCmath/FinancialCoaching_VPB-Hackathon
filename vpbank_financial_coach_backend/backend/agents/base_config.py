"""
Base Agent Configuration
========================

Shared configuration base class for all agents to ensure consistency.
"""

from backend.core.config import settings

class BaseAgentConfig:
    """Base configuration class for all agents."""
    
    @property
    def google_api_key(self):
        return settings.GOOGLE_API_KEY
    
    @property
    def model_name(self):
        return settings.MODEL_NAME
    
    @property
    def temperature(self):
        return settings.LLM_TEMPERATURE
    
    @property
    def debug_mode(self):
        return settings.DEBUG
    
    @property
    def verbose_logging(self):
        return settings.VERBOSE_LOGGING
    
    def validate(self) -> list[str]:
        """Basic validation common to all agents."""
        issues = []
        if not self.google_api_key:
            issues.append("GOOGLE_API_KEY required")
        return issues
    
    def _print_issues(self, issues: list[str], agent_name: str = "Agent"):
        """Helper method to print configuration issues."""
        if issues:
            print(f"⚠️  {agent_name} Configuration Issues:")
            for issue in issues:
                print(f"   • {issue}")
            print()
