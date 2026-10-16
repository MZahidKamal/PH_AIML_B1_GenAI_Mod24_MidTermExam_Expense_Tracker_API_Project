# External imports -----------------------------------------------------------------------------------------------------
from fastapi import status

# Internal imports -----------------------------------------------------------------------------------------------------
from src.core.exceptions import AppException
from src.features.transactions import constants





# Transaction-specific exceptions --------------------------------------------------------------------------------------

# Raised both when the id does not exist AND when it belongs to another user (so other users' ids stay hidden)
class TransactionNotFound(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = constants.TRANSACTION_NOT_FOUND
    message = "Transaction not found."




# ----------------------------------------------------------------------------------------------------------------------
