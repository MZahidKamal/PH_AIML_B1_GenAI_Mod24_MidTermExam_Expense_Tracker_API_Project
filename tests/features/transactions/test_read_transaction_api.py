# External imports -----------------------------------------------------------------------------------------------------
import pytest
from httpx import AsyncClient

# Internal imports -----------------------------------------------------------------------------------------------------
from tests.conftest import AuthUser

URL = "/transactions"





# Get all --------------------------------------------------------------------------------------------------------------

# Exam test: "Get transaction test"
async def test_get_transactions(client: AsyncClient, user: AuthUser, other_user: AuthUser, create_transaction) -> None:
    mine = [await create_transaction(user, title=f"Mine {i}") for i in range(3)]
    await create_transaction(other_user, title="Not mine")

    response = await client.get(URL, headers=user.headers)

    assert response.status_code == 200
    body = response.json()
    assert {item["id"] for item in body} == {item["id"] for item in mine}
    assert all(item["owner_id"] == user.id for item in body)


async def test_new_user_has_no_transactions(client: AsyncClient, user: AuthUser) -> None:
    response = await client.get(URL, headers=user.headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_list_is_sorted_newest_date_first_then_newest_id(
    client: AsyncClient, user: AuthUser, create_transaction
) -> None:
    old = await create_transaction(user, date="2026-09-20")
    new = await create_transaction(user, date="2026-10-03")
    same_day_first = await create_transaction(user, date="2026-10-01")
    same_day_second = await create_transaction(user, date="2026-10-01")

    ids = [item["id"] for item in (await client.get(URL, headers=user.headers)).json()]

    assert ids == [new["id"], same_day_second["id"], same_day_first["id"], old["id"]]


async def test_list_requires_authentication(client: AsyncClient) -> None:
    assert (await client.get(URL)).status_code == 401





# Get one --------------------------------------------------------------------------------------------------------------

# Exam test: "Get specific transaction test"
async def test_get_transaction_by_id(client: AsyncClient, user: AuthUser, create_transaction) -> None:
    created = await create_transaction(user)

    response = await client.get(f"{URL}/{created['id']}", headers=user.headers)

    assert response.status_code == 200
    assert response.json() == created


async def test_get_non_existing_transaction_returns_404(client: AsyncClient, user: AuthUser) -> None:
    response = await client.get(f"{URL}/999999999", headers=user.headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Transaction not found.", "error_code": "TRANSACTION_NOT_FOUND"}


# Another user's transaction looks exactly like a missing one (its existence is not leaked)
async def test_get_other_users_transaction_returns_404(
    client: AsyncClient, user: AuthUser, other_user: AuthUser, create_transaction
) -> None:
    foreign = await create_transaction(other_user)

    response = await client.get(f"{URL}/{foreign['id']}", headers=user.headers)

    assert response.status_code == 404
    assert response.json()["error_code"] == "TRANSACTION_NOT_FOUND"


@pytest.mark.parametrize("bad_id", ["0", "-1", "abc", "1.5"])
async def test_invalid_id_returns_422(client: AsyncClient, user: AuthUser, bad_id: str) -> None:
    assert (await client.get(f"{URL}/{bad_id}", headers=user.headers)).status_code == 422
