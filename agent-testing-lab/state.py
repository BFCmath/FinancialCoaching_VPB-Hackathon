"""
State management for the AI Financial Coach multi-agent system.
Defines the graph state structure used by LangGraph.
"""

from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
import operator


class GraphState(TypedDict):
    """
    State for the AI Financial Coach graph.
    
    This state is passed between all nodes in the graph and maintains
    the conversation history and routing information.
    """
    # Conversation history - fundamental to LangGraph
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Routing control
    next_agent: Optional[str]  # Which agent to route to next
    
    # Additional context for agent coordination
    user_id: str  # Mock user identifier
    task_complete: bool  # Whether the current task is finished
    
    # Agent-specific data sharing
    agent_data: dict  # For passing data between agents 