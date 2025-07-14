"""
Transaction Services - Complete Implementation from Lab
======================================================

This module implements transaction services with full functionality from the lab
with database backend integration, including advanced querying capabilities.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta, date
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database utilities and models
from backend.utils import db_utils
from backend.models import transaction
from .core_services import UserSettingsService, CalculationService

# =============================================================================
# TRANSACTION SERVICE - FROM LAB
# =============================================================================

class TransactionService:
    """
    Transaction service ported from lab with database backend.
    """
    
    @staticmethod
    async def add_money_to_jar_with_confidence(db: AsyncIOMotorDatabase, user_id: str, 
                                             amount: float, jar_name: str, confidence: int) -> str:
        """Add transaction to jar with confidence level."""
        # Validate jar exists
        jar_obj = await db_utils.get_jar_by_name(db, user_id, jar_name.lower().replace(' ', '_'))
        if not jar_obj:
            return f"❌ Jar '{jar_name}' not found."
        
        # Create transaction
        new_transaction = transaction.TransactionInDB(
            id=str(datetime.utcnow().timestamp()),
            user_id=user_id,
            amount=amount,
            jar=jar_obj.name,
            description=f"Transaction added with {confidence}% confidence",
            date=datetime.now().strftime("%Y-%m-%d"),
            time=datetime.now().strftime("%H:%M"),
            source="manual_input"
        )
        
        # Save transaction
        await db_utils.create_transaction_in_db(db, user_id, new_transaction)
        
        # Update jar current amounts
        new_current_amount = jar_obj.current_amount + amount
        total_income = await UserSettingsService.get_user_total_income(db, user_id)
        new_current_percent = new_current_amount / total_income
        
        await db_utils.update_jar_in_db(db, user_id, jar_obj.name, {
            "current_amount": new_current_amount,
            "current_percent": new_current_percent
        })
        
        confidence_emoji = "✅" if confidence >= 90 else "⚠️" if confidence >= 70 else "❓"
        return f"{confidence_emoji} Added {CalculationService.format_currency(amount)} to '{jar_obj.name}' jar ({confidence}% confident). New balance: {CalculationService.format_currency(new_current_amount)}"
    
    @staticmethod
    def report_no_suitable_jar(description: str, suggestion: str) -> str:
        """Report when no suitable jar found."""
        return f"❌ No suitable jar found for: {description}\n💡 Suggestion: {suggestion}"
    
    @staticmethod
    def request_more_info(question: str) -> str:
        """Request more information from user."""
        return f"❓ {question}"

# =============================================================================
# TRANSACTION QUERY SERVICE - ADVANCED QUERYING FROM LAB
# =============================================================================

class TransactionQueryService:
    """
    Advanced transaction querying service from lab with full functionality.
    """
    
    @staticmethod
    async def get_jar_transactions(db: AsyncIOMotorDatabase, user_id: str, 
                                  jar_name: str = None, limit: int = 50, description: str = "") -> Dict[str, Any]:
        """Get transactions for specific jar."""
        if jar_name:
            jar_obj = await db_utils.get_jar_by_name(db, user_id, jar_name.lower().replace(' ', '_'))
            if not jar_obj:
                return {"data": [], "description": f"jar '{jar_name}' not found"}
            transactions = await db_utils.get_transactions_by_jar_for_user(db, user_id, jar_obj.name)
        else:
            transactions = await db_utils.get_all_transactions_for_user(db, user_id)
        
        # Convert to dict format expected by agents
        transaction_dicts = [
            {
                "amount": t.amount,
                "jar": t.jar,
                "description": t.description,
                "date": t.date,
                "time": t.time,
                "source": t.source
            }
            for t in transactions[:limit]
        ]
        
        auto_description = description or (
            f"{jar_name} transactions" if jar_name else "all transactions"
        )
        
        return {
            "data": transaction_dicts,
            "description": f"retrieved {len(transaction_dicts)} {auto_description}"
        }
    
    @staticmethod
    async def get_recent_transactions(db: AsyncIOMotorDatabase, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent transactions within specified days."""
        transactions = await db_utils.get_all_transactions_for_user(db, user_id)
        
        # Filter by date (simplified - assumes date format YYYY-MM-DD)
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        recent_transactions = [t for t in transactions if t.date >= cutoff_date]
        
        return [
            {
                "amount": t.amount,
                "jar": t.jar,
                "description": t.description,
                "date": t.date,
                "time": t.time,
                "source": t.source
            }
            for t in recent_transactions
        ]
    
    @staticmethod
    async def get_time_period_transactions(db: AsyncIOMotorDatabase, user_id: str,
                                         jar_name: str = None, start_date: str = "last_month", 
                                         end_date: str = None, limit: int = 50, description: str = "") -> Dict[str, Any]:
        """Get transactions within date range with flexible date parsing."""
        # Parse dates using flexible date parsing
        start_date_parsed = TransactionQueryService.parse_flexible_date(start_date)
        if end_date:
            end_date_parsed = TransactionQueryService.parse_flexible_date(end_date)
        else:
            end_date_parsed = datetime.now().date()
        
        # Get base transactions
        if jar_name:
            jar_obj = await db_utils.get_jar_by_name(db, user_id, jar_name.lower().replace(' ', '_'))
            if not jar_obj:
                return {"data": [], "description": f"jar '{jar_name}' not found"}
            transactions = await db_utils.get_transactions_by_jar_for_user(db, user_id, jar_obj.name)
        else:
            transactions = await db_utils.get_all_transactions_for_user(db, user_id)
        
        # Filter by date range
        filtered_transactions = []
        for t in transactions:
            try:
                t_date = datetime.strptime(t.date, "%Y-%m-%d").date()
                if start_date_parsed <= t_date <= end_date_parsed:
                    filtered_transactions.append(t)
            except ValueError:
                continue  # Skip invalid dates
        
        # Convert to dict and limit results
        transaction_dicts = [
            {
                "amount": t.amount,
                "jar": t.jar,
                "description": t.description,
                "date": t.date,
                "time": t.time,
                "source": t.source
            }
            for t in filtered_transactions[:limit]
        ]
        
        auto_description = description or (
            f"{jar_name} transactions from {start_date} to {end_date}" if jar_name 
            else f"all transactions from {start_date} to {end_date}"
        )
        
        return {
            "data": transaction_dicts,
            "description": f"retrieved {len(transaction_dicts)} {auto_description}"
        }
    
    @staticmethod
    async def get_amount_range_transactions(db: AsyncIOMotorDatabase, user_id: str,
                                          jar_name: str = None, min_amount: float = None, 
                                          max_amount: float = None, limit: int = 50, 
                                          description: str = "") -> Dict[str, Any]:
        """Get transactions within amount range."""
        # Get base transactions
        if jar_name:
            jar_obj = await db_utils.get_jar_by_name(db, user_id, jar_name.lower().replace(' ', '_'))
            if not jar_obj:
                return {"data": [], "description": f"jar '{jar_name}' not found"}
            transactions = await db_utils.get_transactions_by_jar_for_user(db, user_id, jar_obj.name)
        else:
            transactions = await db_utils.get_all_transactions_for_user(db, user_id)
        
        # Filter by amount range
        filtered_transactions = []
        for t in transactions:
            amount_match = True
            if min_amount is not None and t.amount < min_amount:
                amount_match = False
            if max_amount is not None and t.amount > max_amount:
                amount_match = False
            
            if amount_match:
                filtered_transactions.append(t)
        
        # Convert to dict and limit results
        transaction_dicts = [
            {
                "amount": t.amount,
                "jar": t.jar,
                "description": t.description,
                "date": t.date,
                "time": t.time,
                "source": t.source
            }
            for t in filtered_transactions[:limit]
        ]
        
        range_desc = f"${min_amount or 0:.2f} - ${max_amount or 'unlimited'}"
        auto_description = description or (
            f"{jar_name} transactions in range {range_desc}" if jar_name 
            else f"all transactions in range {range_desc}"
        )
        
        return {
            "data": transaction_dicts,
            "description": f"retrieved {len(transaction_dicts)} {auto_description}"
        }
    
    @staticmethod
    def parse_flexible_date(date_str: str) -> date:
        """Parse various date formats including relative dates."""
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
        
        # Try parsing as YYYY-MM-DD
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
        
        # Default to today
        return today
    
    @staticmethod
    def time_in_range(transaction_time: str, start_hour: int, end_hour: int) -> bool:
        """Check if transaction time falls within hour range."""
        try:
            hour = int(transaction_time.split(":")[0])
            
            if start_hour <= end_hour:  # Normal range (e.g., 9-17)
                return start_hour <= hour <= end_hour
            else:  # Overnight range (e.g., 22-6)
                return hour >= start_hour or hour <= end_hour
        except (ValueError, IndexError):
            return False
    
    @staticmethod
    async def get_complex_transaction(db: AsyncIOMotorDatabase, user_id: str,
                                    jar_name: str = None,
                                    start_date: str = None,
                                    end_date: str = None,
                                    min_amount: float = None,
                                    max_amount: float = None,
                                    start_hour: int = None,
                                    end_hour: int = None,
                                    source_type: str = None,
                                    limit: int = 50,
                                    description: str = "") -> Dict[str, Any]:
        """Complex multi-dimensional transaction filtering with Vietnamese support."""
        # Get all transactions
        all_transactions = await db_utils.get_all_transactions_for_user(db, user_id)
        
        filtered = []
        
        # Apply all filters step by step
        for transaction in all_transactions:
            # 1. Check jar filter
            if jar_name is not None:
                jar_obj = await db_utils.get_jar_by_name(db, user_id, jar_name.lower().replace(' ', '_'))
                if not jar_obj or transaction.jar != jar_obj.name:
                    continue
            
            # 2. Check date range filter
            if start_date is not None:
                parsed_start = TransactionQueryService.parse_flexible_date(start_date)
                parsed_end = TransactionQueryService.parse_flexible_date(end_date) if end_date else datetime.now().date()
                
                try:
                    t_date = datetime.strptime(transaction.date, "%Y-%m-%d").date()
                    if not (parsed_start <= t_date <= parsed_end):
                        continue
                except ValueError:
                    continue
            
            # 3. Check amount range filter
            amount = transaction.amount
            if min_amount is not None and amount < min_amount:
                continue
            if max_amount is not None and amount > max_amount:
                continue
            
            # 4. Check hour range filter
            if start_hour is not None and end_hour is not None:
                if not TransactionQueryService.time_in_range(transaction.time, start_hour, end_hour):
                    continue
            elif start_hour is not None:
                try:
                    hour = int(transaction.time.split(":")[0])
                    if hour < start_hour:
                        continue
                except (ValueError, IndexError):
                    continue
            elif end_hour is not None:
                try:
                    hour = int(transaction.time.split(":")[0])
                    if hour > end_hour:
                        continue
                except (ValueError, IndexError):
                    continue
            
            # 5. Check source filter
            if source_type is not None and transaction.source != source_type:
                continue
            
            # If we get here, transaction passed all filters
            filtered.append({
                "amount": transaction.amount,
                "jar": transaction.jar,
                "description": transaction.description,
                "date": transaction.date,
                "time": transaction.time,
                "source": transaction.source
            })
        
        # Sort by date (newest first) and limit
        filtered.sort(key=lambda t: t["date"], reverse=True)
        limited_filtered = filtered[:limit]
        
        # Generate comprehensive description
        if description.strip():
            final_description = description.strip()
        else:
            filter_parts = []
            
            if jar_name:
                filter_parts.append(f"{jar_name} transactions")
            else:
                filter_parts.append("all transactions")
            
            if start_date or end_date:
                if start_date and end_date:
                    filter_parts.append(f"from {start_date} to {end_date}")
                elif start_date:
                    filter_parts.append(f"from {start_date}")
                elif end_date:
                    filter_parts.append(f"until {end_date}")
            
            if min_amount is not None and max_amount is not None:
                filter_parts.append(f"between ${min_amount}-${max_amount}")
            elif min_amount is not None:
                filter_parts.append(f"over ${min_amount}")
            elif max_amount is not None:
                filter_parts.append(f"under ${max_amount}")
            
            if start_hour is not None and end_hour is not None:
                filter_parts.append(f"between {start_hour}:00-{end_hour}:00")
            elif start_hour is not None:
                filter_parts.append(f"after {start_hour}:00")
            elif end_hour is not None:
                filter_parts.append(f"before {end_hour}:00")
            
            if source_type:
                source_names = {
                    "vpbank_api": "bank data",
                    "manual_input": "manual entries",
                    "text_input": "voice input",
                    "image_input": "scanned receipts"
                }
                filter_parts.append(f"from {source_names.get(source_type, source_type)}")
            
            final_description = "Complex filtering: " + " ".join(filter_parts)
            
            if limit < len(filtered):
                final_description += f" (showing {limit} of {len(filtered)} matches)"
        
        return {
            "data": limited_filtered,
            "description": final_description
        }
