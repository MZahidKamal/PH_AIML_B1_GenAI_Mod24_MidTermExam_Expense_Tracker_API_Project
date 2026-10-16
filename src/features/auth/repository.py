# External imports -----------------------------------------------------------------------------------------------------
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

# Internal imports -----------------------------------------------------------------------------------------------------
from src.features.auth.models import RefreshToken





# Repository -----------------------------------------------------------------------------------------------------------

# Database query layer for the 'refresh_tokens' table
class RefreshTokenRepository:

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    # Store a newly issued refresh token (flush only, the service commits)
    async def create(self, jti: str, user_id: int, expires_at: datetime) -> RefreshToken:
        refresh_token = RefreshToken(jti=jti, user_id=user_id, expires_at=expires_at)
        self.db_session.add(refresh_token)
        await self.db_session.flush()
        return refresh_token

    # Find a token by jti and LOCK its row until the transaction ends (prevents two parallel refreshes)
    async def get_by_jti_for_update(self, jti: str) -> RefreshToken | None:
        return await self.db_session.scalar(
            select(RefreshToken).where(RefreshToken.jti == jti).with_for_update()
        )

    # Mark one token as revoked
    async def revoke(self, refresh_token: RefreshToken) -> None:
        refresh_token.revoked = True
        await self.db_session.flush()

    # Revoke all still-active tokens of a user with a single UPDATE query
    async def revoke_all_for_user(self, user_id: int) -> None:
        await self.db_session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
            .values(revoked=True)
        )





#-----------------------------------------------------------------------------------------------------------------------
