# External imports -----------------------------------------------------------------------------------------------------
import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Internal imports -----------------------------------------------------------------------------------------------------
from src.db.base import SqlalchemyBase
from src.features.transactions.constants import (
    AMOUNT_DECIMAL_PLACES,
    AMOUNT_MAX_DIGITS,
    CATEGORY_MAX_LENGTH,
    TITLE_MAX_LENGTH,
    TYPE_MAX_LENGTH,
    TransactionType,
)

# Imported only for type checkers (avoids a circular import at runtime)
if TYPE_CHECKING:
    from src.features.users.models import User





# Database model -------------------------------------------------------------------------------------------------------

# Define the 'transactions' table: one row per income or expense record
class Transaction(SqlalchemyBase):
    __tablename__ = "transactions"

    # Database-level safety rules and indexes (they protect the data even if a bug skips Pydantic validation)
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("type IN ('income', 'expense')", name="type_valid"),
        # Composite index: speeds up "all transactions of one user, ordered by date"
        Index("ix_transactions_owner_id_date", "owner_id", "date"),
    )

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Short description, e.g. "Grocery shopping"
    title: Mapped[str] = mapped_column(String(TITLE_MAX_LENGTH))

    # Exact money value (NUMERIC(12, 2) in PostgreSQL), never a float
    amount: Mapped[Decimal] = mapped_column(Numeric(AMOUNT_MAX_DIGITS, AMOUNT_DECIMAL_PLACES))

    # "income" or "expense"; stored as plain VARCHAR, read back as TransactionType
    type: Mapped[TransactionType] = mapped_column(
        Enum(
            TransactionType,
            native_enum=False,
            length=TYPE_MAX_LENGTH,
            values_callable=lambda enum_class: [member.value for member in enum_class],
        )
    )

    # Free-text category, e.g. "Food", "Salary", "Rent"
    category: Mapped[str] = mapped_column(String(CATEGORY_MAX_LENGTH))

    # The day the transaction happened (no time part)
    date: Mapped[dt.date]

    # Owner of the transaction; ON DELETE CASCADE removes the user's transactions when the user is deleted
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    # Many-to-one link back to the owning user
    owner: Mapped["User"] = relationship(back_populates="transactions")

    # Readable representation for debugging
    def __repr__(self) -> str:
        return f"<Transaction id={self.id} type={self.type} amount={self.amount} owner_id={self.owner_id}>"





# ----------------------------------------------------------------------------------------------------------------------
