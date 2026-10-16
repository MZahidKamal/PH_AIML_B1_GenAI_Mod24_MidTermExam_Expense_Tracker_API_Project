# External imports -----------------------------------------------------------------------------------------------------
from typing import Any
import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# Internal imports -----------------------------------------------------------------------------------------------------
from src.core import security
from src.core.config import env_settings
from src.core.exceptions import AppException
from src.features.auth.exceptions import InvalidCredentials, InvalidToken, RefreshTokenReused
from src.features.auth.repository import RefreshTokenRepository
from src.features.auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from src.features.users.exceptions import EmailAlreadyExists, UsernameAlreadyExists
from src.features.users.models import User
from src.features.users.repository import UserRepository





# Service --------------------------------------------------------------------------------------------------------------

# Business logic for registration, login, token rotation and logout
class AuthService:

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session
        self.user_repository = UserRepository(db_session)
        self.refresh_token_repository = RefreshTokenRepository(db_session)


    # Register --------------------------------------------------------------------------------------------------------

    async def register(self, data: RegisterRequest) -> User:
        # Friendly check if username or email already exists to prevent duplicates early
        if await self.user_repository.get_by_username(data.username):
            raise UsernameAlreadyExists()
        if await self.user_repository.get_by_email(data.email):
            raise EmailAlreadyExists()

        # Hash the password, create the user record, and handle database integrity conflicts safely
        hashed_password = await security.hash_password(data.password)

        try:
            user = await self.user_repository.create(
                username=data.username, email=data.email, hashed_password=hashed_password
            )
            await self.db_session.commit()
        except IntegrityError as error:
            # Two parallel registrations with the same username/email can both pass the early checks;
            # but the database's unique index stops the second one, and we turn that into a clean 409 error
            await self.db_session.rollback()
            raise self._duplicate_user_error(error) from error

        return user


    # Login -----------------------------------------------------------------------------------------------------------

    async def login(self, data: LoginRequest) -> TokenResponse:
        # Fetch user from repository using the provided 'username'
        user = await self.user_repository.get_by_username(data.username)

        # Run dummy password verification if user does not exist, to prevent timing attacks, then raise 'InvalidCredentials'
        if user is None:
            # Spend the same time as a real check, so attackers cannot discover usernames by timing
            await security.verify_dummy_password(data.password)
            raise InvalidCredentials()

        # Verify the provided 'password' against the stored 'hashed_password'
        if not await security.verify_password(user.hashed_password, data.password):
            raise InvalidCredentials()

        # Issue a new token pair for the authenticated user, commit the database transaction, and return the response
        token_response = await self._issue_token_pair(user.id)
        await self.db_session.commit()
        return token_response


    # Refresh (rotation + reuse detection) ----------------------------------------------------------------------------

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = self._decode_or_raise(refresh_token, security.TOKEN_TYPE_REFRESH)
        stored_token = await self.refresh_token_repository.get_by_jti_for_update(payload["jti"])

        # Token was never issued by us, or belongs to someone else
        if stored_token is None or stored_token.user_id != int(payload["sub"]):
            raise InvalidToken()

        # An already-revoked token is being used again: it was probably stolen -> revoke every session of this user
        if stored_token.revoked:
            await self.refresh_token_repository.revoke_all_for_user(stored_token.user_id)
            await self.db_session.commit()
            raise RefreshTokenReused()

        # Rotation: the old token dies, a brand-new pair is issued, both in one transaction
        await self.refresh_token_repository.revoke(stored_token)
        token_response = await self._issue_token_pair(stored_token.user_id)
        await self.db_session.commit()
        return token_response


    # Logout ----------------------------------------------------------------------------------------------------------

    async def logout(self, refresh_token: str) -> None:
        payload = self._decode_or_raise(refresh_token, security.TOKEN_TYPE_REFRESH)
        stored_token = await self.refresh_token_repository.get_by_jti_for_update(payload["jti"])

        # Idempotent: logging out twice is not an error
        if stored_token is not None and not stored_token.revoked:
            await self.refresh_token_repository.revoke(stored_token)
            await self.db_session.commit()


    # Private helpers -------------------------------------------------------------------------------------------------

    # Create an access + refresh token pair and store the refresh token's jti (no commit here)
    async def _issue_token_pair(self, user_id: int) -> TokenResponse:
        access_token = security.create_access_token(user_id)
        refresh_token, jti, expires_at = security.create_refresh_token(user_id)
        await self.refresh_token_repository.create(jti=jti, user_id=user_id, expires_at=expires_at)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=env_settings.access_token_expire_minutes * 60,
        )

    # Decode a token; any JWT problem (bad signature, expired, wrong type, ...) becomes our InvalidToken error
    @staticmethod
    def _decode_or_raise(token: str, expected_type: str) -> dict[str, Any]:
        try:
            return security.decode_token(token, expected_type)
        except jwt.InvalidTokenError as error:
            raise InvalidToken() from error

    # Decide which duplicate error to raise, using the constraint name from PostgreSQL (thanks to our naming convention)
    @staticmethod
    def _duplicate_user_error(error: IntegrityError) -> AppException:
        diagnostics = getattr(error.orig, "diag", None)
        constraint_name = getattr(diagnostics, "constraint_name", None) or ""
        if "email" in constraint_name:
            return EmailAlreadyExists()
        return UsernameAlreadyExists()





#-----------------------------------------------------------------------------------------------------------------------
