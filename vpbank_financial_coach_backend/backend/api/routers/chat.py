from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.api import deps
from backend.models import user as user_model
from backend.services.orchestrator_service import OrchestratorService
from backend.models.conversation import ConversationTurnInDB
from backend.services.conversation_service import ConversationService

router = APIRouter()

# --- Request Model ---
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, example="How much did I spend on play last month?")

@router.post("/", response_model=ConversationTurnInDB)
async def handle_chat_message(
    request: ChatRequest,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Handles a user's chat message through the orchestrator service.
    
    This endpoint:
    1. Validates the user's message
    2. Processes the message using the orchestrator service
    3. Returns the complete conversation turn (ConversationTurnInDB)
    4. Raises HTTPException for any errors (proper FastAPI error handling)
    """
    try:
        # Process the message through orchestrator service
        conversation_turn = await OrchestratorService.process_chat_message(
            db=db,
            user_id=str(current_user.id),
            message=request.message
        )
        
        return conversation_turn
        
    except ValueError as e:
        print(f"Error processing chat message: {str(e)}")
        # Handle validation errors from orchestrator service
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error processing chat message: {str(e)}")
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat message: {str(e)}"
        )
        

@router.get("/history", response_model=List[ConversationTurnInDB])
async def get_chat_history(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user),
    limit: int = Query(20, ge=1, le=100, description="Number of recent conversation turns to retrieve.")
):
    """
    Retrieves the conversation history for the currently authenticated user.
    """
    try:
        # Fetch the history using static service method
        history = await ConversationService.get_conversation_history(
            db=db,
            user_id=str(current_user.id),
            limit=limit
        )
        
        return history
        
    except ValueError as e:
        print(f"Error retrieving chat history: {str(e)}")
        # Handle validation errors from conversation service
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error retrieving chat history: {str(e)}")
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )