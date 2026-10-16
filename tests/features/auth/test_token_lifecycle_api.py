# External imports -----------------------------------------------------------------------------------------------------
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Internal imports -----------------------------------------------------------------------------------------------------
from src.core import security
from src.features.auth.models import RefreshToken
from tests.conftest import AuthUser

REFRESH_URL = "/auth/refresh"
LOGOUT_URL = "/auth/logout"





# Helpers --------------------------------------------------------------------------------------------------------------

async def refresh(client: AsyncClient, refresh_token: str):
    return await client.post(REFRESH_URL, json={"refresh_token": refresh_token})


async def stored_token(db_session: AsyncSession, refresh_token: str) -> RefreshToken | None:
    jti = security.decode_token(refresh_token, security.TOKEN_TYPE_REFRESH)["jti"]
    db_session.expire_all()  # always read the latest state from the database
    return await db_session.scalar(select(RefreshToken).where(RefreshToken.jti == jti))





# Refresh + rotation ---------------------------------------------------------------------------------------------------

async def test_refresh_returns_a_new_pair_and_revokes_the_old_token(
    client: AsyncClient, db_session: AsyncSession, user: AuthUser
) -> None:
    response = await refresh(client, user.refresh_token)

    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["refresh_token"] != user.refresh_token
    assert (await stored_token(db_session, user.refresh_token)).revoked is True
    assert (await stored_token(db_session, new_tokens["refresh_token"])).revoked is False


async def test_new_access_token_works(client: AsyncClient, user: AuthUser) -> None:
    new_access = (await refresh(client, user.refresh_token)).json()["access_token"]
    response = await client.get("/transactions", headers={"Authorization": f"Bearer {new_access}"})
    assert response.status_code == 200


@pytest.mark.parametrize("bad_token", ["this.is.not-a-token", ""])
async def test_refresh_with_invalid_token_returns_401_or_422(client: AsyncClient, bad_token: str) -> None:
    response = await refresh(client, bad_token)
    # An empty string fails schema validation (422); a malformed token fails JWT validation (401)
    assert response.status_code == (422 if bad_token == "" else 401)


async def test_access_token_cannot_be_used_to_refresh(client: AsyncClient, user: AuthUser) -> None:
    response = await refresh(client, user.access_token)

    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_TOKEN"





# Reuse detection ------------------------------------------------------------------------------------------------------

async def test_reusing_a_rotated_token_revokes_every_session(
    client: AsyncClient, db_session: AsyncSession, user: AuthUser
) -> None:
    newest = (await refresh(client, user.refresh_token)).json()["refresh_token"]

    reuse = await refresh(client, user.refresh_token)

    assert reuse.status_code == 401
    assert reuse.json()["error_code"] == "REFRESH_TOKEN_REUSED"
    db_session.expire_all()
    tokens = (await db_session.scalars(select(RefreshToken).where(RefreshToken.user_id == user.id))).all()
    assert tokens and all(token.revoked for token in tokens)

    # Even the newest token is dead now: the real user must log in again
    assert (await refresh(client, newest)).json()["error_code"] == "REFRESH_TOKEN_REUSED"





# Logout ---------------------------------------------------------------------------------------------------------------

async def test_logout_revokes_the_refresh_token(client: AsyncClient, db_session: AsyncSession, user: AuthUser) -> None:
    response = await client.post(LOGOUT_URL, json={"refresh_token": user.refresh_token})

    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully."}
    assert (await stored_token(db_session, user.refresh_token)).revoked is True


async def test_logout_is_idempotent(client: AsyncClient, user: AuthUser) -> None:
    first = await client.post(LOGOUT_URL, json={"refresh_token": user.refresh_token})
    second = await client.post(LOGOUT_URL, json={"refresh_token": user.refresh_token})
    assert first.status_code == second.status_code == 200


async def test_refresh_after_logout_is_rejected(client: AsyncClient, user: AuthUser) -> None:
    await client.post(LOGOUT_URL, json={"refresh_token": user.refresh_token})

    response = await refresh(client, user.refresh_token)

    assert response.status_code == 401
    assert response.json()["error_code"] == "REFRESH_TOKEN_REUSED"


async def test_logout_with_invalid_token_returns_401(client: AsyncClient) -> None:
    response = await client.post(LOGOUT_URL, json={"refresh_token": "this.is.not-a-token"})
    assert response.status_code == 401


# Documents a known, accepted limitation: access tokens are stateless and live until they expire
async def test_access_token_still_works_after_logout_until_it_expires(client: AsyncClient, user: AuthUser) -> None:
    await client.post(LOGOUT_URL, json={"refresh_token": user.refresh_token})
    assert (await client.get("/transactions", headers=user.headers)).status_code == 200
