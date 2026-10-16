# External imports -----------------------------------------------------------------------------------------------------
from httpx import AsyncClient

# Internal imports -----------------------------------------------------------------------------------------------------
from tests.conftest import AuthUser

URL = "/transactions"





# Success --------------------------------------------------------------------------------------------------------------

# Exam test: "Delete transaction test"
async def test_delete_transaction(client: AsyncClient, user: AuthUser, create_transaction) -> None:
    created = await create_transaction(user)

    response = await client.delete(f"{URL}/{created['id']}", headers=user.headers)

    assert response.status_code == 200
    assert response.json() == {"message": f"Transaction {created['id']} deleted successfully."}
    assert (await client.get(f"{URL}/{created['id']}", headers=user.headers)).status_code == 404


async def test_delete_removes_only_that_transaction(client: AsyncClient, user: AuthUser, create_transaction) -> None:
    keep = await create_transaction(user, title="Keep")
    remove = await create_transaction(user, title="Remove")

    await client.delete(f"{URL}/{remove['id']}", headers=user.headers)

    remaining = (await client.get(URL, headers=user.headers)).json()
    assert [item["id"] for item in remaining] == [keep["id"]]





# Failures -------------------------------------------------------------------------------------------------------------

async def test_delete_twice_returns_404(client: AsyncClient, user: AuthUser, create_transaction) -> None:
    created = await create_transaction(user)
    await client.delete(f"{URL}/{created['id']}", headers=user.headers)

    response = await client.delete(f"{URL}/{created['id']}", headers=user.headers)

    assert response.status_code == 404
    assert response.json()["error_code"] == "TRANSACTION_NOT_FOUND"


async def test_cannot_delete_other_users_transaction(
    client: AsyncClient, user: AuthUser, other_user: AuthUser, create_transaction
) -> None:
    foreign = await create_transaction(other_user)

    response = await client.delete(f"{URL}/{foreign['id']}", headers=user.headers)

    assert response.status_code == 404
    assert (await client.get(f"{URL}/{foreign['id']}", headers=other_user.headers)).status_code == 200


async def test_delete_requires_authentication(client: AsyncClient) -> None:
    assert (await client.delete(f"{URL}/1")).status_code == 401
