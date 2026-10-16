# External imports -----------------------------------------------------------------------------------------------------
from fastapi import Request, status
from fastapi.responses import JSONResponse





# Base exception -------------------------------------------------------------------------------------------------------

# Every feature-specific exception inherits from this; the global handler turns it into a JSON error response
class AppException(Exception):
    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "APP_ERROR"
    message: str = "An application error occurred."
    headers: dict[str, str] | None = None

    def __init__(self, message: str | None = None) -> None:
        # Use a custom message if given, otherwise the class default message
        self.message = message or self.message
        super().__init__(self.message)





# Global exception handler ---------------------------------------------------------------------------------------------

# Convert any AppException into a consistent JSON error response (with optional HTTP headers).
# The parameter is typed as Exception to match Starlette's expected handler signature;
# at runtime Starlette only calls this handler with AppException (and its subclasses).
async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    app_exc = exc if isinstance(exc, AppException) else AppException()

    return JSONResponse(
        status_code=app_exc.status_code,
        content={"detail": app_exc.message, "error_code": app_exc.error_code},
        headers=app_exc.headers,
    )





# ----------------------------------------------------------------------------------------------------------------------
