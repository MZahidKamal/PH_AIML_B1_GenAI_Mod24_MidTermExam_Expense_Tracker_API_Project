# External imports -----------------------------------------------------------------------------------------------------
import datetime as dt

import pytest
from httpx import AsyncClient

# Internal imports -----------------------------------------------------------------------------------------------------
from tests.conftest import AuthUser

URL = "/transactions"
VALID = {"title": "Groceries", "amount": 150.75, "type": "expense", "category": "Food", "date": "2026-10-01"}





# Success --------------------------------------------------------------------------------------------------------------

# Exam test: "Create transaction test"
async def test_create_transaction(client: AsyncClient, user: AuthUser) -> None:
    response = await client.post(URL, json=VALID, headers=user.headers)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["owner_id"] == user.id
    assert {key: body[key] for key in VALID} == VALID


async def test_create_without_date_uses_today(client: AsyncClient, user: AuthUser) -> None:
    payload = {key: value for key, value in VALID.items() if key != "date"}

    response = await client.post(URL, json=payload, headers=user.headers)

    assert response.status_code == 201
    assert response.json()["date"] == dt.date.today().isoformat()


async def test_create_trims_title_and_category(client: AsyncClient, user: AuthUser) -> None:
    response = await client.post(URL, json=VALID | {"title": "  Groceries  ", "category": " Food "}, headers=user.headers)
    assert (response.json()["title"], response.json()["category"]) == ("Groceries", "Food")


async def test_amount_is_stored_exactly(client: AsyncClient, user: AuthUser) -> None:
    # 0.1 + 0.2 is 0.30000000000000004 with floats; NUMERIC(12, 2) keeps money exact
    response = await client.post(URL, json=VALID | {"amount": "0.30"}, headers=user.headers)
    assert response.json()["amount"] == 0.3


async def test_amount_is_returned_as_a_json_number(client: AsyncClient, user: AuthUser) -> None:
    response = await client.post(URL, json=VALID | {"amount": 5000}, headers=user.headers)
    assert isinstance(response.json()["amount"], (int, float))





# Validation -----------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"amount": 0}, id="amount-zero"),
        pytest.param({"amount": -10}, id="amount-negative"),
        pytest.param({"amount": 1.555}, id="amount-3-decimals"),
        pytest.param({"amount": "abc"}, id="amount-not-a-number"),
        pytest.param({"amount": 10_000_000_000}, id="amount-too-large"),
        pytest.param({"type": "gift"}, id="type-unknown"),
        pytest.param({"type": "Expense"}, id="type-wrong-case"),
        pytest.param({"title": "   "}, id="title-blank"),
        pytest.param({"title": "x" * 101}, id="title-too-long"),
        pytest.param({"category": "x" * 51}, id="category-too-long"),
        pytest.param({"date": "2026-13-40"}, id="date-invalid"),
        pytest.param({"owner_id": 999}, id="owner-id-mass-assignment"),
    ],
)
async def test_invalid_transaction_returns_422(client: AsyncClient, user: AuthUser, overrides: dict) -> None:
    response = await client.post(URL, json=VALID | overrides, headers=user.headers)
    assert response.status_code == 422


async def test_empty_body_returns_422(client: AsyncClient, user: AuthUser) -> None:
    assert (await client.post(URL, json={}, headers=user.headers)).status_code == 422


async def test_create_requires_authentication(client: AsyncClient) -> None:
    assert (await client.post(URL, json=VALID)).status_code == 401
