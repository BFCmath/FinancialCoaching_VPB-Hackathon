"""
Orchestrator - Central Router
=============================

Stateful router that classifies intents, handles locks, and uses tool calling for routing.
Single flow with LLM deciding direct response or tool calls (agent routes).

This orchestrator works with backend services and properly integrates with the production backend.
"""

from typing import Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Import backend components
from backend.core.config import settings
from backend.models.conversation import ConversationTurnBase, ConversationTurnCreate, ConversationTurnInDB
from backend.agents.orchestrator.prompt import build_orchestrator_prompt
from backend.agents.orchestrator.tools import get_all_orchestrator_tools
from backend.services.conversation_service import ConversationService
from backend.utils import db_utils

# Constants
MAX_MEMORY_TURNS = 10

def create_llm_with_tools():
    """Create Gemini LLM with orchestrator tools bound."""
    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is required")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite-preview-06-17",
        temperature=0.1,
        google_api_key=settings.GOOGLE_API_KEY
    )
    return llm.bind_tools(get_all_orchestrator_tools())

def filter_agent_history(history: List[ConversationTurnInDB], agent_name: str) -> List[ConversationTurnInDB]:
    """Filter history to turns involving specific agent."""
    list_turn = [turn for turn in history if agent_name in turn.agent_list]
    return list_turn

async def process_task_async(task: str, user_id: str, db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """
    Main async entry point for orchestrator processing.
    
    Args:
        task: User input message
        user_id: Current user ID
        db: Database connection
            
    Returns:
        Dict with response and metadata
    """
    tool_calls_made = []
    
    try:
        # Initialize services
        conversation_service = ConversationService(db, user_id)
        
        # Create LLM with tools
        llm_with_tools = create_llm_with_tools()
        
        # Check if there's an active agent lock
        locked_agent = await db_utils.get_agent_lock_for_user(db, user_id)
        
        if locked_agent:
            print(f"🔒 User locked to agent: {locked_agent}")
            # Handle locked agent routing
            # For now, just release the lock and continue with orchestrator
            await db_utils.set_agent_lock_for_user(db, user_id, None)
        
        # Get conversation history (last 10 turns)
        conversation_history = await conversation_service.get_conversation_history(limit=MAX_MEMORY_TURNS)
        
        # Build prompt with history
        prompt = build_orchestrator_prompt(task, conversation_history)
        
        # Initialize messages for LLM
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=task)
        ]
        
        # Invoke LLM with tools
        response = llm_with_tools.invoke(messages)
        
        # If no tool calls, provide direct response
        if not response.tool_calls:
            direct_response = response.content
            
            # Log the conversation turn
            turn_data = ConversationTurnCreate(
                user_input=task,
                agent_output=direct_response,
                agent_list=['orchestrator'],
                tool_call_list=[]
            )
            await conversation_service.add_conversation_turn(turn_data)
            
            return {"response": direct_response, "requires_follow_up": False}
        
        # Process tool calls
        responses = []
        requires_follow_up = False
        
        for tool_call in response.tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            tool_calls_made.append(f"{tool_name}(args={tool_args})")
            
            # Execute the tool
            tool_func = next((t for t in get_all_orchestrator_tools() if t.name == tool_name), None)
            if tool_func:
                result = tool_func.invoke(tool_args)
                responses.append(result["response"])
                if result.get("requires_follow_up", False):
                    requires_follow_up = True
            else:
                responses.append(f"❌ Tool {tool_name} not found")
        
        # Combine responses
        final_response = "\n\n".join(responses) if len(responses) > 1 else responses[0]
        
        # Log the conversation turn with tool calls
        turn_data = ConversationTurnCreate(
            user_input=task,
            agent_output=final_response,
            agent_list=['orchestrator'],
            tool_call_list=tool_calls_made
        )
        await conversation_service.add_conversation_turn(turn_data)
        
        return {"response": final_response, "requires_follow_up": requires_follow_up}
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = f"❌ Orchestrator error: {str(e)}"
        return {"response": error_msg, "requires_follow_up": False}


def process_task(task: str, conversation_history: List[ConversationTurnInDB] = None) -> Dict[str, Any]:
    """
    Legacy sync interface for backward compatibility.
    This should not be used directly in backend - use process_task_async instead.
    
    Args:
        task: User input
        conversation_history: Legacy parameter (ignored)
        
    Returns:
        Error message directing to use async interface
    """
    return {
        "response": "❌ This orchestrator requires async interface. Use AgentOrchestratorService.process_chat_message() instead.",
        "requires_follow_up": False
    }