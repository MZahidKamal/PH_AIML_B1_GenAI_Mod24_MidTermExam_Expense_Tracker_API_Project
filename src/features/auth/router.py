# External imports -----------------------------------------------------------------------------------------------------
from fastapi import APIRouter, status

# Internal imports -----------------------------------------------------------------------------------------------------
from src.features.auth.dependencies import AuthServiceDep
from src.features.auth.schemas import LoginRequest, RefreshTokenRequest, RegisterRequest, TokenResponse
from src.features.users.schemas import UserRead
from src.shared.schemas import MessageResponse





# Router ---------------------------------------------------------------------------------------------------------------

# All routes in this file start with /auth and are grouped under "Authentication" in Swagger
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Register a new user")
async def register(data: RegisterRequest, auth_service: AuthServiceDep):
    return await auth_service.register(data)


@router.post("/login", response_model=TokenResponse, summary="Log in and receive access + refresh tokens")
async def login(data: LoginRequest, auth_service: AuthServiceDep):
    return await auth_service.login(data)


@router.post("/refresh", response_model=TokenResponse, summary="Exchange a refresh token for a new token pair")
async def refresh_tokens(data: RefreshTokenRequest, auth_service: AuthServiceDep):
    return await auth_service.refresh(data.refresh_token)


@router.post("/logout", response_model=MessageResponse, summary="Revoke a refresh token")
async def logout(data: RefreshTokenRequest, auth_service: AuthServiceDep):
    await auth_service.logout(data.refresh_token)
    return MessageResponse(message="Logged out successfully.")





#-----------------------------------------------------------------------------------------------------------------------
