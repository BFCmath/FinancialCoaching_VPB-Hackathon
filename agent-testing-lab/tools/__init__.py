"""
Tools package for the AI Financial Coach multi-agent system.
Contains all tool implementations for each specialized agent.
"""

from .jar_manager_tools import *
from .transaction_classifier_tools import *
from .fee_manager_tools import *
from .budget_advisor_tools import *
from .alerting_coach_tools import *
from .insight_generator_tools import *
from .knowledge_base_tools import *

__all__ = [
    # JarManager tools
    'get_all_jars',
    'add_jar', 
    'update_jar',
    'delete_jar',
    
    # TransactionClassifier tools
    'log_transaction',
    'get_transaction_history',
    'find_historical_categorization',
    
    # FeeManager tools
    'get_all_fees',
    'add_recurring_fee',
    'update_recurring_fee', 
    'delete_recurring_fee',
    
    # BudgetAdvisor tools
    'get_income',
    
    # AlertingCoach tools (inherits from others)
    
    # InsightGenerator tools (inherits from others)
    
    # KnowledgeBase tools
    'query_knowledge_base',
] 