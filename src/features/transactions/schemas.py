# External imports -----------------------------------------------------------------------------------------------------
import datetime as dt
from decimal import Decimal
from typing import Annotated, Self
from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, StringConstraints, model_validator

# Internal imports -----------------------------------------------------------------------------------------------------
from src.features.transactions.constants import (
    AMOUNT_DECIMAL_PLACES,
    AMOUNT_MAX_DIGITS,
    CATEGORY_MAX_LENGTH,
    TITLE_MAX_LENGTH,
    TransactionType,
)





# Reusable field types -------------------------------------------------------------------------------------------------

# Title: trimmed, 1-100 characters
Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TITLE_MAX_LENGTH), Field(examples=["Groceries"])
]

# Category: trimmed, 1-50 characters
Category = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=CATEGORY_MAX_LENGTH), Field(examples=["Food"])
]

# Amount sent by the client: must be > 0, max 12 digits, max 2 decimal places
PositiveAmount = Annotated[
    Decimal,
    Field(gt=0, max_digits=AMOUNT_MAX_DIGITS, decimal_places=AMOUNT_DECIMAL_PLACES, examples=[150.75]),
]

# Amount sent back to the client: Pydantic would write Decimal as a JSON string ("150.75"),
# this serializer makes it a JSON number (150.75) instead
AmountOut = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]





# Request schemas ------------------------------------------------------------------------------------------------------

# POST /transactions; extra="forbid" rejects unknown fields (e.g. a client cannot send its own owner_id)
class TransactionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title
    amount: PositiveAmount
    type: TransactionType
    category: Category
    date: dt.date = Field(default_factory=dt.date.today, description="Defaults to today if omitted")


# PUT /transactions/{transaction_id}: partial update, only the fields that are sent will change
class TransactionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title | None = None
    amount: PositiveAmount | None = None
    type: TransactionType | None = None
    category: Category | None = None
    date: dt.date | None = None

    # Reject an empty body and explicit nulls (the database columns are NOT NULL)
    @model_validator(mode="after")
    def check_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")
        null_fields = [name for name in self.model_fields_set if getattr(self, name) is None]
        if null_fields:
            raise ValueError(f"These fields cannot be null: {', '.join(sorted(null_fields))}")
        return self


# GET /transactions/filter query parameters; all optional, unknown parameters are rejected
class TransactionFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: TransactionType | None = None
    category: Category | None = None
    minimum_amount: Annotated[Decimal, Field(ge=0)] | None = None
    maximum_amount: Annotated[Decimal, Field(ge=0)] | None = None

    # A range like minimum_amount=5000&maximum_amount=100 makes no sense
    @model_validator(mode="after")
    def check_amount_range(self) -> Self:
        if (
            self.minimum_amount is not None
            and self.maximum_amount is not None
            and self.minimum_amount > self.maximum_amount
        ):
            raise ValueError("minimum_amount must not be greater than maximum_amount.")
        return self





# Response schemas -----------------------------------------------------------------------------------------------------

# Transaction data returned in responses
class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    amount: AmountOut
    type: TransactionType
    category: str
    date: dt.date
    owner_id: int





# ----------------------------------------------------------------------------------------------------------------------
