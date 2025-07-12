"""
Configuration for Transaction History Fetcher
==============================================

Configuration for transaction data retrieval using LangChain tool binding.
"""

import os
from dataclasses import dataclass
from typing import Optional

# Load .env file if available
from dotenv import load_dotenv
load_dotenv()


@dataclass
class Config:
    """Configuration for transaction history fetcher."""
    
    # LLM settings for tool binding
    google_api_key: Optional[str] = None
    model_name: str = "gemini-2.5-flash-lite-preview-06-17"
    temperature: float = 0.1
    
    # Transaction retrieval settings
    max_transactions_per_query: int = 100
    default_transaction_limit: int = 50
    
    # Tool selection settings
    enable_multi_tool_queries: bool = True
    max_tools_per_query: int = 5
    
    # Testing and debug
    debug_mode: bool = False
    mock_data_mode: bool = True  # Use mock data for testing
    verbose_logging: bool = True  # Enable detailed logging for debugging
    def __post_init__(self):
        """Load from environment variables."""
        self.google_api_key = os.getenv("GOOGLE_API_KEY", self.google_api_key)
        self.model_name = os.getenv("MODEL_NAME", self.model_name)
        
        # Temperature setting
        temp_str = os.getenv("LLM_TEMPERATURE")
        if temp_str:
            try:
                self.temperature = float(temp_str)
            except ValueError:
                pass
        
        # Transaction limits
        max_trans_str = os.getenv("MAX_TRANSACTIONS")
        if max_trans_str:
            try:
                self.max_transactions_per_query = int(max_trans_str)
            except ValueError:
                pass
        
        # Boolean settings
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1", "yes")
        self.mock_data_mode = os.getenv("MOCK_DATA_MODE", "true").lower() in ("true", "1", "yes")
        self.enable_multi_tool_queries = os.getenv("ENABLE_MULTI_TOOL", "true").lower() in ("true", "1", "yes")
    
    def validate(self) -> list[str]:
        """Validate configuration."""
        issues = []
        
        if not self.google_api_key:
            issues.append("GOOGLE_API_KEY required for LLM operations")
        
        if self.max_transactions_per_query <= 0:
            issues.append("MAX_TRANSACTIONS must be positive")
        
        if self.temperature < 0 or self.temperature > 1:
            issues.append("LLM_TEMPERATURE must be between 0 and 1")
        
        if self.max_tools_per_query <= 0:
            issues.append("MAX_TOOLS_PER_QUERY must be positive")
        
        return issues


# Global config instance
config = Config()

# Validate and warn about issues
issues = config.validate()
if issues:
    print("⚠️  Transaction History Fetcher Configuration Issues:")
    for issue in issues:
        print(f"   • {issue}")
    print()

# Success message for valid config
if not issues and config.debug_mode:
    print("✅ Transaction History Fetcher configuration loaded successfully")
    print(f"   • Model: {config.model_name}")
    print(f"   • Mock data mode: {config.mock_data_mode}")
    print(f"   • Max transactions: {config.max_transactions_per_query}")
    print(f"   • Multi-tool queries: {config.enable_multi_tool_queries}")
    print()
