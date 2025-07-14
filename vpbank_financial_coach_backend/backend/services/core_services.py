"""
Core Financial Services - Foundation Classes
===========================================

This module contains the core foundation services that other services depend on.
Extended with full functionality from the lab.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta, date
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database utilities and models
from backend.utils import db_utils
from backend.models import user_settings

# =============================================================================
# FOUNDATION SERVICES - USER SETTINGS & CALCULATIONS
# =============================================================================

class UserSettingsService:
    """Service for managing user financial settings."""
    
    @staticmethod
    async def get_user_total_income(db: AsyncIOMotorDatabase, user_id: str) -> float:
        """Get user's total income, defaulting to 5000.0 if not set."""
        user_settings_doc = await db_utils.get_user_settings(db, user_id)
        if user_settings_doc:
            return user_settings_doc.total_income
        return 5000.0
    
    @staticmethod
    async def update_user_total_income(db: AsyncIOMotorDatabase, user_id: str, new_income: float) -> user_settings.UserSettingsInDB:
        """Update user's total income."""
        settings_update = user_settings.UserSettingsUpdate(total_income=new_income)
        return await db_utils.create_or_update_user_settings(db, user_id, settings_update)

class CalculationService:
    """Service for financial calculations - extended with lab functionality."""
    
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
    def calculate_percent_from_amount(amount: float, total_income: float) -> float:
        """Convert dollar amount to percentage of total income."""
        return db_utils.calculate_percent_from_amount(amount, total_income)
    
    @staticmethod
    def calculate_amount_from_percent(percent: float, total_income: float) -> float:
        """Convert percentage to dollar amount based on total income."""
        return db_utils.calculate_amount_from_percent(percent, total_income)
    
    @staticmethod
    async def calculate_jar_total_allocation(db: AsyncIOMotorDatabase, user_id: str) -> float:
        """Calculate total percentage allocation across all jars."""
        jars = await db_utils.get_all_jars_for_user(db, user_id)
        return sum(jar.percent for jar in jars)
    
    @staticmethod
    async def validate_jar_percentages(db: AsyncIOMotorDatabase, user_id: str) -> Tuple[bool, float]:
        """Validate that total jar allocation doesn't exceed 100%."""
        total = await CalculationService.calculate_jar_total_allocation(db, user_id)
        return total <= 1.0, total
