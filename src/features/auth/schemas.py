# External imports -----------------------------------------------------------------------------------------------------
from typing import Annotated, Literal
from pydantic import BaseModel, Field, StringConstraints, AfterValidator

# Internal imports -----------------------------------------------------------------------------------------------------
from src.features.auth.constants import PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH, TOKEN_TYPE_BEARER
from src.features.users.constants import USERNAME_MAX_LENGTH
from src.features.users.schemas import UserBase





# Helper ---------------------------------------------------------------------------------------------------------------

# Reject a password that contains any whitespace (space, tab, newline) anywhere: start, middle or end
def _reject_any_whitespace(value: str) -> str:
    if any(character.isspace() for character in value):
        raise ValueError("Password must not contain spaces.")
    return value





# Reusable field types -------------------------------------------------------------------------------------------------

# Password used at registration: 8-128 characters and no whitespace anywhere
NewPassword = Annotated[
    str,
    Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        examples=["StrongPass123"]
    ),
    AfterValidator(_reject_any_whitespace),
]





# Request schemas ------------------------------------------------------------------------------------------------------

# POST /auth/register: username + email (inherited from UserBase) + password
class RegisterRequest(UserBase):
    password: NewPassword


# POST /auth/login: only basic checks here; the real check is against the database
class LoginRequest(BaseModel):
    username: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=USERNAME_MAX_LENGTH)
    ] = Field(examples=["zk_dev"])
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH, examples=["StrongPass123"])


# POST /auth/refresh and POST /auth/logout
class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)





# Response schemas -----------------------------------------------------------------------------------------------------

# Returned by login and refresh
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = TOKEN_TYPE_BEARER
    expires_in: int = Field(description="Seconds until the access token expires")





#-----------------------------------------------------------------------------------------------------------------------
