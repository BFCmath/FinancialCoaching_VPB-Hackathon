"""
Service Adapters - Lab Compatibility Layer
=========================================

This module provides adapters that bridge the gap between lab interfaces
and backend database requirements, ensuring exact compatibility with agent tools.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
import asyncio
import concurrent.futures

# Import services
from .transaction_service import TransactionService
from .communication_service import AgentCommunicationService
from .fee_service import FeeManagementService

# =============================================================================
# CLASSIFIER TOOLS COMPATIBILITY LAYER
# =============================================================================

class ClassifierServiceAdapter:
    """
    Adapter that provides the exact interface that classifier tools.py expects.
    This bridges the gap between lab interface and backend database requirements.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = user_id
        self.transaction_service = TransactionService()
        self.communication_service = AgentCommunicationService()
    
    def add_money_to_jar_with_confidence(self, amount: float, jar_name: str, confidence: int) -> str:
        """
        Lab-compatible interface for adding money to jar.
        This function signature matches exactly what classifier tools.py expects.
        """
        # Since this is called from async context but classifier expects sync,
        # we need to handle this carefully
        try:
            # Create a new event loop if we're not in one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're already in an async context, create a new thread
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            lambda: asyncio.run(
                                self.transaction_service.add_money_to_jar_with_confidence(
                                    self.db, self.user_id, amount, jar_name, confidence
                                )
                            )
                        )
                        return future.result()
                else:
                    # Run in current loop
                    return loop.run_until_complete(
                        self.transaction_service.add_money_to_jar_with_confidence(
                            self.db, self.user_id, amount, jar_name, confidence
                        )
                    )
            except RuntimeError:
                # No event loop, create new one
                return asyncio.run(
                    self.transaction_service.add_money_to_jar_with_confidence(
                        self.db, self.user_id, amount, jar_name, confidence
                    )
                )
        except Exception as e:
            return f"❌ Error adding transaction: {str(e)}"
    
    def report_no_suitable_jar(self, description: str, suggestion: str) -> str:
        """Lab-compatible interface for reporting no suitable jar."""
        return self.transaction_service.report_no_suitable_jar(description, suggestion)
    
    def call_transaction_fetcher(self, user_query: str, description: str = "") -> Dict[str, Any]:
        """
        Lab-compatible interface for calling transaction fetcher.
        This function signature matches exactly what classifier tools.py expects.
        """
        try:
            # Handle async call in sync context
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, use executor
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            lambda: asyncio.run(
                                self.communication_service.call_transaction_fetcher(
                                    self.db, self.user_id, user_query, description
                                )
                            )
                        )
                        return future.result()
                else:
                    # Run in current loop
                    return loop.run_until_complete(
                        self.communication_service.call_transaction_fetcher(
                            self.db, self.user_id, user_query, description
                        )
                    )
            except RuntimeError:
                # No event loop, create new one
                return asyncio.run(
                    self.communication_service.call_transaction_fetcher(
                        self.db, self.user_id, user_query, description
                    )
                )
        except Exception as e:
            return {
                "data": [],
                "error": f"Failed to fetch transactions: {str(e)}",
                "description": description
            }

# =============================================================================
# FEE TOOLS COMPATIBILITY LAYER
# =============================================================================

class FeeServiceAdapter:
    """
    Adapter that provides the exact interface that fee tools.py expects.
    This bridges the gap between lab interface and backend database requirements.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = user_id
        self.fee_service = FeeManagementService()
    
    def create_recurring_fee(self, name: str, amount: float, description: str, pattern_type: str,
                           pattern_details: Optional[List[int]], target_jar: str, 
                           confidence: int = 85) -> str:
        """
        Lab-compatible interface for creating recurring fee.
        This function signature matches exactly what fee tools.py expects.
        """
        try:
            # Handle async call in sync context
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, use executor
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            lambda: asyncio.run(
                                self.fee_service.create_recurring_fee(
                                    self.db, self.user_id, name, amount, description, 
                                    pattern_type, pattern_details, target_jar, confidence
                                )
                            )
                        )
                        return future.result()
                else:
                    # Run in current loop
                    return loop.run_until_complete(
                        self.fee_service.create_recurring_fee(
                            self.db, self.user_id, name, amount, description, 
                            pattern_type, pattern_details, target_jar, confidence
                        )
                    )
            except RuntimeError:
                # No event loop, create new one
                return asyncio.run(
                    self.fee_service.create_recurring_fee(
                        self.db, self.user_id, name, amount, description, 
                        pattern_type, pattern_details, target_jar, confidence
                    )
                )
        except Exception as e:
            return f"❌ Error creating recurring fee: {str(e)}"
    
    def adjust_recurring_fee(self, fee_name: str, new_amount: Optional[float] = None,
                           new_description: Optional[str] = None, new_pattern_type: Optional[str] = None,
                           new_pattern_details: Optional[List[int]] = None, new_target_jar: Optional[str] = None,
                           disable: bool = False, confidence: int = 85) -> str:
        """
        Lab-compatible interface for adjusting recurring fee.
        This function signature matches exactly what fee tools.py expects.
        """
        try:
            # Handle async call in sync context
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, use executor
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            lambda: asyncio.run(
                                self.fee_service.adjust_recurring_fee(
                                    self.db, self.user_id, fee_name, new_amount, new_description,
                                    new_pattern_type, new_pattern_details, new_target_jar, disable, confidence
                                )
                            )
                        )
                        return future.result()
                else:
                    # Run in current loop
                    return loop.run_until_complete(
                        self.fee_service.adjust_recurring_fee(
                            self.db, self.user_id, fee_name, new_amount, new_description,
                            new_pattern_type, new_pattern_details, new_target_jar, disable, confidence
                        )
                    )
            except RuntimeError:
                # No event loop, create new one
                return asyncio.run(
                    self.fee_service.adjust_recurring_fee(
                        self.db, self.user_id, fee_name, new_amount, new_description,
                        new_pattern_type, new_pattern_details, new_target_jar, disable, confidence
                    )
                )
        except Exception as e:
            return f"❌ Error adjusting recurring fee: {str(e)}"
    
    def delete_recurring_fee(self, fee_name: str, reason: str) -> str:
        """
        Lab-compatible interface for deleting recurring fee.
        This function signature matches exactly what fee tools.py expects.
        """
        try:
            # Handle async call in sync context
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, use executor
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            lambda: asyncio.run(
                                self.fee_service.delete_recurring_fee(
                                    self.db, self.user_id, fee_name, reason
                                )
                            )
                        )
                        return future.result()
                else:
                    # Run in current loop
                    return loop.run_until_complete(
                        self.fee_service.delete_recurring_fee(
                            self.db, self.user_id, fee_name, reason
                        )
                    )
            except RuntimeError:
                # No event loop, create new one
                return asyncio.run(
                    self.fee_service.delete_recurring_fee(
                        self.db, self.user_id, fee_name, reason
                    )
                )
        except Exception as e:
            return f"❌ Error deleting recurring fee: {str(e)}"
    
    def list_recurring_fees(self, active_only: bool = True, target_jar: Optional[str] = None) -> str:
        """
        Lab-compatible interface for listing recurring fees.
        This function signature matches exactly what fee tools.py expects.
        """
        try:
            # Handle async call in sync context
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, use executor
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            lambda: asyncio.run(
                                self.fee_service.list_recurring_fees(
                                    self.db, self.user_id, active_only, target_jar
                                )
                            )
                        )
                        return future.result()
                else:
                    # Run in current loop
                    return loop.run_until_complete(
                        self.fee_service.list_recurring_fees(
                            self.db, self.user_id, active_only, target_jar
                        )
                    )
            except RuntimeError:
                # No event loop, create new one
                return asyncio.run(
                    self.fee_service.list_recurring_fees(
                        self.db, self.user_id, active_only, target_jar
                    )
                )
        except Exception as e:
            return f"❌ Error listing recurring fees: {str(e)}"

# =============================================================================
# JAR TOOLS COMPATIBILITY LAYER  
# =============================================================================

class JarServiceAdapter:
    """
    Adapter that provides the exact interface that jar tools.py expects.
    This bridges the gap between lab interface and backend database requirements.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, user_id: str):
        self.db = db
        self.user_id = user_id
        from .jar_service import JarManagementService
        self.jar_service = JarManagementService()
    
    def create_jar(self, name: List[str], description: List[str], 
                  percent: Optional[List[float]] = None, amount: Optional[List[float]] = None,
                  confidence: int = 85) -> str:
        """
        Lab-compatible interface for creating jars.
        This function signature matches exactly what jar tools.py expects.
        """
        try:
            # Handle async call in sync context
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, use executor
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            lambda: asyncio.run(
                                self.jar_service.create_jar(
                                    self.db, self.user_id, name, description, 
                                    percent, amount, confidence
                                )
                            )
                        )
                        return future.result()
                else:
                    # Run in current loop
                    return loop.run_until_complete(
                        self.jar_service.create_jar(
                            self.db, self.user_id, name, description, 
                            percent, amount, confidence
                        )
                    )
            except RuntimeError:
                # No event loop, create new one
                return asyncio.run(
                    self.jar_service.create_jar(
                        self.db, self.user_id, name, description, 
                        percent, amount, confidence
                    )
                )
        except Exception as e:
            return f"❌ Error creating jar: {str(e)}"
    
    def update_jar(self, jar_name: List[str], new_name: Optional[List[str]] = None,
                  new_description: Optional[List[str]] = None, new_percent: Optional[List[float]] = None,
                  new_amount: Optional[List[float]] = None, confidence: int = 85) -> str:
        """
        Lab-compatible interface for updating jars.
        This function signature matches exactly what jar tools.py expects.
        """
        try:
            # Handle async call in sync context
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, use executor
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            lambda: asyncio.run(
                                self.jar_service.update_jar(
                                    self.db, self.user_id, jar_name, new_name, new_description,
                                    new_percent, new_amount, confidence
                                )
                            )
                        )
                        return future.result()
                else:
                    # Run in current loop
                    return loop.run_until_complete(
                        self.jar_service.update_jar(
                            self.db, self.user_id, jar_name, new_name, new_description,
                            new_percent, new_amount, confidence
                        )
                    )
            except RuntimeError:
                # No event loop, create new one
                return asyncio.run(
                    self.jar_service.update_jar(
                        self.db, self.user_id, jar_name, new_name, new_description,
                        new_percent, new_amount, confidence
                    )
                )
        except Exception as e:
            return f"❌ Error updating jar: {str(e)}"
    
    def delete_jar(self, jar_name: List[str], reason: str) -> str:
        """
        Lab-compatible interface for deleting jars.
        This function signature matches exactly what jar tools.py expects.
        """
        try:
            # Handle async call in sync context
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, use executor
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            lambda: asyncio.run(
                                self.jar_service.delete_jar(
                                    self.db, self.user_id, jar_name, reason
                                )
                            )
                        )
                        return future.result()
                else:
                    # Run in current loop
                    return loop.run_until_complete(
                        self.jar_service.delete_jar(
                            self.db, self.user_id, jar_name, reason
                        )
                    )
            except RuntimeError:
                # No event loop, create new one
                return asyncio.run(
                    self.jar_service.delete_jar(
                        self.db, self.user_id, jar_name, reason
                    )
                )
        except Exception as e:
            return f"❌ Error deleting jar: {str(e)}"
    
    def list_jars(self) -> str:
        """
        Lab-compatible interface for listing jars.
        This function signature matches exactly what jar tools.py expects.
        """
        try:
            # Handle async call in sync context
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, use executor
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            lambda: asyncio.run(
                                self.jar_service.list_jars(
                                    self.db, self.user_id
                                )
                            )
                        )
                        return future.result()
                else:
                    # Run in current loop
                    return loop.run_until_complete(
                        self.jar_service.list_jars(
                            self.db, self.user_id
                        )
                    )
            except RuntimeError:
                # No event loop, create new one
                return asyncio.run(
                    self.jar_service.list_jars(
                        self.db, self.user_id
                    )
                )
        except Exception as e:
            return f"❌ Error listing jars: {str(e)}"

# =============================================================================
# GLOBAL SERVICE INSTANCES FOR AGENT COMPATIBILITY
# =============================================================================

# Global variables to hold service instances configured with database context
_classifier_transaction_service = None
_classifier_communication_service = None
_fee_service = None
_jar_service = None

def configure_classifier_services(db: AsyncIOMotorDatabase, user_id: str):
    """
    Configure global service instances for classifier tools.py compatibility.
    This must be called before classifier tools are used.
    """
    global _classifier_transaction_service, _classifier_communication_service
    
    adapter = ClassifierServiceAdapter(db, user_id)
    _classifier_transaction_service = adapter
    _classifier_communication_service = adapter

def configure_fee_services(db: AsyncIOMotorDatabase, user_id: str):
    """
    Configure global service instances for fee tools.py compatibility.
    This must be called before fee tools are used.
    """
    global _fee_service
    
    adapter = FeeServiceAdapter(db, user_id)
    _fee_service = adapter

def configure_jar_services(db: AsyncIOMotorDatabase, user_id: str):
    """
    Configure global service instances for jar tools.py compatibility.
    This must be called before jar tools are used.
    """
    global _jar_service
    
    adapter = JarServiceAdapter(db, user_id)
    _jar_service = adapter

def get_transaction_service():
    """
    Get transaction service instance for classifier tools.py.
    This function signature matches exactly what classifier tools.py expects.
    """
    if _classifier_transaction_service is None:
        raise RuntimeError(
            "Classifier services not configured. Call configure_classifier_services() first."
        )
    return _classifier_transaction_service

def get_communication_service():
    """
    Get communication service instance for classifier tools.py.
    This function signature matches exactly what classifier tools.py expects.
    """
    if _classifier_communication_service is None:
        raise RuntimeError(
            "Classifier services not configured. Call configure_classifier_services() first."
        )
    return _classifier_communication_service

def get_fee_service():
    """
    Get fee service instance for fee tools.py.
    This function signature matches exactly what fee tools.py expects.
    """
    if _fee_service is None:
        raise RuntimeError(
            "Fee services not configured. Call configure_fee_services() first."
        )
    return _fee_service

def get_jar_service():
    """
    Get jar service instance for jar tools.py.
    This function signature matches exactly what jar tools.py expects.
    """
    if _jar_service is None:
        raise RuntimeError(
            "Jar services not configured. Call configure_jar_services() first."
        )
    return _jar_service
