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
# Import agent interfaces
from backend.agents.classifier.interface import ClassifierInterface
from backend.agents.fee.interface import FeeManagerInterface  
from backend.agents.jar.interface import JarManagerInterface
from backend.agents.knowledge.interface import KnowledgeInterface
from backend.agents.plan.interface import BudgetAdvisorInterface
from backend.agents.transaction_fetcher.interface import TransactionFetcherInterface
from backend.agents.orchestrator.tools import set_orchestrator_context

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

async def route_to_agent(agent_name: str, task: str, db: AsyncIOMotorDatabase, user_id: str, conversation_history: List[ConversationTurnInDB]) -> Dict[str, Any]:
    """
    Route a task to a specific Enhanced Pattern 2 agent.
    
    Args:
        agent_name: Name of the agent (classifier, jar, fee, knowledge, plan, fetcher)
        task: Task description for the agent
        db: Database connection
        user_id: User identifier
        conversation_history: Conversation history
        
    Returns:
        Agent response dict
    """
    try:
        # Route to appropriate agent
        if agent_name == "classifier":
            interface = ClassifierInterface()
            return await interface.process_task(task, db, user_id, conversation_history)
        
        elif agent_name == "jar":
            interface = JarManagerInterface()
            return await interface.process_task(task, db, user_id, conversation_history)
        
        elif agent_name == "fee":
            interface = FeeManagerInterface()
            return await interface.process_task(task, db, user_id, conversation_history)
        
        elif agent_name == "knowledge":
            interface = KnowledgeInterface()
            return await interface.process_task(task, db, user_id, conversation_history)
        
        elif agent_name == "plan":
            interface = BudgetAdvisorInterface()
            return await interface.process_task(task, db, user_id, conversation_history)
        
        elif agent_name == "fetcher":
            interface = TransactionFetcherInterface()
            return await interface.process_task(task, db, user_id, conversation_history)
        
        else:
            return {
                "response": f"❌ Unknown agent: {agent_name}",
                "requires_follow_up": False
            }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "response": f"❌ Error calling {agent_name} agent: {str(e)}",
            "requires_follow_up": False
        }

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
        # Set context for orchestrator tools
        
        # Initialize services
        conversation_service = ConversationService(db, user_id)
        
        # Get conversation history (last 10 turns)
        conversation_history = await conversation_service.get_conversation_history(limit=MAX_MEMORY_TURNS)
        
        # Set context for tools
        set_orchestrator_context(db, user_id, conversation_history)
        
        # Create LLM with tools
        llm_with_tools = create_llm_with_tools()
        
        # Check if there's an active agent lock
        locked_agent = await db_utils.get_agent_lock_for_user(db, user_id)
        
        if locked_agent:
            print(f"🔒 User locked to agent: {locked_agent}")
            # Route directly to locked agent
            result = await route_to_agent(locked_agent, task, db, user_id, conversation_history)
            
            # Check if the locked agent still requires follow-up
            if not result.get("requires_follow_up", False):
                # Release the lock if no more follow-up needed
                await db_utils.set_agent_lock_for_user(db, user_id, None)
                print(f"🔓 Released lock from agent: {locked_agent} (conversation complete)")
            
            # Log the conversation turn for locked agent with metadata
            turn_data = ConversationTurnCreate(
                user_input=task,
                agent_output=result["response"],
                agent_list=[locked_agent],
                tool_call_list=[],
                metadata=result.get("metadata", {})  # Include agent metadata (e.g., plan stage)
            )
            await conversation_service.add_conversation_turn(turn_data)
            
            return result
        
        # Build prompt with history
        prompt = build_orchestrator_prompt(task, conversation_history)
        
        # Initialize messages for LLM
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=task)
        ]
        
        # Invoke LLM with tools to get routing decision
        response = llm_with_tools.invoke(messages)
        
        # If no tool calls, provide direct response
        if not response.tool_calls:
            direct_response = response.content
            
            # Release any existing agent lock for direct responses
            await db_utils.set_agent_lock_for_user(db, user_id, None)
            
            # Log the conversation turn
            turn_data = ConversationTurnCreate(
                user_input=task,
                agent_output=direct_response,
                agent_list=['orchestrator'],
                tool_call_list=[]
            )
            await conversation_service.add_conversation_turn(turn_data)
            
            return {"response": direct_response, "requires_follow_up": False}
        
        # Process the first tool call (orchestrator should only call one routing tool)
        tool_call = response.tool_calls[0]
        tool_name = tool_call['name']
        tool_args = tool_call['args']
        tool_calls_made.append(f"{tool_name}(args={tool_args})")
        
        # Execute the routing tool
        tool_func = next((t for t in get_all_orchestrator_tools() if t.name == tool_name), None)
        if not tool_func:
            error_msg = f"❌ Tool {tool_name} not found"
            await conversation_service.add_conversation_turn(ConversationTurnCreate(
                user_input=task, agent_output=error_msg, agent_list=['orchestrator'], tool_call_list=tool_calls_made
            ))
            return {"response": error_msg, "requires_follow_up": False}
        
        # Get routing decision
        routing_result = tool_func.invoke(tool_args)
        
        # Handle routing based on action type
        action = routing_result.get("action")
        
        if action == "direct_response":
            # Direct response from orchestrator
            final_response = routing_result["response"]
            
            # Release any existing agent lock for direct responses
            await db_utils.set_agent_lock_for_user(db, user_id, None)
            
            turn_data = ConversationTurnCreate(
                user_input=task,
                agent_output=final_response,
                agent_list=['orchestrator'],
                tool_call_list=tool_calls_made
            )
            await conversation_service.add_conversation_turn(turn_data)
            
            return {"response": final_response, "requires_follow_up": False}
        
        elif action == "single_worker_routing":
            # Route to single agent
            worker = routing_result["worker"]
            worker_task = routing_result["task"]
            
            result = await route_to_agent(worker, worker_task, db, user_id, conversation_history)
            
            # Set agent lock if the agent requires follow-up
            if result.get("requires_follow_up", False):
                await db_utils.set_agent_lock_for_user(db, user_id, worker)
                print(f"🔒 Locked user to agent: {worker} (requires follow-up)")
            else:
                # Release any existing lock if no follow-up needed
                await db_utils.set_agent_lock_for_user(db, user_id, None)
            
            # Log orchestrator decision + agent response with metadata
            turn_data = ConversationTurnCreate(
                user_input=task,
                agent_output=result["response"],
                agent_list=['orchestrator', worker],
                tool_call_list=tool_calls_made,
                metadata=result.get("metadata", {})  # Include agent metadata (e.g., plan stage)
            )
            await conversation_service.add_conversation_turn(turn_data)
            
            return result
        
        elif action == "multiple_worker_routing":
            # Route to multiple agents
            import json
            tasks = json.loads(routing_result["tasks"])
            
            responses = []
            agents_used = ['orchestrator']
            requires_follow_up = False
            last_agent_needing_followup = None
            combined_metadata = {}
            
            for task_info in tasks:
                worker = task_info["worker"]
                worker_task = task_info["task"]
                
                result = await route_to_agent(worker, worker_task, db, user_id, conversation_history)
                responses.append(f"**{worker.title()}**: {result['response']}")
                agents_used.append(worker)
                
                # Collect metadata from agents (especially plan stage info)
                if result.get("metadata"):
                    combined_metadata[f"{worker}_metadata"] = result["metadata"]
                
                if result.get("requires_follow_up", False):
                    requires_follow_up = True
                    last_agent_needing_followup = worker  # Track the last agent that needs follow-up
            
            # Set agent lock to the last agent that requires follow-up
            if requires_follow_up and last_agent_needing_followup:
                await db_utils.set_agent_lock_for_user(db, user_id, last_agent_needing_followup)
                print(f"🔒 Locked user to agent: {last_agent_needing_followup} (from multi-routing)")
            else:
                # Release any existing lock if no follow-up needed
                await db_utils.set_agent_lock_for_user(db, user_id, None)
            
            final_response = "\n\n".join(responses)
            
            turn_data = ConversationTurnCreate(
                user_input=task,
                agent_output=final_response,
                agent_list=agents_used,
                tool_call_list=tool_calls_made,
                metadata=combined_metadata  # Include all agent metadata
            )
            await conversation_service.add_conversation_turn(turn_data)
            
            return {"response": final_response, "requires_follow_up": requires_follow_up}
        
        else:
            error_msg = f"❌ Unknown routing action: {action}"
            await conversation_service.add_conversation_turn(ConversationTurnCreate(
                user_input=task, agent_output=error_msg, agent_list=['orchestrator'], tool_call_list=tool_calls_made
            ))
            return {"response": error_msg, "requires_follow_up": False}
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = f"❌ Orchestrator error: {str(e)}"
        
        # Try to log error turn
        try:
            conversation_service = ConversationService(db, user_id)
            await conversation_service.add_conversation_turn(ConversationTurnCreate(
                user_input=task, agent_output=error_msg, agent_list=['orchestrator'], tool_call_list=tool_calls_made
            ))
        except:
            pass
            
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