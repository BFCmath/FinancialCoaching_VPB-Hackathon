"""
Knowledge Base Agent Tools
==========================

3 core tools for the knowledge base agent:
1. search_online() - Search for financial knowledge using DuckDuckGo
2. get_application_information() - Get hardcoded app documentation  
3. respond() - Final answer tool (stops ReAct execution)
"""

from typing import Dict, Any
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun


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
def get_application_information(description: str = "") -> Dict[str, Any]:
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
    
    # Concise app documentation
    APP_INFO = {
        "app_overview": {
            "name": "VPBank Personal Finance Assistant",
            "description": "Smart personal finance app for budgeting, tracking spending, and achieving financial goals automatically.",
            "main_features": [
                "🏺 Smart Budget Jars",
                "🤖 Automatic Transaction Sorting", 
                "💡 Smart Budget Suggestions",
                "📊 Advanced Search",
                "💳 Subscription Tracker"
            ]
        },
        
        "jar_system": {
            "overview": "Virtual budget jars for spending categories",
            "how_it_works": "Create jars for categories (groceries, dining, etc.), set budgets, transactions auto-sort into jars",
            "example": "Set $400 for groceries, see remaining balance after each shopping trip"
        },
        
        "budget_suggestions": {
            "overview": "Personalized budget recommendations based on spending patterns",
            "what_it_does": "Analyzes spending and suggests realistic budgets for each category",
            "example": "If you spend $350 on groceries, suggests $380 budget with saving tips"
        },
        
        "auto_categorization": {
            "overview": "Automatically sorts transactions into budget categories",
            "how_it_works": "Looks at transaction descriptions and amounts to assign to correct jar",
            "examples": [
                "Starbucks → Dining jar",
                "Shell Gas → Transportation jar",
                "Netflix → Entertainment jar"
            ]
        },
        
        "transaction_search": {
            "overview": "Find transactions using natural language",
            "features": "Search by amount, date, category, description, supports Vietnamese",
            "examples": [
                "Show coffee purchases last month",
                "Grocery shopping over $100",
                "Vietnamese: 'ăn trưa dưới 20 đô'"
            ]
        },
        
        "subscription_tracking": {
            "overview": "Track recurring payments and subscriptions",
            "features": "List subscriptions, renewal alerts, total monthly cost",
            "examples": "Netflix, Spotify, gym memberships, phone bills"
        }
    }
    
    return {
        "data": {
            "complete_app_info": APP_INFO,
            "source": "app_documentation"
        },
        "description": description or "complete app information and features"
    }


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
    
    return {
        "data": {
            "final_answer": answer,
            "response_type": "complete",
            "source": "knowledge"
        },
        "description": description or "final response to user question"
    }


# Helper function for LangChain tool binding
def get_all_knowledge_tools():
    """Return all knowledge base tools for LLM binding."""
    return [
        search_online,
        get_application_information, 
        respond
    ]
