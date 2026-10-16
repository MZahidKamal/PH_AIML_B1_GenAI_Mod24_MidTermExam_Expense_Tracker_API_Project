# External imports -----------------------------------------------------------------------------------------------------
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Internal imports -----------------------------------------------------------------------------------------------------
from src.features.users.models import User





# Repository -----------------------------------------------------------------------------------------------------------

# Database query layer for the 'users' table: only queries, no business rules, no HTTP knowledge
class UserRepository:

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    # Find a user by primary key (returns None if not found)
    async def get_by_id(self, user_id: int) -> User | None:
        return await self.db_session.get(User, user_id)

    # Find a user by username (returns None if not found)
    async def get_by_username(self, username: str) -> User | None:
        return await self.db_session.scalar(select(User).where(User.username == username))

    # Find a user by email (returns None if not found)
    async def get_by_email(self, email: str) -> User | None:
        return await self.db_session.scalar(select(User).where(User.email == email))

    # Add a new user; flush sends the INSERT so the database-generated id is available, but does NOT commit
    async def create(self, username: str, email: str, hashed_password: str) -> User:
        user = User(username=username, email=email, hashed_password=hashed_password)
        self.db_session.add(user)
        await self.db_session.flush()
        return user





# ----------------------------------------------------------------------------------------------------------------------
