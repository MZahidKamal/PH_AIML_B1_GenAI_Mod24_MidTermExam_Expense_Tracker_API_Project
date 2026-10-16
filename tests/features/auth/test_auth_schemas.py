# External imports -----------------------------------------------------------------------------------------------------
import pytest
from pydantic import ValidationError

# Internal imports -----------------------------------------------------------------------------------------------------
from src.features.auth.schemas import LoginRequest, RegisterRequest, TokenResponse





# Helper ---------------------------------------------------------------------------------------------------------------

def register(password: str) -> RegisterRequest:
    return RegisterRequest(username="zk_dev", email="zk@example.com", password=password)





# Register: password rules ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("password", ["StrongPass123", "12345678", "a" * 128, "Pässwörd!#%"])
def test_valid_passwords_are_accepted(password: str) -> None:
    assert register(password).password == password


@pytest.mark.parametrize(
    "password",
    [
        pytest.param(" StrongPass123", id="space-at-start"),
        pytest.param("StrongPass123 ", id="space-at-end"),
        pytest.param("Strong Pass123", id="space-in-middle"),
        pytest.param("Strong\tPass123", id="tab"),
        pytest.param("Strong\nPass123", id="newline"),
        pytest.param("short", id="too-short"),
        pytest.param("a" * 129, id="too-long"),
    ],
)
def test_invalid_passwords_are_rejected(password: str) -> None:
    with pytest.raises(ValidationError):
        register(password)


def test_register_inherits_username_and_email_rules() -> None:
    data = RegisterRequest(username="  zk_dev ", email=" ZK@Example.com ", password="StrongPass123")
    assert (data.username, data.email) == ("zk_dev", "zk@example.com")





# Login ----------------------------------------------------------------------------------------------------------------

def test_login_trims_the_username() -> None:
    assert LoginRequest(username="  zk_dev  ", password="x").username == "zk_dev"


@pytest.mark.parametrize("payload", [{"username": "", "password": "x"}, {"username": "zk", "password": ""}, {}])
def test_login_rejects_empty_or_missing_fields(payload: dict) -> None:
    with pytest.raises(ValidationError):
        LoginRequest(**payload)





# Token response -------------------------------------------------------------------------------------------------------

def test_token_type_defaults_to_bearer() -> None:
    assert TokenResponse(access_token="a", refresh_token="r", expires_in=900).token_type == "bearer"
