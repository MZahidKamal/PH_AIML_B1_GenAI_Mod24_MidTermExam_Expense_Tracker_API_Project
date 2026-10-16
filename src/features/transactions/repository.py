# External imports -----------------------------------------------------------------------------------------------------
import datetime as dt
from collections.abc import Sequence
from decimal import Decimal
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# Internal imports -----------------------------------------------------------------------------------------------------
from src.features.transactions.constants import TransactionType
from src.features.transactions.models import Transaction





# Repository -----------------------------------------------------------------------------------------------------------

# Database query layer for the 'transactions' table; every read is scoped to one owner
class TransactionRepository:

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    # Insert a new transaction (flush only, the service commits)
    async def create(
        self,
        owner_id: int,
        title: str,
        amount: Decimal,
        type: TransactionType,
        category: str,
        date: dt.date,
    ) -> Transaction:
        transaction = Transaction(
            owner_id=owner_id, title=title, amount=amount, type=type, category=category, date=date
        )
        self.db_session.add(transaction)
        await self.db_session.flush()
        return transaction

    # Find one transaction by id, but ONLY if it belongs to this owner (returns None otherwise)
    async def get_for_owner(self, transaction_id: int, owner_id: int) -> Transaction | None:
        return await self.db_session.scalar(
            select(Transaction).where(Transaction.id == transaction_id, Transaction.owner_id == owner_id)
        )

    # List an owner's transactions, newest first; every filter is optional and only applied when given
    async def list_for_owner(
        self,
        owner_id: int,
        type: TransactionType | None = None,
        category: str | None = None,
        minimum_amount: Decimal | None = None,
        maximum_amount: Decimal | None = None,
    ) -> Sequence[Transaction]:
        statement = select(Transaction).where(Transaction.owner_id == owner_id)

        if type is not None:
            statement = statement.where(Transaction.type == type)
        if category is not None:
            # Case-insensitive exact match: "food", "Food" and "FOOD" are the same category
            statement = statement.where(func.lower(Transaction.category) == category.lower())
        if minimum_amount is not None:
            statement = statement.where(Transaction.amount >= minimum_amount)
        if maximum_amount is not None:
            statement = statement.where(Transaction.amount <= maximum_amount)

        statement = statement.order_by(Transaction.date.desc(), Transaction.id.desc())
        return (await self.db_session.scalars(statement)).all()

    # Apply only the given changes to an existing transaction
    async def update(self, transaction: Transaction, changes: dict[str, Any]) -> Transaction:
        for field_name, value in changes.items():
            setattr(transaction, field_name, value)
        await self.db_session.flush()
        return transaction

    # Delete a transaction row
    async def delete(self, transaction: Transaction) -> None:
        await self.db_session.delete(transaction)
        await self.db_session.flush()





# ----------------------------------------------------------------------------------------------------------------------
