# External imports -----------------------------------------------------------------------------------------------------
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Internal imports -----------------------------------------------------------------------------------------------------
from src.core.config import env_settings
from src.features.users.models import User
from tests.conftest import AuthUser

# Any protected route works here; GET /transactions is the simplest one
PROTECTED_URL = "/transactions"





# Tests ----------------------------------------------------------------------------------------------------------------

async def test_valid_access_token_is_accepted(client: AsyncClient, user: AuthUser) -> None:
    assert (await client.get(PROTECTED_URL, headers=user.headers)).status_code == 200


async def test_missing_token_returns_401_with_bearer_challenge(client: AsyncClient) -> None:
    response = await client.get(PROTECTED_URL)

    assert response.status_code == 401
    assert response.json()["error_code"] == "NOT_AUTHENTICATED"
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "authorization",
    [
        pytest.param("Bearer this.is.not-a-token", id="garbage-token"),
        pytest.param("Bearer ", id="empty-token"),
    ],
)
async def test_invalid_tokens_are_rejected(client: AsyncClient, authorization: str) -> None:
    response = await client.get(PROTECTED_URL, headers={"Authorization": authorization})
    assert response.status_code == 401


async def test_wrong_authorization_scheme_is_rejected(client: AsyncClient, user: AuthUser) -> None:
    response = await client.get(PROTECTED_URL, headers={"Authorization": f"Basic {user.access_token}"})
    assert response.status_code == 401
    assert response.json()["error_code"] == "NOT_AUTHENTICATED"


async def test_refresh_token_cannot_be_used_as_access_token(client: AsyncClient, user: AuthUser) -> None:
    response = await client.get(PROTECTED_URL, headers={"Authorization": f"Bearer {user.refresh_token}"})

    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_TOKEN"


async def test_expired_access_token_is_rejected(client: AsyncClient, user: AuthUser) -> None:
    past = datetime.now(UTC) - timedelta(hours=1)
    expired = jwt.encode(
        {"sub": str(user.id), "type": "access", "jti": "x", "iat": past, "exp": past + timedelta(minutes=15)},
        env_settings.secret_key,
        algorithm=env_settings.algorithm,
    )
    response = await client.get(PROTECTED_URL, headers={"Authorization": f"Bearer {expired}"})

    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_TOKEN"


async def test_token_of_a_deleted_user_is_rejected(client: AsyncClient, db_session: AsyncSession, user: AuthUser) -> None:
    await db_session.delete(await db_session.get(User, user.id))
    await db_session.commit()

    response = await client.get(PROTECTED_URL, headers=user.headers)

    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_TOKEN"
