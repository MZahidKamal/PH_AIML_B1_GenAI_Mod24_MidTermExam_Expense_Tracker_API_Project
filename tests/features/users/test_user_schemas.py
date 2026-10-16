# External imports -----------------------------------------------------------------------------------------------------
import pytest
from pydantic import ValidationError

# Internal imports -----------------------------------------------------------------------------------------------------
from src.features.users.schemas import UserBase, UserRead





# Username -------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("username", ["zk_dev", "ZK_Dev_2026", "a" * 50, "abc"])
def test_valid_usernames_are_accepted(username: str) -> None:
    assert UserBase(username=username, email="zk@example.com").username == username


@pytest.mark.parametrize(
    "username",
    [
        pytest.param("ab", id="too-short"),
        pytest.param("a" * 51, id="too-long"),
        pytest.param("zk dev", id="space-inside"),
        pytest.param("zk-dev", id="dash"),
        pytest.param("zk@dev", id="special-char"),
        pytest.param("", id="empty"),
    ],
)
def test_invalid_usernames_are_rejected(username: str) -> None:
    with pytest.raises(ValidationError):
        UserBase(username=username, email="zk@example.com")


def test_username_is_trimmed() -> None:
    assert UserBase(username="  zk_dev  ", email="zk@example.com").username == "zk_dev"





# Email ----------------------------------------------------------------------------------------------------------------

def test_email_is_trimmed_and_lowercased() -> None:
    assert UserBase(username="zk_dev", email="  ZK@Example.COM ").email == "zk@example.com"


@pytest.mark.parametrize("email", ["not-an-email", "zk@", "@example.com", "zk example@x.com", ""])
def test_invalid_emails_are_rejected(email: str) -> None:
    with pytest.raises(ValidationError):
        UserBase(username="zk_dev", email=email)





# Response schema ------------------------------------------------------------------------------------------------------

def test_user_read_never_exposes_password_fields() -> None:
    assert set(UserRead.model_fields) == {"id", "username", "email"}
