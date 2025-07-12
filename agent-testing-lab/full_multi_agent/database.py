"""
Database Schema and Storage for VPBank AI Financial Coach
========================================================

Pure schema definitions and storage containers only.
All operations and utility functions are in utils.py.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
import json

# =============================================================================
# CONVERSATION LOCK SYSTEM (Active Agent Context)
# =============================================================================

# Global variable for conversation lock pattern
ACTIVE_AGENT_CONTEXT: Optional[str] = None  # None or agent_name ("budget_advisor", etc.)

def set_active_agent_context(agent_name: Optional[str] = None):
    """Set conversation lock for multi-turn conversations"""
    global ACTIVE_AGENT_CONTEXT
    ACTIVE_AGENT_CONTEXT = agent_name

def get_active_agent_context() -> Optional[str]:
    """Get current conversation lock agent"""
    return ACTIVE_AGENT_CONTEXT

# =============================================================================
# DATA STRUCTURES (Based on database.md)
# =============================================================================

@dataclass
class Jar:
    """
    JARS schema from database.md lines 1-8
    Budget jar for financial allocation management
    """
    name: str                    # Jar identifier (PRIMARY KEY)
    description: str             # Human description  
    percent: float              # Budget allocation (0.0-1.0)
    current_percent: float      # Current balance (0.0-1.0)
    current_amount: float       # Current amount in dollars
    amount: float               # Budget amount in dollars
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

@dataclass
class Transaction:
    """
    TRANSACTIONS schema from database.md lines 9-16
    Financial transaction record
    """
    amount: float               # Transaction amount (DECIMAL precision)
    jar: str                   # Reference to jar name (FOREIGN KEY)
    description: str           # Transaction description
    date: str                  # Date string (YYYY-MM-DD format)
    time: str                  # Time string (HH:MM format)
    source: str                # Transaction source (vpbank_api, manual_input, text_input, image_input)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

@dataclass
class RecurringFee:
    """
    FEES schema from database.md lines 17-26
    Recurring payment schedule definition
    """
    name: str                          # Fee identifier (PRIMARY KEY)
    amount: float                      # Fee amount (DECIMAL)
    description: str                   # Fee description
    target_jar: str                    # Reference to jar name (FOREIGN KEY)
    pattern_type: str                  # "daily", "weekly", "monthly" (ENUM)
    pattern_details: List[int]         # [1,3,5] for Mon/Wed/Fri (JSON/ARRAY)
    created_date: datetime             # Creation timestamp
    next_occurrence: datetime          # Next payment date (INDEXED)
    is_active: bool                    # Active status (BOOLEAN)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert datetime objects to ISO strings for JSON serialization
        result['created_date'] = self.created_date.isoformat()
        result['next_occurrence'] = self.next_occurrence.isoformat()
        return result

@dataclass
class BudgetPlan:
    """
    PLAN schema from database.md lines 27-33
    Financial planning document
    """
    name: str                          # Plan identifier (PRIMARY KEY)
    detail_description: str            # Plan description (TEXT)
    day_created: str                   # Creation date string
    status: str                        # "active", "completed", "paused" (ENUM)
    jar_recommendations: Optional[str] = None  # Optional jar proposals (TEXT/JSON)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

@dataclass
class ConversationTurn:
    """
    Conversation History schema from database.md lines 37-46
    Chat log entry with context tracking
    """
    user_input: str                    # User's input (TEXT)
    agent_output: str                  # Agent's response (TEXT)
    agent_list: List[str] = field(default_factory=list)      # Agents involved (JSON ARRAY)
    tool_call_list: List[str] = field(default_factory=list)  # Tools called (JSON ARRAY)
    timestamp: datetime = field(default_factory=datetime.now) # Conversation timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result

# =============================================================================
# MOCK DATABASE STORAGE CONTAINERS
# =============================================================================

# JARS storage - Dictionary keyed by jar name
# Production: PostgreSQL table with constraints
JARS_STORAGE: Dict[str, Jar] = {
    "necessities": Jar(
        name="necessities", 
        description="This is the foundation of your budget, covering essential living costs. Use it for non-negotiable expenses like rent/mortgage, utilities (electricity, water, internet), groceries, essential transportation, and insurance. Covers all your must-haves for daily life.", 
        percent=0.55, 
        current_percent=0.33, 
        current_amount=1650.0, 
        amount=2750.0
    ),
    "long_term_savings": Jar(
        name="long_term_savings", 
        description="Your safety net and goal-achiever. This jar is for saving for big-ticket items and preparing for the unexpected. Use it for your emergency fund, a down payment on a car or home, a dream vacation, or future family planning. For future goals and unexpected emergencies.", 
        percent=0.10, 
        current_percent=0.04, 
        current_amount=200.0, 
        amount=500.0
    ),
    "play": Jar(
        name="play", 
        description="This is your mandatory guilt-free fun money! You MUST spend this every month to pamper yourself and enjoy life. Use it for movies, dining out, hobbies, short trips, or buying something special just for you. The goal is to prevent burnout and make budgeting enjoyable.", 
        percent=0.10, 
        current_percent=0.06, 
        current_amount=300.0, 
        amount=500.0
    ),
    "education": Jar(
        name="education", 
        description="Invest in your greatest asset: you. This jar is for personal growth and learning new skills that can increase your knowledge and earning potential. Use it for books, online courses, seminars, workshops, or coaching. For books, courses, and self-development.", 
        percent=0.10, 
        current_percent=0.03, 
        current_amount=150.0, 
        amount=500.0
    ),
    "financial_freedom": Jar(
        name="financial_freedom", 
        description="Your golden goose. This money is for building wealth and generating passive income so you eventually don't have to work for money. Use it for stocks, bonds, mutual funds, or other income-generating assets. You never spend this money, you only invest it.", 
        percent=0.10, 
        current_percent=0.015, 
        current_amount=75.0, 
        amount=500.0
    ),
    "give": Jar(
        name="give", 
        description="Practice generosity and cultivate a mindset of abundance. Use this money to make a positive impact, whether through charity, donations, helping a friend in need, or buying an unexpected gift for a loved one. For charity and making a positive impact on others (5% of income).", 
        percent=0.05, 
        current_percent=0.005, 
        current_amount=25.0, 
        amount=250.0
    )
}
# TRANSACTIONS storage - List of all transactions
# Production: PostgreSQL + TimescaleDB for time-series optimization
TRANSACTIONS_STORAGE: List[Transaction] = []

# FEES storage - Dictionary keyed by fee name
# Production: PostgreSQL table with scheduling indexes
FEES_STORAGE: Dict[str, RecurringFee] = {}

# BUDGET PLANS storage - Dictionary keyed by plan name
# Production: PostgreSQL + MongoDB hybrid for flexible jar_recommendations
BUDGET_PLANS_STORAGE: Dict[str, BudgetPlan] = {}

# CONVERSATION HISTORY storage - List of conversation turns
# Production: MongoDB for flexible schema and high write volume
CONVERSATION_HISTORY: List[ConversationTurn] = []

# =============================================================================
# KNOWLEDGE BASE (Static Data)
# =============================================================================

# KNOWLEDGE BASE - Static app documentation (from database.md lines 34-36)
# Production: Elasticsearch for full-text search + Redis cache
APP_INFO: str = """
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
# CONFIGURATION CONSTANTS
# =============================================================================

# Financial calculation constants
TOTAL_INCOME: float = 5000.0         # Sample monthly income for percentage calculations

# System configuration
MAX_MEMORY_TURNS: int = 10           # Maximum conversation history to keep

# T. Harv Eker's official 6-jar percentages
DEFAULT_JAR_PERCENTAGES = {
    "necessities": 0.55,        # 55% - Essential expenses
    "long_term_savings": 0.10,  # 10% - Future financial security
    "play": 0.10,               # 10% - Entertainment and enjoyment
    "education": 0.10,          # 10% - Learning and skill development
    "financial_freedom": 0.10,  # 10% - Investment/passive income
    "give": 0.05                # 5% - Charity and helping others
}

# Valid transaction sources (ENUM values for production)
TRANSACTION_SOURCES = [
    "vpbank_api",      # Bank API imported transactions
    "manual_input",    # Manually entered by user
    "text_input",      # Voice/text processed transactions
    "image_input"      # Receipt/image processed transactions
]

# Valid plan statuses (ENUM values for production)
PLAN_STATUSES = [
    "active",          # Currently active plan
    "completed",       # Successfully completed plan
    "paused"           # Temporarily paused plan
]

# Valid fee pattern types (ENUM values for production)
FEE_PATTERN_TYPES = [
    "daily",           # Every day
    "weekly",          # Weekly schedule with specific days
    "monthly"          # Monthly schedule with specific dates
]

# =============================================================================
# SCHEMA VALIDATION CONSTANTS (DO NOT USE IN DEV LAB)
# =============================================================================

# # Validation constraints for production database
# CONSTRAINTS = {
#     "jar_name_max_length": 100,
#     "jar_description_max_length": 500,
#     "percent_min": 0.0,
#     "percent_max": 1.0,
#     "amount_min": 0.01,
#     "transaction_description_max_length": 1000,
#     "fee_name_max_length": 200,
#     "plan_name_max_length": 200,
#     "plan_description_max_length": 5000
# }

# # Database indexes for production (PostgreSQL)
# RECOMMENDED_INDEXES = {
#     "jars": ["name (PRIMARY KEY)", "percent"],
#     "transactions": ["(date, jar)", "(amount, date)", "(source, date)", "jar (FOREIGN KEY)"],
#     "fees": ["name (PRIMARY KEY)", "next_occurrence", "(is_active, next_occurrence)", "target_jar (FOREIGN KEY)"],
#     "plans": ["name (PRIMARY KEY)", "status", "day_created"],
#     "conversation_history": ["(session_id, timestamp)", "timestamp"]
# }

# # =============================================================================
# # TYPE DEFINITIONS FOR PRODUCTION
# # =============================================================================

# # SQL DDL for production PostgreSQL schema
# SQL_SCHEMA = """
# -- Jars table with constraints
# CREATE TABLE jars (
#     name VARCHAR(100) PRIMARY KEY,
#     description TEXT NOT NULL,
#     percent DECIMAL(5,4) NOT NULL CHECK (percent >= 0.0 AND percent <= 1.0),
#     current_percent DECIMAL(5,4) NOT NULL CHECK (current_percent >= 0.0),
#     current_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
#     amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
#     created_at TIMESTAMP DEFAULT NOW(),
#     updated_at TIMESTAMP DEFAULT NOW()
# );

# -- Transactions table with foreign key
# CREATE TABLE transactions (
#     id SERIAL PRIMARY KEY,
#     amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
#     jar_name VARCHAR(100) NOT NULL REFERENCES jars(name) ON DELETE CASCADE,
#     description TEXT NOT NULL,
#     transaction_date DATE NOT NULL,
#     transaction_time TIME NOT NULL,
#     source VARCHAR(20) NOT NULL CHECK (source IN ('vpbank_api', 'manual_input', 'text_input', 'image_input')),
#     created_at TIMESTAMP DEFAULT NOW()
# );

# -- Recurring fees table
# CREATE TABLE recurring_fees (
#     name VARCHAR(200) PRIMARY KEY,
#     amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
#     description TEXT NOT NULL,
#     target_jar VARCHAR(100) NOT NULL REFERENCES jars(name) ON DELETE CASCADE,
#     pattern_type VARCHAR(20) NOT NULL CHECK (pattern_type IN ('daily', 'weekly', 'monthly')),
#     pattern_details JSONB,
#     created_date TIMESTAMP NOT NULL DEFAULT NOW(),
#     next_occurrence TIMESTAMP NOT NULL,
#     is_active BOOLEAN NOT NULL DEFAULT TRUE
# );

# -- Budget plans table
# CREATE TABLE budget_plans (
#     name VARCHAR(200) PRIMARY KEY,
#     detail_description TEXT NOT NULL,
#     day_created DATE NOT NULL DEFAULT CURRENT_DATE,
#     status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'completed', 'paused')),
#     jar_recommendations TEXT,
#     created_at TIMESTAMP DEFAULT NOW(),
#     updated_at TIMESTAMP DEFAULT NOW()
# );

# -- Active agent contexts for conversation lock
# CREATE TABLE active_agent_contexts (
#     session_id VARCHAR(255) PRIMARY KEY,
#     agent_name VARCHAR(100) NOT NULL,
#     created_at TIMESTAMP DEFAULT NOW(),
#     expires_at TIMESTAMP NOT NULL
# );
# """

# # MongoDB schema for conversation history
# MONGODB_SCHEMA = {
#     "conversation_history": {
#         "user_input": "string",
#         "agent_output": "string", 
#         "agent_list": ["string"],
#         "tool_call_list": ["string"],
#         "timestamp": "date",
#         "session_id": "string"
#     },
#     "indexes": [
#         {"session_id": 1, "timestamp": 1},
#         {"timestamp": 1},
#         {"agent_list": 1}
#     ]
# }

# # Elasticsearch mapping for knowledge base
# ELASTICSEARCH_MAPPING = {
#     "app_documentation": {
#         "properties": {
#             "section": {"type": "keyword"},
#             "title": {"type": "text", "analyzer": "standard"},
#             "content": {"type": "text", "analyzer": "standard"},
#             "keywords": {"type": "keyword"},
#             "examples": {"type": "text"},
#             "last_updated": {"type": "date"}
#         }
#     }
# }
