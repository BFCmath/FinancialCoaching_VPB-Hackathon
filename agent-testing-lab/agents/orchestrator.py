"""
Orchestrator Agent - The central router and only user-facing agent.
Routes tasks to specialized worker agents based on user intent.
"""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from state import GraphState


# Agent routing tools - these are "tools" that just indicate which agent to route to
@tool
def route_to_jar_manager(task_description: str) -> str:
    """
    Route to JarManager for budget jar operations like creating, updating, or deleting jars.
    Use this when user wants to manage their budget jars.
    """
    return f"Routing to JarManager: {task_description}"


@tool  
def route_to_transaction_classifier(task_description: str) -> str:
    """
    Route to TransactionClassifier for logging transactions from natural language.
    Use this when user describes spending money on something.
    """
    return f"Routing to TransactionClassifier: {task_description}"


@tool
def route_to_fee_manager(task_description: str) -> str:
    """
    Route to FeeManager for setting up or managing recurring fees/subscriptions.
    Use this when user mentions recurring payments, subscriptions, or regular fees.
    """
    return f"Routing to FeeManager: {task_description}"


@tool
def route_to_budget_advisor(task_description: str) -> str:
    """
    Route to BudgetAdvisor for financial planning and goal-oriented advice.
    Use this when user asks for help with saving goals, financial planning, or spending analysis.
    """
    return f"Routing to BudgetAdvisor: {task_description}"


@tool
def route_to_knowledge_base(task_description: str) -> str:
    """
    Route to KnowledgeBase for general financial education questions.
    Use this when user asks about financial concepts, definitions, or general advice.
    """
    return f"Routing to KnowledgeBase: {task_description}"


# Orchestrator tools list
ORCHESTRATOR_TOOLS = [
    route_to_jar_manager,
    route_to_transaction_classifier, 
    route_to_fee_manager,
    route_to_budget_advisor,
    route_to_knowledge_base
]


def create_orchestrator_node(model_name: str = "gemini-pro"):
    """
    Creates the orchestrator node function for the graph.
    
    Args:
        model_name: Name of the Google AI model to use
    
    Returns:
        Function suitable for use as a LangGraph node
    """
    
    # Initialize the LLM with tool calling capability
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.1,
        convert_system_message_to_human=True
    )
    llm_with_tools = llm.bind_tools(ORCHESTRATOR_TOOLS)
    
    def orchestrator_node(state: GraphState) -> GraphState:
        """
        Orchestrator node function that analyzes user input and routes to appropriate agent.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated graph state with routing decision
        """
        
        # System prompt for the orchestrator
        system_prompt = """
You are the Orchestrator of an AI Financial Coach system. Your job is to analyze user requests 
and route them to the appropriate specialist agent using the routing tools available to you.

ROUTING GUIDELINES:
- Budget jar operations (create, update, delete jars) → route_to_jar_manager
- Transaction logging ("I spent $X on Y") → route_to_transaction_classifier  
- Recurring fees/subscriptions → route_to_fee_manager
- Financial planning, savings goals, spending analysis → route_to_budget_advisor
- General financial education questions → route_to_knowledge_base

Always use exactly one routing tool per user request. Include a brief description of the task 
when calling the routing tool.

If the user's intent is unclear, ask a clarifying question instead of routing.
"""
        
        # Get the latest human message
        messages = state["messages"]
        latest_message = messages[-1] if messages else None
        
        if not latest_message or not isinstance(latest_message, HumanMessage):
            # If no human message or returning from worker agent, provide final response
            if state.get("task_complete", False):
                # Task is complete, provide final user response
                return {
                    "messages": [AIMessage(content="Task completed successfully!")],
                    "next_agent": None,
                    "task_complete": False
                }
            else:
                return {
                    "messages": [AIMessage(content="Hello! I'm your AI Financial Coach. How can I help you manage your finances today?")],
                    "next_agent": None,
                    "task_complete": False
                }
        
        # Prepare messages for the LLM
        conversation_history = [SystemMessage(content=system_prompt)]
        conversation_history.extend(messages)
        
        # Get routing decision from LLM
        response = llm_with_tools.invoke(conversation_history)
        
        # Check if tools were called (routing decision made)
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_call = response.tool_calls[0]
            function_name = tool_call["name"]
            
            # Map function names to agent names
            agent_mapping = {
                "route_to_jar_manager": "jar_manager",
                "route_to_transaction_classifier": "transaction_classifier",
                "route_to_fee_manager": "fee_manager", 
                "route_to_budget_advisor": "budget_advisor",
                "route_to_knowledge_base": "knowledge_base"
            }
            
            next_agent = agent_mapping.get(function_name)
            
            return {
                "messages": [response],
                "next_agent": next_agent,
                "task_complete": False
            }
        else:
            # No routing decision - probably asking for clarification
            return {
                "messages": [response],
                "next_agent": None,
                "task_complete": False
            }
    
    return orchestrator_node 