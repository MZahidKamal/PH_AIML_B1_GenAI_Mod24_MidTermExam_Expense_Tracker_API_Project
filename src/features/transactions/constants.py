# External imports -----------------------------------------------------------------------------------------------------
from enum import StrEnum





# Transaction type -----------------------------------------------------------------------------------------------------

# The only two allowed values for a transaction's type; StrEnum members behave like normal strings
class TransactionType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"


# Field length limits (shared by the SQLAlchemy model and the Pydantic schemas) ----------------------------------------
TITLE_MAX_LENGTH = 100
CATEGORY_MAX_LENGTH = 50
TYPE_MAX_LENGTH = 10

# Amount precision: up to 12 digits in total, 2 of them after the decimal point (max 9,999,999,999.99)
AMOUNT_MAX_DIGITS = 12
AMOUNT_DECIMAL_PLACES = 2


# Error codes returned in error responses ------------------------------------------------------------------------------
TRANSACTION_NOT_FOUND = "TRANSACTION_NOT_FOUND"





# ----------------------------------------------------------------------------------------------------------------------
