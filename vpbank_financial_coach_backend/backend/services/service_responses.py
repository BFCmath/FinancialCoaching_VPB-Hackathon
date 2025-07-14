"""
Service Response Models for standardized API responses
====================================================

This module defines standardized response models for service layer operations
to ensure consistent error handling and response formats across all API endpoints.
"""

from typing import Optional, Any, List, Union
from pydantic import BaseModel
from enum import Enum

class ServiceResultStatus(str, Enum):
    """Standard status codes for service operations."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class ServiceError(BaseModel):
    """Standard error model for service operations."""
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[dict] = None

class ServiceResult(BaseModel):
    """Standard result model for service operations."""
    status: ServiceResultStatus
    message: str
    data: Optional[Any] = None
    errors: Optional[List[ServiceError]] = None
    warnings: Optional[List[str]] = None
    
    @classmethod
    def success(cls, message: str, data: Any = None, warnings: List[str] = None) -> "ServiceResult":
        """Create a successful result."""
        return cls(
            status=ServiceResultStatus.SUCCESS,
            message=message,
            data=data,
            warnings=warnings
        )
    
    @classmethod
    def error(cls, message: str, errors: List[ServiceError] = None, code: str = "OPERATION_FAILED") -> "ServiceResult":
        """Create an error result."""
        if errors is None:
            errors = [ServiceError(code=code, message=message)]
        return cls(
            status=ServiceResultStatus.ERROR,
            message=message,
            errors=errors
        )
    
    @classmethod
    def validation_error(cls, field: str, message: str) -> "ServiceResult":
        """Create a validation error result."""
        return cls(
            status=ServiceResultStatus.ERROR,
            message=f"Validation failed for {field}",
            errors=[ServiceError(code="VALIDATION_ERROR", message=message, field=field)]
        )
    
    @classmethod
    def not_found_error(cls, resource: str, identifier: str) -> "ServiceResult":
        """Create a not found error result."""
        return cls(
            status=ServiceResultStatus.ERROR,
            message=f"{resource} not found",
            errors=[ServiceError(code="NOT_FOUND", message=f"{resource} '{identifier}' not found")]
        )
    
    @classmethod
    def conflict_error(cls, resource: str, identifier: str) -> "ServiceResult":
        """Create a conflict error result."""
        return cls(
            status=ServiceResultStatus.ERROR,
            message=f"{resource} already exists",
            errors=[ServiceError(code="CONFLICT", message=f"{resource} '{identifier}' already exists")]
        )

    def is_success(self) -> bool:
        """Check if the result is successful."""
        return self.status == ServiceResultStatus.SUCCESS
    
    def is_error(self) -> bool:
        """Check if the result is an error."""
        return self.status == ServiceResultStatus.ERROR
    
    def get_error_message(self) -> str:
        """Get the primary error message."""
        if self.errors and len(self.errors) > 0:
            return self.errors[0].message
        return self.message
    
    def get_error_code(self) -> Optional[str]:
        """Get the primary error code."""
        if self.errors and len(self.errors) > 0:
            return self.errors[0].code
        return None

class JarOperationResult(ServiceResult):
    """Specialized result for jar operations."""
    
    @classmethod
    def jar_created(cls, jar_name: str, allocation: str, rebalance_info: str = None) -> "JarOperationResult":
        """Create a successful jar creation result."""
        message = f"Successfully created jar '{jar_name}' with {allocation} allocation"
        warnings = [rebalance_info] if rebalance_info else None
        return cls.success(message=message, data={"jar_name": jar_name}, warnings=warnings)
    
    @classmethod
    def jars_created(cls, jar_count: int, jar_names: List[str], rebalance_info: str = None) -> "JarOperationResult":
        """Create a successful multiple jar creation result."""
        message = f"Successfully created {jar_count} jars: {', '.join(jar_names)}"
        warnings = [rebalance_info] if rebalance_info else None
        return cls.success(message=message, data={"jar_names": jar_names}, warnings=warnings)
    
    @classmethod
    def jar_updated(cls, jar_name: str, changes: List[str], rebalance_info: str = None) -> "JarOperationResult":
        """Create a successful jar update result."""
        message = f"Successfully updated jar '{jar_name}': {', '.join(changes)}"
        warnings = [rebalance_info] if rebalance_info else None
        return cls.success(message=message, data={"jar_name": jar_name, "changes": changes}, warnings=warnings)
    
    @classmethod
    def jar_deleted(cls, jar_name: str, reason: str, rebalance_info: str = None) -> "JarOperationResult":
        """Create a successful jar deletion result."""
        message = f"Successfully deleted jar '{jar_name}'. Reason: {reason}"
        warnings = [rebalance_info] if rebalance_info else None
        return cls.success(message=message, data={"jar_name": jar_name, "reason": reason}, warnings=warnings)

class TransactionOperationResult(ServiceResult):
    """Specialized result for transaction operations."""
    
    @classmethod
    def transaction_created(cls, transaction_id: str, amount: float, jar_name: str) -> "TransactionOperationResult":
        """Create a successful transaction creation result."""
        message = f"Successfully created transaction for ${amount:.2f} in jar '{jar_name}'"
        return cls.success(message=message, data={"transaction_id": transaction_id, "amount": amount, "jar_name": jar_name})

class FeeOperationResult(ServiceResult):
    """Specialized result for fee operations."""
    
    @classmethod
    def fee_created(cls, fee_name: str, amount: float, pattern: str) -> "FeeOperationResult":
        """Create a successful fee creation result."""
        message = f"Successfully created recurring fee '{fee_name}' for ${amount:.2f} ({pattern})"
        return cls.success(message=message, data={"fee_name": fee_name, "amount": amount, "pattern": pattern})

class PlanOperationResult(ServiceResult):
    """Specialized result for plan operations."""
    
    @classmethod
    def plan_created(cls, plan_name: str, status: str) -> "PlanOperationResult":
        """Create a successful plan creation result."""
        message = f"Successfully created budget plan '{plan_name}' with status '{status}'"
        return cls.success(message=message, data={"plan_name": plan_name, "status": status})
