"""
Configuration for Classifier Agent using Backend Settings
=========================================================

This module provides classifier configuration by wrapping the backend settings.
Maintains compatibility with lab config pattern while using backend infrastructure.
"""

from backend.core.config import settings
from backend.agents.base_config import BaseAgentConfig

class ClassifierConfig(BaseAgentConfig):
    """Classifier configuration using backend settings."""
    
    # Inherits all base properties: google_api_key, model_name, temperature, debug_mode, verbose_logging
    
    @property
    def max_react_iterations(self):
        return settings.MAX_REACT_ITERATIONS

# Global config for backward compatibility
config = ClassifierConfig()

# Warn about issues
issues = config.validate()
config._print_issues(issues, "Classifier")
