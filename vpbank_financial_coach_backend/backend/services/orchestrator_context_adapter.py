"""
Orchestrator Context Adapter - Backend-Only Context Management
==============================================================

This adapter manages user context for orchestrator operations using only backend services.
Since we've migrated fully to backend, this no longer bridges to lab but provides 
user-scoped context management.
"""

from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.services.conversation_service import ConversationService
from backend.services.financial_services import (
    JarManagementService, 
    TransactionService, 
    FeeManagementService,
    PlanManagementService
)
from backend.utils import db_utils
from backend.models.conversation import ConversationTurnBase


class OrchestratorContextAdapter:
    """
    Context manager for orchestrator operations using pure backend services.
    
    This adapter:
    1. Provides user-scoped context for orchestrator operations
    2. Manages conversation history and agent locks
    3. Ensures proper cleanup and state management
    4. Works entirely with backend services (no lab dependencies)
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        """Initialize context adapter for specific user."""
        self.db = db
        self.user_id = user_id
        self.conversation_service = ConversationService(db, user_id)
        
        # Initialize financial services
        self.jar_service = JarManagementService()
        self.transaction_service = TransactionService()
        self.fee_service = FeeManagementService()
        self.plan_service = PlanManagementService()
        
        # Track current context
        self.context_data = {
            "jars": [],
            "transactions": [],
            "fees": [],
            "plans": [],
            "conversation_history": [],
            "agent_lock": None
        }
    
    async def __aenter__(self):
        """Setup user context."""
        try:
            await self._load_user_context()
            return self
        except Exception as e:
            print(f"Error setting up user context: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup context."""
        try:
            await self._cleanup_context()
        except Exception as e:
            print(f"Error cleaning up context: {e}")
    
    async def _load_user_context(self):
        """Load user data into context."""
        try:
            # Load user jars
            user_jars = await db_utils.get_all_jars_for_user(self.db, self.user_id)
            self.context_data["jars"] = [self._convert_jar_to_dict(jar) for jar in user_jars]
            
            # Load user transactions
            user_transactions = await db_utils.get_all_transactions_for_user(self.db, self.user_id)
            self.context_data["transactions"] = [self._convert_transaction_to_dict(trans) for trans in user_transactions]
            
            # Load user fees
            user_fees = await db_utils.get_all_fees_for_user(self.db, self.user_id)
            self.context_data["fees"] = [self._convert_fee_to_dict(fee) for fee in user_fees]
            
            # Load user plans
            user_plans = await db_utils.get_all_plans_for_user(self.db, self.user_id)
            self.context_data["plans"] = [self._convert_plan_to_dict(plan) for plan in user_plans]
            
            # Load conversation history
            conversations = await self.conversation_service.get_conversation_history(limit=20)
            self.context_data["conversation_history"] = [self._convert_conversation_to_dict(conv) for conv in conversations]
            
            # Get agent lock
            agent_lock = await self.conversation_service.get_agent_lock()
            self.context_data["agent_lock"] = agent_lock
            
            print(f"✅ Loaded context for user {self.user_id}: "
                  f"{len(self.context_data['jars'])} jars, "
                  f"{len(self.context_data['transactions'])} transactions, "
                  f"{len(self.context_data['fees'])} fees, "
                  f"{len(self.context_data['plans'])} plans, "
                  f"{len(self.context_data['conversation_history'])} conversations, "
                  f"agent_lock: {self.context_data['agent_lock']}")
            
        except Exception as e:
            print(f"Error loading user context: {e}")
            raise
    
    async def _cleanup_context(self):
        """Clean up context data."""
        try:
            # Clear context data
            self.context_data = {
                "jars": [],
                "transactions": [],
                "fees": [],
                "plans": [],
                "conversation_history": [],
                "agent_lock": None
            }
            
            print(f"🧹 Cleaned up context for user {self.user_id}")
            
        except Exception as e:
            print(f"Error cleaning up context: {e}")
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current user context."""
        return {
            "user_id": self.user_id,
            "jars_count": len(self.context_data["jars"]),
            "transactions_count": len(self.context_data["transactions"]),
            "fees_count": len(self.context_data["fees"]),
            "plans_count": len(self.context_data["plans"]),
            "conversation_turns": len(self.context_data["conversation_history"]),
            "agent_lock": self.context_data["agent_lock"]
        }
    
    def _convert_jar_to_dict(self, jar_data) -> Dict[str, Any]:
        """Convert backend jar to dictionary format."""
        return {
            "name": jar_data.name,
            "description": jar_data.description,
            "percent": jar_data.percent,
            "amount": jar_data.amount
        }
    
    def _convert_transaction_to_dict(self, trans_data) -> Dict[str, Any]:
        """Convert backend transaction to dictionary format."""
        return {
            "amount": trans_data.amount,
            "jar": trans_data.jar,
            "description": trans_data.description,
            "date": trans_data.date,
            "time": trans_data.time,
            "source": trans_data.source
        }
    
    def _convert_fee_to_dict(self, fee_data) -> Dict[str, Any]:
        """Convert backend fee to dictionary format."""
        return {
            "name": fee_data.name,
            "amount": fee_data.amount,
            "frequency": fee_data.frequency,
            "jar": fee_data.jar,
            "next_occurrence": fee_data.next_occurrence,
            "description": fee_data.description
        }
    
    def _convert_plan_to_dict(self, plan_data) -> Dict[str, Any]:
        """Convert backend plan to dictionary format."""
        return {
            "name": plan_data.name,
            "description": plan_data.description,
            "target_amount": plan_data.target_amount,
            "current_amount": plan_data.current_amount,
            "target_date": plan_data.target_date,
            "priority": plan_data.priority,
            "status": plan_data.status
        }
    
    def _convert_conversation_to_dict(self, conv_data) -> Dict[str, Any]:
        """Convert backend conversation to dictionary format."""
        return {
            "user_input": conv_data.user_input,
            "agent_output": conv_data.agent_output,
            "agent_list": conv_data.agent_list,
            "tool_call_list": conv_data.tool_call_list
        }
