# External imports -----------------------------------------------------------------------------------------------------
from fastapi import status

# Internal imports -----------------------------------------------------------------------------------------------------
from src.core.exceptions import AppException
from src.features.auth import constants

# HTTP standard header for 401 responses: tells the client to authenticate with a Bearer token
_BEARER_CHALLENGE = {"WWW-Authenticate": "Bearer"}





# Auth-specific exceptions ---------------------------------------------------------------------------------------------

class InvalidCredentials(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = constants.INVALID_CREDENTIALS
    message = "Incorrect username or password."
    headers = _BEARER_CHALLENGE


class NotAuthenticated(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = constants.NOT_AUTHENTICATED
    message = "Not authenticated."
    headers = _BEARER_CHALLENGE


class InvalidToken(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = constants.INVALID_TOKEN
    message = "Invalid or expired token."
    headers = _BEARER_CHALLENGE


class RefreshTokenReused(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = constants.REFRESH_TOKEN_REUSED
    message = "Refresh token reuse detected. All sessions have been revoked. Please log in again."
    headers = _BEARER_CHALLENGE





#-----------------------------------------------------------------------------------------------------------------------
