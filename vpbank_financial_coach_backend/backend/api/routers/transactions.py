from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, date
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.api import deps
from backend.utils import transaction_utils
from backend.utils import jar_utils
from backend.models import user as user_model
from backend.models import transaction as transaction_model

router = APIRouter()

@router.post("/", response_model=transaction_model.TransactionInDB, status_code=status.HTTP_201_CREATED)
async def create_new_transaction(
    transaction_in: transaction_model.TransactionCreate,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Creates a new transaction and updates the corresponding jar's balance.
    """
    user_id = str(current_user.id)
    
    # Validate that the target jar exists for the user
    target_jar = await jar_utils.get_jar_by_name(db, user_id, transaction_in.jar)
    if not target_jar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jar '{transaction_in.jar}' not found for this user."
        )

    # Prepare the transaction data as a dictionary
    transaction_dict_to_save = transaction_in.model_dump()
    transaction_dict_to_save['user_id'] = user_id
    
    # Create the transaction in the database
    saved_transaction = await transaction_utils.create_transaction_in_db(db, transaction_dict_to_save)

    # Update the jar's current balance by adding the transaction amount (spent money)
    await jar_utils.add_money_to_jar(db, user_id, transaction_in.jar, transaction_in.amount)

    return saved_transaction


@router.get("/", response_model=List[transaction_model.TransactionInDB])
async def list_transactions(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user),
    jar: Optional[str] = Query(None, description="Filter by jar name."),
    limit: int = Query(50, ge=1, le=100, description="Number of transactions to return.")
):
    """
    Retrieves a list of transactions for the current user.
    """
    user_id = str(current_user.id)
    
    if jar:
        transactions = await transaction_utils.get_transactions_by_jar_for_user(db, user_id, jar)
    else:
        transactions = await transaction_utils.get_all_transactions_for_user(db, user_id)
    
    # Apply limit
    return transactions[:limit]

@router.get("/by-source/{source}", response_model=List[transaction_model.TransactionInDB])
async def get_transactions_by_source(
    source: transaction_model.TransactionSource,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Get transactions filtered by source type.
    """
    user_id = str(current_user.id)
    transactions = await transaction_utils.get_transactions_by_source_for_user(db, user_id, source)
    return transactions

@router.get("/by-amount-range", response_model=List[transaction_model.TransactionInDB])
async def get_transactions_by_amount_range(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum transaction amount."),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum transaction amount.")
):
    """
    Get transactions filtered by amount range.
    """
    user_id = str(current_user.id)
    
    if min_amount is None and max_amount is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of min_amount or max_amount must be provided."
        )
    
    transactions = await transaction_utils.get_transactions_by_amount_range_for_user(
        db, user_id, min_amount, max_amount
    )
    return transactions

@router.get("/by-date-range", response_model=List[transaction_model.TransactionInDB])
async def get_transactions_by_date_range(
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user),
    start_date: str = Query(..., description="Start date in ISO format (YYYY-MM-DDTHH:MM:SS)."),
    end_date: Optional[str] = Query(None, description="End date in ISO format (YYYY-MM-DDTHH:MM:SS).")
):
    """
    Get transactions filtered by date range.
    """
    user_id = str(current_user.id)
    
    # Validate date format
    try:
        datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)."
        )
    
    transactions = await transaction_utils.get_transactions_by_date_range_for_user(
        db, user_id, start_date, end_date
    )
    return transactions


@router.get("/{transaction_id}", response_model=transaction_model.TransactionInDB)
async def get_transaction(
    transaction_id: str,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Get a specific transaction by its ID.
    """
    user_id = str(current_user.id)
    transaction = await transaction_utils.get_transaction_by_id(db, user_id, transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found."
        )
    
    return transaction

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    db: AsyncIOMotorDatabase = Depends(deps.get_db),
    current_user: user_model.UserInDB = Depends(deps.get_current_user)
):
    """
    Delete a transaction by its ID and refund the amount to the jar.
    """
    user_id = str(current_user.id)
    
    # Get transaction first to refund the jar
    transaction = await transaction_utils.get_transaction_by_id(db, user_id, transaction_id)
    if not transaction:
        print(f"Transaction {transaction_id} not found for user {user_id}.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found."
        )
    
    # Delete the transaction
    deleted = await transaction_utils.delete_transaction_by_id(db, user_id, transaction_id)
    
    if not deleted:
        print(f"Failed to delete transaction {transaction_id} for user {user_id}.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found."
        )
    
    # Remove the spent amount from the jar (since transaction is being deleted)
    await jar_utils.subtract_money_from_jar(db, user_id, transaction.jar, transaction.amount)
    
    return