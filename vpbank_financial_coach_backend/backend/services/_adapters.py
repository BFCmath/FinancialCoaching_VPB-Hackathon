"""
Service Adapters - Lab Compatibility Layer
=========================================

Provides adapters that bridge lab sync interfaces with backend async services.
Removed globals; use factory functions to create adapters.
Adapters for Classifier, Fee, Jar services.
Uses concurrent.futures for sync calls to async methods.
"""

from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import asyncio
import concurrent.futures

# Import services
from .transaction_service import TransactionService
from .communication_service import AgentCommunicationService
from .fee_service import FeeManagementService
from .jar_service import JarManagementService
from .transaction_service import TransactionQueryService
from .knowledge_service import KnowledgeService
from .plan_service import PlanManagementService
from .service_responses import ServiceResult, JarOperationResult
class BaseAdapter:
    """
    Base class for sync/async bridging.
    """
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = user_id
    
    def _call_sync(self, async_method: callable, *args, **kwargs) -> Any:
        """Call async method from sync context."""
        def run_async():
            return asyncio.run(async_method(self.db, self.user_id, *args, **kwargs))
        
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(run_async).result()

class ClassifierAdapter(BaseAdapter):
    """
    Adapter for classifier tools.py interface.
    """
    def add_money_to_jar_with_confidence(self, amount: float, jar_name: str, confidence: int) -> str:
        return self._call_sync(TransactionService.add_money_to_jar_with_confidence, amount, jar_name, confidence)
    
    def report_no_suitable_jar(self, description: str, suggestion: str) -> str:
        return TransactionService.report_no_suitable_jar(description, suggestion)
    
    def call_transaction_fetcher(self, user_query: str, description: str = "") -> Dict[str, Any]:
        return self._call_sync(AgentCommunicationService.call_transaction_fetcher, user_query, description)

class FeeAdapter(BaseAdapter):
    """
    Adapter for fee tools.py interface.
    """
    def create_recurring_fee(self, name: str, amount: float, description: str, pattern_type: str,
                             pattern_details: Optional[List[int]], target_jar: str, 
                             confidence: int = 85) -> str:
        return self._call_sync(FeeManagementService.create_recurring_fee, name, amount, description, 
                               pattern_type, pattern_details, target_jar, confidence)
    
    def adjust_recurring_fee(self, fee_name: str, new_amount: Optional[float] = None,
                             new_description: Optional[str] = None, new_pattern_type: Optional[str] = None,
                             new_pattern_details: Optional[List[int]] = None, new_target_jar: Optional[str] = None,
                             disable: bool = False, confidence: int = 85) -> str:
        return self._call_sync(FeeManagementService.adjust_recurring_fee, fee_name, new_amount, new_description,
                               new_pattern_type, new_pattern_details, new_target_jar, disable, confidence)
    
    def delete_recurring_fee(self, fee_name: str, reason: str) -> str:
        return self._call_sync(FeeManagementService.delete_recurring_fee, fee_name, reason)
    
    def list_recurring_fees(self, active_only: bool = True, target_jar: Optional[str] = None) -> str:
        return self._call_sync(FeeManagementService.list_recurring_fees, active_only, target_jar)

class JarAdapter(BaseAdapter):
    """
    Adapter for jar tools.py interface.
    Converts new JarOperationResult responses back to string format for lab compatibility.
    """
    def create_jar(self, name: List[str], description: List[str], 
                   percent: Optional[List[float]] = None, amount: Optional[List[float]] = None,
                   confidence: int = 85) -> str:
        result = self._call_sync(JarManagementService.create_jar, name, description, percent, amount, confidence)
        return self._format_jar_result(result)
    
    def update_jar(self, jar_name: List[str], new_name: Optional[List[str]] = None,
                   new_description: Optional[List[str]] = None, new_percent: Optional[List[float]] = None,
                   new_amount: Optional[List[float]] = None, confidence: int = 85) -> str:
        result = self._call_sync(JarManagementService.update_jar, jar_name, new_name, new_description, 
                               new_percent, new_amount, confidence)
        return self._format_jar_result(result)
    
    def delete_jar(self, jar_name: List[str], reason: str) -> str:
        result = self._call_sync(JarManagementService.delete_jar, jar_name, reason)
        return self._format_jar_result(result)
    
    def list_jars(self) -> str:
        return self._call_sync(JarManagementService.list_jars)
    
    def _format_jar_result(self, result) -> str:
        """Convert JarOperationResult back to string format for lab compatibility."""
        if hasattr(result, 'is_error') and result.is_error():
            # Format error response with emoji for consistency
            error_message = result.get_error_message()
            return f"❌ {error_message}"
        elif hasattr(result, 'is_success') and result.is_success():
            # Format success response with emoji for consistency
            message = result.message
            # Add warnings if present
            if hasattr(result, 'warnings') and result.warnings:
                warning_text = "\n".join(result.warnings)
                message += f"\n{warning_text}"
            return f"✅ {message}"
        else:
            # Fallback for string responses (like list_jars)
            return str(result)

class TransactionFetcherAdapter(BaseAdapter):
    """
    Adapter for transaction_fetcher tools.py interface.
    Proxies to TransactionQueryService methods.
    """
    def parse_flexible_date(self, date_str: str):
        return TransactionQueryService._parse_flexible_date(date_str)
    
    def time_in_range(self, transaction_time: str, start_hour: int, end_hour: int) -> bool:
        return TransactionQueryService._time_in_range(transaction_time, start_hour, end_hour)
    
    def get_jar_transactions(self, jar_name: str = None, limit: int = 50, description: str = "") -> Dict[str, Any]:
        return self._call_sync(TransactionQueryService.get_jar_transactions, jar_name, limit, description)
    
    def get_time_period_transactions(self, jar_name: str = None, start_date: str = "last_month", 
                                   end_date: str = None, limit: int = 50, description: str = "") -> Dict[str, Any]:
        return self._call_sync(TransactionQueryService.get_time_period_transactions, 
                               jar_name, start_date, end_date, limit, description)
    
    def get_amount_range_transactions(self, jar_name: str = None, min_amount: float = None, 
                                    max_amount: float = None, limit: int = 50, description: str = "") -> Dict[str, Any]:
        return self._call_sync(TransactionQueryService.get_amount_range_transactions, 
                               jar_name, min_amount, max_amount, limit, description)
    
    def get_hour_range_transactions(self, jar_name: str = None, start_hour: int = 6, 
                                  end_hour: int = 22, limit: int = 50, description: str = "") -> Dict[str, Any]:
        return self._call_sync(TransactionQueryService.get_hour_range_transactions, 
                               jar_name, start_hour, end_hour, limit, description)
    
    def get_source_transactions(self, jar_name: str = None, source_type: str = "vpbank_api", 
                              limit: int = 50, description: str = "") -> Dict[str, Any]:
        return self._call_sync(TransactionQueryService.get_source_transactions, 
                               jar_name, source_type, limit, description)
    
    def get_complex_transaction(self, jar_name: str = None, start_date: str = None, end_date: str = None,
                              min_amount: float = None, max_amount: float = None, start_hour: int = None,
                              end_hour: int = None, source_type: str = None, limit: int = 50, 
                              description: str = "") -> Dict[str, Any]:
        return self._call_sync(TransactionQueryService.get_complex_transaction, 
                               jar_name, start_date, end_date, min_amount, max_amount, 
                               start_hour, end_hour, source_type, limit, description)
        
class KnowledgeAdapter(BaseAdapter):
    """
    Adapter for knowledge tools.py interface.
    """
    def get_application_information(self, description: str = "") -> Dict[str, Any]:
        return self._call_sync(KnowledgeService.get_application_information, description)
    
    def respond(self, answer: str, description: str = "") -> Dict[str, Any]:
        return KnowledgeService.respond(answer, description)
class PlanAdapter(BaseAdapter):
    """
    Adapter for plan tools.py interface.
    """
    def create_plan(self, name: str, description: str, status: str = "active", 
                   jar_propose_adjust_details: Optional[str] = None, confidence: int = 85) -> str:
        return self._call_sync(PlanManagementService.create_plan, name, description, status, 
                               jar_propose_adjust_details, confidence)
    
    def adjust_plan(self, name: str, description: Optional[str] = None, status: Optional[str] = None,
                   jar_propose_adjust_details: Optional[str] = None, confidence: int = 85) -> str:
        return self._call_sync(PlanManagementService.adjust_plan, name, description, status,
                               jar_propose_adjust_details, confidence)
    
    def get_plan(self, status: str = "active", description: str = "") -> Dict[str, Any]:
        return self._call_sync(PlanManagementService.get_plan, status, description)
    
    def delete_plan(self, plan_name: str, reason: str = "") -> str:
        return self._call_sync(PlanManagementService.delete_plan, plan_name, reason)
    
    def call_transaction_fetcher(self, user_query: str, description: str = "") -> Dict[str, Any]:
        return self._call_sync(AgentCommunicationService.call_transaction_fetcher, user_query, description)

# Factory functions
def get_classifier_adapter(db: AsyncIOMotorDatabase, user_id: str) -> ClassifierAdapter:
    return ClassifierAdapter(db, user_id)

def get_fee_adapter(db: AsyncIOMotorDatabase, user_id: str) -> FeeAdapter:
    return FeeAdapter(db, user_id)

def get_jar_adapter(db: AsyncIOMotorDatabase, user_id: str) -> JarAdapter:
    return JarAdapter(db, user_id)

def get_transaction_fetcher_service(db: AsyncIOMotorDatabase, user_id: str) -> TransactionFetcherAdapter:
    return TransactionFetcherAdapter(db, user_id)

def get_knowledge_adapter(db: AsyncIOMotorDatabase, user_id: str) -> KnowledgeAdapter:
    return KnowledgeAdapter(db, user_id)

def get_plan_adapter(db: AsyncIOMotorDatabase, user_id: str) -> PlanAdapter:
    return PlanAdapter(db, user_id)