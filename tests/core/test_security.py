# External imports -----------------------------------------------------------------------------------------------------
from datetime import UTC, datetime, timedelta

import jwt
import pytest

# Internal imports -----------------------------------------------------------------------------------------------------
from src.core import security
from src.core.config import env_settings





# Helper ---------------------------------------------------------------------------------------------------------------

# Build a token by hand, so tests can create expired, tampered or incomplete tokens
def make_token(*, secret: str | None = None, algorithm: str | None = None, **claims) -> str:
    now = datetime.now(UTC)
    payload = {"sub": "1", "type": security.TOKEN_TYPE_ACCESS, "jti": "abc", "iat": now, "exp": now + timedelta(minutes=5)}
    payload.update(claims)
    payload = {key: value for key, value in payload.items() if value is not None}
    return jwt.encode(payload, secret or env_settings.secret_key, algorithm=algorithm or env_settings.algorithm)





# Password hashing -----------------------------------------------------------------------------------------------------

async def test_hash_password_returns_argon2_hash_not_plain_text() -> None:
    hashed = await security.hash_password("StrongPass123")
    assert hashed != "StrongPass123"
    assert hashed.startswith("$argon2")


async def test_same_password_gets_a_different_hash_each_time() -> None:
    # A random salt is added every time, so equal passwords never produce equal hashes
    assert await security.hash_password("StrongPass123") != await security.hash_password("StrongPass123")


async def test_verify_password_accepts_correct_and_rejects_wrong_password() -> None:
    hashed = await security.hash_password("StrongPass123")
    assert await security.verify_password(hashed, "StrongPass123") is True
    assert await security.verify_password(hashed, "WrongPass123") is False


async def test_verify_password_returns_false_for_a_broken_hash() -> None:
    assert await security.verify_password("not-a-real-hash", "StrongPass123") is False





# Token creation -------------------------------------------------------------------------------------------------------

def test_access_token_contains_all_required_claims() -> None:
    payload = security.decode_token(security.create_access_token(42), security.TOKEN_TYPE_ACCESS)

    assert payload["sub"] == "42"
    assert payload["type"] == security.TOKEN_TYPE_ACCESS
    assert payload["jti"]
    assert payload["exp"] - payload["iat"] == env_settings.access_token_expire_minutes * 60


def test_refresh_token_returns_its_jti_and_expiry() -> None:
    token, jti, expires_at = security.create_refresh_token(42)
    payload = security.decode_token(token, security.TOKEN_TYPE_REFRESH)

    assert payload["jti"] == jti
    assert payload["exp"] == int(expires_at.timestamp())
    assert expires_at - datetime.now(UTC) > timedelta(days=env_settings.refresh_token_expire_days) - timedelta(minutes=1)


def test_every_token_gets_a_unique_jti() -> None:
    first = security.decode_token(security.create_access_token(1), security.TOKEN_TYPE_ACCESS)
    second = security.decode_token(security.create_access_token(1), security.TOKEN_TYPE_ACCESS)
    assert first["jti"] != second["jti"]





# Token decoding (every way a token can be bad) ------------------------------------------------------------------------

def test_decode_rejects_a_token_of_the_wrong_type() -> None:
    refresh_token, _, _ = security.create_refresh_token(1)
    with pytest.raises(jwt.InvalidTokenError):
        security.decode_token(refresh_token, security.TOKEN_TYPE_ACCESS)


def test_decode_rejects_an_expired_token() -> None:
    expired = make_token(exp=datetime.now(UTC) - timedelta(seconds=1))
    with pytest.raises(jwt.ExpiredSignatureError):
        security.decode_token(expired, security.TOKEN_TYPE_ACCESS)


def test_decode_rejects_a_token_signed_with_another_secret() -> None:
    forged = make_token(secret="an-attackers-secret-key-that-is-long-enough-for-hs256")
    with pytest.raises(jwt.InvalidSignatureError):
        security.decode_token(forged, security.TOKEN_TYPE_ACCESS)


def test_decode_rejects_a_tampered_token() -> None:
    header, payload, signature = security.create_access_token(1).split(".")
    tampered = ".".join([header, payload[:-2] + ("AA" if payload[-2:] != "AA" else "BB"), signature])
    with pytest.raises(jwt.InvalidTokenError):
        security.decode_token(tampered, security.TOKEN_TYPE_ACCESS)


@pytest.mark.parametrize("missing_claim", ["sub", "type", "jti", "iat", "exp"])
def test_decode_rejects_a_token_with_a_missing_claim(missing_claim: str) -> None:
    incomplete = make_token(**{missing_claim: None})
    with pytest.raises(jwt.InvalidTokenError):
        security.decode_token(incomplete, security.TOKEN_TYPE_ACCESS)


def test_decode_rejects_an_unsigned_none_algorithm_token() -> None:
    now = datetime.now(UTC)
    unsigned = jwt.encode(
        {"sub": "1", "type": "access", "jti": "x", "iat": now, "exp": now + timedelta(minutes=5)}, key=None, algorithm="none"
    )
    with pytest.raises(jwt.InvalidTokenError):
        security.decode_token(unsigned, security.TOKEN_TYPE_ACCESS)


@pytest.mark.parametrize("garbage", ["", "abc", "a.b.c", "this.is.not-a-token"])
def test_decode_rejects_garbage(garbage: str) -> None:
    with pytest.raises(jwt.InvalidTokenError):
        security.decode_token(garbage, security.TOKEN_TYPE_ACCESS)
