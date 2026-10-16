# External imports -----------------------------------------------------------------------------------------------------
from typing import Annotated
from fastapi import Depends

# Internal imports -----------------------------------------------------------------------------------------------------
from src.api.v1.deps import DbSession
from src.features.auth.service import AuthService





# Feature dependencies -------------------------------------------------------------------------------------------------

# Build an AuthService with this request's database session
async def get_auth_service(db_session: DbSession) -> AuthService:
    return AuthService(db_session)


# Type alias used in the router
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]





#-----------------------------------------------------------------------------------------------------------------------
