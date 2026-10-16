# External imports -----------------------------------------------------------------------------------------------------
from typing import Annotated
from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, StringConstraints, BeforeValidator

# Internal imports -----------------------------------------------------------------------------------------------------
from src.features.users.constants import (
    USERNAME_MIN_LENGTH,
    USERNAME_MAX_LENGTH,
    USERNAME_PATTERN,
    EMAIL_MIN_LENGTH,
    EMAIL_MAX_LENGTH,
)





# Helper ---------------------------------------------------------------------------------------------------------------

# Remove leading/trailing spaces if the value is a string
def _strip_if_string(value: object) -> object:
    return value.strip() if isinstance(value, str) else value





# Reusable field types -------------------------------------------------------------------------------------------------

# Username: trimmed, 3-50 characters, only letters, digits and underscores
Username = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
        pattern=USERNAME_PATTERN,
    ),
    Field(examples=["zk_dev"]),
]


# Email: trimmed, format validated by EmailStr, length-checked, then converted to lowercase
NormalizedEmail = Annotated[
    EmailStr,
    BeforeValidator(_strip_if_string),
    AfterValidator(str.lower),
    Field(
        min_length=EMAIL_MIN_LENGTH,
        max_length=EMAIL_MAX_LENGTH,
        examples=["zk@example.com"]
    ),
]





# Schemas --------------------------------------------------------------------------------------------------------------

# Shared input fields; the auth feature's register schema extends this and adds a password field
class UserBase(BaseModel):
    username: Username
    email: NormalizedEmail


# Public user data returned in responses (hashed_password is intentionally excluded)
class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr





# ----------------------------------------------------------------------------------------------------------------------
