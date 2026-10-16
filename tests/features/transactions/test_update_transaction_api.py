# External imports -----------------------------------------------------------------------------------------------------
import pytest
from httpx import AsyncClient

# Internal imports -----------------------------------------------------------------------------------------------------
from tests.conftest import AuthUser

URL = "/transactions"





# Success --------------------------------------------------------------------------------------------------------------

# Exam test: "Update transaction test"
async def test_update_transaction(client: AsyncClient, user: AuthUser, create_transaction) -> None:
    created = await create_transaction(user)
    changes = {"title": "Weekly groceries", "amount": 99.90, "type": "expense", "category": "Household", "date": "2026-10-05"}

    response = await client.put(f"{URL}/{created['id']}", json=changes, headers=user.headers)

    assert response.status_code == 200
    assert response.json() == created | changes


async def test_partial_update_changes_only_the_sent_fields(
    client: AsyncClient, user: AuthUser, create_transaction
) -> None:
    created = await create_transaction(user)

    response = await client.put(f"{URL}/{created['id']}", json={"amount": 99.9}, headers=user.headers)

    assert response.status_code == 200
    assert response.json() == created | {"amount": 99.9}


async def test_update_is_persisted(client: AsyncClient, user: AuthUser, create_transaction) -> None:
    created = await create_transaction(user)
    await client.put(f"{URL}/{created['id']}", json={"title": "Changed"}, headers=user.headers)

    response = await client.get(f"{URL}/{created['id']}", headers=user.headers)

    assert response.json()["title"] == "Changed"





# Failures -------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({}, id="empty-body"),
        pytest.param({"title": None}, id="null-value"),
        pytest.param({"amount": -5}, id="negative-amount"),
        pytest.param({"type": "gift"}, id="unknown-type"),
        pytest.param({"owner_id": 999}, id="owner-id-change"),
    ],
)
async def test_invalid_update_returns_422(client: AsyncClient, user: AuthUser, create_transaction, payload: dict) -> None:
    created = await create_transaction(user)
    assert (await client.put(f"{URL}/{created['id']}", json=payload, headers=user.headers)).status_code == 422


async def test_update_non_existing_transaction_returns_404(client: AsyncClient, user: AuthUser) -> None:
    response = await client.put(f"{URL}/999999999", json={"amount": 1}, headers=user.headers)

    assert response.status_code == 404
    assert response.json()["error_code"] == "TRANSACTION_NOT_FOUND"


async def test_cannot_update_other_users_transaction(
    client: AsyncClient, user: AuthUser, other_user: AuthUser, create_transaction
) -> None:
    foreign = await create_transaction(other_user, amount=20)

    response = await client.put(f"{URL}/{foreign['id']}", json={"amount": 1}, headers=user.headers)

    assert response.status_code == 404
    unchanged = await client.get(f"{URL}/{foreign['id']}", headers=other_user.headers)
    assert unchanged.json()["amount"] == 20


async def test_update_requires_authentication(client: AsyncClient) -> None:
    assert (await client.put(f"{URL}/1", json={"amount": 1})).status_code == 401
