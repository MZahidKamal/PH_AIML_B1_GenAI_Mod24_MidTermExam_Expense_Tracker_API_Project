# External imports -----------------------------------------------------------------------------------------------------
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi.concurrency import run_in_threadpool

# Internal imports -----------------------------------------------------------------------------------------------------
from src.core.config import env_settings





# Password hashing (Argon2) --------------------------------------------------------------------------------------------

# One shared hasher instance with argon2-cffi's secure default parameters
_password_hasher = PasswordHasher()

# Pre-computed hash used when a username does not exist, so a failed login always takes about the same time
_DUMMY_PASSWORD_HASH = _password_hasher.hash("dummy-password-used-only-for-timing-protection")


# Synchronous verify helper: to verify password and handle exceptions safely, returns True/False instead of raising
def _verify_password_sync(hashed_password: str, plain_password: str) -> bool:
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


# Hash a password asynchronously in a worker thread, so the CPU-heavy hashing does not block the async event loop
async def hash_password(plain_password: str) -> str:
    return await run_in_threadpool(_password_hasher.hash, plain_password)


# Verify a password asynchronously against its hash in a worker thread
async def verify_password(hashed_password: str, plain_password: str) -> bool:
    return await run_in_threadpool(_verify_password_sync, hashed_password, plain_password)


# Run a fake verification (used when the user does not exist) to prevent username discovery by timing attacks
async def verify_dummy_password(plain_password: str) -> None:
    await run_in_threadpool(_verify_password_sync, _DUMMY_PASSWORD_HASH, plain_password)





# JWT tokens (PyJWT) ---------------------------------------------------------------------------------------------------

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

# Claims every token must contain all of these mentioned below; otherwise decoding fails if any is missing
_REQUIRED_CLAIMS = ["sub", "type", "jti", "iat", "exp"]


# Build and sign a token; returns (token, jti, expires_at)
def _create_token(user_id: int, token_type: str, expires_delta: timedelta) -> tuple[str, str, datetime]:
    issued_at = datetime.now(UTC)
    expires_at = issued_at + expires_delta
    jti = uuid4().hex

    payload = {
        "sub": str(user_id),    # subject: whose token this is (must be a string)
        "type": token_type,     # access or refresh
        "jti": jti,             # unique token id
        "iat": issued_at,       # issued at
        "exp": expires_at,      # expiry time
    }
    token = jwt.encode(payload, env_settings.secret_key, algorithm=env_settings.algorithm)
    return token, jti, expires_at


# Short-lived token sent with every protected request
def create_access_token(user_id: int) -> str:
    token, _, _ = _create_token(
        user_id, TOKEN_TYPE_ACCESS, timedelta(minutes=env_settings.access_token_expire_minutes)
    )
    return token


# Long-lived token used only to get a new token pair; its jti and expiry are stored in the database
def create_refresh_token(user_id: int) -> tuple[str, str, datetime]:
    return _create_token(
        user_id, TOKEN_TYPE_REFRESH, timedelta(days=env_settings.refresh_token_expire_days)
    )


# Verify signature, expiry, required claims and token type; raises jwt.InvalidTokenError on any problem
def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    payload = jwt.decode(
        token,
        env_settings.secret_key,
        algorithms=[env_settings.algorithm],
        options={"require": _REQUIRED_CLAIMS},
    )
    if payload["type"] != expected_type:
        raise jwt.InvalidTokenError("Unexpected token type.")
    return payload





# ----------------------------------------------------------------------------------------------------------------------
