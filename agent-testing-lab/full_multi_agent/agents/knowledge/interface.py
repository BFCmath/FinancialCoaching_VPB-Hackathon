"""
Knowledge Agent Interface for Orchestrator
==========================================

Clean interface for the orchestrator to call the knowledge agent.

Usage:
    from agents.knowledge.interface import KnowledgeAgent
    
    knowledge_agent = KnowledgeAgent()
    result = knowledge_agent.process(task="What is compound interest?")
"""

from .main import get_knowledge


class KnowledgeManagerInterface:
    """
    Knowledge Agent Interface
    
    Handles financial knowledge questions and app documentation using ReAct framework.
    Uses online search and built-in app documentation to provide comprehensive answers.
    """
    
    def __init__(self):
        """Initialize the knowledge agent."""
        self.agent_name = "Knowledge Agent"
        self.capabilities = [
            "Financial knowledge questions",
            "App documentation and features",
            "Online search for financial concepts",
            "ReAct reasoning framework",
            "Multi-step information gathering",
            "Comprehensive answer synthesis"
        ]
    
    def process(self, task: str) -> str:
        """
        Process knowledge request task.
        
        Args:
            task: User's knowledge question
                Examples: 
                - "What is compound interest?"
                - "How does the jar system work?"
                - "What budgeting features does the app have?"
                - "How do I track my subscriptions?"
                - "What is the difference between saving and investing?"
                
        Returns:
            Comprehensive answer using ReAct reasoning process
            
        Examples:
            >>> knowledge_agent = KnowledgeAgent()
            >>> knowledge_agent.process("What is compound interest?")
            "Compound interest is the interest calculated on the initial principal and also on the accumulated interest..."
            
            >>> knowledge_agent.process("How does the jar system work?")
            "The jar system helps you organize your budget by creating virtual containers for different spending categories..."
        """
        return get_knowledge(task)
    
    def get_status(self) -> dict:
        """Get agent status information."""
        return {
            "agent_name": self.agent_name,
            "status": "ready",
            "capabilities": self.capabilities,
            "description": "Provides financial knowledge and app documentation using ReAct reasoning framework"
        }
    
    def get_available_tools(self) -> list:
        """Get list of available tools."""
        return [
            "search_online - Search for financial knowledge using DuckDuckGo",
            "get_application_information - Get app documentation and features",
            "respond - Provide final comprehensive answer"
        ]
    
    def get_knowledge_domains(self) -> list:
        """Get list of knowledge domains this agent can help with."""
        return [
            "Financial concepts (compound interest, budgeting, investing)",
            "App features and functionality",
            "Budget jar system",
            "Transaction categorization",
            "Subscription tracking",
            "Financial planning basics",
            "Money management tips"
        ]


# Convenience function for direct usage
def process_knowledge_request(task: str) -> str:
    """
    Direct function interface for knowledge requests.
    
    Args:
        task: Knowledge request task
        
    Returns:
        Knowledge response
    """
    return get_knowledge(task)

def get_agent_interface() -> KnowledgeManagerInterface:
    """Factory function to get an instance of the agent interface."""
    return KnowledgeManagerInterface() 