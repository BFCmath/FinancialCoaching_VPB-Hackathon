"""
Transaction Services - Complete Implementation from Lab
=======================================================

This module implements the complete transaction services ported from the lab
with database backend, maintaining exact same interface and behavior.
Covers all transaction operations from lab utils.py and service.py:
- save_transaction, get_all_transactions, get_transactions_by_jar, get_transactions_by_date_range
- get_transactions_by_amount_range, get_transactions_by_source, calculate_jar_spending_total
- add_money_to_jar_with_confidence, report_no_suitable_jar, request_more_info
- All query methods including get_complex_transaction
All methods are async where appropriate.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database utilities and models
from backend.utils import db_utils
from backend.models.transaction import TransactionInDB, TransactionCreate
from backend.models.jar import JarUpdate
from .core_services import CalculationService, UserSettingsService
from .confidence_service import ConfidenceService

class TransactionService:
    """
    Transaction management and query service.
    Combines functionality from lab's classifier_test and transaction_fetcher.
    """
    
    @staticmethod
    async def save_transaction(db: AsyncIOMotorDatabase, user_id: str, transaction_data: TransactionCreate) -> TransactionInDB:
        """Save transaction to database."""
        is_valid, errors = await TransactionService.validate_transaction_data(db, user_id, transaction_data)
        if not is_valid:
            raise ValueError(f"Invalid transaction data: {', '.join(errors)}")
        
        return await db_utils.create_transaction_in_db(db, user_id, transaction_data)
    
    @staticmethod
    async def get_all_transactions(db: AsyncIOMotorDatabase, user_id: str) -> List[TransactionInDB]:
        """Get all transactions for user."""
        return await db_utils.get_all_transactions_for_user(db, user_id)
    
    @staticmethod
    async def get_transactions_by_jar(db: AsyncIOMotorDatabase, user_id: str, jar_name: str) -> List[TransactionInDB]:
        """Get transactions for specific jar."""
        jar = await db_utils.get_jar_by_name(db, user_id, jar_name.lower().replace(' ', '_'))
        if not jar:
            raise ValueError(f"Jar '{jar_name}' not found")
        return await db_utils.get_transactions_by_jar_for_user(db, user_id, jar.name)
    
    @staticmethod
    async def get_transactions_by_date_range(db: AsyncIOMotorDatabase, user_id: str, 
                                             start_date: str, end_date: Optional[str] = None) -> List[TransactionInDB]:
        """Get transactions within date range."""
        start_parsed = TransactionQueryService._parse_flexible_date(start_date)
        end_parsed = TransactionQueryService._parse_flexible_date(end_date) if end_date else datetime.now().date()
        return await db_utils.get_transactions_by_date_range_for_user(db, user_id, start_parsed, end_parsed)
    
    @staticmethod
    async def get_transactions_by_amount_range(db: AsyncIOMotorDatabase, user_id: str, 
                                               min_amount: Optional[float] = None, max_amount: Optional[float] = None) -> List[TransactionInDB]:
        """Get transactions within amount range."""
        return await db_utils.get_transactions_by_amount_range_for_user(db, user_id, min_amount, max_amount)

    @staticmethod
    async def get_transactions_by_source(db: AsyncIOMotorDatabase, user_id: str, source: str) -> List[TransactionInDB]:
        """Get transactions by source type."""
        return await db_utils.get_transactions_by_source_for_user(db, user_id, source)
    
    @staticmethod
    async def calculate_jar_spending_total(db: AsyncIOMotorDatabase, user_id: str, jar_name: str) -> float:
        """Calculate total spending for a specific jar."""
        transactions = await TransactionService.get_transactions_by_jar(db, user_id, jar_name)
        return sum(t.amount for t in transactions)
    
    @staticmethod
    async def add_money_to_jar_with_confidence(db: AsyncIOMotorDatabase, user_id: str,
                                               amount: float, jar_name: str, confidence: int) -> str:
        """Add money to jar with confidence-based formatting."""
        jar = await db_utils.get_jar_by_name(db, user_id, jar_name.lower().replace(' ', '_'))
        if not jar:
            return "❌ Error: Jar '{jar_name}' not found"
        
        transaction = TransactionCreate(
            amount=amount,
            jar=jar.name,
            description=f"Transaction classified to {jar.name}",
            date=datetime.now().strftime("%Y-%m-%d"),
            time=datetime.now().strftime("%H:%M"),
            source="manual_input"
        )
        
        await TransactionService.save_transaction(db, user_id, transaction)
        
        # Update jar current amount
        new_current_amount = jar.current_amount + amount
        new_current_percent = await CalculationService.calculate_percent_from_amount(db, user_id, new_current_amount)
        update_data = JarUpdate(current_amount=new_current_amount, current_percent=new_current_percent)
        await db_utils.update_jar_in_db(db, user_id, jar.name, update_data)
        
        result = f"Added {CalculationService.format_currency(amount)} to {jar.name} jar"
        return ConfidenceService.format_confidence_response(result, confidence)
    
    @staticmethod
    def report_no_suitable_jar(description: str, suggestion: str) -> str:
        """Report when no existing jar matches the transaction."""
        return f"❌ Cannot classify '{description}'. {suggestion}"
    
    @staticmethod
    def request_more_info(question: str) -> str:
        """Ask user for more information when input is ambiguous."""
        return f"❓ {question}"
    
    @staticmethod
    async def validate_transaction_data(db: AsyncIOMotorDatabase, user_id: str, transaction_data: TransactionCreate) -> Tuple[bool, List[str]]:
        """Validate transaction data."""
        errors = []
        
        if not CalculationService.validate_positive_amount(transaction_data.amount):
            errors.append(f"Amount {transaction_data.amount} must be positive")
        
        jar = await db_utils.get_jar_by_name(db, user_id, transaction_data.jar)
        if not jar:
            errors.append(f"Jar '{transaction_data.jar}' does not exist")
        
        if not transaction_data.description or not transaction_data.description.strip():
            errors.append("Description cannot be empty")
        
        # Validate date format
        try:
            datetime.strptime(transaction_data.date, "%Y-%m-%d")
        except ValueError:
            errors.append(f"Invalid date format: {transaction_data.date}")
        
        return len(errors) == 0, errors

class TransactionQueryService:
    """
    Advanced transaction querying service.
    """
    
    @staticmethod
    async def get_jar_transactions(db: AsyncIOMotorDatabase, user_id: str, jar_name: Optional[str] = None, 
                                   limit: int = 50, description: str = "") -> Dict[str, Any]:
        """Get transactions filtered by jar."""
        if jar_name:
            transactions = await TransactionService.get_transactions_by_jar(db, user_id, jar_name)
        else:
            transactions = await TransactionService.get_all_transactions(db, user_id)
        
        transaction_dicts = [t.dict() for t in transactions[:limit]]
        auto_desc = description or (f"{jar_name} transactions" if jar_name else "all transactions")
        return {"data": transaction_dicts, "description": f"retrieved {len(transaction_dicts)} {auto_desc}"}
    
    @staticmethod
    async def get_time_period_transactions(db: AsyncIOMotorDatabase, user_id: str, jar_name: Optional[str] = None, 
                                           start_date: str = "last_month", end_date: Optional[str] = None, 
                                           limit: int = 50, description: str = "") -> Dict[str, Any]:
        """Get transactions within date range."""
        if jar_name:
            transactions = await TransactionService.get_transactions_by_jar(db, user_id, jar_name)
        else:
            transactions = await TransactionService.get_all_transactions(db, user_id)
        
        start_parsed = TransactionQueryService._parse_flexible_date(start_date)
        end_parsed = TransactionQueryService._parse_flexible_date(end_date) if end_date else datetime.now().date()
        
        filtered = [t for t in transactions if start_parsed <= datetime.strptime(t.date, "%Y-%m-%d").date() <= end_parsed][:limit]
        transaction_dicts = [t.dict() for t in filtered]
        
        auto_desc = description or (f"{jar_name} transactions from {start_date} to {end_date or 'now'}" if jar_name else f"all transactions from {start_date} to {end_date or 'now'}")
        return {"data": transaction_dicts, "description": f"retrieved {len(transaction_dicts)} {auto_desc}"}
    
    @staticmethod
    async def get_amount_range_transactions(db: AsyncIOMotorDatabase, user_id: str, jar_name: Optional[str] = None, 
                                            min_amount: float = None, max_amount: float = None, limit: int = 50, 
                                            description: str = "") -> Dict[str, Any]:
        """Get transactions within amount range."""
        if jar_name:
            transactions = await TransactionService.get_transactions_by_jar(db, user_id, jar_name)
        else:
            transactions = await TransactionService.get_all_transactions(db, user_id)
        
        filtered = []
        for t in transactions:
            if (min_amount is None or t.amount >= min_amount) and (max_amount is None or t.amount <= max_amount):
                filtered.append(t)
        
        filtered = filtered[:limit]
        transaction_dicts = [t.dict() for t in filtered]
        
        range_desc = f"{CalculationService.format_currency(min_amount or 0)} - {CalculationService.format_currency(max_amount or 'unlimited')}"
        auto_desc = description or (f"{jar_name} transactions in range {range_desc}" if jar_name else f"all transactions in range {range_desc}")
        return {"data": transaction_dicts, "description": f"retrieved {len(transaction_dicts)} {auto_desc}"}
    
    @staticmethod
    async def get_hour_range_transactions(db: AsyncIOMotorDatabase, user_id: str, jar_name: Optional[str] = None, 
                                          start_hour: int = 6, end_hour: int = 22, limit: int = 50, 
                                          description: str = "") -> Dict[str, Any]:
        """Get transactions within hour range."""
        if jar_name:
            transactions = await TransactionService.get_transactions_by_jar(db, user_id, jar_name)
        else:
            transactions = await TransactionService.get_all_transactions(db, user_id)
        
        filtered = [t for t in transactions if TransactionQueryService._time_in_range(t.time, start_hour, end_hour)][:limit]
        transaction_dicts = [t.dict() for t in filtered]
        
        time_range = f"{start_hour:02d}:00 - {end_hour:02d}:00"
        auto_desc = description or (f"{jar_name} transactions between {time_range}" if jar_name else f"all transactions between {time_range}")
        return {"data": transaction_dicts, "description": f"retrieved {len(transaction_dicts)} {auto_desc}"}
    
    @staticmethod
    async def get_source_transactions(db: AsyncIOMotorDatabase, user_id: str, jar_name: Optional[str] = None, 
                                      source_type: str = "vpbank_api", limit: int = 50, 
                                      description: str = "") -> Dict[str, Any]:
        """Get transactions by source type."""
        if jar_name:
            transactions = await TransactionService.get_transactions_by_jar(db, user_id, jar_name)
        else:
            transactions = await TransactionService.get_all_transactions(db, user_id)
        
        filtered = [t for t in transactions if t.source == source_type][:limit]
        transaction_dicts = [t.dict() for t in filtered]
        
        auto_desc = description or (f"{jar_name} transactions from {source_type}" if jar_name else f"all transactions from {source_type}")
        return {"data": transaction_dicts, "description": f"retrieved {len(transaction_dicts)} {auto_desc}"}
    
    @staticmethod
    async def get_complex_transaction(db: AsyncIOMotorDatabase, user_id: str,
                                      jar_name: Optional[str] = None,
                                      start_date: Optional[str] = None,
                                      end_date: Optional[str] = None,
                                      min_amount: Optional[float] = None,
                                      max_amount: Optional[float] = None,
                                      start_hour: Optional[int] = None,
                                      end_hour: Optional[int] = None,
                                      source_type: Optional[str] = None,
                                      limit: int = 50,
                                      description: str = "") -> Dict[str, Any]:
        """Complex multi-dimensional transaction filtering."""
        transactions = await TransactionService.get_all_transactions(db, user_id)
        
        filtered = []
        start_parsed = TransactionQueryService._parse_flexible_date(start_date) if start_date else None
        end_parsed = TransactionQueryService._parse_flexible_date(end_date) if end_date else None
        
        for t in transactions:
            if jar_name and t.jar != jar_name:
                continue
            if start_parsed and datetime.strptime(t.date, "%Y-%m-%d").date() < start_parsed:
                continue
            if end_parsed and datetime.strptime(t.date, "%Y-%m-%d").date() > end_parsed:
                continue
            if min_amount is not None and t.amount < min_amount:
                continue
            if max_amount is not None and t.amount > max_amount:
                continue
            if start_hour is not None and end_hour is not None and not TransactionQueryService._time_in_range(t.time, start_hour, end_hour):
                continue
            if source_type and t.source != source_type:
                continue
            filtered.append(t)
        
        filtered.sort(key=lambda t: t.date, reverse=True)
        limited = filtered[:limit]
        transaction_dicts = [t.dict() for t in limited]
        
        # Generate description
        filter_parts = []
        if jar_name:
            filter_parts.append(jar_name)
        if start_date:
            filter_parts.append(f"from {start_date}")
        if end_date:
            filter_parts.append(f"to {end_date}")
        if min_amount is not None:
            filter_parts.append(f"min {min_amount}")
        if max_amount is not None:
            filter_parts.append(f"max {max_amount}")
        if start_hour is not None:
            filter_parts.append(f"start_hour {start_hour}")
        if end_hour is not None:
            filter_parts.append(f"end_hour {end_hour}")
        if source_type:
            filter_parts.append(source_type)
        
        final_desc = description or f"Filtered transactions: {', '.join(filter_parts)}" if filter_parts else "All transactions"
        return {"data": transaction_dicts, "description": final_desc}

    @staticmethod
    def _parse_flexible_date(date_str: Optional[str]) -> date:
        if not date_str:
            return datetime.now().date()
        
        date_str = date_str.lower().strip()
        today = datetime.now().date()
        
        relative_dates = {
            "today": today,
            "yesterday": today - timedelta(days=1),
            "last_week": today - timedelta(weeks=1),
            "last_month": today - timedelta(days=30),
            "this_month": today.replace(day=1),
            "last_year": today - timedelta(days=365),
            "this_week": today - timedelta(days=today.weekday())
        }
        
        if date_str in relative_dates:
            return relative_dates[date_str]
        
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return today
    
    @staticmethod
    def _time_in_range(time_str: str, start_hour: int, end_hour: int) -> bool:
        try:
            hour = int(time_str.split(":")[0])
            if start_hour <= end_hour:
                return start_hour <= hour <= end_hour
            else:
                return hour >= start_hour or hour <= end_hour
        except (ValueError, IndexError):
            return False