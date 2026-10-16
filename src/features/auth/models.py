# External imports -----------------------------------------------------------------------------------------------------
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, String, false, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Internal imports -----------------------------------------------------------------------------------------------------
from src.db.base import SqlalchemyBase
from src.features.auth.constants import JTI_MAX_LENGTH

# Imported only for type checkers (avoids a circular import at runtime)
if TYPE_CHECKING:
    from src.features.users.models import User





# Database model -------------------------------------------------------------------------------------------------------

# Define the 'refresh_tokens' table: one row per issued refresh token
class RefreshToken(SqlalchemyBase):
    __tablename__ = "refresh_tokens"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Unique token id (the 'jti' claim inside the refresh token); indexed for fast lookup
    jti: Mapped[str] = mapped_column(String(JTI_MAX_LENGTH), unique=True, index=True)

    # Owner of the token; ON DELETE CASCADE removes tokens automatically when the user is deleted
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    # Expiry timestamp, stored with time zone
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # True after rotation, logout or reuse detection; a revoked token can never be used again
    revoked: Mapped[bool] = mapped_column(default=False, server_default=false())

    # Set by PostgreSQL itself at insert time
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Many-to-one link back to the owning user
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    # Readable representation for debugging (never includes the token itself)
    def __repr__(self) -> str:
        return f"<RefreshToken id={self.id} user_id={self.user_id} revoked={self.revoked}>"





#-----------------------------------------------------------------------------------------------------------------------
