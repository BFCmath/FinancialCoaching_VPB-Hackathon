"""
Knowledge Base Agent Tools - Enhanced Pattern 2
==============================================

3 core tools for the knowledge base agent:
1. search_online() - Search for financial knowledge using DuckDuckGo
2. get_application_information() - Get hardcoded app documentation  
3. respond() - Final answer tool (stops ReAct execution)

Enhanced Pattern 2 implementation with dependency injection for production-ready multi-user support.
"""

import sys
import os

# Add the parent directories to path to import from service layer
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import direct async services (no adapters)
from backend.services.knowledge_service import KnowledgeService


class KnowledgeServiceContainer:
    """
    Request-scoped service container for knowledge agent.
    Provides direct access to async services.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = user_id


def get_all_knowledge_tools(services: KnowledgeServiceContainer) -> List[tool]:
    """
    Create knowledge tools with injected service dependencies.
    
    Args:
        services: Service container with user context
        
    Returns:
        List of LangChain tools for knowledge operations
    """
    
    @tool
    def search_online(query: str, description: str = "") -> Dict[str, Any]:
        """
        Search online for financial knowledge and information using DuckDuckGo.
        
        Args:
            query: The search query for financial information
            description: What you're searching for
            
        Returns:
            Dict with search results
            
        Examples:
            search_online("compound interest definition")
            search_online("budgeting basics guide")
            search_online("investment strategies for beginners")
        """
        
        search_tool = DuckDuckGoSearchRun()
        
        # Enhance query with financial context for better results
        enhanced_query = f"{query} financial definition guide explanation"
        
        try:
            search_results = search_tool.run(enhanced_query)
            
            return {
                "data": {
                    "query": query,
                    "results": search_results,
                    "source": "online_search"
                },
                "description": description or f"online search for: {query}"
            }
            
        except Exception as e:
            return {
                "data": {
                    "query": query,
                    "results": f"Search error: {str(e)}. Please try a different search term.",
                    "source": "online_search"
                },
                "description": f"search error for: {query}"
            }

    @tool
    async def get_application_information(description: str = "") -> Dict[str, Any]:
        """
        Get complete information about the personal finance app and all its features.
        Returns all app documentation in one call.
        
        Args:
            description: What app information you need
            
        Returns:
            Dict with all app information
            
        Examples:
            get_application_information("need jar system info")
            get_application_information("want to know about budget features")
        """
        return await KnowledgeService.get_application_information(services.db, services.user_id, description)

    @tool  
    def respond(answer: str, description: str = "") -> Dict[str, Any]:
        """
        Provide the final response to the user's question.
        Call this tool when you have gathered enough information to answer the user's question.
        This stops the ReAct execution.
        
        Args:
            answer: The complete answer to the user's question
            description: Brief description of what you're responding about
            
        Returns:
            Dict with the final response
            
        Examples:
            respond("Compound interest is...")
            respond("The jar system works by...")
        """
        return KnowledgeService.respond(answer, description)

    # Return all tools for LLM binding
    return [
        search_online,
        get_application_information, 
        respond
    ]
