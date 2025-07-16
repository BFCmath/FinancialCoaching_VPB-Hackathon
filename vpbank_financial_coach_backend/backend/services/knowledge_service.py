"""
Knowledge Service - Complete Implementation from Lab
=================================================

Refactored knowledge service with async database operations and user context.
Maintained original interface while adding type hints, docstrings, and optimizations.
- Made all db-accessing methods async.
- Standardized response formats.
- Added error handling for db operations.
- Optimized context loading.
- Added get_help_information from lab communication service for completeness.
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database utilities
from backend.utils import general_utils

APP_INFO = """
{
  "app_overview": {
    "name": "VPBank Personal Finance Assistant",
    "description": "Smart personal finance app for budgeting, tracking spending, and achieving financial goals automatically.",
    "main_features": ["Smart Budget Jars", "Automatic Transaction Sorting", "Smart Budget Suggestions", "Advanced Search", "Subscription Tracker"]
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
    "examples": ["Starbucks → Dining jar", "Shell Gas → Transportation jar", "Netflix → Entertainment jar"]
  },
  "transaction_search": {
    "overview": "Find transactions using natural language",
    "features": "Search by amount, date, category, description, supports Vietnamese",
    "examples": ["Show coffee purchases last month", "Grocery shopping over $100", "Vietnamese: 'ăn trưa dưới 20 đô'"]
  },
  "subscription_tracking": {
    "overview": "Track recurring payments and subscriptions",
    "features": "List subscriptions, renewal alerts, total monthly cost",
    "examples": "Netflix, Spotify, gym memberships, phone bills"
  }
}
"""

class KnowledgeService:
    """
    Knowledge service providing app information and help documentation.
    Integrated with database for user-specific context.
    """
    
    @staticmethod
    async def get_application_information(db: AsyncIOMotorDatabase, user_id: str, 
                                           description: str = "") -> Dict[str, Any]:
        """
        Get app documentation with optional user context.
        
        Args:
            db: Database connection
            user_id: User identifier
            description: Optional description override
            
        Returns:
            Dict with app info and description
        """
        # Parse APP_INFO JSON
        try:
            app_info = json.loads(APP_INFO)
        except json.JSONDecodeError:
            app_info = {"error": "Could not parse app information"}
        
        # Add user context
        try:
            jars = await general_utils.get_all_jars_for_user(db, user_id)
            transactions = await general_utils.get_all_transactions_for_user(db, user_id)
            fees = await general_utils.get_all_fees_for_user(db, user_id)
            plans = await general_utils.get_all_plans_for_user(db, user_id)
            
            app_info["user_context"] = {
                "total_jars": len(jars),
                "jar_names": [j.name for j in jars],
                "transactions_count": len(transactions),
                "active_fees": len([f for f in fees if f.is_active]),
                "active_plans": len([p for p in plans if p.status == "active"])
            }
        except Exception as e:
            app_info["user_context"] = {"error": str(e)}
        
        return {
            "data": {
                "complete_app_info": app_info,
                "source": "app_documentation"
            },
            "description": description or "complete app information and features"
        }
    
    @staticmethod
    def respond(answer: str, description: str = "") -> Dict[str, Any]:
        """
        Provide final response for ReAct completion.
        
        Args:
            answer: The response text
            description: Optional description
            
        Returns:
            Formatted response dict
        """
        return {
            "data": {
                "final_answer": answer,
                "response_type": "complete",
                "source": "knowledge"
            },
            "description": description or "final response to user question"
        }
    
    @staticmethod
    async def search_help(db: AsyncIOMotorDatabase, user_id: str, query: str) -> str:
        """
        Search help documentation based on query with user context.
        
        Args:
            db: Database connection
            user_id: User identifier
            query: Search query
            
        Returns:
            Formatted help text
        """
        query_lower = query.lower()
        
        # Get app info with user context
        app_result = await KnowledgeService.get_application_information(db, user_id)
        app_info = app_result["data"]["complete_app_info"]
        
        help_sections = []
        
        # Match query to sections
        if any(word in query_lower for word in ["jar", "budget", "category"]):
            help_sections.append("🏺 JAR SYSTEM:")
            help_sections.append(f"   {app_info['jar_system']['overview']}")
            help_sections.append(f"   How it works: {app_info['jar_system']['how_it_works']}")
            help_sections.append(f"   Example: {app_info['jar_system']['example']}")
        
        if any(word in query_lower for word in ["transaction", "search", "find"]):
            help_sections.append("🔍 TRANSACTION SEARCH:")
            help_sections.append(f"   {app_info['transaction_search']['overview']}")
            help_sections.append(f"   Features: {app_info['transaction_search']['features']}")
            help_sections.append(f"   Examples: {', '.join(app_info['transaction_search']['examples'])}")
        
        if any(word in query_lower for word in ["subscription", "recurring", "fee"]):
            help_sections.append("🔄 SUBSCRIPTION TRACKING:")
            help_sections.append(f"   {app_info['subscription_tracking']['overview']}")
            help_sections.append(f"   Features: {app_info['subscription_tracking']['features']}")
            help_sections.append(f"   Examples: {app_info['subscription_tracking']['examples']}")
        
        if any(word in query_lower for word in ["suggestion", "recommend", "automatic"]):
            help_sections.append("🎯 SMART BUDGET SUGGESTIONS:")
            help_sections.append(f"   {app_info['budget_suggestions']['overview']}")
            help_sections.append(f"   What it does: {app_info['budget_suggestions']['what_it_does']}")
            help_sections.append(f"   Example: {app_info['budget_suggestions']['example']}")
        
        if not help_sections:
            # General help
            help_sections.append("📱 VPBANK PERSONAL FINANCE ASSISTANT")
            help_sections.append(f"   {app_info['app_overview']['description']}")
            help_sections.append(f"   Main features: {', '.join(app_info['app_overview']['main_features'])}")
        
        return "\n".join(help_sections)
    
    @staticmethod
    def get_help_information(query: str = "") -> Dict[str, Any]:
        """
        Get help information based on user query.
        
        Args:
            query: Optional query to filter help
            
        Returns:
            Help information dict
        """
        help_categories = {
            "jars": {
                "description": "Budget jar management using T. Harv Eker's 6-jar system",
                "commands": [
                    "Create new jars with percentage or dollar allocation",
                    "Update existing jar settings and descriptions", 
                    "Delete jars with automatic rebalancing",
                    "List all jars with current allocation status"
                ]
            },
            "transactions": {
                "description": "Smart expense tracking and categorization",
                "commands": [
                    "Classify expenses into appropriate jars",
                    "View transaction history by jar or date range",
                    "Search transactions by amount, time, or source",
                    "Get spending insights and patterns"
                ]
            },
            "fees": {
                "description": "Recurring subscription and bill management", 
                "commands": [
                    "Set up recurring fees with flexible schedules",
                    "Adjust or cancel existing subscriptions",
                    "Track upcoming due dates and amounts",
                    "Categorize fees into appropriate jars"
                ]
            },
            "planning": {
                "description": "Financial goal setting and budget planning",
                "commands": [
                    "Create budget plans with target amounts and dates",
                    "Track progress toward financial goals",
                    "Get recommendations for budget optimization",
                    "Analyze spending patterns and trends"
                ]
            }
        }
        
        relevant_category = None
        if query:
            query_lower = query.lower()
            for category in help_categories:
                if category in query_lower:
                    relevant_category = category
                    break
        
        return {
            "status": "success",
            "query": query,
            "relevant_category": relevant_category,
            "help_categories": help_categories,
            "general_help": "I can help you manage your finances using the 6-jar budgeting system. Ask me about jars, transactions, fees, or planning!"
        }