# External imports -----------------------------------------------------------------------------------------------------
from collections.abc import Sequence
from sqlalchemy.ext.asyncio import AsyncSession

# Internal imports -----------------------------------------------------------------------------------------------------
from src.features.transactions.exceptions import TransactionNotFound
from src.features.transactions.models import Transaction
from src.features.transactions.repository import TransactionRepository
from src.features.transactions.schemas import TransactionCreate, TransactionFilter, TransactionUpdate





# Service --------------------------------------------------------------------------------------------------------------

# Business logic for transactions; every method receives the logged-in user's id as owner_id
class TransactionService:

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session
        self.transaction_repository = TransactionRepository(db_session)

    # Create: the owner always comes from the token, never from the request body
    async def create(self, owner_id: int, data: TransactionCreate) -> Transaction:
        transaction = await self.transaction_repository.create(owner_id=owner_id, **data.model_dump())
        await self.db_session.commit()
        return transaction

    # Read all of the owner's transactions
    async def list(self, owner_id: int) -> Sequence[Transaction]:
        return await self.transaction_repository.list_for_owner(owner_id)

    # Read the owner's transactions that match the given filters
    async def filter(self, owner_id: int, filters: TransactionFilter) -> Sequence[Transaction]:
        return await self.transaction_repository.list_for_owner(owner_id, **filters.model_dump())

    # Read one transaction; missing OR someone else's -> 404
    async def get(self, owner_id: int, transaction_id: int) -> Transaction:
        transaction = await self.transaction_repository.get_for_owner(transaction_id, owner_id)
        if transaction is None:
            raise TransactionNotFound()
        return transaction

    # Partial update: exclude_unset keeps only the fields the client actually sent
    async def update(self, owner_id: int, transaction_id: int, data: TransactionUpdate) -> Transaction:
        transaction = await self.get(owner_id, transaction_id)
        await self.transaction_repository.update(transaction, data.model_dump(exclude_unset=True))
        await self.db_session.commit()
        return transaction

    # Delete one of the owner's transactions
    async def delete(self, owner_id: int, transaction_id: int) -> None:
        transaction = await self.get(owner_id, transaction_id)
        await self.transaction_repository.delete(transaction)
        await self.db_session.commit()





# ----------------------------------------------------------------------------------------------------------------------
