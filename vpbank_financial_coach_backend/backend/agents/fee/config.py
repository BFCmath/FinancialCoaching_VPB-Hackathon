"""
Configuration for Fee Manager Agent using Backend Settings
==========================================================

This module provides fee manager configuration by wrapping the backend settings.
Maintains compatibility with lab config pattern while using backend infrastructure.
"""

from backend.core.config import settings
from backend.agents.base_config import BaseAgentConfig

class FeeConfig(BaseAgentConfig):
    """Fee manager configuration using backend settings."""
    
    # Inherits all base properties: google_api_key, model_name, temperature, debug_mode, verbose_logging
    
    @property
    def high_confidence_threshold(self):
        return getattr(settings, 'HIGH_CONFIDENCE_THRESHOLD', 80)
    
    @property 
    def low_confidence_threshold(self):
        return getattr(settings, 'LOW_CONFIDENCE_THRESHOLD', 50)

# Global config for backward compatibility
config = FeeConfig()

# Warn about issues
issues = config.validate()
config._print_issues(issues, "Fee Manager")
