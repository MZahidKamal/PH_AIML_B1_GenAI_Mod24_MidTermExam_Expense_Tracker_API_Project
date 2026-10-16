# External imports -----------------------------------------------------------------------------------------------------
from typing import Annotated
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

# Internal imports -----------------------------------------------------------------------------------------------------
from src.core import security
from src.db.session import get_db
from src.features.auth.exceptions import InvalidToken, NotAuthenticated
from src.features.users.models import User
from src.features.users.repository import UserRepository





# Database session dependency ------------------------------------------------------------------------------------------

# Type alias: any route/dependency that declares 'db_session: DbSession' gets one session per request
DbSession = Annotated[AsyncSession, Depends(get_db)]





# Current user dependency ----------------------------------------------------------------------------------------------

# Reads 'Authorization: Bearer <token>'; auto_error=False lets us return our own consistent 401 error
bearer_scheme = HTTPBearer(auto_error=False, bearerFormat="JWT")


# Resolve the logged-in user from the access token, or raise 401
async def get_current_user(
    db_session: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None:
        raise NotAuthenticated()

    try:
        payload = security.decode_token(credentials.credentials, security.TOKEN_TYPE_ACCESS)
    except jwt.InvalidTokenError as error:
        raise InvalidToken() from error

    # The token may be valid but the user may have been deleted in the meantime
    user = await UserRepository(db_session).get_by_id(int(payload["sub"]))
    if user is None:
        raise InvalidToken()

    return user


# Type alias: any route that declares 'current_user: CurrentUser' is protected automatically
CurrentUser = Annotated[User, Depends(get_current_user)]





#-----------------------------------------------------------------------------------------------------------------------
