"""
Main graph definition for the AI Financial Coach multi-agent system.
Defines the workflow, routing logic, and agent coordination.
"""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from state import GraphState
from agents import create_orchestrator_node, create_worker_node
from agents.workers import AGENT_PROMPTS
from tools import *


def create_routing_function():
    """
    Creates the routing function that determines which agent to execute next.
    
    Returns:
        Function that takes graph state and returns next node name
    """
    def route_to_agent(state: GraphState) -> str:
        """
        Routing logic based on orchestrator's decision.
        
        Args:
            state: Current graph state
            
        Returns:
            Name of the next node to execute
        """
        next_agent = state.get("next_agent")
        
        if next_agent:
            return next_agent
        elif state.get("task_complete", False):
            return "orchestrator"
        else:
            return END
    
    return route_to_agent


def create_financial_coach_graph():
    """
    Creates and compiles the complete financial coach graph.
    
    Returns:
        Compiled LangGraph ready for execution
    """
    
    # Define agent tool mappings
    agent_tools = {
        "jar_manager": [get_all_jars, add_jar, update_jar, delete_jar],
        "transaction_classifier": [log_transaction, get_transaction_history, get_all_jars, find_historical_categorization],
        "fee_manager": [get_all_fees, add_recurring_fee, update_recurring_fee, delete_recurring_fee, get_all_jars],
        "budget_advisor": [get_income, get_all_jars, get_transaction_history, get_all_fees],
        "knowledge_base": [query_knowledge_base]
    }
    
    # Create the graph
    workflow = StateGraph(GraphState)
    
    # Add the orchestrator node
    orchestrator = create_orchestrator_node()
    workflow.add_node("orchestrator", orchestrator)
    
    # Add worker agent nodes
    for agent_name, tools in agent_tools.items():
        worker_node = create_worker_node(
            agent_name=agent_name,
            system_prompt=AGENT_PROMPTS[agent_name],
            tools=tools
        )
        workflow.add_node(agent_name, worker_node)
    
    # Add tool execution node for all tools
    all_tools = []
    for tools in agent_tools.values():
        all_tools.extend(tools)
    
    tool_node = ToolNode(all_tools)
    workflow.add_node("tools", tool_node)
    
    # Set entry point
    workflow.set_entry_point("orchestrator")
    
    # Add routing edges from orchestrator to worker agents
    routing_function = create_routing_function()
    workflow.add_conditional_edges(
        "orchestrator",
        routing_function,
        {
            "jar_manager": "jar_manager",
            "transaction_classifier": "transaction_classifier", 
            "fee_manager": "fee_manager",
            "budget_advisor": "budget_advisor",
            "knowledge_base": "knowledge_base",
            END: END
        }
    )
    
    # Add edges from worker agents back to orchestrator
    for agent_name in agent_tools.keys():
        workflow.add_edge(agent_name, "orchestrator")
    
    # Compile the graph
    app = workflow.compile()
    
    return app


def create_simple_routing_graph():
    """
    Creates a simplified version for testing routing logic.
    
    Returns:
        Compiled LangGraph with basic routing
    """
    
    # Create a simpler graph for testing
    workflow = StateGraph(GraphState)
    
    # Add just the orchestrator and one worker for testing
    orchestrator = create_orchestrator_node()
    workflow.add_node("orchestrator", orchestrator)
    
    # Add a simple jar manager for testing
    jar_manager = create_worker_node(
        agent_name="jar_manager",
        system_prompt=AGENT_PROMPTS["jar_manager"],
        tools=[get_all_jars, add_jar, update_jar, delete_jar]
    )
    workflow.add_node("jar_manager", jar_manager)
    
    # Add transaction classifier for testing
    transaction_classifier = create_worker_node(
        agent_name="transaction_classifier", 
        system_prompt=AGENT_PROMPTS["transaction_classifier"],
        tools=[log_transaction, get_transaction_history, get_all_jars, find_historical_categorization]
    )
    workflow.add_node("transaction_classifier", transaction_classifier)
    
    # Add knowledge base for testing
    knowledge_base = create_worker_node(
        agent_name="knowledge_base",
        system_prompt=AGENT_PROMPTS["knowledge_base"],
        tools=[query_knowledge_base]
    )
    workflow.add_node("knowledge_base", knowledge_base)
    
    # Set entry point
    workflow.set_entry_point("orchestrator")
    
    # Add conditional routing
    def simple_route(state: GraphState) -> str:
        next_agent = state.get("next_agent")
        if next_agent in ["jar_manager", "transaction_classifier", "knowledge_base"]:
            return next_agent
        elif state.get("task_complete", False):
            return "orchestrator"
        else:
            return END
    
    workflow.add_conditional_edges(
        "orchestrator",
        simple_route,
        {
            "jar_manager": "jar_manager",
            "transaction_classifier": "transaction_classifier",
            "knowledge_base": "knowledge_base", 
            END: END
        }
    )
    
    # Add edges back to orchestrator
    workflow.add_edge("jar_manager", "orchestrator")
    workflow.add_edge("transaction_classifier", "orchestrator")
    workflow.add_edge("knowledge_base", "orchestrator")
    
    # Compile the graph
    app = workflow.compile()
    
    return app


if __name__ == "__main__":
    # Test graph creation
    print("Creating financial coach graph...")
    graph = create_simple_routing_graph()
    print("Graph created successfully!")
    
    # Test with a simple input
    initial_state = {
        "messages": [],
        "next_agent": None,
        "user_id": "test_user",
        "task_complete": False,
        "agent_data": {}
    }
    
    print("Testing graph initialization...")
    result = graph.invoke(initial_state)
    print("Graph test completed!")
    print(f"Final messages: {[msg.content for msg in result['messages']]}") 