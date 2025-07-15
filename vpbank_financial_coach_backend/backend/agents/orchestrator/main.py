# backend/agents/orchestrator/main.py

from typing import Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
import traceback

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

# Import backend components
from backend.core.config import settings
from backend.models.conversation import ConversationTurnCreate
from backend.services.conversation_service import ConversationService
from .prompt import build_orchestrator_prompt
from .tools import get_all_orchestrator_tools, OrchestratorServiceContainer

MAX_MEMORY_TURNS = 10

class OrchestratorAgent:
    """A class-based orchestrator agent following the standard agent pattern."""

    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = user_id
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite-preview-06-17",
            temperature=0.1,
            google_api_key=settings.GOOGLE_API_KEY
        )
        self.conversation_service = ConversationService(self.db, self.user_id)

    async def _get_tools(self) -> List:
        history = await self.conversation_service.get_conversation_history(limit=MAX_MEMORY_TURNS)
        services = OrchestratorServiceContainer(self.db, self.user_id, history)
        return get_all_orchestrator_tools(services)

    async def process_request(self, task: str) -> Dict[str, Any]:
        """Processes the user's request by routing it to the correct tool."""
        try:
            tools = await self._get_tools()
            llm_with_tools = self.llm.bind_tools(tools)

            history = await self.conversation_service.get_conversation_history(limit=MAX_MEMORY_TURNS)
            locked_agent = await self.conversation_service.check_conversation_lock()

            # If locked to an agent, route directly
            if locked_agent:
                tool_to_call = next((t for t in tools if t.name == f"route_to_{locked_agent}"), None)
                if tool_to_call:
                    result = await tool_to_call.ainvoke({"task_description": task})
                    if not result.get("requires_follow_up", False):
                        await self.conversation_service.release_conversation_lock()
                    return result

            # Build prompt and invoke LLM
            prompt = build_orchestrator_prompt(task, history)
            messages = [SystemMessage(content=prompt), HumanMessage(content=task)]
            response = await llm_with_tools.ainvoke(messages)

            if not response.tool_calls:
                return {"response": "I'm not sure how to handle that. Could you rephrase your request?", "requires_follow_up": False}

            # Execute the chosen tool
            tool_call = response.tool_calls[0]
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            
            tool_func = next((t for t in tools if t.name == tool_name), None)
            if not tool_func:
                return {"response": f"Error: Could not find tool '{tool_name}'.", "requires_follow_up": False}
            
            result = await tool_func.ainvoke(tool_args)

            # Set lock if the tool's response indicates a follow-up is needed
            if result.get("requires_follow_up", False):
                # Infer agent name from tool name for locking
                if "route_to_" in tool_name:
                    agent_to_lock = tool_name.replace("route_to_", "")
                    await self.conversation_service.lock_conversation_to_agent(agent_to_lock)
            
            return result

        except Exception as e:
            traceback.print_exc()
            return {"response": f"An unexpected error occurred in the orchestrator: {str(e)}", "requires_follow_up": False}

async def process_task_async(task: str, user_id: str, db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """
    Main async entry point for orchestrator processing.
    """
    agent = OrchestratorAgent(db, user_id)
    result = await agent.process_request(task)

    # Log the full conversation turn
    conversation_service = ConversationService(db, user_id)
    turn_data = ConversationTurnCreate(
        user_input=task,
        agent_output=result.get("response", "No response generated."),
        agent_list=['orchestrator'], # Simplified logging
        tool_call_list=[], # Tool calls are now an implementation detail of the agent
        metadata=result.get("metadata", {})
    )
    await conversation_service.add_conversation_turn(turn_data)

    return result