"""
Knowledge Agent Package
=======================

LLM-powered knowledge base agent with ReAct reasoning framework.

Main Components:
- KnowledgeAgent: Main agent interface for orchestrator
- get_knowledge: Core knowledge retrieval function  
- Tools: Service-integrated tools for online search and app documentation

Features:
- ReAct (Reason-Act) framework for multi-step reasoning
- DuckDuckGo online search for financial concepts
- Built-in app documentation and features
- Comprehensive answer synthesis

Usage:
    from agents.knowledge import KnowledgeAgent
    
    agent = KnowledgeAgent()
    result = agent.process("What is compound interest?")
"""

from .interface import KnowledgeAgent, knowledge_agent, process_knowledge_request
from .main import get_knowledge, process_task

__all__ = [
    "KnowledgeAgent",
    "knowledge_agent", 
    "get_knowledge",
    "process_knowledge_request",
    "process_task"
]

__version__ = "1.0.0"
__agent_name__ = "Knowledge Agent" 