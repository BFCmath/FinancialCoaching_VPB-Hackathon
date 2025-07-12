"""
Knowledge Base Agent Configuration
=================================

Configuration management for the knowledge base agent.
Handles environment variables, settings, and defaults.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for the Knowledge Base Agent"""
    
    def __init__(self):
        """Initialize configuration with environment variables and defaults"""
        
        # Required: Google AI API Key
        self.google_api_key = self._get_required_env("GOOGLE_API_KEY")
        
        # LLM Configuration
        self.model_name = os.getenv("MODEL_NAME", "gemini-2.5-flash-lite-preview-06-17")
        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
        
        # Processing Configuration
        self.max_react_iterations = int(os.getenv("MAX_REACT_ITERATIONS", "6"))
        self.search_timeout = int(os.getenv("SEARCH_TIMEOUT", "30"))
        
        # Feature Toggles
        self.enable_online_search = self._get_bool_env("ENABLE_ONLINE_SEARCH", "true")
        self.enable_app_documentation = self._get_bool_env("ENABLE_APP_DOCUMENTATION", "true")
        self.enable_debug_mode = self._get_bool_env("DEBUG_MODE", "false")
        
        # Development Settings
        self.debug_mode = self._get_bool_env("DEBUG_MODE", "false")
        self.verbose_logging = self._get_bool_env("VERBOSE_LOGGING", "false")
        self.mock_search_mode = self._get_bool_env("MOCK_SEARCH_MODE", "false")
        
        # Validate configuration
        self._validate_config()
    
    def _get_required_env(self, key: str) -> str:
        """
        Get a required environment variable.
        
        Args:
            key: Environment variable key
            
        Returns:
            Environment variable value
            
        Raises:
            ValueError: If the required variable is not set
        """
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set. Please check your .env file.")
        return value
    
    def _get_bool_env(self, key: str, default: str = "false") -> bool:
        """
        Get a boolean environment variable.
        
        Args:
            key: Environment variable key
            default: Default value as string
            
        Returns:
            Boolean value
        """
        value = os.getenv(key, default).lower()
        return value in ("true", "1", "yes", "on")
    
    def _validate_config(self):
        """Validate the configuration settings"""
        
        # Validate temperature range
        if not 0.0 <= self.llm_temperature <= 2.0:
            raise ValueError(f"LLM_TEMPERATURE must be between 0.0 and 2.0, got {self.llm_temperature}")
        
        # Validate max iterations
        if not 1 <= self.max_react_iterations <= 20:
            raise ValueError(f"MAX_REACT_ITERATIONS must be between 1 and 20, got {self.max_react_iterations}")
        
        # Validate search timeout
        if not 5 <= self.search_timeout <= 120:
            raise ValueError(f"SEARCH_TIMEOUT must be between 5 and 120 seconds, got {self.search_timeout}")
    
    def get_llm_config(self) -> dict:
        """
        Get LLM configuration dictionary.
        
        Returns:
            Dictionary with LLM configuration
        """
        return {
            "model": self.model_name,
            "google_api_key": self.google_api_key,
            "temperature": self.llm_temperature
        }
    
    def get_processing_config(self) -> dict:
        """
        Get processing configuration dictionary.
        
        Returns:
            Dictionary with processing configuration
        """
        return {
            "max_react_iterations": self.max_react_iterations,
            "search_timeout": self.search_timeout,
            "debug_mode": self.debug_mode
        }
    
    def get_feature_flags(self) -> dict:
        """
        Get feature flags dictionary.
        
        Returns:
            Dictionary with feature flags
        """
        return {
            "enable_online_search": self.enable_online_search,
            "enable_app_documentation": self.enable_app_documentation,
            "enable_debug_mode": self.enable_debug_mode,
            "verbose_logging": self.verbose_logging,
            "mock_search_mode": self.mock_search_mode
        }
    
    def display_config(self) -> str:
        """
        Display current configuration (without sensitive data).
        
        Returns:
            Formatted configuration string
        """
        
        config_info = f"""
🔧 Knowledge Base Agent Configuration
=====================================

🤖 LLM Settings:
  • Model: {self.model_name}
  • Temperature: {self.llm_temperature}
  • API Key: {'✓ Set' if self.google_api_key else '✗ Missing'}

⚙️ Processing Settings:
  • Max ReAct Iterations: {self.max_react_iterations}
  • Search Timeout: {self.search_timeout}s
  • Debug Mode: {'✓ Enabled' if self.debug_mode else '✗ Disabled'}

🔧 Feature Flags:
  • Online Search: {'✓ Enabled' if self.enable_online_search else '✗ Disabled'}
  • App Documentation: {'✓ Enabled' if self.enable_app_documentation else '✗ Disabled'}
  • Verbose Logging: {'✓ Enabled' if self.verbose_logging else '✗ Disabled'}
  • Mock Search Mode: {'✓ Enabled' if self.mock_search_mode else '✗ Disabled'}
"""
        return config_info.strip()


# Global configuration instance
config = Config()

# Convenience properties for backward compatibility
google_api_key = config.google_api_key
model_name = config.model_name
llm_temperature = config.llm_temperature
debug_mode = config.debug_mode
max_react_iterations = config.max_react_iterations


def validate_environment() -> bool:
    """
    Validate that the environment is properly configured.
    
    Returns:
        True if environment is valid
    """
    try:
        # Test that we can create a config instance
        test_config = Config()
        
        # Check required settings
        if not test_config.google_api_key:
            print("❌ GOOGLE_API_KEY is required but not set")
            return False
            
        print("✅ Environment configuration is valid")
        return True
        
    except Exception as e:
        print(f"❌ Environment validation failed: {str(e)}")
        return False


def display_environment_help():
    """Display help for setting up the environment"""
    
    help_text = """
🔧 Knowledge Base Agent - Environment Setup
==========================================

Required Environment Variables:
• GOOGLE_API_KEY - Your Google AI API key for Gemini LLM

Optional Settings:
• MODEL_NAME - Gemini model (default: gemini-2.5-flash-lite-preview-06-17)
• LLM_TEMPERATURE - Response creativity 0.0-2.0 (default: 0.1)
• MAX_REACT_ITERATIONS - Max reasoning steps (default: 6)
• SEARCH_TIMEOUT - Search timeout in seconds (default: 30)
• DEBUG_MODE - Enable debug logging (default: false)

Setup Steps:
1. Copy env.example to .env
2. Edit .env and add your GOOGLE_API_KEY
3. Optionally adjust other settings
4. Run the agent

Example .env file:
GOOGLE_API_KEY=your_api_key_here
DEBUG_MODE=true
LLM_TEMPERATURE=0.1
"""
    
    print(help_text.strip())


def get_config_summary() -> dict:
    """
    Get a summary of current configuration.
    
    Returns:
        Dictionary with configuration summary
    """
    return {
        "llm_config": config.get_llm_config(),
        "processing_config": config.get_processing_config(),
        "feature_flags": config.get_feature_flags()
    }


if __name__ == "__main__":
    # Configuration testing and display
    try:
        print(config.display_config())
        print("\n" + "="*50)
        
        if validate_environment():
            print("\n✅ Configuration is ready for use!")
        else:
            print("\n❌ Configuration needs attention")
            print("\nFor help, run:")
            print("python -c 'from config import display_environment_help; display_environment_help()'")
            
    except Exception as e:
        print(f"\n❌ Configuration error: {str(e)}")
        display_environment_help()
