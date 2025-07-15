from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.api import deps
from backend.models import user as user_model
from backend.services.orchestrator_service import OrchestratorService
from backend.models import conversation as conversation_model
from backend.services.conversation_service import ConversationService

router = APIRouter()

# --- Request and Response Models ---
class ChatRequest(BaseModel):
    message: str = Field(..., example="How much did I spend on play last month?") 
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the chat")

class ChatResponse(BaseModel):
    response: str
    success: bool
    context: Optional[Dict[str, Any]] = None

@router.post("/", response_model=ChatResponse)
async def handle_chat_message(
    request: ChatRequest,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_active_user)
):
    """
    Handles a user's chat message through the orchestrator service.
    
    This endpoint:
    1. Creates an OrchestratorService instance for the current user
    2. Processes the message using the orchestrator and backend financial data
    3. Returns an AI-powered response based on user's financial state and agent routing
    """
    try:
        # Create orchestrator service for this user
        orchestrator_service = OrchestratorService(db, str(current_user.id))
        print("Processing chat message:", request.message)
        # Process the message through orchestrator
        result = await orchestrator_service.process_chat_message(
            message=request.message
        )
        
        return ChatResponse(
            response=result["response"],
            success=result["success"],
            context=result.get("context")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat message: {str(e)}"
        )
        

@router.get("/history", response_model=List[conversation_model.ConversationTurnInDB])
async def get_chat_history(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_active_user),
    limit: int = Query(20, ge=1, le=100, description="Number of recent conversation turns to retrieve.")
):
    """
    Retrieves the conversation history for the currently authenticated user.
    """
    try:
        # Instantiate the service for the current user
        conversation_service = ConversationService(db, str(current_user.id))
        
        # Fetch the history from the service
        history = await conversation_service.get_conversation_history(limit=limit)
        
        return history
        
    except Exception as e:
        # Handle potential errors, though less likely for a GET request
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )