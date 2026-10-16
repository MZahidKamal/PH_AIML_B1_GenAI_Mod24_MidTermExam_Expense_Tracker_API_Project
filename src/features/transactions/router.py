# External imports -----------------------------------------------------------------------------------------------------
from typing import Annotated
from fastapi import APIRouter, Path, Query, status, Depends

# Internal imports -----------------------------------------------------------------------------------------------------
from src.api.v1.deps import CurrentUser, get_current_user
from src.features.transactions.dependencies import TransactionServiceDep
from src.features.transactions.schemas import (
    TransactionCreate,
    TransactionFilter,
    TransactionRead,
    TransactionUpdate,
)
from src.shared.schemas import MessageResponse





# Router ---------------------------------------------------------------------------------------------------------------

# All routes start with /transactions; every route requires a valid access token via CurrentUser
# All routes start with /transactions; router-level dependency makes EVERY route in this file require a valid access token
router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
    dependencies=[Depends(get_current_user)],
)

# Reusable path parameter: a positive integer id
TransactionId = Annotated[int, Path(gt=0, description="ID of the transaction")]


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED, summary="Create a transaction")
async def create_transaction(
    data: TransactionCreate, current_user: CurrentUser, transaction_service: TransactionServiceDep
):
    return await transaction_service.create(current_user.id, data)


@router.get("", response_model=list[TransactionRead], summary="Get all my transactions (newest first)")
async def list_transactions(current_user: CurrentUser, transaction_service: TransactionServiceDep):
    return await transaction_service.list(current_user.id)


# IMPORTANT: '/filter' must be declared BEFORE '/{transaction_id}', otherwise "filter" is treated as an id
@router.get("/filter", response_model=list[TransactionRead], summary="Filter my transactions")
async def filter_transactions(
    filters: Annotated[TransactionFilter, Query()],
    current_user: CurrentUser,
    transaction_service: TransactionServiceDep,
):
    return await transaction_service.filter(current_user.id, filters)


@router.get("/{transaction_id}", response_model=TransactionRead, summary="Get one of my transactions")
async def get_transaction(
    transaction_id: TransactionId, current_user: CurrentUser, transaction_service: TransactionServiceDep
):
    return await transaction_service.get(current_user.id, transaction_id)


@router.put("/{transaction_id}", response_model=TransactionRead, summary="Update one of my transactions (partial)")
async def update_transaction(
    transaction_id: TransactionId,
    data: TransactionUpdate,
    current_user: CurrentUser,
    transaction_service: TransactionServiceDep,
):
    return await transaction_service.update(current_user.id, transaction_id, data)


@router.delete("/{transaction_id}", response_model=MessageResponse, summary="Delete one of my transactions")
async def delete_transaction(
    transaction_id: TransactionId, current_user: CurrentUser, transaction_service: TransactionServiceDep
):
    await transaction_service.delete(current_user.id, transaction_id)
    return MessageResponse(message=f"Transaction {transaction_id} deleted successfully.")





# ----------------------------------------------------------------------------------------------------------------------
