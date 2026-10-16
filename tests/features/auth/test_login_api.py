# External imports -----------------------------------------------------------------------------------------------------
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Internal imports -----------------------------------------------------------------------------------------------------
from src.core import security
from src.core.config import env_settings
from src.features.auth.models import RefreshToken
from tests.conftest import AuthUser

LOGIN_URL = "/auth/login"





# Success --------------------------------------------------------------------------------------------------------------

async def test_login_returns_token_pair(client: AsyncClient, user: AuthUser) -> None:
    response = await client.post(LOGIN_URL, json={"username": user.username, "password": user.password})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == env_settings.access_token_expire_minutes * 60
    assert security.decode_token(body["access_token"], security.TOKEN_TYPE_ACCESS)["sub"] == str(user.id)
    assert security.decode_token(body["refresh_token"], security.TOKEN_TYPE_REFRESH)["sub"] == str(user.id)


async def test_login_stores_refresh_token_jti_in_database(
    client: AsyncClient, db_session: AsyncSession, user: AuthUser
) -> None:
    jti = security.decode_token(user.refresh_token, security.TOKEN_TYPE_REFRESH)["jti"]

    stored = await db_session.scalar(select(RefreshToken).where(RefreshToken.jti == jti))

    assert stored is not None
    assert stored.user_id == user.id
    assert stored.revoked is False


async def test_login_trims_spaces_around_username(client: AsyncClient, user: AuthUser) -> None:
    response = await client.post(LOGIN_URL, json={"username": f"  {user.username}  ", "password": user.password})
    assert response.status_code == 200





# Failures -------------------------------------------------------------------------------------------------------------

async def test_wrong_password_returns_401(client: AsyncClient, user: AuthUser) -> None:
    response = await client.post(LOGIN_URL, json={"username": user.username, "password": "WrongPass123"})

    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_CREDENTIALS"
    assert response.headers["WWW-Authenticate"] == "Bearer"


async def test_unknown_user_gets_exactly_the_same_answer_as_wrong_password(client: AsyncClient, user: AuthUser) -> None:
    wrong_password = await client.post(LOGIN_URL, json={"username": user.username, "password": "WrongPass123"})
    unknown_user = await client.post(LOGIN_URL, json={"username": "nobody_here", "password": "WrongPass123"})

    assert unknown_user.status_code == wrong_password.status_code == 401
    assert unknown_user.json() == wrong_password.json()


async def test_missing_fields_return_422(client: AsyncClient) -> None:
    assert (await client.post(LOGIN_URL, json={})).status_code == 422
