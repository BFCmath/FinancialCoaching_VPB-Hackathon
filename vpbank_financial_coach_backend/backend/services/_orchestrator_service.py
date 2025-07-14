# """
# Orchestrator Service - Unified Orchestrator Support
# ==================================================

# Consolidated service combining agent_orchestrator_service.py, orchestrator_context_adapter.py,
# and orchestrator_service.py.
# Handles chat processing, context management, and conversation handling.
# Integrated with all backend services.
# """

# import logging
# from typing import Dict, Optional, Any, List
# from datetime import datetime
# from motor.motor_asyncio import AsyncIOMotorDatabase

# from backend.models.conversation import ConversationTurnCreate
# from backend.utils import db_utils
# from .conversation_service import ConversationService  # Assuming consolidated conversation service
# from .financial_services import FinancialServices  # For accessing other services
# from .core_services import CalculationService

# class OrchestratorService:
#     """
#     Unified orchestrator service for processing messages and managing context.
#     """
    
#     def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
#         self.db = db
#         self.user_id = user_id
#         self.conversation_service = ConversationService(db, user_id)
#         self.logger = logging.getLogger(__name__)
        
#         # Access to other services
#         self.services = FinancialServices.get_all_services(db, user_id)
    
#     async def process_chat_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
#         """
#         Process user message through orchestrator.
        
#         Args:
#             message: User message
#             context: Optional additional context
            
#         Returns:
#             Response dict
#         """
#         try:
#             # Load context
#             full_context = await self._load_context(context)
            
#             # Get history
#             history = await self.conversation_service.get_conversation_history(limit=10)
            
#             # Call orchestrator (assume refactored to async)
#             from backend.agents.orchestrator import Orchestrator
#             orchestrator = Orchestrator(self.db, self.user_id)
#             result = await orchestrator.process_message(message, full_context, history)
            
#             # Store turn
#             turn = ConversationTurnCreate(
#                 user_input=message,
#                 agent_output=result.get("response", ""),
#                 agent_list=result.get("agent_list", []),
#                 tool_call_list=result.get("tool_call_list", [])
#             )
#             await self.conversation_service.add_conversation_turn(turn.user_input, turn.agent_output, 
#                                                                   turn.agent_list, turn.tool_call_list)
            
#             # Format response
#             return self._format_response(result)
            
#         except Exception as e:
#             self.logger.error(f"Orchestrator error for user {self.user_id}: {str(e)}")
#             return self._handle_error(e)
    
#     async def _load_context(self, additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
#         """Load comprehensive user context."""
#         context = {
#             "user_id": self.user_id,
#             "timestamp": datetime.utcnow().isoformat(),
#             "agent_lock": await self.conversation_service.check_conversation_lock()
#         }
        
#         try:
#             jars = await db_utils.get_all_jars_for_user(self.db, self.user_id)
#             transactions = await db_utils.get_all_transactions_for_user(self.db, self.user_id)
#             fees = await db_utils.get_all_fees_for_user(self.db, self.user_id)
#             plans = await db_utils.get_all_plans_for_user(self.db, self.user_id)
            
#             context["jars"] = [j.dict() for j in jars]
#             context["transactions"] = [t.dict() for t in transactions]
#             context["fees"] = [f.dict() for f in fees]
#             context["plans"] = [p.dict() for p in plans]
#         except Exception as e:
#             context["load_error"] = str(e)
        
#         if additional_context:
#             context.update(additional_context)
        
#         return context
    
#     def _format_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
#         """Format orchestrator result."""
#         return {
#             "response": result.get("response", ""),
#             "success": True,
#             "requires_follow_up": result.get("requires_follow_up", False),
#             "context": {
#                 "agent_list": result.get("agent_list", ["orchestrator"]),
#                 "tool_call_list": result.get("tool_call_list", []),
#                 "error_type": result.get("error_type"),
#                 "error_details": result.get("error_details")
#             }
#         }
    
#     def _handle_error(self, error: Exception) -> Dict[str, Any]:
#         """Handle errors."""
#         return {
#             "response": "I apologize, I encountered an issue processing your request. Please try again.",
#             "success": False,
#             "requires_follow_up": False,
#             "context": {
#                 "error_type": type(error).__name__,
#                 "error_details": str(error),
#                 "agent_list": ["orchestrator"],
#                 "tool_call_list": []
#             }
#         }
    
#     async def get_user_stats(self) -> Dict[str, Any]:
#         """Get user statistics."""
#         stats = await CalculationService.get_database_stats(self.db, self.user_id)
#         return stats
    
#     async def export_user_data(self) -> str:
#         """Export user data to JSON."""
#         return await CalculationService.export_database_json(self.db, self.user_id)