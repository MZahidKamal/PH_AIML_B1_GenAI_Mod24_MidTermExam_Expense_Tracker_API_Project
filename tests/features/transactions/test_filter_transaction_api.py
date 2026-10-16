# External imports -----------------------------------------------------------------------------------------------------
import pytest
import pytest_asyncio
from httpx import AsyncClient

# Internal imports -----------------------------------------------------------------------------------------------------
from tests.conftest import AuthUser

URL = "/transactions/filter"





# Shared data ----------------------------------------------------------------------------------------------------------

# Four transactions with different types, categories (and letter cases) and amounts
@pytest_asyncio.fixture
async def sample(user: AuthUser, create_transaction) -> AuthUser:
    await create_transaction(user, title="Groceries", amount=150.75, type="expense", category="Food", date="2026-10-01")
    await create_transaction(user, title="Salary", amount=5000, type="income", category="Salary", date="2026-10-02")
    await create_transaction(user, title="Rent", amount=1200, type="expense", category="rent", date="2026-10-03")
    await create_transaction(user, title="Pizza", amount=45.50, type="expense", category="FOOD", date="2026-09-20")
    return user


async def titles(client: AsyncClient, owner: AuthUser, query: str) -> set[str]:
    response = await client.get(f"{URL}?{query}" if query else URL, headers=owner.headers)
    assert response.status_code == 200, response.text
    return {item["title"] for item in response.json()}





# Tests ----------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("query", "expected"),
    [
        pytest.param("type=expense&category=Food", {"Groceries", "Pizza"}, id="exam-example"),
        pytest.param("category=food", {"Groceries", "Pizza"}, id="category-case-insensitive"),
        pytest.param("category=FOOD", {"Groceries", "Pizza"}, id="category-uppercase"),
        pytest.param("type=income", {"Salary"}, id="type-income"),
        pytest.param("type=expense", {"Groceries", "Rent", "Pizza"}, id="type-expense"),
        pytest.param("minimum_amount=100", {"Groceries", "Salary", "Rent"}, id="minimum-only"),
        pytest.param("maximum_amount=1200", {"Groceries", "Rent", "Pizza"}, id="maximum-only-inclusive"),
        pytest.param("minimum_amount=100&maximum_amount=5000", {"Groceries", "Salary", "Rent"}, id="range-inclusive"),
        pytest.param("minimum_amount=1200&maximum_amount=1200", {"Rent"}, id="exact-amount"),
        pytest.param(
            "type=expense&category=Food&minimum_amount=100&maximum_amount=5000", {"Groceries"}, id="all-filters"
        ),
        pytest.param("category=Travel", set(), id="no-match"),
        pytest.param("", {"Groceries", "Salary", "Rent", "Pizza"}, id="no-filters"),
    ],
)
async def test_filter(client: AsyncClient, sample: AuthUser, query: str, expected: set[str]) -> None:
    assert await titles(client, sample, query) == expected


async def test_filter_result_is_sorted_newest_first(client: AsyncClient, sample: AuthUser) -> None:
    response = await client.get(f"{URL}?type=expense", headers=sample.headers)
    dates = [item["date"] for item in response.json()]
    assert dates == sorted(dates, reverse=True)


async def test_filter_only_returns_own_transactions(
    client: AsyncClient, sample: AuthUser, other_user: AuthUser, create_transaction
) -> None:
    await create_transaction(other_user, title="Other's lunch", category="Food")

    assert await titles(client, other_user, "category=Food") == {"Other's lunch"}
    assert "Other's lunch" not in await titles(client, sample, "category=Food")


@pytest.mark.parametrize(
    "query",
    [
        pytest.param("minimum_amount=5000&maximum_amount=100", id="min-greater-than-max"),
        pytest.param("type=gift", id="unknown-type"),
        pytest.param("minimum_amount=-1", id="negative-minimum"),
        pytest.param("minimum_amount=abc", id="non-numeric-minimum"),
        pytest.param("min_amount=100", id="misspelled-parameter"),
    ],
)
async def test_invalid_filter_returns_422(client: AsyncClient, user: AuthUser, query: str) -> None:
    assert (await client.get(f"{URL}?{query}", headers=user.headers)).status_code == 422


async def test_filter_requires_authentication(client: AsyncClient) -> None:
    assert (await client.get(f"{URL}?type=expense")).status_code == 401
