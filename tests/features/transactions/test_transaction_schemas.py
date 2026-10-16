# External imports -----------------------------------------------------------------------------------------------------
import datetime as dt
from decimal import Decimal

import pytest
from pydantic import ValidationError

# Internal imports -----------------------------------------------------------------------------------------------------
from src.features.transactions.constants import TransactionType
from src.features.transactions.schemas import TransactionCreate, TransactionFilter, TransactionRead, TransactionUpdate





# Helper ---------------------------------------------------------------------------------------------------------------

def create(**overrides) -> TransactionCreate:
    payload = {"title": "Groceries", "amount": "150.75", "type": "expense", "category": "Food", "date": "2026-10-01"}
    payload.update(overrides)
    return TransactionCreate(**payload)





# Create ---------------------------------------------------------------------------------------------------------------

def test_valid_transaction_is_parsed_into_exact_types() -> None:
    data = create()
    assert data.amount == Decimal("150.75")
    assert data.type is TransactionType.EXPENSE
    assert data.date == dt.date(2026, 10, 1)


def test_date_defaults_to_today() -> None:
    payload = {"title": "Salary", "amount": 5000, "type": "income", "category": "Salary"}
    assert TransactionCreate(**payload).date == dt.date.today()


def test_title_and_category_are_trimmed() -> None:
    data = create(title="  Groceries  ", category="  Food ")
    assert (data.title, data.category) == ("Groceries", "Food")


@pytest.mark.parametrize("amount", ["0.01", "1", "150.75", "9999999999.99"])
def test_valid_amounts_are_accepted(amount: str) -> None:
    assert create(amount=amount).amount == Decimal(amount)


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"amount": 0}, id="amount-zero"),
        pytest.param({"amount": -10}, id="amount-negative"),
        pytest.param({"amount": "1.555"}, id="amount-3-decimals"),
        pytest.param({"amount": "10000000000.00"}, id="amount-too-large"),
        pytest.param({"amount": "abc"}, id="amount-not-a-number"),
        pytest.param({"type": "gift"}, id="type-unknown"),
        pytest.param({"type": "Expense"}, id="type-wrong-case"),
        pytest.param({"title": "   "}, id="title-blank"),
        pytest.param({"title": "x" * 101}, id="title-too-long"),
        pytest.param({"category": ""}, id="category-empty"),
        pytest.param({"category": "x" * 51}, id="category-too-long"),
        pytest.param({"date": "2026-13-40"}, id="date-invalid"),
        pytest.param({"owner_id": 2}, id="owner-id-forbidden"),
    ],
)
def test_invalid_transactions_are_rejected(overrides: dict) -> None:
    with pytest.raises(ValidationError):
        create(**overrides)





# Update ---------------------------------------------------------------------------------------------------------------

def test_update_keeps_track_of_only_the_sent_fields() -> None:
    data = TransactionUpdate(amount="99.90")
    assert data.model_dump(exclude_unset=True) == {"amount": Decimal("99.90")}


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({}, id="empty"),
        pytest.param({"title": None}, id="null-title"),
        pytest.param({"amount": None, "title": "x"}, id="null-amount"),
        pytest.param({"amount": -1}, id="negative-amount"),
        pytest.param({"owner_id": 2}, id="owner-id-forbidden"),
    ],
)
def test_invalid_updates_are_rejected(payload: dict) -> None:
    with pytest.raises(ValidationError):
        TransactionUpdate(**payload)





# Filter ---------------------------------------------------------------------------------------------------------------

def test_filter_accepts_equal_minimum_and_maximum() -> None:
    assert TransactionFilter(minimum_amount=100, maximum_amount=100).minimum_amount == 100


@pytest.mark.parametrize(
    "params",
    [
        pytest.param({"minimum_amount": 5000, "maximum_amount": 100}, id="min-greater-than-max"),
        pytest.param({"minimum_amount": -1}, id="negative-minimum"),
        pytest.param({"type": "gift"}, id="unknown-type"),
        pytest.param({"min_amount": 1}, id="misspelled-parameter"),
    ],
)
def test_invalid_filters_are_rejected(params: dict) -> None:
    with pytest.raises(ValidationError):
        TransactionFilter(**params)





# Response -------------------------------------------------------------------------------------------------------------

def test_amount_is_serialized_as_a_json_number_not_a_string() -> None:
    data = TransactionRead(
        id=1, title="t", amount=Decimal("150.75"), type="expense", category="c", date=dt.date(2026, 1, 1), owner_id=1
    )
    assert '"amount":150.75' in data.model_dump_json()
