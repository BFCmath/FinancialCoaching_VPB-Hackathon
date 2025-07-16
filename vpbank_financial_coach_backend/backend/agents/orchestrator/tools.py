# backend/agents/orchestrator/tools.py

import json
from langchain_core.tools import tool
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import json

# Import the main agent functions that we will be routing to
from backend.agents.classifier.interface import ClassifierInterface
from backend.agents.fee.interface import FeeManagerInterface
from backend.agents.jar.interface import JarManagerInterface
from backend.agents.knowledge.interface import KnowledgeInterface
from backend.agents.plan.interface import BudgetAdvisorInterface
from backend.agents.transaction_fetcher.interface import TransactionFetcherInterface
from backend.agents.base_worker import BaseWorkerInterface

class OrchestratorServiceContainer:
    """
    Request-scoped service container for the orchestrator agent.
    Provides direct access to other agent interfaces.
    """
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str, conversation_history: List):
        self.db = db
        self.user_id = user_id
        self.conversation_history = conversation_history

    # Helper method to call other agents with error handling
    async def _route_to_agent(self, agent_interface: BaseWorkerInterface, task: str) -> Dict[str, Any]:
        """
        Route to an agent with comprehensive error handling.
        
        Args:
            agent_interface: The agent interface to call
            task: The task description for the agent
            
        Returns:
            Standardized response dict with error handling
        """
        try:
            # Validate input
            if not task or not task.strip():
                return {
                    "response": "Error: Task description cannot be empty",
                    "agent_lock": None,
                    "tool_calls": [],
                    "error": True
                }
            
            # Call the agent
            result = await agent_interface.process_task(
                task=task.strip(),
                db=self.db,
                user_id=self.user_id,
                conversation_history=self.conversation_history
            )
            
            # Validate agent response format
            if not isinstance(result, dict) or "response" not in result:
                return {
                    "response": f"Error: Agent {agent_interface.agent_name} returned invalid response format",
                    "agent_lock": None,
                    "tool_calls": [],
                    "error": True
                }
            
            # Return the agent result as-is (it should already be in standardized format)
            return result
            
        except Exception as e:
            # Handle any agent call failures
            agent_name = getattr(agent_interface, 'agent_name', 'unknown agent')
            error_message = f"Agent {agent_name} failed: {str(e)}"
            
            return {
                "response": f"I encountered an error while processing your request with {agent_name}: {str(e)}",
                "agent_lock": None,
                "tool_calls": [],
                "error": True
            }

def get_all_orchestrator_tools(services: OrchestratorServiceContainer) -> List[tool]:
    """
    Create orchestrator tools with injected dependencies.
    The tools now directly call the other agents.
    """

    @tool
    def provide_direct_response(response_text: str) -> dict:
        """
        Provide a direct response to the user when no worker routing is needed.
        
        Use this when:
        - User greeting (hello, hi, etc.)
        - Simple questions that don't require specific worker expertise
        - General conversation that doesn't need advanced tool usage
        
        Args:
            response_text: The direct response to give to the user
            
        Returns:
            Direct response action
        """
        # This tool remains synchronous as it doesn't call async services.
        return {"response": response_text, "requires_follow_up": False}

    @tool
    async def route_to_transaction_classifier(task_description: str) -> dict:
        """
        Route to transaction classifier for logging one-time expenses into jars.
        
        Use this when user mentions spending money on something specific:
        - One-time purchases (meal, gas, groceries, shopping, etc.)
        - Any expense that needs to be classified and allocated to jars
        - "$X on Y" type messages
        
        Args:
            task_description: Clear description of the one-time expense to classify
            
        Returns:
            Single worker routing decision
        """
        return await services._route_to_agent(ClassifierInterface(), task_description)

    @tool
    async def route_to_jar_manager(task_description: str) -> dict:
        """
        Route to jar manager for jar CRUD operations (Create, Read, Update, Delete).
        
        Use this when user wants to manage their budget jars:
        - Create new jars ("add vacation jar", "create emergency fund")
        - Modify existing jars ("reduce Save jar to 2%", "increase vacation jar")
        - Delete or view jars
        - Any jar management operations (user may not explicitly mention "jar")
        
        Args:
            task_description: Clear description of the jar management operation
            
        Returns:
            Single worker routing decision
        """
        return await services._route_to_agent(JarManagerInterface(), task_description)

    @tool
    async def route_to_fee_manager(task_description: str) -> dict:
        """
        Route to fee manager for recurring expense management.
        
        Use this when user wants to manage recurring fees:
        - Add recurring fees ("$10 monthly Netflix", "$2 daily coffee", "weekly commute $15")
        - Modify or delete subscriptions/bills
        - List existing recurring fees
        
        Args:
            task_description: Clear description of the recurring fee operation
            
        Returns:
            Single worker routing decision
        """
        return await services._route_to_agent(FeeManagerInterface(), task_description)

    @tool
    async def route_to_budget_advisor(task_description: str) -> dict:
        """
        Route to budget advisor for financial planning and budgeting advice.
        
        Use this when user wants budget planning help:
        - Creating savings plans ("save money for my parents")
        - Budget optimization and financial advice
        - Strategic financial planning questions
        - "How can I..." budget-related questions
        
        Args:
            task_description: Clear description of the planning request
            
        Returns:
            Single worker routing decision
        """
        return await services._route_to_agent(BudgetAdvisorInterface(), task_description)

    @tool
    async def route_to_insight_generator(task_description: str) -> dict:
        """
        Route to insight generator for transaction queries.

        Use this when user wants see transaction history, a list of transactions.
        
        Args:
            task_description: Clear description of what transaction they want to see
            
        Returns:
            Single worker routing decision
        """
        return await services._route_to_agent(TransactionFetcherInterface(), task_description)

    @tool
    async def route_to_knowledge_base(task_description: str) -> dict:
        """
        Route to knowledge base for educational content and financial concepts.
        
        Use this when user wants to learn:
        - Financial concept explanations ("what is compound interest?")
        - App feature explanations
        - Educational content about budgeting, investing, etc.
        
        Args:
            task_description: Clear description of the knowledge request
            
        Returns:
            Single worker routing decision
        """
        return await services._route_to_agent(KnowledgeInterface(), task_description)

    @tool
    async def route_to_multiple_workers(tasks_json: str) -> dict:
        """
        Route to multiple workers when request has multiple distinct tasks.
        
        Use this when user request has multiple distinct tasks that need different workers:
        - "I spent $50 on groceries and want to create a vacation jar" (classifier + jar)
        - "Add Netflix subscription and check my spending patterns" (fee + fetcher)

        # worker available:
        + "classifier", "jar", "fee", "plan", "fetcher", "knowledge"
        
        Args:
            tasks_json: JSON string with format: '[{"worker": "worker_name", "task": "task_description"}]'
            
        Example:
            '[{"worker": "classifier", "task": "spent $50 on groceries"}, {"worker": "jar", "task": "create vacation jar"}]'
            
        Returns:
            Multiple worker routing decision
        """
        try:
            tasks = json.loads(tasks_json)
            responses = []
            final_agent_lock = None
            final_plan_stage = None
            all_tool_calls = []
            any_errors = False

            for task_info in tasks:
                worker_name = task_info["worker"]
                worker_task = task_info["task"]
                
                # Map worker name to its interface
                interface_map = {
                    "classifier": ClassifierInterface(),
                    "jar": JarManagerInterface(),
                    "fee": FeeManagerInterface(),
                    "plan": BudgetAdvisorInterface(),
                    "fetcher": TransactionFetcherInterface(),
                    "knowledge": KnowledgeInterface()
                }
                
                interface = interface_map.get(worker_name)
                if interface:
                    result = await services._route_to_agent(interface, worker_task)
                    responses.append(f"**{worker_name.replace('_', ' ').title()}**:\n{result.get('response', 'No response.')}")
                    
                    # Handle standardized response format
                    if result.get('agent_lock'):
                        final_agent_lock = result.get('agent_lock')  # Last agent with lock wins
                    if result.get('plan_stage'):
                        final_plan_stage = result.get('plan_stage')  # Last plan stage wins
                    if result.get('tool_calls'):
                        all_tool_calls.extend(result.get('tool_calls', []))
                    if result.get('error'):
                        any_errors = True
                else:
                    responses.append(f"**Error**: Unknown worker '{worker_name}'")
                    any_errors = True
            
            # Return standardized multi-agent response format
            return {
                "response": "\n\n".join(responses),
                "agent_lock": final_agent_lock,
                "plan_stage": final_plan_stage,
                "tool_calls": all_tool_calls,
                "error": any_errors
            }
            
        except json.JSONDecodeError as e:
            return {
                "response": f"Error: Invalid JSON format in tasks: {str(e)}",
                "agent_lock": None,
                "tool_calls": [],
                "error": True
            }
        except Exception as e:
            return {
                "response": f"Error processing multiple tasks: {str(e)}",
                "agent_lock": None,
                "tool_calls": [],
                "error": True
            }

    return [
        provide_direct_response,
        route_to_transaction_classifier,
        route_to_jar_manager,
        route_to_fee_manager,
        route_to_budget_advisor,
        route_to_insight_generator,
        route_to_knowledge_base,
        route_to_multiple_workers
    ]