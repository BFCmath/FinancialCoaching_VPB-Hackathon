"""
Core Financial Services - Foundation Classes
===========================================

This module contains the core foundation services that other services depend on.
Extended with full functionality from the lab, including all calculation utilities,
database stats, export, initialization, and reset functions.
All db methods are async.
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import json
# Import database utilities and models
from backend.utils import general_utils
from backend.models import user_settings
from backend.models import jar as jar_model

class UserSettingsService:
    """Service for managing user financial settings."""
    
    @staticmethod
    async def get_user_total_income(db: AsyncIOMotorDatabase, user_id: str) -> float:
        """Get user's total income, defaulting to 5000.0 if not set."""
        user_settings_doc = await general_utils.get_user_settings(db, user_id)
        if user_settings_doc:
            return user_settings_doc.total_income
        return 5000.0
    
    @staticmethod
    async def update_user_total_income(db: AsyncIOMotorDatabase, user_id: str, new_income: float) -> user_settings.UserSettingsInDB:
        """Update user's total income."""
        settings_update = user_settings.UserSettingsUpdate(total_income=new_income)
        return await general_utils.create_or_update_user_settings(db, user_id, settings_update)

class CalculationService:
    """Service for financial calculations - full lab implementation."""
    
    @staticmethod
    def format_currency(amount: float) -> str:
        """Format amount as currency string."""
        return f"${amount:,.2f}"

    @staticmethod
    def format_percentage(percent: float) -> str:
        """Format percentage for display (0.15 -> 15.0%)."""
        return f"{percent * 100:.1f}%"

    @staticmethod
    def validate_percentage_range(percent: float) -> bool:
        """Validate percentage is within 0.0-1.0 range."""
        return 0.0 <= percent <= 1.0

    @staticmethod
    def validate_positive_amount(amount: float) -> bool:
        """Validate amount is positive."""
        return amount > 0
    
    @staticmethod
    async def calculate_percent_from_amount(db: AsyncIOMotorDatabase, user_id: str, amount: float) -> float:
        """Convert dollar amount to percentage of total income."""
        total_income = await UserSettingsService.get_user_total_income(db, user_id)
        return amount / total_income if total_income > 0 else 0.0
    
    @staticmethod
    async def calculate_amount_from_percent(db: AsyncIOMotorDatabase, user_id: str, percent: float) -> float:
        """Convert percentage to dollar amount based on total income."""
        total_income = await UserSettingsService.get_user_total_income(db, user_id)
        return percent * total_income
    
    @staticmethod
    async def calculate_jar_total_allocation(db: AsyncIOMotorDatabase, user_id: str) -> float:
        """Calculate total percentage allocation across all jars."""
        jars = await general_utils.get_all_jars_for_user(db, user_id)
        return sum(jar.percent for jar in jars)
    
    @staticmethod
    async def validate_jar_percentages(db: AsyncIOMotorDatabase, user_id: str) -> Tuple[bool, float]:
        """Validate that total jar allocation doesn't exceed 100%."""
        total = await CalculationService.calculate_jar_total_allocation(db, user_id)
        return total <= 1.0, total
    
    @staticmethod
    async def calculate_jar_spending_total(db: AsyncIOMotorDatabase, user_id: str, jar_name: str) -> float:
        """Calculate total spending for a specific jar."""
        transactions = await general_utils.get_transactions_by_jar_for_user(db, user_id, jar_name)
        return sum(t.amount for t in transactions)
    
    
    # --- END OF NEW FUNCTION ---