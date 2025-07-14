"""
Financial Services Layer - Clean Modular Implementation
======================================================

This module serves as the main entry point for all financial services,
providing a clean interface to the modular service architecture.

REFACTORED ARCHITECTURE:
- Core Financial Services: jar, transaction, fee management
- Agent Support Services: plan, knowledge, confidence, communication  
- Integration Layer: adapters, orchestrator support
- Support Services: conversation, security utilities
"""

# =============================================================================
# CORE FINANCIAL SERVICES
# =============================================================================

# Foundation services (calculations, user settings)
from .core_services import (
    UserSettingsService,
    CalculationService
)

# Core financial operations
from .jar_service import JarManagementService
from .transaction_service import TransactionService, TransactionQueryService  
from .fee_service import FeeManagementService

# =============================================================================
# AGENT SUPPORT SERVICES (SPLIT FROM additional_services.py)
# =============================================================================

# Specialized agent services
from .plan_service import PlanManagementService
from .knowledge_service import KnowledgeService
from .confidence_service import ConfidenceService
from .communication_service import AgentCommunicationService

# =============================================================================
# INTEGRATION LAYER
# =============================================================================

# Lab compatibility adapters
from .adapters import (
    ClassifierServiceAdapter,
    FeeServiceAdapter,
    configure_classifier_services,
    configure_fee_services,
    get_transaction_service,
    get_communication_service,
    get_fee_service
)

# Orchestrator support (consolidated)
from .orchestrator_service import OrchestratorService

# =============================================================================
# SUPPORT SERVICES
# =============================================================================

from .conversation_service import ConversationService
from .security import SecurityService

# =============================================================================
# CONVENIENCE FUNCTIONS FOR BACKWARD COMPATIBILITY
# =============================================================================

# These functions maintain compatibility with existing agent imports
def get_jar_service():
    """Get jar management service."""
    return JarManagementService

def get_plan_service():
    """Get plan management service."""
    return PlanManagementService

def get_knowledge_service():
    """Get knowledge service."""
    return KnowledgeService

def get_confidence_service():
    """Get confidence service."""
    return ConfidenceService

def get_orchestrator_service():
    """Get orchestrator service."""
    return OrchestratorService

# =============================================================================
# SERVICE REGISTRY FOR DISCOVERY
# =============================================================================

AVAILABLE_SERVICES = {
    # Core Financial
    "jar_management": JarManagementService,
    "transaction": TransactionService,
    "transaction_query": TransactionQueryService,
    "fee_management": FeeManagementService,
    "user_settings": UserSettingsService,
    "calculation": CalculationService,
    
    # Agent Support
    "plan_management": PlanManagementService,
    "knowledge": KnowledgeService,
    "confidence": ConfidenceService,
    "agent_communication": AgentCommunicationService,
    
    # Integration
    "orchestrator": OrchestratorService,
    "conversation": ConversationService,
    "security": SecurityService
}
