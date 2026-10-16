# External imports -----------------------------------------------------------------------------------------------------
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Internal imports -----------------------------------------------------------------------------------------------------
from src.features.users.models import User
from src.features.users.repository import UserRepository
from tests.conftest import make_user_payload

REGISTER_URL = "/auth/register"





# Success --------------------------------------------------------------------------------------------------------------

async def test_register_creates_user_and_hides_password(client: AsyncClient) -> None:
    payload = make_user_payload(email="ZK_Mixed@Example.COM")

    response = await client.post(REGISTER_URL, json=payload)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "username", "email"}
    assert body["username"] == payload["username"]
    assert body["email"] == "zk_mixed@example.com"


async def test_register_stores_only_an_argon2_hash(client: AsyncClient, db_session: AsyncSession) -> None:
    payload = make_user_payload()
    await client.post(REGISTER_URL, json=payload)

    stored = await db_session.scalar(select(User).where(User.username == payload["username"]))

    assert stored is not None
    assert stored.hashed_password != payload["password"]
    assert stored.hashed_password.startswith("$argon2")





# Duplicates -----------------------------------------------------------------------------------------------------------

async def test_duplicate_username_returns_409(client: AsyncClient) -> None:
    payload = make_user_payload()
    await client.post(REGISTER_URL, json=payload)

    response = await client.post(REGISTER_URL, json=make_user_payload(username=payload["username"]))

    assert response.status_code == 409
    assert response.json()["error_code"] == "USERNAME_ALREADY_EXISTS"


async def test_duplicate_email_in_different_case_returns_409(client: AsyncClient) -> None:
    payload = make_user_payload()
    await client.post(REGISTER_URL, json=payload)

    response = await client.post(REGISTER_URL, json=make_user_payload(email=payload["email"].upper()))

    assert response.status_code == 409
    assert response.json()["error_code"] == "EMAIL_ALREADY_EXISTS"


# Simulates two registrations at the same moment: the early checks miss the duplicate,
# so the database's unique index must stop it and the service must still answer with a clean 409
@pytest.mark.parametrize(
    ("duplicate_field", "expected_code"),
    [("username", "USERNAME_ALREADY_EXISTS"), ("email", "EMAIL_ALREADY_EXISTS")],
)
async def test_race_condition_duplicate_is_caught_by_database(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, duplicate_field: str, expected_code: str
) -> None:
    first = make_user_payload()
    await client.post(REGISTER_URL, json=first)

    async def not_found(self, value):
        return None

    monkeypatch.setattr(UserRepository, "get_by_username", not_found)
    monkeypatch.setattr(UserRepository, "get_by_email", not_found)

    response = await client.post(REGISTER_URL, json=make_user_payload(**{duplicate_field: first[duplicate_field]}))

    assert response.status_code == 409
    assert response.json()["error_code"] == expected_code





# Validation -----------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"password": "Strong Pass123"}, id="password-with-space"),
        pytest.param({"password": "short"}, id="password-too-short"),
        pytest.param({"username": "zk-dev x"}, id="username-invalid-chars"),
        pytest.param({"username": "ab"}, id="username-too-short"),
        pytest.param({"email": "not-an-email"}, id="email-invalid"),
    ],
)
async def test_invalid_registration_returns_422(client: AsyncClient, overrides: dict) -> None:
    response = await client.post(REGISTER_URL, json=make_user_payload(**overrides))
    assert response.status_code == 422


async def test_missing_fields_return_422(client: AsyncClient) -> None:
    response = await client.post(REGISTER_URL, json={"username": "only_name"})
    assert response.status_code == 422
