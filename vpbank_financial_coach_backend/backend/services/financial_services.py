"""
Financial Services Layer - Unified Entry Point
=============================================

Provides factories for all services, ensuring user-scoped instantiation.
Covers all services from lab service.py, organized by category.
- Core: UserSettingsService, CalculationService
- Jar: JarManagementService
- Transaction: TransactionService, TransactionQueryService
- Fee: FeeManagementService
- Plan: PlanManagementService
- Conversation: ConversationService
- Confidence: ConfidenceService
- Communication: AgentCommunicationService
- Knowledge: KnowledgeService
- Orchestrator: OrchestratorService
- Security: SecurityService
No globals; use factories with db and user_id.
"""

from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import all services
from .core_services import UserSettingsService, CalculationService
from .jar_service import JarManagementService
from .transaction_service import TransactionService, TransactionQueryService
from .fee_service import FeeManagementService
from .plan_service import PlanManagementService
from .conversation_service import ConversationService
from .confidence_service import ConfidenceService
from .communication_service import AgentCommunicationService
from .knowledge_service import KnowledgeService

class FinancialServices:
    """
    Factory class for creating user-scoped service instances.
    """
    
    @staticmethod
    def get_user_settings_service() -> UserSettingsService:
        """Get user settings service (stateless)."""
        return UserSettingsService
    
    @staticmethod
    def get_calculation_service() -> CalculationService:
        """Get calculation service (stateless)."""
        return CalculationService
    
    @staticmethod
    def get_jar_service() -> JarManagementService:
        """Get jar management service (stateless methods)."""
        return JarManagementService
    
    @staticmethod
    def get_transaction_service() -> TransactionService:
        """Get transaction management service (stateless methods)."""
        return TransactionService
    
    @staticmethod
    def get_transaction_query_service() -> TransactionQueryService:
        """Get transaction query service (stateless methods)."""
        return TransactionQueryService
    
    @staticmethod
    def get_fee_service() -> FeeManagementService:
        """Get fee management service (stateless methods)."""
        return FeeManagementService
    
    @staticmethod
    def get_plan_service() -> PlanManagementService:
        """Get plan management service (stateless methods)."""
        return PlanManagementService
    
    @staticmethod
    def get_conversation_service(db: AsyncIOMotorDatabase, user_id: str) -> ConversationService:
        """Get conversation service (user-scoped)."""
        return ConversationService(db, user_id)
    
    @staticmethod
    def get_confidence_service() -> ConfidenceService:
        """Get confidence service (stateless)."""
        return ConfidenceService
    
    @staticmethod
    def get_communication_service() -> AgentCommunicationService:
        """Get agent communication service (stateless methods)."""
        return AgentCommunicationService
    
    @staticmethod
    def get_knowledge_service() -> KnowledgeService:
        """Get knowledge service (stateless methods)."""
        return KnowledgeService
    
    @staticmethod
    def get_all_services(db: AsyncIOMotorDatabase, user_id: str) -> Dict[str, Any]:
        """Get dictionary of all services, instantiating user-scoped ones."""
        return {
            "user_settings": FinancialServices.get_user_settings_service(),
            "calculation": FinancialServices.get_calculation_service(),
            "jar": FinancialServices.get_jar_service(),
            "transaction": FinancialServices.get_transaction_service(),
            "transaction_query": FinancialServices.get_transaction_query_service(),
            "fee": FinancialServices.get_fee_service(),
            "plan": FinancialServices.get_plan_service(),
            "conversation": FinancialServices.get_conversation_service(db, user_id),
            "confidence": FinancialServices.get_confidence_service(),
            "communication": FinancialServices.get_communication_service(),
            "knowledge": FinancialServices.get_knowledge_service(),
        }