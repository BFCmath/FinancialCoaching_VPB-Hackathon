"""
Configuration for Orchestrator using Backend Settings
====================================================

This module provides orchestrator configuration by wrapping the backend settings.
Maintains compatibility with lab config pattern while using backend infrastructure.
"""

from backend.agents.base_config import BaseAgentConfig

class OrchestratorConfig(BaseAgentConfig):
    """Orchestrator configuration using backend settings."""
    
    # Inherits all base properties: google_api_key, model_name, temperature, debug_mode, verbose_logging
    pass

# Global config for backward compatibility
config = OrchestratorConfig()

# Warn about issues
issues = config.validate()
config._print_issues(issues, "Orchestrator") 