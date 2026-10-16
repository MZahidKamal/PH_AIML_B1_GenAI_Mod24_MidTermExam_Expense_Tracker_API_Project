# External imports -----------------------------------------------------------------------------------------------------
from fastapi import status

# Internal imports -----------------------------------------------------------------------------------------------------
from src.core.exceptions import AppException
from src.features.users import constants





# User-specific exceptions ---------------------------------------------------------------------------------------------

class UserNotFound(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = constants.USER_NOT_FOUND
    message = "User not found."


class UsernameAlreadyExists(AppException):
    status_code = status.HTTP_409_CONFLICT
    error_code = constants.USERNAME_ALREADY_EXISTS
    message = "This username is already taken."


class EmailNotFound(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = constants.EMAIL_NOT_FOUND
    message = "Email not found."


class EmailAlreadyExists(AppException):
    status_code = status.HTTP_409_CONFLICT
    error_code = constants.EMAIL_ALREADY_EXISTS
    message = "This email is already registered."





# ----------------------------------------------------------------------------------------------------------------------
