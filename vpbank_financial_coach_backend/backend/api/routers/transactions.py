import sys
import os
from typing import List, Optional
from datetime import date, time
from fastapi import APIRouter, Depends, HTTPException, status, Query

from backend.api import deps
from backend.utils import db_utils
from backend.models import user as user_model
from backend.models import transaction as transaction_model
from motor.motor_asyncio import AsyncIOMotorDatabase


router = APIRouter()

# In backend/api/routers/transactions.py

@router.post("/", response_model=transaction_model.TransactionInDB, status_code=status.HTTP_201_CREATED)
async def create_new_transaction(
    transaction_in: transaction_model.TransactionCreate,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_active_user)
):
    """
    Creates a new transaction and updates the corresponding jar's balance.
    """
    user_id = str(current_user.id)
    
    # 1. Validate that the target jar exists for the user
    target_jar = await db_utils.get_jar_by_name(db, user_id, transaction_in.jar)
    if not target_jar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jar '{transaction_in.jar}' not found for this user."
        )

    # 2. Prepare the transaction data as a dictionary
    transaction_dict_to_save = transaction_in.model_dump(by_alias=True)
    transaction_dict_to_save['user_id'] = user_id
    
    # Create the transaction in the database and get the full model back
    saved_transaction = await db_utils.create_transaction_in_db(db, transaction_dict_to_save)

    # 3. Update the jar's current balance
    new_current_amount = target_jar.current_amount + transaction_in.amount
    
    user_settings = await db_utils.get_user_settings(db, user_id)
    total_income = user_settings.total_income if user_settings and user_settings.total_income > 0 else 5000.0
    new_current_percent = new_current_amount / total_income if total_income > 0 else 0.0

    update_data = {
        "current_amount": new_current_amount,
        "current_percent": new_current_percent
    }
    await db_utils.update_jar_in_db(db, user_id, target_jar.name, update_data)

    return saved_transaction


@router.get("/", response_model=List[transaction_model.TransactionInDB])
async def query_transactions(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_active_user),
    jar: Optional[str] = Query(None, description="Filter by jar name."),
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

    if jar:
        query_filter["jar"] = jar
    
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

    # --- ADD THIS BLOCK TO FIX THE BUG ---
    # Manually convert ObjectId to string for each document before Pydantic validation
    for t in transactions:
        t["_id"] = str(t["_id"])
    # ------------------------------------

    return [transaction_model.TransactionInDB(**t) for t in transactions]