"""
Transaction Fetcher Agent Configuration - Backend Integrated
===========================================================

Configuration management for the transaction fetcher agent, using backend settings.
"""

from backend.core.config import settings
from backend.agents.base_config import BaseAgentConfig

class FetcherConfig(BaseAgentConfig):
    """Transaction fetcher agent configuration using backend settings."""
    
    # This agent uses the base properties:
    # google_api_key, model_name, temperature, debug_mode, verbose_logging
    pass

# Global config for backward compatibility
config = FetcherConfig()

# Warn about issues
issues = config.validate()
config._print_issues(issues, "Transaction Fetcher Agent")