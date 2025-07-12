# agents/orchestrator/tool.py

import sys
import os
from typing import Dict, Any, List

# Add parent directories
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from langchain_core.tools import tool

# Import agent interfaces
from agents.classifier.interface import get_agent_interface as get_classifier
from agents.fee.interface import get_agent_interface as get_fee
from agents.jar.interface import get_agent_interface as get_jar
from agents.knowledge.interface import get_agent_interface as get_knowledge
from agents.plan.interface import get_agent_interface as get_plan
from agents.transaction_fetcher.interface import get_agent_interface as get_fetcher

from utils import get_conversation_history
from database import get_active_agent_context

# Tool registry for agent calls
AGENT_TOOLS = {
    "classifier": get_classifier(),
    "fee": get_fee(),
    "jar": get_jar(),
    "knowledge": get_knowledge(),
    "plan": get_plan(),
    "fetcher": get_fetcher()
}

AGENT_REGISTRY = {
    "classifier": get_classifier(),
    "fee": get_fee(),
    "jar": get_jar(),
    "knowledge": get_knowledge(),
    "plan": get_plan(),
    "fetcher": get_fetcher()
}

@tool
def call_classifier(task: str) -> Dict[str, Any]:
    """
    Calls the Transaction Classifier agent for categorizing transactions.
    Use for queries about classifying expenses into jars.
    """
    history = get_conversation_history()
    return AGENT_TOOLS["classifier"].process_task(task, history)

@tool
def call_fee(task: str) -> Dict[str, Any]:
    """
    Calls the Fee Manager agent for managing recurring fees/subscriptions.
    Use for creating, updating, deleting, or listing subscriptions/bills.
    """
    history = get_conversation_history()
    return AGENT_TOOLS["fee"].process_task(task, history)

@tool
def call_jar(task: str) -> Dict[str, Any]:
    """
    Calls the Jar Manager agent for CRUD on budget jars and rebalancing.
    Use for creating, updating, deleting, or listing jars.
    """
    history = get_conversation_history()
    return AGENT_TOOLS["jar"].process_task(task, history)

@tool
def call_knowledge(task: str) -> Dict[str, Any]:
    """
    Calls the Knowledge Base agent for financial concepts and app features.
    Use for general questions about finance or system functionality.
    """
    history = get_conversation_history()
    return AGENT_TOOLS["knowledge"].process_task(task, history)

@tool
def call_plan(task: str) -> Dict[str, Any]:
    """
    Calls the Budget Advisor agent for financial planning and goals.
    Use for creating/adjusting savings plans or budget advice.
    """
    history = get_conversation_history()
    return AGENT_TOOLS["plan"].process_task(task, history)

@tool
def call_fetcher(task: str) -> Dict[str, Any]:
    """
    Calls the Transaction Fetcher agent for retrieving transaction history.
    Use for querying past transactions with filters.
    """
    history = get_conversation_history()
    return AGENT_TOOLS["fetcher"].process_task(task, history)

def get_all_orchestrator_tools() -> List[tool]:
    """Returns all tools for the orchestrator LLM."""
    return [
        call_classifier,
        call_fee,
        call_jar,
        call_knowledge,
        call_plan,
        call_fetcher
    ]