# backend/agents/orchestrator/main.py

from typing import Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
import traceback

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

# Import backend components
from backend.core.config import settings
from backend.models.conversation import ConversationTurnInDB
from backend.services.conversation_service import ConversationService
from .prompt import build_orchestrator_prompt
from .tools import get_all_orchestrator_tools, OrchestratorServiceContainer

MAX_MEMORY_TURNS = settings.MAX_MEMORY_TURNS

class OrchestratorAgent:
    """A class-based orchestrator agent following the standard agent pattern."""

    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = user_id
        self.llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            temperature=settings.LLM_TEMPERATURE,
            google_api_key=settings.ORCHESTRATOR_GOOGLE_API_KEY
        )

    async def _get_tools(self, history: List[ConversationTurnInDB]) -> List:
        services = OrchestratorServiceContainer(self.db, self.user_id, history)
        return get_all_orchestrator_tools(services)

    async def process_request(self, task: str) -> Dict[str, Any]:
        """Processes the user's request by routing it to the correct tool."""
        try:
            # Validate input
            if not task or not task.strip():
                raise ValueError("Task cannot be empty")
            print("PASS 1")
            history = await ConversationService.get_conversation_history(self.db, self.user_id, limit=MAX_MEMORY_TURNS)
            print("PASS 2")      
            locked_agent = await ConversationService.get_agent_lock(self.db, self.user_id)
            tools = await self._get_tools(history)
            llm_with_tools = self.llm.bind_tools(tools)

            # If locked to an agent, route directly to that agent
            if locked_agent:
                # Map agent names to tool names
                agent_tool_mapping = {
                    "classifier": "route_to_transaction_classifier",
                    "jar": "route_to_jar_manager", 
                    "fee": "route_to_fee_manager",
                    "plan": "route_to_budget_advisor",
                    "fetcher": "route_to_insight_generator",
                    "knowledge": "route_to_knowledge_base"
                }
                
                tool_name = agent_tool_mapping.get(locked_agent)
                if tool_name:
                    tool_to_call = next((t for t in tools if t.name == tool_name), None)
                    if tool_to_call:
                        try:
                            result = await tool_to_call.ainvoke({"task_description": task})
                            return result
                        except Exception as e:
                            # Tool execution failed, return error but keep trying with LLM routing
                            print(f"Direct routing to {locked_agent} failed: {e}")
            print("PASS 3")
            # Build prompt and invoke LLM for routing decision
            prompt = build_orchestrator_prompt(task, history)
            messages = [SystemMessage(content=prompt), HumanMessage(content=task)]
            response = await llm_with_tools.ainvoke(messages)
            if settings.VERBOSE_LOGGING:
                print(f"📝 Orchestrator response: {response}")
            if not response.tool_calls:
                return {"response": "I'm not sure how to handle that. Could you rephrase your request?", "requires_follow_up": False}
            print("PASS 4")
            # Execute the chosen tool
            tool_call = response.tool_calls[0]
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            print("PASS 5")
            tool_func = next((t for t in tools if t.name == tool_name), None)
            if not tool_func:
                return {"response": f"Error: Could not find tool '{tool_name}'.", "requires_follow_up": False}
            
            try:
                result = await tool_func.ainvoke(tool_args)
                return result
            except Exception as e:
                # Handle tool execution errors gracefully
                return {"response": f"I encountered an error while processing your request: {str(e)}", "requires_follow_up": False}

        except ValueError as e:
            # Handle validation errors
            return {"response": f"Invalid request: {str(e)}", "requires_follow_up": False}
        except Exception as e:
            traceback.print_exc()
            return {"response": f"An unexpected error occurred: {str(e)}", "requires_follow_up": False}

async def process_task_async(task: str, user_id: str, db: AsyncIOMotorDatabase) -> ConversationTurnInDB:
    """
    Main async entry point for orchestrator processing.
    Returns ConversationTurnInDB for the orchestrator service.
    """
    try:
        # Validate required parameters
        if not task or not task.strip():
            raise ValueError("Task cannot be empty")
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty") 
        if db is None:
            raise ValueError("Database connection cannot be None")
        # Process the request
        agent = OrchestratorAgent(db, user_id)
        result = await agent.process_request(task.strip())

        # Extract standardized fields from agent response
        agent_output = result.get("response", "No response generated.")
        agent_lock = result.get("agent_lock")  # From standardized agent return format
        plan_stage = result.get("plan_stage")  # From plan agent return format
        tool_calls = result.get("tool_calls", [])
        agent_list = result.get("agent_list", ['orchestrator'])  # Default to orchestrator if not provided

        # Create and save conversation turn with proper agent lock and plan stage
        conversation_turn = await ConversationService.add_conversation_turn(
            db=db,
            user_id=user_id,
            user_input=task.strip(),
            agent_output=agent_output,
            agent_list=agent_list,
            tool_call_list=tool_calls,
            agent_lock=agent_lock,  # Set lock from agent response
            plan_stage=plan_stage   # Set plan stage from agent response
        )

        return conversation_turn
        
    except ValueError as e:
        # Handle validation errors - create error conversation turn
        error_response = f"Invalid request: {str(e)}"
        return await ConversationService.add_conversation_turn(
            db=db,
            user_id=user_id or "unknown",
            user_input=task or "invalid task",
            agent_output=error_response,
            agent_list=['orchestrator'],
            tool_call_list=[]
        )
        
    except Exception as e:
        # Handle unexpected errors - create error conversation turn  
        traceback.print_exc()
        error_response = f"An unexpected error occurred: {str(e)}"
        
        return await ConversationService.add_conversation_turn(
            db=db,
            user_id=user_id or "unknown", 
            user_input=task or "error task",
            agent_output=error_response,
            agent_list=['orchestrator'],
            tool_call_list=[]
        )