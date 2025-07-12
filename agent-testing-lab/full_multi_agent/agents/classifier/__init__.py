"""
Transaction Classifier Agent Package
====================================

LLM-powered transaction classifier that automatically categorizes expenses into budget jars.

Main Components:
- ClassifierAgent: Main agent interface for orchestrator
- classify_transaction: Core classification function  
- Tools: Service-integrated tools for transaction processing

Usage:
    from agents.classifier import ClassifierAgent
    
    agent = ClassifierAgent()
    result = agent.process("meal 20 dollar")
"""

from .interface import ClassifierAgent, classifier_agent, process_transaction_classification
from .main import process_task

__all__ = [
    "ClassifierAgent",
    "classifier_agent", 
    "process_transaction_classification",
    "process_task"
]

__version__ = "1.0.0"
__agent_name__ = "Transaction Classifier" 