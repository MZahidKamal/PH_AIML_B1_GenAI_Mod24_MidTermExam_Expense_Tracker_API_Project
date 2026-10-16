# External imports -----------------------------------------------------------------------------------------------------
import datetime as dt
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# Internal imports -----------------------------------------------------------------------------------------------------
from src.features.transactions.constants import TransactionType
from src.features.transactions.models import Transaction
from src.features.users.models import User
from tests.conftest import AuthUser





# Helper ---------------------------------------------------------------------------------------------------------------

def new_transaction(owner_id: int, **overrides) -> Transaction:
    fields = {
        "title": "Groceries",
        "amount": Decimal("10.00"),
        "type": TransactionType.EXPENSE,
        "category": "Food",
        "date": dt.date(2026, 10, 1),
        "owner_id": owner_id,
    }
    fields.update(overrides)
    return Transaction(**fields)





# Relationship (User <-> Transaction) ----------------------------------------------------------------------------------

async def test_user_and_transaction_are_linked_both_ways(db_session: AsyncSession, user: AuthUser, create_transaction) -> None:
    created = await create_transaction(user)

    owner = await db_session.get(User, user.id)
    transactions = await owner.awaitable_attrs.transactions
    transaction = transactions[0]

    assert [item.id for item in transactions] == [created["id"]]
    assert (await transaction.awaitable_attrs.owner).id == user.id


async def test_deleting_a_user_deletes_their_transactions(
    db_session: AsyncSession, user: AuthUser, create_transaction
) -> None:
    created = await create_transaction(user)

    await db_session.delete(await db_session.get(User, user.id))
    await db_session.commit()

    assert await db_session.scalar(select(Transaction).where(Transaction.id == created["id"])) is None





# Database-level safety rules (they work even if Pydantic validation is bypassed) --------------------------------------

@pytest.mark.parametrize("amount", [Decimal("0"), Decimal("-5")])
async def test_database_rejects_non_positive_amounts(db_session: AsyncSession, user: AuthUser, amount: Decimal) -> None:
    db_session.add(new_transaction(user.id, amount=amount))
    with pytest.raises(IntegrityError, match="ck_transactions_amount_positive"):
        await db_session.flush()


async def test_database_rejects_unknown_owner(db_session: AsyncSession) -> None:
    db_session.add(new_transaction(owner_id=999_999_999))
    with pytest.raises(IntegrityError, match="fk_transactions_owner_id_users"):
        await db_session.flush()
