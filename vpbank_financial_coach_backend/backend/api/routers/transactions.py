import sys
import os
from typing import List, Optional
from datetime import date, time
from fastapi import APIRouter, Depends, HTTPException, status, Query

# --- Path Setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(project_root)

from backend.api import deps
from backend.utils import db_utils
from backend.models import user as user_model
from backend.models import transaction as transaction_model
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import original service for formatting functions if needed
from backend.services.financial_services import TransactionService, JarManagementService, CalculationService

router = APIRouter()

@router.post("/", response_model=transaction_model.TransactionInDB, status_code=status.HTTP_201_CREATED)
async def create_new_transaction(
    transaction_in: transaction_model.TransactionCreate,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_active_user)
):
    """
    Creates a new transaction and updates the corresponding jar's balance.
    This endpoint directly interacts with the database, bypassing the old global state.
    """
    user_id = str(current_user.id)
    
    # 1. Validate that the target jar exists for the user
    target_jar = await db_utils.get_jar_by_name(db, user_id, transaction_in.jar_name)
    if not target_jar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jar '{transaction_in.jar_name}' not found for this user."
        )

    # 2. Create the transaction document to be saved
    transaction_to_save = transaction_model.TransactionInDB(
        user_id=user_id,
        **transaction_in.model_dump(by_alias=True)
    )
    
    # Insert the new transaction into the database
    await db[db_utils.TRANSACTIONS_COLLECTION].insert_one(
        transaction_to_save.model_dump(by_alias=True)
    )

    # 3. Update the jar's current balance
    new_current_amount = target_jar.current_amount + transaction_in.amount
    
    # We need the user's total income to calculate the new percentage
    user_settings = await db_utils.get_user_settings(db, user_id)
    total_income = user_settings.total_income if user_settings and user_settings.total_income > 0 else 5000.0
    
    new_current_percent = new_current_amount / total_income

    update_data = {
        "current_amount": new_current_amount,
        "current_percent": new_current_percent
    }
    await db_utils.update_jar_in_db(db, user_id, target_jar.name, update_data)

    return transaction_to_save


@router.get("/", response_model=List[transaction_model.TransactionInDB])
async def query_transactions(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_active_user),
    jar_name: Optional[str] = Query(None, description="Filter by jar name."),
    start_date: Optional[date] = Query(None, description="Filter by start date (YYYY-MM-DD)."),
    end_date: Optional[date] = Query(None, description="Filter by end date (YYYY-MM-DD)."),
    min_amount: Optional[float] = Query(None, gt=0, description="Filter by minimum transaction amount."),
    max_amount: Optional[float] = Query(None, gt=0, description="Filter by maximum transaction amount."),
    limit: int = Query(50, ge=1, le=1000, description="Number of transactions to return.")
):
    """
    Retrieves a list of transactions for the current user based on filter criteria.
    This endpoint leverages MongoDB's querying capabilities directly.
    """
    user_id = str(current_user.id)
    query_filter = {"user_id": user_id}

    if jar_name:
        query_filter["jar"] = jar_name
    
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date.isoformat()
        if end_date:
            date_filter["$lte"] = end_date.isoformat()
        query_filter["date"] = date_filter

    if min_amount or max_amount:
        amount_filter = {}
        if min_amount:
            amount_filter["$gte"] = min_amount
        if max_amount:
            amount_filter["$lte"] = max_amount
        query_filter["amount"] = amount_filter

    cursor = db[db_utils.TRANSACTIONS_COLLECTION].find(query_filter).sort("date", -1).limit(limit)
    
    transactions = await cursor.to_list(length=limit)
    return [transaction_model.TransactionInDB(**t) for t in transactions]