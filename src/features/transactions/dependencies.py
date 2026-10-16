# External imports -----------------------------------------------------------------------------------------------------
from typing import Annotated
from fastapi import Depends

# Internal imports -----------------------------------------------------------------------------------------------------
from src.api.v1.deps import DbSession
from src.features.transactions.service import TransactionService





# Feature dependencies -------------------------------------------------------------------------------------------------

# Build a TransactionService with this request's database session
async def get_transaction_service(db_session: DbSession) -> TransactionService:
    return TransactionService(db_session)


# Type alias used in the router
TransactionServiceDep = Annotated[TransactionService, Depends(get_transaction_service)]





# ----------------------------------------------------------------------------------------------------------------------
