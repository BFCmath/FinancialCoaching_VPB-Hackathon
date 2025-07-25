"""
Orchestrator Service - Standardized Error Handling Interface
============================================================

Standardized service that interfaces between chat API endpoint and orchestrator.
Returns ConversationTurnInDB objects and raises errors for proper HTTP handling.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.models.conversation import ConversationTurnInDB


class OrchestratorService:
    """Standardized orchestrator service with static methods and proper error handling."""
    
    @staticmethod
    async def process_chat_message(db: AsyncIOMotorDatabase, user_id: str, 
                                   message: str) -> ConversationTurnInDB:
        """
        Main chat processing function - standardized interface to orchestrator.
        
        Args:
            db: Database connection
            user_id: User identifier
            message: User's chat message
            
        Returns:
            ConversationTurnInDB object containing the complete conversation turn
            
        Raises:
            ValueError: For invalid input parameters or processing errors
        """
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")
        if db is None:
            raise ValueError("Database connection cannot be None")
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")
        
        try:
            # Import and call orchestrator process_task_async
            # For now, we'll assume this function exists and returns ConversationTurnInDB
            from backend.agents.orchestrator.main import process_task_async
            
            # Call the orchestrator - assume it returns ConversationTurnInDB
            result = await process_task_async(message.strip(), user_id, db)
            
            # Validate the result is a ConversationTurnInDB object
            if not isinstance(result, ConversationTurnInDB):
                raise ValueError("Orchestrator returned invalid response type")
            print(f"✅ Processed message for user {user_id}: {message.strip()}")
            return result
            
        except ImportError as e:
            # Handle case where orchestrator main module doesn't exist yet
            raise ValueError(f"Orchestrator module not available: {str(e)}")
        except Exception as e:
            # Handle any orchestrator processing errors
            raise ValueError(f"Orchestrator processing failed: {str(e)}")
