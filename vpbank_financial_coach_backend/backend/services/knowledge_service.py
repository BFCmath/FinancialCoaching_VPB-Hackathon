"""
Knowledge Service - Complete Implementation from Lab
=================================================

This module implements the complete knowledge service ported from the lab
with database backend, maintaining exact same interface and behavior.
"""

import json
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database utilities
from backend.utils import db_utils

# =============================================================================
# APPLICATION INFORMATION - FROM LAB
# =============================================================================

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

# =============================================================================
# KNOWLEDGE SERVICE - COMPLETE FROM LAB
# =============================================================================

class KnowledgeService:
    """
    Complete knowledge service from lab with database backend.
    Maintains exact same interface and behavior as the original.
    """
    
    @staticmethod
    async def get_application_information(db: AsyncIOMotorDatabase, user_id: str, 
                                        description: str = "") -> Dict[str, Any]:
        """Get app documentation - matches lab interface exactly."""
        
        # Parse APP_INFO JSON like in lab
        try:
            app_info = json.loads(APP_INFO)
        except json.JSONDecodeError:
            app_info = {"error": "Could not parse app information"}
        
        # Enhance with user context for database backend
        if db and user_id:
            # Get user's current financial summary
            try:
                jars = await db_utils.get_all_jars_for_user(db, user_id)
                recent_transactions = await db_utils.get_user_transactions(db, user_id, limit=5)
                fees = await db_utils.get_all_fees_for_user(db, user_id)
                plans = await db_utils.get_all_plans_for_user(db, user_id)
                
                # Add user context to app info
                app_info["user_context"] = {
                    "total_jars": len(jars),
                    "jar_names": [j.name for j in jars] if jars else [],
                    "recent_transactions_count": len(recent_transactions),
                    "active_fees": len([f for f in fees if f.is_active]),
                    "active_plans": len([p for p in plans if p.status == "active"])
                }
            except Exception:
                # If database access fails, continue with basic app info
                pass
        
        return {
            "data": {
                "complete_app_info": app_info,
                "source": "app_documentation"
            },
            "description": description or "complete app information and features"
        }
    
    @staticmethod
    def respond(answer: str, description: str = "") -> Dict[str, Any]:
        """Provide final response (for ReAct completion) - matches lab interface exactly."""
        
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
        """Search help and documentation based on query."""
        
        query_lower = query.lower()
        
        # Get app info
        app_result = await KnowledgeService.get_application_information(db, user_id)
        app_info = app_result["data"]["complete_app_info"]
        
        help_sections = []
        
        # Search through app features
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

# =============================================================================
# CONFIDENCE SERVICE - FROM LAB
# =============================================================================

class ConfidenceService:
    """
    Confidence handling service used across multiple agents - from lab.
    """
    
    @staticmethod
    def format_confidence_response(result: str, confidence: int) -> str:
        """Format response based on confidence level - matches lab exactly."""
        
        if confidence >= 90:
            return f"✅ {result} ({confidence}% confident)"
        elif confidence >= 70:
            return f"⚠️ {result} ({confidence}% confident - moderate certainty)"
        else:
            return f"❓ {result} ({confidence}% confident - please verify)"
    
    @staticmethod
    def request_clarification(question: str, suggestions: Optional[str] = None) -> str:
        """Request clarification from user - matches lab exactly."""
        
        base_msg = f"❓ {question}"
        if suggestions:
            base_msg += f" {suggestions}"
        
        return base_msg
    
    @staticmethod
    def determine_confidence_level(confidence_score: int) -> str:
        """Convert confidence score to level description - matches lab exactly."""
        
        if confidence_score >= 90:
            return "high"
        elif confidence_score >= 70:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def should_ask_for_confirmation(confidence: int) -> bool:
        """Determine if confirmation is needed based on confidence - matches lab exactly."""
        
        return confidence < 70

# =============================================================================
# AGENT COMMUNICATION SERVICE - FROM LAB
# =============================================================================

class AgentCommunicationService:
    """
    Cross-agent communication service for plan_test integration - from lab.
    """
    
    @staticmethod
    async def call_transaction_fetcher(db: AsyncIOMotorDatabase, user_id: str, 
                                     user_query: str, description: str = "") -> Dict[str, Any]:
        """Call transaction fetcher service - database-backed version."""
        
        # Import here to avoid circular imports
        from .transaction_service import TransactionQueryService
        
        # Use our TransactionQueryService to handle the query
        try:
            result = await TransactionQueryService.search_transactions_natural_language(
                db, user_id, user_query, limit=50
            )
            
            return {
                "data": {"query_result": result},
                "description": description or f"transaction query: {user_query}"
            }
        except Exception as e:
            return {
                "data": {"error": str(e)},
                "description": f"error processing query: {user_query}"
            }
        
        return {
            "status": "success",
            "data": app_info,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def get_help_information(query: str = "") -> Dict[str, Any]:
        """Get help information based on user query."""
        
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
        
        # If specific query provided, try to match relevant category
        relevant_category = None
        if query:
            query_lower = query.lower()
            for category, info in help_categories.items():
                if category in query_lower or any(keyword in query_lower for keyword in 
                    ["jar", "transaction", "fee", "plan", "budget", "expense", "subscription"]):
                    relevant_category = category
                    break
        
        return {
            "status": "success",
            "query": query,
            "relevant_category": relevant_category,
            "help_categories": help_categories,
            "general_help": "I can help you manage your finances using the 6-jar budgeting system. Ask me about jars, transactions, fees, or planning!"
        }
    
    @staticmethod
    def respond(answer: str, description: str = "") -> Dict[str, Any]:
        """Generate a response for user queries."""
        return {
            "status": "success",
            "response": answer,
            "context": description if description else "General response",
            "timestamp": datetime.utcnow().isoformat()
        }
